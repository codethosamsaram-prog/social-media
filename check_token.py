"""Can the stored Instagram token still publish? Never prints the token.

    python check_token.py     exit 1 if it can't, or if it runs out within WARN_DAYS

The pipeline calls publish_problem() before rendering, and token-check.yml runs this every morning
before the first reel, so a dead token raises an alert instead of silently costing a day's posts.
"""

from __future__ import annotations

import sys
import time

import httpx

from config import settings

WARN_DAYS = 14
# Token or permission errors. Anything else (Meta hiccups, rate limits) may clear by itself.
FATAL_CODES = {10, 102, 190, 200}


def _get(url: str, **params: str) -> dict:
    """Empty on network trouble. httpx exceptions contain the URL, so they are never shown."""
    try:
        resp = httpx.get(url, params={**params, "access_token": settings.instagram_access_token}, timeout=30)
        return resp.json()
    except (httpx.HTTPError, ValueError):
        return {}


def publish_problem() -> str | None:
    """Why this token can't publish, or None. An unreachable Meta is not a verdict on the token."""
    settings.require("instagram_access_token", "instagram_user_id")
    data = _get(f"{settings.graph_base}/{settings.instagram_user_id}/content_publishing_limit")
    err = data.get("error") or {}
    if err.get("code") in FATAL_CODES:
        return f"Instagram token can't publish: {err.get('message')}"
    return None


def expiry_problem() -> str | None:
    """Facebook-type tokens report their expiry dates; 0 means that date never comes."""
    if settings.instagram_access_token.startswith("IG"):
        return None  # refresh-token.yml renews these
    info = _get(f"{settings.graph_base}/debug_token", input_token=settings.instagram_access_token).get("data") or {}
    limit = time.time() + WARN_DAYS * 86400
    for field, label in (("expires_at", "token"), ("data_access_expires_at", "data access")):
        when = info.get(field) or 0
        if when and when < limit:
            day = time.strftime("%Y-%m-%d", time.gmtime(when))
            return f"Instagram {label} runs out on {day}: generate a new Page token and store it"
    return None


def main() -> int:
    problem = publish_problem() or expiry_problem()
    print(problem or "Instagram token OK")
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main())
