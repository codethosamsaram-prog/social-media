"""Daily "they're hiring" reel: the top 3 companies with fresh engineering openings in India.

Data comes only from the companies' own public career boards (Greenhouse, Lever, Ashby job-board
APIs: free, no key). Nothing is invented: every company, role, count and link in the reel is what the
board returned at discovery time, and the DM sends the real careers links.

Ranking: engineering roles located in India (city or "Remote - India"), weighted towards roles
published in the last 14 days. Companies featured in the last 7 hiring reels are skipped so the
feed rotates.

    python hiring.py --dry-run     # print today's top 3
    python hiring.py               # enqueue the hiring reel
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import re
from typing import Any, Callable

import httpx

Log = Callable[[str], None]

# (display name, board type, board token, domain for the logo, brand colour)
COMPANIES: list[tuple[str, str, str, str, str]] = [
    # Indian companies
    ("Razorpay", "greenhouse", "razorpaysoftwareprivatelimited", "razorpay.com", "#3395ff"),
    ("Groww", "greenhouse", "groww", "groww.in", "#00d09c"),
    ("HackerRank", "greenhouse", "hackerrank", "hackerrank.com", "#2ec866"),
    ("CRED", "lever", "cred", "cred.club", "#e5e5e5"),
    ("Meesho", "lever", "meesho", "meesho.com", "#f43397"),
    ("Zeta", "lever", "zeta", "zeta.tech", "#6c5ce7"),
    ("Sarvam AI", "ashby", "sarvam", "sarvam.ai", "#ff7a45"),
    # Global companies with India engineering offices
    ("Stripe", "greenhouse", "stripe", "stripe.com", "#635bff"),
    ("Databricks", "greenhouse", "databricks", "databricks.com", "#ff3621"),
    ("Cloudflare", "greenhouse", "cloudflare", "cloudflare.com", "#f38020"),
    ("MongoDB", "greenhouse", "mongodb", "mongodb.com", "#00ed64"),
    ("Datadog", "greenhouse", "datadog", "datadoghq.com", "#8a4cff"),
    ("Okta", "greenhouse", "okta", "okta.com", "#3d6ef5"),
    ("Elastic", "greenhouse", "elastic", "elastic.co", "#fec514"),
    ("Coinbase", "greenhouse", "coinbase", "coinbase.com", "#0052ff"),
    ("Twilio", "greenhouse", "twilio", "twilio.com", "#f22f46"),
    ("GitLab", "greenhouse", "gitlab", "gitlab.com", "#fc6d26"),
    ("Airbnb", "greenhouse", "airbnb", "airbnb.com", "#ff5a5f"),
    ("Pinterest", "greenhouse", "pinterest", "pinterest.com", "#e60023"),
    ("Reddit", "greenhouse", "reddit", "reddit.com", "#ff4500"),
    ("Dropbox", "greenhouse", "dropbox", "dropbox.com", "#0061ff"),
    ("Instacart", "greenhouse", "instacart", "instacart.com", "#43b02a"),
    ("Anthropic", "greenhouse", "anthropic", "anthropic.com", "#d97757"),
    ("Palantir", "lever", "palantir", "palantir.com", "#e5e5e5"),
    ("Spotify", "lever", "spotify", "spotify.com", "#1ed760"),
    ("OpenAI", "ashby", "openai", "openai.com", "#e5e5e5"),
    ("Notion", "ashby", "notion", "notion.so", "#e5e5e5"),
    ("Ramp", "ashby", "ramp", "ramp.com", "#e4f222"),
    ("Supabase", "ashby", "supabase", "supabase.com", "#3ecf8e"),
    ("Replit", "ashby", "replit", "replit.com", "#f26207"),
    ("Perplexity", "ashby", "perplexity", "perplexity.ai", "#20b8cd"),
]

INDIA = re.compile(
    r"\b(india|bengaluru|bangalore|hyderabad|pune|mumbai|gurgaon|gurugram|noida|delhi|new delhi|chennai|"
    r"kolkata|ahmedabad|jaipur|kochi|coimbatore|trivandrum|thiruvananthapuram|indore|chandigarh)\b", re.I)
ENGINEERING = re.compile(
    r"\b(engineer|engineering|developer|sde|software|swe|devops|sre|site reliability|backend|back-end|frontend|"
    r"front-end|full[ -]?stack|machine learning|ml|data scientist|data engineer|android|ios|mobile|platform|"
    r"infrastructure|security engineer|qa|test automation|architect)\b", re.I)
NOT_ENGINEERING = re.compile(r"\b(sales|account executive|recruit|marketing|legal|counsel|finance|hr|people partner)\b", re.I)

FRESH_DAYS = 14
ROTATE_LAST = 7
HOOKS = ["THEY ARE HIRING", "HIRING IN INDIA", "APPLY THIS WEEK", "JOBS DROPPED TODAY", "OPEN ROLES NOW",
         "DEVS WANTED NOW", "HIRING ENGINEERS NOW"]


def _parse_time(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):  # Lever: epoch milliseconds
        return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc)
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _jobs(client: httpx.Client, kind: str, token: str) -> list[dict[str, Any]]:
    """Normalise a board into [{title, location, url, published}]."""
    out: list[dict[str, Any]] = []
    if kind == "greenhouse":
        data = client.get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs").json()
        for j in data.get("jobs", []):
            out.append({"title": j.get("title", ""), "location": (j.get("location") or {}).get("name", ""),
                        "url": j.get("absolute_url", ""), "published": _parse_time(j.get("first_published") or j.get("updated_at"))})
    elif kind == "lever":
        for j in client.get(f"https://api.lever.co/v0/postings/{token}?mode=json").json():
            cats = j.get("categories") or {}
            locs = [cats.get("location") or ""] + list(cats.get("allLocations") or [])
            out.append({"title": j.get("text", ""), "location": " / ".join(dict.fromkeys(l for l in locs if l)),
                        "url": j.get("hostedUrl", ""), "published": _parse_time(j.get("createdAt"))})
    elif kind == "ashby":
        data = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{token}").json()
        for j in data.get("jobs", []):
            locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
            country = ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry") or ""
            out.append({"title": j.get("title", ""), "location": " / ".join(dict.fromkeys(l for l in locs + [country] if l)),
                        "url": j.get("jobUrl", ""), "published": _parse_time(j.get("publishedAt"))})
    return out


def _careers_url(kind: str, token: str) -> str:
    return {"greenhouse": f"https://boards.greenhouse.io/{token}", "lever": f"https://jobs.lever.co/{token}",
            "ashby": f"https://jobs.ashbyhq.com/{token}"}[kind]


def _city(location: str) -> str:
    m = INDIA.search(location)
    if not m:
        return "India"
    city = m.group(1).title()
    return {"Bangalore": "Bengaluru", "Gurgaon": "Gurugram", "India": "India"}.get(city, city)


def scan(log: Log = print) -> list[dict[str, Any]]:
    """Every company with at least one engineering opening in India, best first."""
    now = dt.datetime.now(dt.timezone.utc)

    def one(company: tuple[str, str, str, str, str]) -> dict[str, Any] | None:
        name, kind, token, domain, color = company
        try:
            with httpx.Client(timeout=25, headers={"User-Agent": "Mozilla/5.0 (code_tho_samsaram hiring bot)"}) as client:
                jobs = _jobs(client, kind, token)
        except Exception as exc:  # noqa: BLE001 - a dead board never blocks the rest
            log(f"Hiring: {name} board failed: {exc}")
            return None
        india = [j for j in jobs if INDIA.search(j["location"]) and ENGINEERING.search(j["title"])
                 and not NOT_ENGINEERING.search(j["title"])]
        if not india:
            return None
        fresh = [j for j in india if j["published"] and (now - j["published"]).days <= FRESH_DAYS]
        newest = sorted(india, key=lambda j: j["published"] or dt.datetime.min.replace(tzinfo=dt.timezone.utc), reverse=True)
        top = newest[0]
        cities = sorted({_city(j["location"]) for j in india}, key=lambda c: -sum(_city(j["location"]) == c for j in india))
        return {
            "name": name, "domain": domain, "color": color,
            "roles": len(india), "fresh": len(fresh),
            "top_role": re.sub(r"\s+", " ", top["title"]).strip()[:48],
            "cities": cities[:2],
            "url": _careers_url(kind, token),
            "score": len(fresh) * 3 + min(len(india), 30),
        }

    with cf.ThreadPoolExecutor(12) as pool:
        found = [c for c in pool.map(one, COMPANIES) if c]
    found.sort(key=lambda c: c["score"], reverse=True)
    log(f"Hiring: {len(found)} companies have engineering openings in India")
    return found


def recently_featured() -> set[str]:
    import topic_fetcher as tq

    items = [i for i in tq.load_queue() if i.get("category") == "hiring"]
    items.sort(key=lambda i: i.get("created_at", ""))
    return {c["name"] for i in items[-ROTATE_LAST:] for c in (i.get("hiring") or {}).get("companies", [])}


def _spoken_count(n: int) -> str:
    return f"{n}" if n < 100 else "over a hundred"


def build_item(companies: list[dict[str, Any]], day_tag: str) -> dict[str, Any]:
    import random

    import topic_fetcher as tq

    names = [c["name"] for c in companies]
    who = f"{names[0]}, {names[1]} and {names[2]}"
    lines = []
    for c in companies:
        where = " and ".join(c["cities"])
        lines.append(f"{c['name']} has {_spoken_count(c['roles'])} engineering roles open in {where}.")
    item = tq.make_item(
        category="hiring",
        topic=f"{who} are hiring engineers in India ({day_tag})",
        keyword="HIRING",
        keyword_spoken="hiring",
        hook=random.choice(HOOKS),
        script=f"{who} are hiring in India right now. " + " ".join(lines),
        link=companies[0]["url"],
        snippet="",
        caption=(f"🚨 {who} are hiring engineers in India right now.\n\n"
                 + "\n".join(f"🏢 {c['name']}: {c['roles']} open roles ({', '.join(c['cities'])}), e.g. {c['top_role']}"
                             for c in companies)),
        hashtags=["#hiring", "#jobsinindia", "#softwarejobs", "#bangalorejobs", "#developers"],
        source="career_boards",
    )
    item["id"] = f"hiring-{day_tag}"
    item["links"] = [{"label": c["name"], "url": c["url"]} for c in companies]
    item["hiring"] = {"companies": companies, "checked_at": tq.now_iso()}
    return item


def discover_hiring(log: Log = print, day_tag: str | None = None) -> dict[str, Any] | None:
    import topic_fetcher as tq

    day_tag = day_tag or dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date().isoformat()
    if tq.get_item(f"hiring-{day_tag}"):
        log(f"Hiring: today's reel hiring-{day_tag} is already queued")
        return None
    ranked = scan(log)
    skip = recently_featured()
    picks = [c for c in ranked if c["name"] not in skip][:3]
    if len(picks) < 3:  # not enough new names: allow repeats rather than skip the day
        picks += [c for c in ranked if c not in picks][: 3 - len(picks)]
    if len(picks) < 3:
        log("Hiring: fewer than 3 companies with India openings found, skipping today")
        return None
    log("Hiring: " + ", ".join(f"{c['name']} ({c['roles']} roles, {c['fresh']} new)" for c in picks))
    return build_item(picks, day_tag)


def main() -> None:
    import topic_fetcher as tq

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    item = discover_hiring()
    if not item:
        return
    if args.dry_run:
        import json

        print(json.dumps({k: item[k] for k in ("id", "hook", "script", "links", "caption")}, indent=2, ensure_ascii=False))
        return
    tq.append_items([item])
    print(f"Queued {item['id']}")


if __name__ == "__main__":
    main()
