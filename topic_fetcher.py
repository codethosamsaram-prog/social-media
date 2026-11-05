"""Topic Discovery Engine + the JSON video queue store.

Sources (each one is optional and fails independently):
  * GitHub Trending (HTML scrape, BeautifulSoup)  -> category "repo"
  * GitHub Search API fallback (no key needed)     -> category "repo"
  * Hacker News "Show HN" AI launches (Algolia)    -> category "ai_tool"
  * Google Custom Search JSON API (key + cx)       -> "repo" / "ai_tool"
  * Curated O(1)-space LeetCode trick library      -> category "dsa"

Every discovery is turned into a complete reel blueprint (3-word hook, voice
script, code snippet, DM link, 5 hashtags) and appended to topics_queue.json.

CLI:
    python topic_fetcher.py                # discover + enqueue (2 per source)
    python topic_fetcher.py --limit 3      # more per source
    python topic_fetcher.py --dry-run      # print blueprints, don't write
    python topic_fetcher.py --list         # show the queue
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import tempfile
import textwrap
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable

import httpx
from bs4 import BeautifulSoup

from config import settings

Log = Callable[[str], None]

CATEGORIES: dict[str, str] = {
    "ai_tool": "Hidden AI Tools",
    "repo": "Repos",
    "dsa": "DSA Tricks",
    "dev_tip": "Dev Tips",
    "website": "Dev Tips",
    "hiring": "Hiring in India",
}

STATUSES = ("queued", "needs_review", "rendering", "rendered", "published", "failed")

# Generic comment keywords that resolve to "the latest item of this category".
CATEGORY_KEYWORDS: dict[str, str] = {
    "AITOOL": "ai_tool",
    "REPO": "repo",
    "LEETCODE": "dsa",
    "WEBSITE": "website",
    "ASYNC": "dev_tip",
    "HIRING": "hiring",
    "JOBS": "hiring",
}

HASHTAGS: dict[str, list[str]] = {
    "ai_tool": ["#ai", "#aitools", "#coding", "#developers", "#vscode"],
    "repo": ["#github", "#opensource", "#coding", "#developers", "#ai"],
    "dsa": ["#leetcode", "#dsa", "#python", "#coding", "#programming"],
    "dev_tip": ["#python", "#coding", "#developers", "#programming", "#vscode"],
    "website": ["#webdev", "#coding", "#developers", "#programming", "#devtools"],
    "hiring": ["#hiring", "#jobsinindia", "#softwarejobs", "#bangalorejobs", "#developers"],
}

STOCK_QUERIES: dict[str, list[str]] = {
    "ai_tool": ["artificial intelligence", "coding laptop dark", "neon technology"],
    "repo": ["computer screen code", "programmer typing night", "server room lights"],
    "dsa": ["programmer thinking", "abstract binary code", "dark desk setup"],
    "dev_tip": ["coding laptop dark", "developer workspace", "fast city night"],
    "website": ["laptop web browsing night", "developer workspace", "minimal desk setup"],
    "hiring": ["modern office india", "team meeting office", "bangalore city night"],
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Queue store (thread-safe, atomic writes)
# ---------------------------------------------------------------------------

_LOCK = threading.RLock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_queue() -> list[dict[str, Any]]:
    with _LOCK:
        path = settings.queue_file
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8") or "[]")
        items = data.get("items", []) if isinstance(data, dict) else data
        return [dict(i) for i in items]


def _removed_keys() -> list[str]:
    path = settings.queue_file
    data = json.loads(path.read_text(encoding="utf-8") or "[]") if path.exists() else []
    return data.get("removed", []) if isinstance(data, dict) else []


def save_queue(items: list[dict[str, Any]], removed: Iterable[str] = ()) -> None:
    with _LOCK:
        path = settings.queue_file
        payload = {"account": f"@{settings.account_handle}", "updated_at": now_iso(), "items": items,
                   "removed": sorted({*_removed_keys(), *removed})}
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".queue-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        # Windows refuses to replace a file another process is reading; retry briefly.
        for attempt in range(10):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == 9:
                    os.unlink(tmp)
                    raise
                time.sleep(0.1)


def get_item(item_id: str) -> dict[str, Any] | None:
    return next((i for i in load_queue() if i.get("id") == item_id), None)


def update_item(item_id: str, **fields: Any) -> dict[str, Any]:
    with _LOCK:
        items = load_queue()
        for item in items:
            if item.get("id") == item_id:
                item.update(fields)
                item["updated_at"] = now_iso()
                save_queue(items)
                return dict(item)
    raise KeyError(f"Queue item not found: {item_id}")


def delete_item(item_id: str) -> bool:
    with _LOCK:
        items = load_queue()
        kept = [i for i in items if i.get("id") != item_id]
        if len(kept) == len(items):
            return False
        # Remember what was deleted, or the next discovery run would fetch it straight back.
        gone = [key for i in items if i.get("id") == item_id for key in topic_keys(i)]
        save_queue(kept, removed=gone)
        return True


def next_queued() -> dict[str, Any] | None:
    queued = [i for i in load_queue() if i.get("status", "queued") == "queued"]
    queued.sort(key=lambda i: i.get("created_at", ""))
    return queued[0] if queued else None


def _norm_link(link: str) -> str:
    link = (link or "").strip().lower().split("#")[0]
    link = re.sub(r"^https?://(www\.)?", "", link)
    link = re.sub(r"[?&](utm_\w+|ref)=[^&]*", "", link)
    return re.sub(r"\.git$", "", link.rstrip("/"))


# These teach the same idea as another trick, so a second reel would read as a repost.
SAME_DSA_TOPIC = {"xor_missing": "xor_single", "negate": "floyd"}


def _name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\.(dev|io|ai|app|so|sh|com)$", "", name.strip().lower()))


def topic_keys(item: dict[str, Any]) -> set[str]:
    """Everything that identifies a topic. Two items sharing any key are the same reel, so the same
    product found by two sources (a GitHub repo and its website, say) only gets queued once."""
    if item.get("category") == "hiring":  # a daily reel: its link is a company page that comes round again
        return {f"id:{item.get('id')}"}
    topic = (item.get("topic") or "").strip().lower()
    keys = {f"link:{_norm_link(item.get('link', ''))}", f"topic:{topic}"}
    trick = (item.get("dsa") or {}).get("trick")
    if trick:
        keys.add(f"dsa:{SAME_DSA_TOPIC.get(trick, trick)}")
    if item.get("category") == "dsa":  # their titles share words like "O(1) space", which proves nothing
        return keys
    names = re.findall(r"\(([^)]+)\)", topic)
    if ":" in topic:
        names.append(topic.split(":", 1)[0])
    repo = re.match(r"github\.com/[^/]+/([^/]+)$", _norm_link(item.get("link", "")))
    if repo:
        names.append(repo.group(1))
    for name in names:
        key = _name_key(name)
        if len(key) >= 3 and key != "githubtrending":
            keys.add(f"name:{key}")
    return keys


def known_keys() -> set[str]:
    """Every topic ever queued, posted or deleted. Published items stay in the queue file for this."""
    with _LOCK:
        return {*_removed_keys(), *(key for i in load_queue() for key in topic_keys(i))}


def unseen(candidates: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """The first `limit` new topics. Sources must filter before cutting to their limit: the top results
    barely change between runs, so cutting first returns only old topics and new ones are never reached."""
    known, fresh = known_keys(), []
    for item in candidates:
        keys = topic_keys(item)
        if keys & known:
            continue
        known |= keys
        fresh.append(item)
        if len(fresh) >= limit:
            break
    return fresh


def append_items(new_items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate + append, skipping any topic already queued, posted or deleted."""
    with _LOCK:
        items = load_queue()
        known = known_keys()
        added: list[dict[str, Any]] = []
        for item in new_items:
            item = validate_item(item)
            keys = topic_keys(item)
            if keys & known:
                continue
            items.append(item)
            added.append(item)
            known |= keys
        if added:
            save_queue(items)
        return added


# ---------------------------------------------------------------------------
# Blueprint construction + validation
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF‍️]+"
)
_URL_RE = re.compile(r"https?://\S+")


def clean_text(text: str) -> str:
    text = _URL_RE.sub("", text or "")
    text = _EMOJI_RE.sub("", text)
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip()


def trim_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text.strip().rstrip(".")
    return " ".join(words[:limit]).rstrip(",;:-").rstrip(".")


def short_description(desc: str, limit: int = 12) -> str:
    """First clause of a description, at most `limit` words, ending cleanly."""
    desc = clean_text(desc)
    first = re.split(r"(?<=[.!?])\s|\s[-|]\s|;\s", desc, maxsplit=1)[0]
    return trim_words(first, limit)


def spoken(text: str) -> str:
    """Make names TTS-friendly: browser-use -> browser use, foo_bar -> foo bar."""
    text = re.sub(r"[-_/]+", " ", text)
    text = re.sub(r"\.(dev|io|ai|app|so|sh)\b", r" dot \1", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def make_id(category: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
    return f"{category.replace('_', '')}-{digest}"


def make_item(
    *,
    category: str,
    topic: str,
    keyword: str,
    hook: str,
    script: str,
    link: str,
    snippet: str,
    language: str = "python",
    filename: str = "main.py",
    keyword_spoken: str | None = None,
    stock_queries: list[str] | None = None,
    hashtags: list[str] | None = None,
    caption: str | None = None,
    source: str = "manual",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item = {
        "id": make_id(category, link or topic),
        "topic": topic.strip(),
        "keyword": keyword.upper(),
        "keyword_spoken": keyword_spoken or keyword.lower(),
        "category": category,
        "hook": hook.upper(),
        "script": script.strip(),
        "link": link.strip(),
        "code": {"language": language, "filename": filename, "snippet": snippet.rstrip()},
        "stock_queries": stock_queries or STOCK_QUERIES[category],
        "hashtags": hashtags or HASHTAGS[category],
        "caption": caption or topic.strip(),
        "source": source,
        "status": "queued",
        "created_at": now_iso(),
    }
    if extra:
        item["meta"] = extra
    return validate_item(item)


def validate_item(item: dict[str, Any]) -> dict[str, Any]:
    """Enforce the algorithm rules every reel depends on. Raises ValueError."""
    item = dict(item)
    for key in ("id", "topic", "keyword", "category", "hook", "script", "link"):
        if not str(item.get(key, "")).strip():
            raise ValueError(f"Queue item is missing '{key}'")
    if item["category"] not in CATEGORIES:
        raise ValueError(f"Unknown category '{item['category']}'")
    item["keyword"] = item["keyword"].strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{3,20}", item["keyword"]):
        raise ValueError(f"Keyword must be 3-20 letters/digits: {item['keyword']!r}")
    item["hook"] = " ".join(item["hook"].upper().split())
    if len(item["hook"].split()) != 3:
        raise ValueError(f"Hook must be exactly 3 words: {item['hook']!r}")
    tags = [t if t.startswith("#") else f"#{t}" for t in item.get("hashtags") or HASHTAGS[item["category"]]]
    tags = list(dict.fromkeys(t.lower() for t in tags))
    for fallback in HASHTAGS[item["category"]] + ["#coding", "#developers", "#programming", "#tech"]:
        if len(tags) >= 5:
            break
        if fallback not in tags:
            tags.append(fallback)
    item["hashtags"] = tags[:5]
    code = item.get("code") or {}
    item["code"] = {
        "language": code.get("language") or "text",
        "filename": code.get("filename") or "snippet.txt",
        "snippet": (code.get("snippet") or item["topic"]).rstrip(),
    }
    item.setdefault("keyword_spoken", item["keyword"].lower())
    item.setdefault("stock_queries", STOCK_QUERIES[item["category"]])
    item.setdefault("caption", item["topic"])
    item.setdefault("status", "queued")
    item.setdefault("created_at", now_iso())
    if item["status"] not in STATUSES:
        item["status"] = "queued"
    return item


# ---------------------------------------------------------------------------
# Source: GitHub
# ---------------------------------------------------------------------------

# Exactly 3 words each, grouped by the trigger they pull (rotate so the feed never repeats an opener):
#   curiosity gap · loss aversion · social proof · identity · contrarian · urgency
REPO_HOOKS = [
    "THIS REPO EXPLODED", "OPEN SOURCE GOLD", "STAR THIS NOW", "GITHUB IS CRAZY",   # hype / urgency
    "NOBODY TALKS ABOUT", "DEVS ARE SLEEPING", "GITHUB HIDDEN GEM",                  # curiosity gap
    "STOP PAYING FOR", "DELETE YOUR SUBSCRIPTION",                                   # loss aversion
    "SENIORS USE THIS", "BOOKMARK THIS REPO",                                        # identity / save trigger
]


def _repo_item(full_name: str, description: str, stars_today: int | None, stars: int | None,
               language: str | None, source: str) -> dict[str, Any] | None:
    owner, _, name = full_name.partition("/")
    desc = short_description(description, 12)
    if not name or len(desc.split()) < 3:
        return None
    star_line = (
        f"{stars_today:,} new stars today" if stars_today
        else f"{stars:,} stars already" if stars else "and it's climbing fast"
    )
    script = f"This GitHub repo is exploding. {spoken(name)}: {desc}. {star_line}."
    wrapped = textwrap.wrap(desc, 34)[:3]
    snippet_lines = [
        f"# {full_name}",
        f"# +{stars_today:,} stars today" if stars_today else f"# {stars or 0:,} stars",
        "",
        f"git clone https://github.com/{full_name}.git",
        f"cd {name}",
        "",
        *[f"# {line}" for line in wrapped],
    ]
    tags = list(HASHTAGS["repo"])
    if language and language.lower() in {"python", "typescript", "javascript", "rust", "go"}:
        tags[-1] = f"#{language.lower()}"
    return make_item(
        category="repo",
        topic=f"{name}: {desc} (GitHub trending)",
        keyword="REPO",
        keyword_spoken="repo",
        hook=random.choice(REPO_HOOKS),
        script=script,
        link=f"https://github.com/{full_name}",
        snippet="\n".join(snippet_lines),
        language="bash",
        filename="terminal",
        hashtags=tags,
        caption=f"{name} is trending on GitHub 🔥 {desc}.",
        source=source,
        extra={"stars_today": stars_today, "stars": stars, "language": language},
    ) | {"repo": {"full_name": full_name, "description": desc, "stars": stars or 0, "stars_today": stars_today,
                  "language": language}}


# --- README -> "how it works" / setup / use cases -------------------------------------

INSTALL_RE = re.compile(
    r"^\s*\$?\s*((?:pip|pipx|uv)\s+(?:install|add|tool install)\s+\S+|npm\s+(?:i|install)\s+(?:-g\s+)?\S+|"
    r"npx\s+\S+|pnpm\s+add\s+\S+|yarn\s+add\s+\S+|bun\s+add\s+\S+|brew\s+install\s+\S+|"
    r"cargo\s+install\s+\S+|go\s+install\s+\S+|docker\s+run\s+.+)$", re.M)
CODE_LANGS = {"python", "py", "ts", "typescript", "js", "javascript", "tsx", "jsx", "go", "rust", "rs"}
FEATURE_HEAD = re.compile(r"^#{1,4}\s*[^\w\n]*\s*(features|key features|highlights|why|use cases|what can|"
                          r"capabilities|what it does|what you can)", re.I | re.M)
ICONS = [(r"agent|\bai\b|llm|model|gpt", "🤖"), (r"fast|speed|perf|blazing", "⚡"), (r"secur|auth|privacy", "🔒"),
         (r"data|analytic|chart|dashboard", "📊"), (r"web|browser|site|scrap", "🌐"), (r"\btest", "🧪"),
         (r"mobile|ios|android", "📱"), (r"cloud|deploy|server", "☁️"), (r"code|\bide\b|editor|\bdev", "💻"),
         (r"chat|message|voice", "💬"), (r"file|\bdoc|pdf", "📄"), (r"search|find", "🔎")]
DEMO_EXT = {"python": "py", "py": "py", "typescript": "ts", "ts": "ts", "tsx": "tsx", "javascript": "js", "js": "js",
            "jsx": "jsx", "go": "go", "rust": "rs", "rs": "rs"}
DEMO_LANG = {"py": "python", "rs": "rust", "ts": "typescript", "js": "javascript"}


STOPWORDS = {"a", "an", "the", "to", "of", "for", "and", "or", "in", "on", "with", "your", "by", "is"}


def clip_words(text: str, max_chars: int) -> str:
    """Cut at a word boundary (never mid-word) and drop dangling connector words."""
    words = text.split()
    while words and len(" ".join(words)) > max_chars:
        words.pop()
    while words and words[-1].lower().strip(",.;:") in STOPWORDS:
        words.pop()
    return " ".join(words).rstrip(",.;:")


def _icon(text: str) -> str:
    return next((icon for pattern, icon in ICONS if re.search(pattern, text, re.I)), "🛠️")


def _md_plain(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>|[*_`~]", "", text)
    return clean_text(text)


def readme_explainer(readme: str, full_name: str, desc: str) -> dict[str, Any]:
    """Heuristic explainer from a README: install command, a short demo snippet, feature bullets."""
    blocks = re.findall(r"```([\w+-]*)[^\n]*\n(.*?)```", readme, re.S)
    install = next((m.group(1).strip() for _, body in blocks for m in [INSTALL_RE.search(body)] if m), None)
    demo = None
    for lang, body in blocks:
        lines = body.strip("\n").splitlines()
        lang = lang.lower()
        if (lang in CODE_LANGS and 3 <= len(lines) <= 18 and not INSTALL_RE.search(body)
                and max(map(len, lines[:12])) <= 64):
            demo = {"snippet": "\n".join(lines[:12]), "language": DEMO_LANG.get(lang, lang),
                    "filename": f"example.{DEMO_EXT.get(lang, 'txt')}", "focus": []}
            break
    cases: list[dict[str, str]] = []
    head = FEATURE_HEAD.search(readme)
    if head:
        section = re.split(r"^#{1,4}\s", readme[head.end():], maxsplit=1, flags=re.M)[0]
        for raw in re.findall(r"^\s*[-*+]\s+(.+)$", section, re.M):
            text = _md_plain(raw)
            if len(text.split()) < 2 or raw.lstrip().startswith(("http", "[!", "![")):
                continue
            parts = re.split(r"\s[-–—]\s|:\s", text, maxsplit=1)
            title = clip_words(parts[0], 30)
            detail = clip_words(parts[1], 44) if len(parts) > 1 else ""
            if len(title.split()) < 2:
                continue
            cases.append({"icon": _icon(text), "title": title, "detail": detail, "cue": title.split()[0].lower()})
            if len(cases) == 3:
                break
    first_import = ""
    if demo:
        first_import = next((ln.strip() for ln in demo["snippet"].splitlines()
                             if re.match(r"\s*(from|import|use|const|require)\b", ln)), "")
    how = [
        {"icon": "📦", "title": "Install it", "detail": (install or f"git clone {full_name}")[:34], "cue": "install"},
        {"icon": "🧩", "title": "Plug it in", "detail": (first_import or "a few lines of config")[:34], "cue": "plug"},
        {"icon": "🚀", "title": "Run it", "detail": trim_words(desc, 5)[:34], "cue": "run"},
    ]
    return {
        "install": install or f"git clone https://github.com/{full_name}",
        "demo_code": demo,
        "how": how,
        "use_cases": cases,
        "narration": {"how": "Here's how it works. Install it, plug it into your project, and run it.",
                      "demo": "Setup really is this small." if demo else "Setup is a single command."},
    }


def enrich_repo(client: httpx.Client, item: dict[str, Any], log: Log) -> dict[str, Any]:
    repo = item.get("repo") or {}
    full = repo.get("full_name")
    if not full:
        return item
    try:
        resp = client.get(f"https://api.github.com/repos/{full}/readme", headers={"Accept": "application/vnd.github.raw"})
        resp.raise_for_status()
        explainer = readme_explainer(resp.text, full, repo.get("description", ""))
        item["repo"] = {**repo, **explainer}
        log(f"README: {full} -> install '{explainer['install']}', {len(explainer['use_cases'])} use cases")
        if len(explainer["use_cases"]) < 3:
            item["status"] = "needs_review"
            log(f"{full}: README too thin for a full explainer, parked as needs_review (add use cases, then queue it)")
    except Exception as exc:  # noqa: BLE001
        log(f"README fetch failed for {full}: {exc}")
    return item


def _int(text: str) -> int | None:
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) if digits else None


def discover_github_trending(client: httpx.Client, limit: int, log: Log) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for url in ("https://github.com/trending/python?since=daily", "https://github.com/trending?since=daily"):
        resp = client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select("article.Box-row"):
            link = row.select_one("h2 a")
            if not link or not link.get("href"):
                continue
            full_name = link["href"].strip("/")
            if full_name in seen or full_name.count("/") != 1:
                continue
            seen.add(full_name)
            desc_el = row.select_one("p")
            lang_el = row.select_one('[itemprop="programmingLanguage"]')
            stars_el = row.select_one('a[href$="/stargazers"]')
            today_el = row.select_one("span.d-inline-block.float-sm-right")
            item = _repo_item(
                full_name,
                desc_el.get_text(" ", strip=True) if desc_el else "",
                _int(today_el.get_text()) if today_el else None,
                _int(stars_el.get_text()) if stars_el else None,
                lang_el.get_text(strip=True) if lang_el else None,
                "github_trending",
            )
            if item:
                results.append(item)
    results.sort(key=lambda i: (i.get("meta") or {}).get("stars_today") or 0, reverse=True)
    log(f"GitHub Trending: {len(results)} candidate repos")
    return unseen(results, limit)


def discover_github_api(client: httpx.Client, limit: int, log: Log) -> list[dict[str, Any]]:
    since = (datetime.now(timezone.utc) - timedelta(days=21)).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    resp = client.get(
        "https://api.github.com/search/repositories",
        params={"q": f"created:>{since} stars:>300", "sort": "stars", "order": "desc", "per_page": 15},
        headers=headers,
    )
    resp.raise_for_status()
    results = []
    for repo in resp.json().get("items", []):
        item = _repo_item(repo["full_name"], repo.get("description") or "", None,
                          repo.get("stargazers_count"), repo.get("language"), "github_search")
        if item:
            results.append(item)
    log(f"GitHub Search API: {len(results)} fast-rising repos")
    return unseen(results, limit)


# ---------------------------------------------------------------------------
# Source: Hacker News (AI tool launches)
# ---------------------------------------------------------------------------

AI_HOOKS = [
    "HIDDEN AI TOOL", "AI DOES THIS", "STOP DOING MANUALLY", "UNDERRATED AI TOOL",
    "THIS FEELS ILLEGAL", "NOBODY USES THIS", "YOUR NEW COWORKER",                   # curiosity / novelty
    "STOP WASTING HOURS", "JUNIORS DON'T KNOW", "SAVE THIS NOW",                     # loss aversion / identity / save
]
AI_TERMS = re.compile(r"\b(ai|llm|gpt|agent|agents|copilot|claude|gemini|model|ml|rag)\b", re.I)


def _ai_tool_item(title: str, url: str, source: str) -> dict[str, Any] | None:
    title = clean_text(re.sub(r"^(show|launch) hn:\s*", "", title, flags=re.I))
    parts = re.split(r"\s[–—-]\s|:\s|,\s", title, maxsplit=1)
    if len(parts) < 2:
        return None
    name, desc = parts[0].strip(), trim_words(parts[1].strip(), 12)
    if not name or len(name) > 40 or len(desc.split()) < 3:
        return None
    domain = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    script = f"This AI tool is criminally underrated. {spoken(name)}: {desc}."
    snippet = "\n".join([
        "// hidden AI tool of the day",
        f'const tool = "{name}";',
        f'const site = "{domain}";',
        "",
        *[f"// {line}" for line in textwrap.wrap(desc, 36)[:3]],
        "",
        "await tool.tryIt(); // link in DMs",
    ])
    return make_item(
        category="ai_tool",
        topic=f"{name}: {desc}",
        keyword="AITOOL",
        keyword_spoken="AI tool",
        hook=random.choice(AI_HOOKS),
        script=script,
        link=url,
        snippet=snippet,
        language="javascript",
        filename="ai-tool.js",
        caption=f"{name}: {desc} 🤖",
        source=source,
    ) | {"browser": {"url": domain, "mock": "landing", "headline": name,
                     "bullets": [trim_words(p.strip(), 6) for p in re.split(r",\s|\sand\s|\swith\s", desc) if p.strip()][:3]}}


def discover_hn_ai_tools(client: httpx.Client, limit: int, log: Log) -> list[dict[str, Any]]:
    week_ago = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
    hits: dict[str, dict[str, Any]] = {}
    for query in ("AI", "LLM", "agent", "GPT", "Claude"):
        resp = client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "show_hn",
                    "numericFilters": f"created_at_i>{week_ago},points>25", "hitsPerPage": 30},
        )
        resp.raise_for_status()
        for hit in resp.json().get("hits", []):
            hits[hit["objectID"]] = hit
    results = []
    for hit in sorted(hits.values(), key=lambda h: h.get("points") or 0, reverse=True):
        title, url = hit.get("title") or "", hit.get("url")
        if not url or not AI_TERMS.search(title):
            continue
        item = _ai_tool_item(title, url, "hacker_news")
        if item:
            results.append(item)
    log(f"Hacker News Show HN: {len(results)} AI tool launches")
    return unseen(results, limit)


# ---------------------------------------------------------------------------
# Source: Google Custom Search JSON API
# ---------------------------------------------------------------------------

GOOGLE_QUERIES = [
    "new AI tool for developers launched",
    "trending github repository AI agent",
]


def discover_google(client: httpx.Client, limit: int, log: Log) -> list[dict[str, Any]]:
    if not (settings.google_search_api_key and settings.google_search_cx):
        log("Google Custom Search: skipped (GOOGLE_SEARCH_API_KEY / GOOGLE_SEARCH_CX not set)")
        return []
    results = []
    for query in GOOGLE_QUERIES:
        resp = client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": settings.google_search_api_key, "cx": settings.google_search_cx,
                    "q": query, "dateRestrict": "d7", "num": 8},
        )
        resp.raise_for_status()
        for hit in resp.json().get("items", []):
            link, title, snippet = hit.get("link", ""), hit.get("title", ""), hit.get("snippet", "")
            match = re.match(r"https?://github\.com/([\w.-]+/[\w.-]+)/?$", link)
            if match:
                item = _repo_item(match.group(1), snippet, None, None, None, "google_search")
            else:
                item = _ai_tool_item(f"{title.split(' | ')[0]}: {snippet}", link, "google_search")
            if item:
                results.append(item)
    log(f"Google Custom Search: {len(results)} results")
    return unseen(results, limit)


# ---------------------------------------------------------------------------
# Source: Gemini with Google Search grounding
# ---------------------------------------------------------------------------

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_PROMPT = """Search the web for what software developers are talking about in the 7 days before {today}.
Find {count} items: open-source GitHub repositories that are trending, and newly launched AI tools for developers.

Reply with ONLY a JSON array, no prose and no code fence. Each element:
{{"kind": "repo" or "tool", "name": "short product or repo name", "url": "...", "summary": "what it does, 6 to 12 plain words"}}

For a repo, url must be the exact https://github.com/owner/name page. For a tool, url must be its official site.
Only include things you found in the search results. Never guess a URL."""


GEMINI_PICK_PROMPT = """Below are today's Hacker News front-page stories, one per line as: title | url
Pick up to {count} that a software developer would use in their work: GitHub repositories of developer software, and AI tools.
A "tool" must be software built on AI that helps with coding or building software, because the reel will call it an AI tool.
Skip news, essays, hardware, games, media players, and anything else. Returning fewer items, or an empty array, is correct when few qualify.

Reply with ONLY a JSON array, no prose and no code fence. Each element:
{{"kind": "repo" or "tool", "name": "short product or repo name", "url": "the exact url from its line", "summary": "what it does, 6 to 12 plain words"}}

Stories:
{stories}"""
GEMINI_FALLBACK_MODEL = "gemini-flash-lite-latest"


def _gemini_call(client: httpx.Client, prompt: str, search: bool) -> str:
    """Tries the configured model, then the lighter one when the first is overloaded or out of quota."""
    body: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.3}}
    if search:
        body["tools"] = [{"google_search": {}}]
    error = ""
    for model in dict.fromkeys((settings.gemini_model, GEMINI_FALLBACK_MODEL)):
        resp = client.post(GEMINI_URL.format(model=model), json=body, timeout=120,
                           headers={"x-goog-api-key": settings.gemini_api_key})  # a header keeps the key out of logged URLs
        if resp.status_code == 200:
            return "".join(p.get("text", "") for p in resp.json()["candidates"][0]["content"]["parts"])
        error = f"{model} HTTP {resp.status_code}: {resp.json().get('error', {}).get('message', '')[:120]}"
        if resp.status_code not in (429, 503):
            break
    raise RuntimeError(error)


def _gemini_candidates(client: httpx.Client, count: int, log: Log) -> list[dict[str, Any]]:
    try:
        text = _gemini_call(client, GEMINI_PROMPT.format(today=now_iso()[:10], count=count), search=True)
    except RuntimeError as exc:
        # Google Search grounding needs billing on many keys. Plain Gemini can still choose from live headlines.
        log(f"Gemini: search unavailable ({str(exc)[:90]}), picking from the Hacker News front page instead")
        hits = client.get("https://hn.algolia.com/api/v1/search", params={"tags": "front_page", "hitsPerPage": 40}).json()["hits"]
        stories = "\n".join(f"{h['title']} | {h['url']}" for h in hits if h.get("url"))
        text = _gemini_call(client, GEMINI_PICK_PROMPT.format(count=count, stories=stories), search=False)
    match = re.search(r"\[.*\]", text, re.S)
    rows = json.loads(match.group(0)) if match else []
    return [r for r in rows if isinstance(r, dict) and r.get("url") and r.get("name")]


def discover_gemini(client: httpx.Client, limit: int, log: Log) -> list[dict[str, Any]]:
    """Model output is untrusted: a repo must exist on GitHub and a tool's site must answer before it is queued."""
    if not settings.gemini_api_key:
        log("Gemini: skipped (GEMINI_API_KEY not set)")
        return []
    results: list[dict[str, Any]] = []
    known = known_keys()
    rows = _gemini_candidates(client, limit * 3, log)
    for row in rows:
        url, summary = str(row["url"]).strip(), clean_text(str(row.get("summary", "")))
        match = re.match(r"https?://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?/?$", url)
        item = None
        if match:
            meta = client.get(f"https://api.github.com/repos/{match.group(1)}")
            if meta.status_code == 200:
                info = meta.json()
                item = _repo_item(info["full_name"], info.get("description") or summary, None,
                                  info.get("stargazers_count"), info.get("language"), "gemini")
        elif url.startswith("https://") and client.get(url).status_code < 400:
            item = _ai_tool_item(f"{row['name']}: {summary}", url, "gemini")
        if item and topic_keys(item) & known:
            log(f"Gemini: already have '{str(row['name'])[:40]}'")
            continue
        if item:
            known |= topic_keys(item)
            results.append(enrich_repo(client, item, log))
        else:
            log(f"Gemini: dropped unverifiable '{str(row['name'])[:40]}'")
        if len(results) >= limit:
            break
    log(f"Gemini: {len(results)} verified of {len(rows)} suggested")
    return results


# ---------------------------------------------------------------------------
# Source: curated O(1)-space LeetCode tricks
# ---------------------------------------------------------------------------

def discover_dsa(limit: int, log: Log) -> list[dict[str, Any]]:
    from storyboard import DSA_TRICKS

    known = known_keys()
    fresh = [(k, t) for k, t in DSA_TRICKS.items()
             if f"dsa:{SAME_DSA_TOPIC.get(k, k)}" not in known and f"link:{_norm_link(t['link'])}" not in known]
    random.shuffle(fresh)
    results = []
    for key, t in fresh[:limit]:
        item = make_item(
            category="dsa", topic=t["topic"], keyword="LEETCODE", keyword_spoken="leetcode", hook=t["hook"],
            script=t["narration"]["visualize"], link=t["link"], snippet=t["snippet"], language="python",
            filename=t["filename"], caption=f"{t['topic']} 🧠", source="dsa_library",
        )
        item["dsa"] = {"trick": key}
        results.append(item)
    log(f"DSA library: {len(fresh)} unused traced tricks, taking {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def discover(limit_per_source: int = 2, log: Log = print) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    with httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        repos: list[dict[str, Any]] = []
        try:
            repos = discover_github_trending(client, limit_per_source, log)
        except Exception as exc:  # noqa: BLE001 - every source is best-effort
            log(f"GitHub Trending failed: {exc}")
        if not repos:
            try:
                repos = discover_github_api(client, limit_per_source, log)
            except Exception as exc:  # noqa: BLE001
                log(f"GitHub Search API failed: {exc}")
        found += [enrich_repo(client, item, log) for item in repos]
        for name, fn in (("Gemini", discover_gemini), ("Hacker News", discover_hn_ai_tools), ("Google Search", discover_google)):
            try:
                found += fn(client, limit_per_source, log)
            except Exception as exc:  # noqa: BLE001
                log(f"{name} failed: {exc}")
    found += discover_dsa(limit_per_source, log)
    return found


def discover_and_enqueue(limit_per_source: int = 2, log: Log = print) -> list[dict[str, Any]]:
    added = append_items(discover(limit_per_source, log))
    log(f"Queued {len(added)} new reel blueprint(s)")
    return added


# Trending topics go stale and the queue posts oldest first, so don't let the backlog outrun posting (5 a day).
MAX_BACKLOG = 20


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover trending dev topics and enqueue reels.")
    parser.add_argument("--limit", type=int, default=2, help="max items per source")
    parser.add_argument("--dry-run", action="store_true", help="print blueprints without saving")
    parser.add_argument("--list", action="store_true", help="print the current queue and exit")
    args = parser.parse_args()

    if args.list:
        for item in load_queue():
            print(f"[{item['status']:>9}] {item['id']:<20} {item['keyword']:<9} {item['topic']}")
        return
    if args.dry_run:
        print(json.dumps(discover(args.limit), indent=2, ensure_ascii=False))
        return
    backlog = sum(i.get("status") == "queued" for i in load_queue())
    if backlog >= MAX_BACKLOG:
        print(f"{backlog} reels already queued: nothing to fetch")
        return
    for item in discover_and_enqueue(args.limit):
        print(f"+ {item['id']}  {item['keyword']:<9} {item['topic']}")


if __name__ == "__main__":
    main()
