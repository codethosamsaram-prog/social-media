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
from pathlib import Path

import httpx

import config  # noqa: F401 - loads .env into os.environ

ENV_FILE = Path(__file__).parent / ".env"
HOST = "https://graph.instagram.com"


def get(path: str, **params: str) -> dict:
    """Errors are reduced to Meta's message: an httpx exception would include the token in its URL."""
    try:
        resp = httpx.get(f"{HOST}/{path}", params=params, timeout=30)
        data = resp.json()
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Instagram token and store it for automation.")
    parser.add_argument("--push", metavar="OWNER/REPO", help="also store secrets in Vercel and GitHub")
    args = parser.parse_args()

    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    uid = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if not token or not uid:
        print("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID must both be in .env")
        return 1
    if not token.startswith("IGAA"):
        print("This token does not start with IGAA, so it is not an Instagram Login token. Generate one under "
              "Instagram > API setup with Instagram login.")
        return 1

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
