"""Should this tick post a reel? Compares what is due by now (IST) with what actually went up today.

GitHub runs this every 15 minutes. Late or dropped schedules and failed runs therefore fix themselves:
the next tick sees the shortfall and posts. Writes go=true|false and kind=dev|hiring to GITHUB_OUTPUT.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys

from check_token import _get, publish_problem
from config import settings

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
# The daily mix (user's request 2026-11-11): 2 DSA, 2 interview concepts, 1 quiz, 1 hiring. No trending repos:
# those only post when a category's queue is empty (auto_pipeline.next_for falls back).
SLOTS = ((8, "dsa"), (11, "interview"), (13, "hiring"), (15, "quiz"), (18, "dsa"), (21, "interview"))
# Start this early so a late GitHub run still makes its slot. auto_pipeline holds the post until the slot time.
LEAD = dt.timedelta(minutes=30)


def slot_time(now: dt.datetime, hour: int) -> dt.datetime:
    return now.replace(hour=hour, minute=0, second=0, microsecond=0)


def decide(now: dt.datetime, posted: int, done: list[str]) -> str | None:
    """The kind of reel to start now, or None when today is on track. `done` is today's published categories
    from the queue; the first due slot whose kind is still short wins, so a missed slot is made up in kind."""
    due = [kind for hour, kind in SLOTS if now + LEAD >= slot_time(now, hour)]
    if posted >= len(due):
        return None
    left = list(done)
    for kind in due:
        if kind in left:
            left.remove(kind)
        else:
            return kind
    return SLOTS[min(posted, len(SLOTS) - 1)][1]  # the queue lost a record: go by position


def _ist_date(stamp: str | None) -> dt.date | None:
    try:
        return dt.datetime.fromisoformat((stamp or "").replace("+0000", "+00:00")).astimezone(IST).date()
    except ValueError:
        return None


def instagram_count(today: dt.date) -> int | None:
    """Our reels on Instagram today, None if Meta didn't answer. Every caption we write starts "Day N"."""
    data = _get(f"{settings.graph_base}/{settings.instagram_user_id}/media", fields="timestamp,caption", limit="25")
    if "data" not in data:
        return None
    return sum(1 for m in data["data"] if _ist_date(m.get("timestamp")) == today
               and (m.get("caption") or "").startswith("Day "))


def queue_published(today: dt.date) -> list[dict]:
    items = json.loads(settings.queue_file.read_text(encoding="utf-8")).get("items", [])
    return [i for i in items if i.get("status") == "published" and _ist_date(i.get("published_at")) == today]


def main() -> int:
    problem = publish_problem()
    if problem:
        print(problem)
        return 1
    now = dt.datetime.now(IST)
    recorded = queue_published(now.date())
    # Instagram catches a post whose queue update never got committed; the queue covers Meta being down.
    posted = max(instagram_count(now.date()) or 0, len(recorded))
    kind = decide(now, posted, [i.get("category") for i in recorded])
    post_at = slot_time(now, SLOTS[posted][0]).isoformat() if kind else ""
    print(f"{now:%H:%M} IST, {posted} posted today: {f'{kind} reel for {post_at}' if kind else 'on track'}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"go={'true' if kind else 'false'}\nkind={kind or ''}\npost_at={post_at}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
