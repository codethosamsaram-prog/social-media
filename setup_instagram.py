"""One-time go-live setup. Reads secrets from .env and never prints them.

Put these in .env first:
    INSTAGRAM_ACCESS_TOKEN=...      required (short-lived is fine if the app secret is present)
    INSTAGRAM_USER_ID=...           required
    INSTAGRAM_APP_SECRET=...        turns a short-lived token into a 60-day one; verifies webhooks
    GH_PAT=...                      optional, lets the weekly job renew the token
    VERCEL_TOKEN=...                optional, lets that job update Vercel too

    python setup_instagram.py               check the token and upgrade it to long-lived
    python setup_instagram.py --push REPO   also store everything in Vercel and GitHub (owner/name)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

import config  # noqa: F401 - loads .env into os.environ

ENV_FILE = Path(__file__).parent / ".env"
HOST = "https://graph.instagram.com"
HOST_FB = "https://graph.facebook.com/v23.0"


def get(path: str, host: str = HOST, **params: str) -> dict:
    """Errors are reduced to Meta's message: an httpx exception would include the token in its URL."""
    for attempt in range(5):
        try:
            resp = httpx.get(f"{host}/{path}", params=params, timeout=30)
            data = resp.json()
            break
        except httpx.TransportError as exc:  # connection drops to Meta are common and short-lived
            if attempt == 4:
                return {"error": {"message": f"{type(exc).__name__}, check your internet connection and retry"}}
            time.sleep(3 * (attempt + 1))
        except (httpx.HTTPError, ValueError) as exc:
            return {"error": {"message": type(exc).__name__}}
    return data if resp.status_code < 400 else {"error": data.get("error") or {"message": f"HTTP {resp.status_code}"}}


def save_env(key: str, value: str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    lines = [ln for ln in lines if not ln.startswith(f"{key}=")] + [f"{key}={value}"]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def store(cmd: list[str], value: str, label: str) -> bool:
    exe = shutil.which(cmd[0])
    if not exe:
        print(f"  {label}: {cmd[0]} is not installed")
        return False
    proc = subprocess.run([exe, *cmd[1:]], input=value, text=True, capture_output=True, check=False)
    print(f"  {label}: {'saved' if proc.returncode == 0 else 'FAILED, exit ' + str(proc.returncode)}")
    return proc.returncode == 0


def push(repo: str, token: str, uid: str, secret: str) -> bool:
    ok = True
    vercel = {"INSTAGRAM_ACCESS_TOKEN": token, "INSTAGRAM_USER_ID": uid, "META_APP_SECRET": secret}
    for name, value in vercel.items():
        if value:
            ok &= store(["npx", "--yes", "vercel", "env", "add", name, "production", "--force"], value, f"Vercel {name}")

    link = json.loads((Path(__file__).parent / ".vercel" / "project.json").read_text(encoding="utf-8"))
    github = {
        "INSTAGRAM_ACCESS_TOKEN": token,
        "INSTAGRAM_USER_ID": uid,
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "GH_PAT": os.environ.get("GH_PAT", ""),
        "VERCEL_TOKEN": os.environ.get("VERCEL_TOKEN", ""),
        "VERCEL_ORG_ID": link.get("orgId", ""),
        "VERCEL_PROJECT_ID": link.get("projectId", ""),
    }
    for name, value in github.items():
        if value:
            ok &= store(["gh", "secret", "set", name, "--repo", repo], value, f"GitHub {name}")
    return ok


def token_info(token: str, secret: str) -> dict:
    app = get("app", HOST_FB, fields="id", access_token=token).get("id")
    if not app or not secret:
        return {}
    return get("debug_token", HOST_FB, input_token=token, access_token=f"{app}|{secret}").get("data", {})


def make_dm_token(token: str, secret: str) -> int:
    """DMs go out as the Page. A Page token taken from a long-lived user token does not expire."""
    app = get("app", HOST_FB, fields="id", access_token=token).get("id")
    longer = get("oauth/access_token", HOST_FB, grant_type="fb_exchange_token", client_id=app,
                 client_secret=secret, fb_exchange_token=token)
    if not longer.get("access_token"):
        print(f"Could not extend the token: {longer.get('error', {}).get('message')}")
        return 1
    pages = get("me/accounts", HOST_FB, fields="id,name,access_token,instagram_business_account{id}",
                access_token=longer["access_token"]).get("data", [])
    page = next((p for p in pages if p.get("instagram_business_account")), None)
    if not page or not page.get("access_token"):
        print(f"No Page linked to Instagram found (pages seen: {len(pages)})")
        return 1
    info = token_info(page["access_token"], secret)
    print(f"Page: {page['name']} | token type: {info.get('type')} | expires_at: {info.get('expires_at')} (0 = never)")
    print(f"Permissions: {info.get('scopes')}")
    save_env("PAGE_ACCESS_TOKEN", page["access_token"])
    save_env("FACEBOOK_PAGE_ID", page["id"])
    print("Saved PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env")
    return 0


def push_dm() -> int:
    """Vercel only: --push-posting decides what GitHub posts with."""
    page_token = os.environ.get("PAGE_ACCESS_TOKEN", "").strip()
    page_id = os.environ.get("FACEBOOK_PAGE_ID", "").strip()
    if not page_token or not page_id:
        print("Run --dm-token first")
        return 1
    ok = store(["npx", "--yes", "vercel", "env", "add", "INSTAGRAM_ACCESS_TOKEN", "production", "--force"],
               page_token, "Vercel INSTAGRAM_ACCESS_TOKEN (Page token)")
    ok &= store(["npx", "--yes", "vercel", "env", "add", "FACEBOOK_PAGE_ID", "production", "--force"],
                page_id, "Vercel FACEBOOK_PAGE_ID")
    return 0 if ok else 1


def unusable_for_posting(token: str, secret: str) -> str | None:
    """Unattended posting needs a token Meta confirms is valid and never expires. An unknown answer is a no."""
    info = token_info(token, secret)
    if not info.get("is_valid"):
        return "it is invalid or expired, or Meta could not confirm it"
    if info.get("expires_at") != 0:
        return "it expires, so posting would stop when it does"
    return None


def push_posting(repo: str, uid: str, secret: str) -> int:
    """GitHub only: post with the Page token after proving it can publish."""
    token = os.environ.get("PAGE_ACCESS_TOKEN", "").strip()
    if not token:
        print("Run --dm-token first")
        return 1
    reason = unusable_for_posting(token, secret)
    if reason:
        print(f"Refusing to store this token: {reason}.")
        return 1
    limit = get(f"{uid}/content_publishing_limit", HOST_FB, access_token=token)
    if "error" in limit:
        print(f"Token cannot publish: {limit['error'].get('message')}")
        return 1
    return 0 if store(["gh", "secret", "set", "INSTAGRAM_ACCESS_TOKEN", "--repo", repo], token,
                      "GitHub INSTAGRAM_ACCESS_TOKEN (Page token)") else 1


def facebook_token(args: argparse.Namespace, token: str, uid: str, secret: str) -> int:
    """Facebook Login (EAA...) tokens only count if they can reach the Instagram account they will post to."""
    reason = unusable_for_posting(token, secret) if args.push else None
    if reason:
        print(f"Refusing to store this token: {reason}.")
        return 1
    if not uid.isdigit():
        pages = get("me/accounts", HOST_FB, fields="instagram_business_account{id,username}", access_token=token)
        found = [p["instagram_business_account"] for p in pages.get("data", []) if p.get("instagram_business_account")]
        if not found:
            print("INSTAGRAM_USER_ID must be the numeric ID, and this token lists no linked Instagram account "
                  f"(pages found: {len(pages.get('data', []))}). It needs pages_show_list and "
                  "pages_read_engagement, with the Instagram account linked to a Facebook Page.")
            return 1
        uid = str(found[0]["id"])
        save_env("INSTAGRAM_USER_ID", uid)

    account = get(uid, HOST_FB, fields="id,username", access_token=token)
    if "error" in account:
        print(f"Token cannot read Instagram account {uid}: {account['error'].get('message')}")
        return 1
    limit = get(f"{uid}/content_publishing_limit", HOST_FB, access_token=token)
    if "error" in limit:
        print(f"Token cannot publish for @{account.get('username')}: {limit['error'].get('message')}")
        return 1
    print(f"Token works and can publish for @{account.get('username')}")
    if args.push:
        return 0 if push(args.push, token, uid, secret) else 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Instagram token and store it for automation.")
    parser.add_argument("--push", metavar="OWNER/REPO", help="also store secrets in Vercel and GitHub")
    parser.add_argument("--push-infra", metavar="OWNER/REPO", help="store only the non-Instagram secrets, then stop")
    parser.add_argument("--dm-token", action="store_true", help="turn a user token into a Page token for DMs, in .env")
    parser.add_argument("--push-dm", action="store_true", help="store the Page token and Page ID in Vercel only")
    parser.add_argument("--push-posting", metavar="OWNER/REPO", help="check the Page token, then post with it from GitHub")
    args = parser.parse_args()

    if args.push_infra:
        # Everything except Instagram, safe before the token works: a bad token would burn queue retries.
        return 0 if push(args.push_infra, "", "", "") else 1

    if args.push_dm:
        return push_dm()

    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    uid = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if args.push_posting:
        return push_posting(args.push_posting, uid, secret)
    if args.dm_token:
        return make_dm_token(token, secret)
    if not token or not uid:
        print("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID must both be in .env")
        return 1
    if token.startswith("EAA"):
        return facebook_token(args, token, uid, secret)

    me = get("me", fields="user_id,username", access_token=token)
    if "error" in me:
        print(f"Token rejected: {me['error'].get('message')}")
        return 1
    print(f"Token works for @{me.get('username')}")
    if me.get("user_id") and str(me["user_id"]) != uid:
        print("INSTAGRAM_USER_ID in .env differs from this token's account; using the token's ID")
        uid = str(me["user_id"])
        save_env("INSTAGRAM_USER_ID", uid)

    if secret:
        longer = get("access_token", grant_type="ig_exchange_token", client_secret=secret, access_token=token)
        if longer.get("access_token"):
            token = longer["access_token"]
            save_env("INSTAGRAM_ACCESS_TOKEN", token)
            print(f"Upgraded to a long-lived token, valid for {int(longer.get('expires_in', 0)) // 86400} days")
        else:
            print(f"Token kept as it is (it may already be long-lived): {longer.get('error', {}).get('message')}")
    else:
        print("No INSTAGRAM_APP_SECRET: a short-lived token would stop working within about an hour")

    if args.push:
        return 0 if push(args.push, token, uid, secret) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
