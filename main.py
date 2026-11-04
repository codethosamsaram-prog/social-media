"""Meta Webhook & Auto-DM microservice + Command Dashboard API.

Routes
  GET  /webhook                      Meta hub.challenge verification
  POST /webhook                      Instagram comment events -> keyword -> private-reply DM
  GET  /dashboard                    static/dashboard.html
  GET  /api/stats                    metric cards + growth series
  GET  /api/queue                    reel queue (filter ?category=&status=)
  POST /api/queue                    add a topic
  DELETE /api/queue/{id}             remove a topic
  POST /api/queue/{id}/render        render (and optionally publish) in a worker thread
  POST /api/fetch-trending           run the Topic Discovery Engine
  GET  /api/logs                     recent log events (polling fallback)
  POST /api/simulate-comment         dry-run a fake comment through the webhook logic
  WS   /ws/logs                      live log stream
  GET  /api/health                   liveness probe

Run:  uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import importlib.util
import json
import os
import re
import shutil
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

import topic_fetcher as tq
from config import SERVERLESS, settings

# ---------------------------------------------------------------------------
# Live log hub (WebSocket fan-out + backlog)
# ---------------------------------------------------------------------------


class LogHub:
    def __init__(self) -> None:
        self.backlog: deque[dict[str, Any]] = deque(maxlen=400)
        self.clients: set[WebSocket] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    async def emit(self, level: str, message: str, **meta: Any) -> None:
        event = {"id": uuid.uuid4().hex[:12], "ts": tq.now_iso(), "level": level, "message": message, **meta}
        self.backlog.append(event)
        _console(f"[{level.upper():>7}] {message}")
        for ws in list(self.clients):
            try:
                await ws.send_json(event)
            except Exception:  # noqa: BLE001 - client went away
                self.clients.discard(ws)

    def emit_threadsafe(self, level: str, message: str, **meta: Any) -> None:
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.emit(level, message, **meta), self.loop)
        else:
            _console(f"[{level.upper():>7}] {message}")


def _console(line: str) -> None:
    """print() that survives emoji in comments on non-UTF-8 consoles (Windows cp1252)."""
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)


hub = LogHub()

# ---------------------------------------------------------------------------
# Persistent state (events, dedupe, cooldowns, insights cache)
# ---------------------------------------------------------------------------


class StateStore:
    MAX_EVENTS = 4000
    MAX_SEEN = 5000

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.data: dict[str, Any] = {"events": [], "seen_comments": [], "cooldowns": {}, "insights": {}}
        if path.exists():
            try:
                self.data.update(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        self._seen = set(self.data["seen_comments"])

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def mark_comment(self, comment_id: str) -> bool:
        """True if this comment is new (and records it), False if already handled."""
        with self.lock:
            if comment_id in self._seen:
                return False
            self._seen.add(comment_id)
            seen = self.data["seen_comments"]
            seen.append(comment_id)
            if len(seen) > self.MAX_SEEN:
                for old in seen[: len(seen) - self.MAX_SEEN]:
                    self._seen.discard(old)
                del seen[: len(seen) - self.MAX_SEEN]
            self._save()
            return True

    def record(self, kind: str, **fields: Any) -> None:
        with self.lock:
            events = self.data["events"]
            events.append({"kind": kind, "ts": tq.now_iso(), **fields})
            if len(events) > self.MAX_EVENTS:
                del events[: len(events) - self.MAX_EVENTS]
            self._save()

    def claim_cooldown(self, user_id: str, item_id: str, hours: int) -> bool:
        """True if the user may get this item's DM now (and starts the cooldown)."""
        if not user_id or hours <= 0:
            return True
        key = f"{user_id}:{item_id}"
        now = time.time()
        with self.lock:
            cooldowns = self.data["cooldowns"]
            if now - cooldowns.get(key, 0) < hours * 3600:
                return False
            cooldowns[key] = now
            for k in [k for k, v in cooldowns.items() if now - v > 7 * 86400]:
                del cooldowns[k]
            self._save()
            return True

    def set_insights(self, media_id: str, metrics: dict[str, Any]) -> None:
        with self.lock:
            self.data["insights"][media_id] = {**metrics, "fetched_at": tq.now_iso()}
            self._save()

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return json.loads(json.dumps(self.data))


state = StateStore(settings.data_dir / "state.json")

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_s: float) -> None:
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str) -> float:
        """0 if allowed, otherwise seconds until the next slot frees up."""
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return self.window - (now - q[0])
            q.append(now)
            return 0.0


class TokenBucket:
    """Outbound DM throttle so the account stays under Meta's automated-DM limits."""

    def __init__(self, per_hour: int) -> None:
        self.capacity = float(min(per_hour, 20))
        self.tokens = self.capacity
        self.rate = per_hour / 3600.0
        self.updated = time.monotonic()

    async def acquire(self) -> None:
        while True:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens >= 1:
                self.tokens -= 1
                return
            await asyncio.sleep((1 - self.tokens) / self.rate)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int, window_s: float, bucket: str):
    limiter = SlidingWindowLimiter(limit, window_s)

    async def dependency(request: Request) -> None:
        retry = limiter.check(f"{bucket}:{client_ip(request)}")
        if retry:
            raise HTTPException(429, f"Rate limit exceeded for {bucket}",
                                headers={"Retry-After": str(int(retry) + 1)})

    return dependency


def require_dashboard_token(request: Request) -> None:
    if not settings.dashboard_token:
        return
    supplied = request.headers.get("x-dashboard-token") or request.query_params.get("token") or ""
    if not hmac.compare_digest(supplied, settings.dashboard_token):
        raise HTTPException(401, "Dashboard token required")


api_limit = rate_limit(120, 60, "api")
webhook_limit = rate_limit(1200, 60, "webhook")
heavy_limit = rate_limit(6, 600, "heavy")

# ---------------------------------------------------------------------------
# Meta Graph API (async)
# ---------------------------------------------------------------------------


class GraphAPIError(RuntimeError):
    def __init__(self, status: int, error: dict[str, Any]) -> None:
        self.status, self.error = status, error
        self.code = error.get("code")
        super().__init__(f"Graph API {status} (code {self.code}): {error.get('message', 'unknown error')}")

    @property
    def retryable(self) -> bool:
        return self.status >= 500 or self.status == 429 or self.code in {1, 2, 4, 17, 32, 613}


http: httpx.AsyncClient | None = None


async def graph(method: str, path: str, *, params: dict[str, Any] | None = None,
                body: dict[str, Any] | None = None) -> dict[str, Any]:
    global http
    if http is None:  # serverless platforms may skip the lifespan hook
        http = httpx.AsyncClient(timeout=30)
    query = {**(params or {}), "access_token": settings.instagram_access_token}
    resp = await http.request(method, f"{settings.graph_base}/{path.lstrip('/')}", params=query, json=body)
    try:
        data = resp.json()
    except ValueError:
        data = {"error": {"message": resp.text[:300]}}
    if resp.status_code >= 400 or "error" in data:
        raise GraphAPIError(resp.status_code, data.get("error", {}))
    return data


def messages_path() -> str:
    # The Instagram ID works on both hosts; the Page route would also need pages_messaging.
    return f"{settings.instagram_user_id}/messages"


# ---------------------------------------------------------------------------
# Keyword resolution + DM copy
# ---------------------------------------------------------------------------

GENERIC_TRIGGERS = {"LINK", "CODE", "SEND", "DM"}

_queue_cache: dict[str, Any] = {"mtime": None, "items": []}


def queue_items() -> list[dict[str, Any]]:
    try:
        mtime = settings.queue_file.stat().st_mtime
    except FileNotFoundError:
        return []
    if _queue_cache["mtime"] != mtime:
        _queue_cache["items"] = tq.load_queue()
        _queue_cache["mtime"] = mtime
    return _queue_cache["items"]


def _freshest(items: list[dict[str, Any]]) -> dict[str, Any]:
    return max(items, key=lambda i: (i.get("status") == "published", i.get("published_at") or "",
                                     i.get("created_at") or ""))


def resolve_item(text: str, media_id: str | None) -> tuple[dict[str, Any] | None, str | None]:
    """Map a comment to the queue item whose link should be DM'd. Returns (item, matched keyword)."""
    tokens = set(re.findall(r"[A-Z0-9]+", text.upper()))
    if not tokens:
        return None, None
    items = [i for i in queue_items() if i.get("link")]
    on_media = [i for i in items if media_id and i.get("ig_media_id") == media_id]
    for item in on_media:
        if item["keyword"] in tokens:
            return item, item["keyword"]
    for item in on_media:
        hit = tokens & (GENERIC_TRIGGERS | set(tq.CATEGORY_KEYWORDS))
        if hit:
            return item, sorted(hit)[0]
    by_keyword = [i for i in items if i["keyword"] in tokens]
    if by_keyword:
        item = _freshest(by_keyword)
        return item, item["keyword"]
    for token in sorted(tokens):
        category = tq.CATEGORY_KEYWORDS.get(token)
        candidates = [i for i in items if i.get("category") == category]
        if candidates:
            return _freshest(candidates), token
    return None, None


def build_dm(item: dict[str, Any]) -> str:
    if item.get("links"):
        lines = "\n".join(f"👉 {link['label']}: {link['url']}" for link in item["links"])
        return (
            f"Hey dev! 🚀 Thanks for commenting on @{settings.account_handle}! Here are the careers pages:\n\n"
            f"{lines}\n\nAll the best with your applications! Hit FOLLOW for a new hiring list every day. 💼"
        )
    return (
        f"Hey dev! 🚀 Thanks for commenting on @{settings.account_handle}! "
        f"If you're following us, here is your instant code link: {item['link']}\n\n"
        f"Make sure to hit the FOLLOW button for daily hacks!"
    )


# ---------------------------------------------------------------------------
# DM worker
# ---------------------------------------------------------------------------


@dataclass
class DMJob:
    comment_id: str
    user_id: str
    username: str
    item_id: str
    keyword: str
    text: str
    media_id: str | None


dm_queue: asyncio.Queue[DMJob] | None = None
dm_bucket = TokenBucket(settings.dm_rate_per_hour)


async def send_dm(job: DMJob) -> None:
    for attempt in range(1, 4):
        try:
            await graph("POST", messages_path(),
                        body={"recipient": {"comment_id": job.comment_id}, "message": {"text": job.text}})
            state.record("dm_sent", user=job.username, user_id=job.user_id, item_id=job.item_id,
                         keyword=job.keyword, comment_id=job.comment_id, media_id=job.media_id)
            await hub.emit("success", f"DM sent to @{job.username} ({job.keyword})", item_id=job.item_id)
            break
        except (GraphAPIError, httpx.HTTPError) as exc:
            retryable = isinstance(exc, httpx.HTTPError) or exc.retryable
            if attempt < 3 and retryable:
                await hub.emit("warn", f"DM to @{job.username} failed (attempt {attempt}), retrying: {exc}")
                await asyncio.sleep(2 ** attempt * 3)
                continue
            state.record("dm_failed", user=job.username, item_id=job.item_id, keyword=job.keyword, error=str(exc))
            await hub.emit("error", f"DM to @{job.username} failed: {exc}")
            return
    if settings.public_reply_enabled:
        try:
            await graph("POST", f"{job.comment_id}/replies", params={"message": settings.public_reply_text})
        except (GraphAPIError, httpx.HTTPError) as exc:
            await hub.emit("warn", f"Public reply failed: {exc}")


async def dm_worker() -> None:
    assert dm_queue is not None
    while True:
        job = await dm_queue.get()
        try:
            await dm_bucket.acquire()
            await send_dm(job)
        except Exception as exc:  # noqa: BLE001 - never let the worker die
            await hub.emit("error", f"DM worker error: {exc}")
        finally:
            dm_queue.task_done()


# ---------------------------------------------------------------------------
# Webhook processing
# ---------------------------------------------------------------------------


async def handle_comment(value: dict[str, Any], dry_run: bool = False) -> None:
    comment_id = str(value.get("id") or "")
    text = value.get("text") or ""
    sender = value.get("from") or {}
    user_id, username = str(sender.get("id") or ""), sender.get("username") or "unknown"
    media_id = (value.get("media") or {}).get("id")
    tag = "[SIMULATED] " if dry_run else ""
    if not comment_id:
        return
    if user_id == settings.instagram_user_id or username.lower() == settings.account_handle.lower():
        return  # our own replies
    if not dry_run and not state.mark_comment(comment_id):
        await hub.emit("info", f"Duplicate delivery for comment {comment_id}, skipped")
        return

    await hub.emit("comment", f"{tag}@{username}: {text[:140]}", media_id=media_id)
    if not dry_run:
        state.record("comment", user=username, user_id=user_id, media_id=media_id, comment_id=comment_id)

    item, keyword = resolve_item(text, media_id)
    if not item:
        await hub.emit("info", f"{tag}No trigger keyword in comment from @{username}")
        return
    if not dry_run:
        state.record("keyword_hit", user=username, item_id=item["id"], keyword=keyword)
        if not state.claim_cooldown(user_id, item["id"], settings.dm_cooldown_hours):
            await hub.emit("info", f"@{username} already got the {keyword} link recently, skipped")
            return

    job = DMJob(comment_id, user_id, username, item["id"], keyword or item["keyword"], build_dm(item), media_id)
    if dry_run:
        await hub.emit("dm", f"{tag}Would DM @{username} -> {item['link']} ({job.keyword})", item_id=item["id"])
        return
    if not settings.instagram_ready:
        state.record("dm_failed", user=username, item_id=item["id"], keyword=job.keyword, error="credentials missing")
        await hub.emit("error", "INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ID not set, cannot DM")
        return
    if SERVERLESS or dm_queue is None:
        # No background worker survives between serverless invocations: send now, inside the request.
        await send_dm(job)
        return
    await dm_queue.put(job)
    await hub.emit("dm", f"Queued DM for @{username} -> {job.keyword} (pending {dm_queue.qsize()})",
                   item_id=item["id"])


async def process_payload(payload: dict[str, Any], dry_run: bool = False) -> int:
    handled = 0
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            if change.get("field") == "comments" and isinstance(change.get("value"), dict):
                await handle_comment(change["value"], dry_run)
                handled += 1
        if entry.get("messaging"):
            await hub.emit("info", f"Received {len(entry['messaging'])} messaging event(s) (not handled)")
    return handled


# ---------------------------------------------------------------------------
# Insights refresher
# ---------------------------------------------------------------------------

INSIGHT_METRICS = "views,reach,likes,comments,shares,saved"


async def refresh_insights() -> int:
    if not settings.instagram_ready:
        return 0
    refreshed = 0
    for item in queue_items():
        media_id = item.get("ig_media_id")
        if not media_id:
            continue
        try:
            data = await graph("GET", f"{media_id}/insights", params={"metric": INSIGHT_METRICS})
        except (GraphAPIError, httpx.HTTPError) as exc:
            await hub.emit("warn", f"Insights for {media_id} failed: {exc}")
            continue
        metrics: dict[str, Any] = {"item_id": item["id"]}
        for metric in data.get("data", []):
            if metric.get("total_value"):
                metrics[metric["name"]] = metric["total_value"].get("value", 0)
            elif metric.get("values"):
                metrics[metric["name"]] = metric["values"][0].get("value", 0)
        state.set_insights(media_id, metrics)
        refreshed += 1
    return refreshed


async def insights_loop() -> None:
    while True:
        try:
            count = await refresh_insights()
            if count:
                await hub.emit("info", f"Refreshed insights for {count} reel(s)")
        except Exception as exc:  # noqa: BLE001
            await hub.emit("warn", f"Insights refresh error: {exc}")
        await asyncio.sleep(1800)


# ---------------------------------------------------------------------------
# Background jobs (render / discovery) in worker threads
# ---------------------------------------------------------------------------

render_lock = threading.Lock()
render_state: dict[str, Any] = {"running": False, "item_id": None, "started_at": None, "publish": False}


def render_available() -> bool:
    if SERVERLESS:
        return False
    return all(importlib.util.find_spec(m) for m in ("edge_tts", "pygments", "numpy")) and bool(shutil.which("node"))


def _render_job(item_id: str, publish: bool) -> None:
    def log(message: str) -> None:
        hub.emit_threadsafe("render", message, item_id=item_id)

    try:
        import auto_pipeline

        auto_pipeline.process_topic(item_id, publish=publish, log=log)
        hub.emit_threadsafe("success", f"Render job finished for {item_id}", item_id=item_id)
    except Exception as exc:  # noqa: BLE001
        hub.emit_threadsafe("error", f"Render job failed for {item_id}: {exc}", item_id=item_id)
    finally:
        render_state.update(running=False, item_id=None, started_at=None)
        render_lock.release()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http, dm_queue
    hub.loop = asyncio.get_running_loop()
    http = httpx.AsyncClient(timeout=30)
    dm_queue = asyncio.Queue()
    tasks = [asyncio.create_task(dm_worker()), asyncio.create_task(insights_loop())]
    missing = [k for k, ok in settings.status().items() if not ok]
    await hub.emit("info", f"Server up. Graph host {settings.graph_api_host}. "
                           f"Not configured: {', '.join(missing) or 'nothing'}")
    if not settings.meta_app_secret:
        await hub.emit("warn", "META_APP_SECRET not set: webhook signatures are NOT verified")
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await http.aclose()


app = FastAPI(title="code_tho_samsaram reel factory", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse("/dashboard")


@app.get("/dashboard", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(settings.static_dir / "dashboard.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "time": tq.now_iso()}


# ---- Webhook ------------------------------------------------------------------


@app.get("/webhook", dependencies=[Depends(webhook_limit)])
async def verify_webhook(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
) -> PlainTextResponse:
    if (hub_mode == "subscribe" and settings.verify_token
            and hmac.compare_digest(hub_verify_token, settings.verify_token)):
        await hub.emit("success", "Meta webhook verification succeeded")
        return PlainTextResponse(hub_challenge)
    await hub.emit("warn", "Meta webhook verification rejected (bad mode or verify token)")
    raise HTTPException(403, "Verification failed")


@app.post("/webhook", dependencies=[Depends(webhook_limit)])
async def receive_webhook(request: Request) -> dict[str, Any]:
    raw = await request.body()
    if settings.meta_app_secret:
        expected = "sha256=" + hmac.new(settings.meta_app_secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(request.headers.get("x-hub-signature-256", ""), expected):
            await hub.emit("warn", f"Rejected webhook with bad signature from {client_ip(request)}")
            raise HTTPException(403, "Invalid signature")
    try:
        payload = json.loads(raw or b"{}")
    except ValueError:
        raise HTTPException(400, "Body must be JSON")
    handled = await process_payload(payload)
    return {"status": "EVENT_RECEIVED", "handled": handled}


# ---- Dashboard API ---------------------------------------------------------------

protected = [Depends(api_limit), Depends(require_dashboard_token)]


def _day(ts: str) -> str:
    return ts[:10]


@app.get("/api/stats", dependencies=protected)
async def stats() -> dict[str, Any]:
    snap = state.snapshot()
    events = snap["events"]
    count = lambda kind: sum(1 for e in events if e["kind"] == kind)  # noqa: E731
    comments, dms_sent, dms_failed, hits = count("comment"), count("dm_sent"), count("dm_failed"), count("keyword_hit")

    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=13 - i)).isoformat() for i in range(14)]
    series = {d: {"comments": 0, "dms": 0} for d in days}
    keywords: dict[str, int] = defaultdict(int)
    for e in events:
        d = _day(e["ts"])
        if d in series:
            if e["kind"] == "comment":
                series[d]["comments"] += 1
            elif e["kind"] == "dm_sent":
                series[d]["dms"] += 1
        if e["kind"] == "keyword_hit" and e.get("keyword"):
            keywords[e["keyword"]] += 1

    insights = snap["insights"]
    real_views = sum(int(m.get("views") or 0) for m in insights.values())
    views = real_views if real_views else comments * settings.est_views_per_comment
    items = queue_items()
    by_status: dict[str, int] = defaultdict(int)
    for item in items:
        by_status[item.get("status", "queued")] += 1

    return {
        "est_views": views,
        "views_source": "instagram_insights" if real_views else "estimate",
        "comments": comments,
        "keyword_hits": hits,
        "dms_sent": dms_sent,
        "dms_failed": dms_failed,
        "dms_pending": dm_queue.qsize() if dm_queue else 0,
        "conversion_rate": round(100 * dms_sent / comments, 1) if comments else 0.0,
        "growth": {"labels": days, "comments": [series[d]["comments"] for d in days],
                   "dms": [series[d]["dms"] for d in days]},
        "top_keywords": sorted(keywords.items(), key=lambda kv: kv[1], reverse=True)[:6],
        "queue": {"total": len(items), **by_status},
        "render": {**render_state, "available": render_available()},
        "integrations": settings.status(),
        "account": settings.account_handle,
    }


@app.get("/api/queue", dependencies=protected)
async def get_queue(category: str | None = None, status: str | None = None) -> dict[str, Any]:
    items = queue_items()
    if category:
        wanted = {c for c, label in tq.CATEGORIES.items() if c == category or label == category}
        items = [i for i in items if i.get("category") in wanted]
    if status:
        items = [i for i in items if i.get("status") == status]
    items = sorted(items, key=lambda i: i.get("created_at", ""), reverse=True)
    return {"items": items, "categories": tq.CATEGORIES}


class TopicIn(BaseModel):
    topic: str = Field(min_length=8, max_length=160)
    keyword: str = Field(pattern=r"^[A-Za-z0-9]{3,20}$")
    category: Literal["ai_tool", "repo", "dsa", "dev_tip", "website"]
    hook: str
    script: str = Field(min_length=20, max_length=400)
    link: str = Field(pattern=r"^https://\S+$")
    code: str = ""
    language: str = "python"
    filename: str = "main.py"
    keyword_spoken: str | None = None
    hashtags: list[str] | None = None

    @field_validator("hook")
    @classmethod
    def three_words(cls, v: str) -> str:
        if len(v.split()) != 3:
            raise ValueError("hook must be exactly 3 words")
        return v.upper()

    @field_validator("hashtags")
    @classmethod
    def five_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) != 5:
            raise ValueError("exactly 5 hashtags required")
        return v


@app.post("/api/queue", dependencies=protected, status_code=201)
async def add_topic(body: TopicIn) -> dict[str, Any]:
    item = tq.make_item(
        category=body.category, topic=body.topic, keyword=body.keyword, hook=body.hook,
        script=body.script, link=body.link, snippet=body.code or body.topic, language=body.language,
        filename=body.filename, keyword_spoken=body.keyword_spoken, hashtags=body.hashtags, source="dashboard",
    )
    added = tq.append_items([item])
    if not added:
        raise HTTPException(409, "A topic with that link or title is already queued")
    await hub.emit("info", f"Added topic '{item['topic']}' ({item['keyword']})")
    return added[0]


@app.delete("/api/queue/{item_id}", dependencies=protected)
async def remove_topic(item_id: str) -> dict[str, Any]:
    if not tq.delete_item(item_id):
        raise HTTPException(404, "No such item")
    await hub.emit("info", f"Deleted {item_id}")
    return {"deleted": item_id}


@app.post("/api/queue/{item_id}/render", dependencies=[*protected, Depends(heavy_limit)], status_code=202)
async def render_item(item_id: str, publish: bool = False) -> dict[str, Any]:
    if not tq.get_item(item_id):
        raise HTTPException(404, "No such item")
    if not render_available():
        raise HTTPException(503, "Rendering dependencies are not installed on this host; "
                                 "run auto_pipeline.py via GitHub Actions instead")
    if not render_lock.acquire(blocking=False):
        raise HTTPException(409, f"Already rendering {render_state['item_id']}")
    render_state.update(running=True, item_id=item_id, started_at=tq.now_iso(), publish=publish)
    threading.Thread(target=_render_job, args=(item_id, publish), daemon=True).start()
    await hub.emit("render", f"Render job started for {item_id} (publish={publish})", item_id=item_id)
    return {"started": item_id, "publish": publish}


@app.post("/api/fetch-trending", dependencies=[*protected, Depends(heavy_limit)])
async def fetch_trending(limit: int = Query(2, ge=1, le=5)) -> dict[str, Any]:
    await hub.emit("info", "Topic discovery started")

    def log(message: str) -> None:
        hub.emit_threadsafe("discover", message)

    added = await asyncio.to_thread(tq.discover_and_enqueue, limit, log)
    await hub.emit("success", f"Discovery finished: {len(added)} new topic(s) queued")
    return {"added": added, "count": len(added)}


@app.get("/api/logs", dependencies=protected)
async def get_logs(after: str | None = None) -> dict[str, Any]:
    events = list(hub.backlog)
    if after:
        ids = [e["id"] for e in events]
        if after in ids:
            events = events[ids.index(after) + 1:]
    return {"events": events[-200:]}


class SimulatedComment(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    username: str = Field("test_dev", max_length=30)
    media_id: str | None = None


@app.post("/api/simulate-comment", dependencies=protected)
async def simulate_comment(body: SimulatedComment) -> dict[str, Any]:
    payload = {"object": "instagram", "entry": [{"id": settings.instagram_user_id or "0", "time": int(time.time()),
               "changes": [{"field": "comments", "value": {
                   "id": f"sim-{uuid.uuid4().hex[:10]}", "text": body.text,
                   "from": {"id": f"sim-{body.username}", "username": body.username},
                   "media": {"id": body.media_id or "sim-media", "media_product_type": "REELS"}}}]}]}
    await process_payload(payload, dry_run=True)
    item, keyword = resolve_item(body.text, body.media_id)
    return {"matched": bool(item), "keyword": keyword, "item_id": item["id"] if item else None,
            "dm_preview": build_dm(item) if item else None}


@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket) -> None:
    if settings.dashboard_token and not hmac.compare_digest(ws.query_params.get("token", ""),
                                                            settings.dashboard_token):
        await ws.close(code=4401)
        return
    await ws.accept()
    for event in list(hub.backlog)[-80:]:
        await ws.send_json(event)
    hub.clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive pings from the dashboard
    except WebSocketDisconnect:
        pass
    finally:
        hub.clients.discard(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
