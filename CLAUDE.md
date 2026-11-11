# @code_tho_samsaram Reel Factory

Faceless Instagram Reels engine for the **@code_tho_samsaram** account. Niche (since 2026-11-11, user's request): daily DSA patterns, interview concepts explained simply, and coding quizzes, plus a daily India hiring reel. Trending repos/AI tools are only a fallback. Everything runs on free tiers: Vercel for the webhook and dashboard, GitHub Actions for rendering and posting, edge-tts, Whisper and Pexels. Videos go straight to Meta through resumable upload, with no public host (tmpfiles.org's direct links stopped working).

## Files

| File | Role |
|---|---|
| `config.py` | Loads env vars (plus an optional `.env`). Exposes `settings`. Creates `data/`, `output/`, `assets/`. |
| `topics_queue.json` | The reel queue. Source of truth for keywords, DM links, statuses and published media IDs. |
| `topic_fetcher.py` | Topic Discovery Engine and the queue store (load/save/update/append with atomic writes). `discover_evergreen` keeps `EVERGREEN_TARGET` reels of each daily category queued: library first, then Gemini top-up. Trending sources run only while fewer than `TRENDING_RESERVE` trending reels are queued. |
| `content_library.py` | Hand-written DSA (with tests), interview-concept and quiz entries, their checks (`check_dsa` runs tests in an isolated subprocess; Gemini output must pass too) and builders that emit explicit storyboards. |
| `storyboard.py` | Turns a queue item into narrated, timed scenes per category (DSA traces run the real algorithm). |
| `auto_pipeline.py` | Render orchestrator: storyboard → edge-tts → Whisper → sound design → Remotion. Also the Meta publisher. |
| `check_token.py` | Can the stored token still publish, and when does it run out? Runs before each render and daily in `token-check.yml`. |
| `hiring.py` | Daily "hiring in India" reel: top 3 companies by fresh India engineering openings, from public Greenhouse/Lever/Ashby boards. |
| `.github/workflows/reel.yml` | Wakes every 15 minutes; posts only when `slot_gate.py` says today is behind. |
| `slot_gate.py` | The 6 slots, IST: 08 dsa, 11 interview, 13 hiring, 15 quiz, 18 dsa, 21 interview. Compares what is due with what is on Instagram, so missed runs fix themselves, and picks the first due category still short today. `auto_pipeline.next_for` falls back through `FALLBACK` when a category's queue is empty. |
| `video/` | Remotion (React) project that renders 1080×1920 motion graphics from `output/<id>/props.json`. |
| `main.py` | FastAPI app: Meta webhook, auto-DM worker, dashboard REST API, WebSocket log stream. |
| `static/dashboard.html` | Single-file command dashboard (Tailwind, FontAwesome and Chart.js from CDNs). |

Runtime folders (git-ignore them): `.env`, `data/` (webhook state), `output/` (renders), `assets/stock/` (Pexels cache). `assets/fonts/` is downloaded automatically. Keep `assets/music/` and `assets/sfx/` if you add your own files.

## Architecture

```
                    ┌──────────────────────── GitHub Actions (cron, free) ────────────────────────┐
                    │                                                                             │
 GitHub Trending ─┐ │  topic_fetcher.py ──append──▶ topics_queue.json ◀──status/media_id── auto_pipeline.py
 GitHub Search  ──┤ │   (discover)                     ▲    │                                │    │
 HN Show HN (AI) ─┼─┼──────────────────────────────────┘    │ git push                       │    │
 Google CSE     ──┤ │                                       │                                │    │
 DSA library    ──┘ └───────────────────────────────────────┼────────────────────────────────┼────┘
                                                            ▼                                │
                                              Render auto-deploy (free web service)          │
                                                            │                                │
   Instagram comment ──Meta webhook──▶ POST /webhook ──▶ main.py                             │
                                        │ verify X-Hub-Signature-256                         │
                                        │ dedupe comment id, 24h per-user cooldown            │
                                        │ keyword → queue item (by ig_media_id, then keyword) │
                                        ▼                                                    │
                                   DM queue ─token bucket─▶ POST /{ig-id}/messages            │
                                        │                  {recipient:{comment_id}}          │
                                        └─▶ POST /{comment-id}/replies ("check your DMs")    │
                                                                                             │
   /dashboard ◀── /api/stats /api/queue /api/fetch-trending /ws/logs                         │
                                                                                             │
 auto_pipeline.py render: storyboard → edge-tts → Whisper words → props.json ──────────────┘
                          → ducked music + SFX → Remotion MP4 → /media (REELS, resumable) → upload to Meta
                          → poll status_code=FINISHED → /media_publish → permalink
```

## Reel spec (enforced in code)

- **Length per category** (`storyboard.LENGTHS`): `dsa` and `repo` run 20–34 s; `hiring` 14–26 s; everything else 7–12 s.
  `voice_scenes` synthesizes every scene, and if the reel runs long it raises the speaking rate (from `+15%`, max `+40%`), scaled by how much *speech* must go (padding and `MIN_DUR` don't shrink). Still too long → optional scenes are dropped. Too short → stretchable scenes grow.
- **Library formats** (`content_library`): DSA hook → problem → naive → approach steps (`how`) → code → CTA. Interview hook → simple analogy (`how`) → "say this" cards (`use_cases`) → CTA. Quiz hook → `quiz` scene (question, optional code, 4 options, spoken 3-2-1 countdown timed by Whisper cues on "three/two/one", reveal on "answer") → quiz CTA (`QuizCta`, no DM promise). Quiz `say` text must not contain "three" or "answer".
- **Legacy formats:** `dsa` hook → problem → naive (O(n) stamp) → animated trace → code → CTA. `repo` hook → repo card → how it works → setup demo → use cases → CTA. Others hook → browser/compare/code → CTA. A queue item can carry an explicit `storyboard` list to hand-author a reel.
- **3-word hook** first; `validate_item` rejects other hook lengths. Captions are hidden on hook and CTA scenes.
- **Captions:** karaoke words timed to Whisper timestamps, aligned back to the script text (`align_to_script`).
- **Audio:** the hook is voice only (user disliked per-word hits: the "dum dum dum"). A drumless bed (or `assets/music/*`) fades in after the hook, ducked to 25 % under the voice. Whoosh on every cut, bright snaps on stamps, typing clicks, per-step ticks, a riser into the CTA. No sound has a sub-bass thump.
- **Editing:** every reel draws one option per axis in `storyboard.AXES`. `storyboard.emphasis` marks stressed words; the camera moves on them, strong ones also fire a burst. The camera is scaled to 35 % on full-width layouts so it never crops them. Avatars are soft 3D-style human characters in SVG (`Presenter.tsx`), never robots or flat cartoons (user's rule), and male only because the voice is male (user's rule), with mouth shapes from word timings.
- **Spoken opening (user's rule, every reel):** the interesting line first, then "Day N." (`storyboard.spoken_opening`). DSA continues "Imagine you get this question in your interview.", then goes straight into the problem and explanation. Interview reels add "Here it is, explained simply." and quizzes "Let's see if you get it right." (`storyboard.OPENING_FOLLOW`).
- **Day N** badge at the top and "Day N" in the caption; Day 1 = `DAY_ONE` (2026-11-04, IST). No progress bar at the bottom (user asked to remove it).
- **Styles** (`storyboard.pick_style`): weighted-random per axis (look, hook, captions, cta, hookFont, presenter), never repeating the previous reel's choice, weighted by `learned_weights` from Insights (`engagement_score`: likes + 3·comments + 4·shares + 3·saves per view). Chosen style is saved as `style_used`; `style` on an item pins axes. Hiring reels always use the `triple` (follow/like/comment) ending.
- **Exactly 5 hashtags.** `validate_item` pads or truncates.
- **Voice:** `en-US-AndrewNeural` at `+4%`, pitch `+6Hz` (user asked twice for less bass). Max speed-up `+22%`. `voice_eq`: high-pass at 170 Hz, chest cut under 380 Hz, highs lifted; all music under 220 Hz is removed, music level 0.36. The CTA scene says "Comment {keyword_spoken} and I'll DM you the link."
- **edge-tts throttling:** bursts get empty streams (`NoAudioReceived`). TTS runs 2 at a time with exponential-backoff retries; keep it that way.
- **Remotion** occasionally loses its temp audio-mixing dir on Windows; `render_remotion` retries once.

Fallbacks, so a render always finishes:
- No `PEXELS_API_KEY`: the hook uses the animated background.
- Nothing in `assets/music/`: a procedural drumless bed plays instead (`music` style axis).
- Whisper not installed: edge-tts WordBoundary timings are used.

## Queue item schema

```jsonc
{
  "id": "seed-03-bitxor",            // unique
  "topic": "Solve array duplicates in O(1) space with Bitwise XOR",
  "keyword": "BITXOR",               // A-Z0-9, 3-20 chars, comment trigger
  "keyword_spoken": "bit X-O-R",     // how the voice says it in the CTA
  "category": "dsa",                 // dsa | interview | quiz | hiring | ai_tool | repo | dev_tip | website
  "hook": "XOR KILLS DUPLICATES",    // exactly 3 words
  "script": "…",                     // voice body; CTA is appended automatically
  "link": "https://…",               // what the auto-DM sends
  "code": {"language": "python", "filename": "x.py", "snippet": "…"},
  "stock_queries": ["…"],            // Pexels searches
  "hashtags": ["#a","#b","#c","#d","#e"],
  "caption": "…",
  "status": "queued",                // queued | rendering | rendered | published | failed
  // set by the pipeline:
  "video_path": "output/<id>/reel.mp4", "ig_media_id": "…", "permalink": "…", "published_at": "…", "error": "…"
}
```

Keyword resolution in `main.resolve_item`:
1. The keyword of the queue item whose `ig_media_id` matches the commented media.
2. A generic trigger (`LINK`, `CODE`, `SEND`, `DM`, or a category keyword) on that same media.
3. A global keyword match. Published items win, then the most recently created.
4. A category keyword (`AITOOL`, `REPO`, `LEETCODE`, `WEBSITE`, `ASYNC`) resolves to the freshest item in that category.

## Environment schema

| Variable | Required for | Default | Notes |
|---|---|---|---|
| `INSTAGRAM_ACCESS_TOKEN` | publish, DMs, insights | — | Long-lived token. `IGAA…` (Instagram Login) is sent to `graph.instagram.com`; `EAA…` (Facebook Login page token) to `graph.facebook.com`. |
| `INSTAGRAM_USER_ID` | publish, DMs | — | The IG professional account ID. |
| `VERIFY_TOKEN` | webhook setup | — | Any random string; enter the same one in the Meta dashboard. |
| `PEXELS_API_KEY` | stock footage | — | Free at pexels.com/api. |
| `GOOGLE_SEARCH_API_KEY` | discovery (optional) | — | Custom Search JSON API. |
| `GOOGLE_SEARCH_CX` | discovery (optional) | — | Programmable Search Engine ID. Google search is skipped unless both Google vars are set. |
| `GEMINI_API_KEY` | discovery (optional) | — | Gemini with Google Search grounding finds this week's repos and AI tools; every URL is checked before it is queued. |
| `GEMINI_MODEL` | discovery | `gemini-flash-latest` | Any model that supports the `google_search` tool. |
| `META_APP_SECRET` | webhook security | — | Turns on `X-Hub-Signature-256` verification. **Set this in production.** |
| `FACEBOOK_PAGE_ID` | DMs on graph.facebook.com | `me` | Only for Facebook-Login setups. |
| `GRAPH_API_VERSION` | — | `v23.0` | |
| `GRAPH_API_HOST` | — | auto | Overrides the host auto-detection. |
| `DASHBOARD_TOKEN` | dashboard auth | — | When set, every `/api/*` route and `/ws/logs` require it. **Set this on Render.** |
| `GITHUB_TOKEN` | discovery (optional) | — | Raises the GitHub Search API rate limit. |
| `ACCOUNT_HANDLE` | — | `code_tho_samsaram` | |
| `TTS_VOICE` / `TTS_RATE` / `TTS_PITCH` | — | `en-US-AndrewNeural` / `+4%` / `+6Hz` | |
| `WHISPER_MODEL` | — | `base` | `tiny` is faster on CI. |
| `DM_RATE_PER_HOUR` | — | `180` | Outbound DM token bucket, kept under Meta's limits. |
| `DM_COOLDOWN_HOURS` | — | `24` | One DM per user per item within this window. |
| `PUBLIC_REPLY_ENABLED` / `PUBLIC_REPLY_TEXT` | — | `true` / "Sent! Check your DMs 📩🔥" | Public reply under the comment, which also boosts engagement. |
| `EST_VIEWS_PER_COMMENT` | — | `100` | Used for "Est. Views" until Insights data exists. |
| `DATA_DIR`, `OUTPUT_DIR`, `ASSETS_DIR`, `QUEUE_FILE` | — | project folders | |

## Local development

```bash
python -m venv .venv && .venv\Scripts\activate          # Windows (source .venv/bin/activate elsewhere)
pip install torch --index-url https://download.pytorch.org/whl/cpu   # small CPU-only torch for Whisper
pip install -r requirements-render.txt
cd video && npm ci && cd ..                               # Remotion (Node 18+)
python auto_pipeline.py --id seed-03-bitxor --no-publish  # → output/seed-03-bitxor/reel.mp4
python topic_fetcher.py --dry-run                         # preview discoveries
uvicorn main:app --port 8000                              # http://localhost:8000/dashboard
```

Don't use `--reload` on Windows. The reloader breaks the worker threads and the WebSocket.

To test the webhook locally, use the dashboard's **Dry-run webhook** form. It never sends real DMs. To test against real Meta traffic, expose port 8000 with a tunnel (`cloudflared tunnel --url http://localhost:8000`).

## Meta app setup (once)

1. In developers.facebook.com, create an app of type **Business** and add the **Instagram** product, using *API setup with Instagram login*.
2. Connect the @code_tho_samsaram professional account and generate a token with these scopes: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_comments`, `instagram_business_manage_messages`. Exchange it for a long-lived token, which lasts 60 days. Refresh it with `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=…`.
3. Under **Webhooks**, set the callback URL to `https://<render-app>.onrender.com/webhook` and the verify token to `VERIFY_TOKEN`. Subscribe to the **comments** field.
4. In the Instagram app, turn on **Settings → Messages → Connected tools → Allow access to messages**.
5. Until the app passes App Review with Advanced Access, webhooks and DMs only fire for accounts that have a role on the app.

## Deploy the webhook on Render (free)

`render.yaml` at the repo root:

```yaml
services:
  - type: web
    name: code-tho-samsaram
    runtime: python
    plan: free
    buildCommand: pip install fastapi "uvicorn[standard]" httpx pydantic beautifulsoup4
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.9"
      - key: INSTAGRAM_ACCESS_TOKEN
        sync: false
      - key: INSTAGRAM_USER_ID
        sync: false
      - key: VERIFY_TOKEN
        sync: false
      - key: META_APP_SECRET
        sync: false
      - key: DASHBOARD_TOKEN
        sync: false
      - key: GOOGLE_SEARCH_API_KEY
        sync: false
      - key: GOOGLE_SEARCH_CX
        sync: false
```

On Render the build installs only the server dependencies, so the dashboard's Render buttons report "render deps not installed here". That is intentional: torch and Whisper don't fit in the free 512 MB instance. Rendering happens in GitHub Actions.

Free-tier caveats:
- The free instance sleeps after 15 minutes idle. Meta retries webhook deliveries, so wake-ups are survivable, but a free uptime pinger on `/api/health` keeps DMs instant.
- `data/state.json` (DM history and stats) lives on Render's ephemeral disk and resets on every deploy.
- Each push from the Actions bot redeploys the service. That is how the server learns the new `ig_media_id` → keyword mapping.

## Render + publish with GitHub Actions (free)

The workflow lives in `.github/workflows/reel.yml`: 2 DSA + 2 interview + 1 quiz + 1 hiring reel a day, run as `auto_pipeline.py --category <kind>`. It ticks every 15 minutes and `slot_gate.py` decides whether a reel is due, catching up one reel per tick within the same IST day. Runs start up to 30 minutes before a slot (`slot_gate.LEAD`) and `auto_pipeline.hold_for_slot` holds the post until the slot time. GitHub's schedule runs late (about hourly in practice), so cron-job.org also calls `workflow_dispatch` with `gated=true`, which goes through the same gate; other manual dispatches skip it. A run that posts discovers (`topic_fetcher.py --limit 2`, or `hiring.py` for the hiring reel; failure here is not fatal), renders + publishes (`auto_pipeline.py [--category hiring]`), then commits `topics_queue.json` back. No hiring reel falls back to a dev reel. A published reel is never posted again: an empty queue fails the run and opens an alert, and the next tick discovers again.

Add the secrets under **Settings → Secrets and variables → Actions**: `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`, optional `PEXELS_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_CX`.

## Deploy (Vercel)

Live at https://code-tho-samsaram.vercel.app (project `code-tho-samsaram`). `npx vercel deploy --prod --yes`. `config.SERVERLESS` (the `VERCEL` env var) moves runtime state to `/tmp` and sends DMs inline in the webhook request. `DASHBOARD_TOKEN`/`VERIFY_TOKEN` are Vercel production env vars; a local copy is in `.deploy-secrets`. The dashboard API takes the token as the `X-Dashboard-Token` header or `?token=`.

## Going live (free path: Vercel + GitHub Actions)

Chosen over Render because Vercel's free plan doesn't sleep and the webhook already works there. Use a public GitHub repo for unlimited Actions minutes.

1. Put the Instagram values in `.env` (the list is at the top of `setup_instagram.py`), then run `python setup_instagram.py --push owner/repo`. It upgrades the token and stores secrets in Vercel and GitHub without printing them.
2. `reel.yml` deploys to Vercel after each run using `VERCEL_TOKEN`, which updates the dashboard and keyword map. No Vercel-GitHub link is needed.
3. Meta callback URL: `https://code-tho-samsaram.vercel.app/webhook`, verify token: `VERIFY_TOKEN`, field: `comments`.
4. `refresh-token.yml` renews `IGAA` tokens weekly (needs the `GH_PAT` secret; `VERCEL_TOKEN` also updates Vercel) and skips `EAA` tokens.

The never-expiring Page token does both jobs: GitHub posts with it (`setup_instagram.py --push-posting owner/repo`, which refuses anything that isn't valid, permanent and able to publish) and Vercel sends DMs with it (`--dm-token`, then `--push-dm`). `INSTAGRAM_ACCESS_TOKEN` in `.env` is only an input to `--dm-token`, and usually short-lived. Its data access still has an end date, about 90 days out.

A bad token raises an alert instead of losing a day: `token-check.yml` runs at 06:00 IST, failed reel runs do the same, and both open a GitHub issue assigned to the owner (`.github/alert-issue.sh`). The pipeline checks the token before rendering, so a dead one costs no render and none of the reel's attempts. DMs go to `/{instagram-id}/messages`. They need **Allow access to messages** on in the Instagram app, and App Review before they reach accounts without a role on the app.

`process_topic` refuses to publish without credentials before touching the item, and a failed reel goes back to `queued` until its third attempt (`MAX_ATTEMPTS`).

## Conventions

- All queue writes go through `topic_fetcher` (`append_items`, `update_item`, `delete_item`). These hold a lock and replace the file atomically. Never write `topics_queue.json` by hand while the server is running.
- `main.py` reads the queue through `queue_items()`, which caches it and reloads when the file's mtime changes. Edits from a render thread or a redeploy are picked up automatically.
- **No repeats (user's rule).** `topic_fetcher.topic_keys` identifies a topic by link, title, product name and DSA idea (`SAME_DSA_TOPIC`); sharing any key makes two items the same reel. Published items stay in the queue file as the history, and `delete_item` records keys under `removed`, so deleted topics don't come back. Sources call `unseen` before cutting to their limit. `topic_fetcher.py` stops fetching at `MAX_BACKLOG` queued reels.
- Discovery sources are best-effort. Each one catches its own errors and logs them, so one dead source never blocks the rest.
- Inspect a render without playing it: `imageio_ffmpeg`'s ffmpeg (Remotion's bundled one lacks the `select` filter).
- The pipeline imports heavy dependencies (whisper, edge-tts) lazily, so `main.py` runs without them.
- DMs are Instagram *private replies*, sent with `recipient.comment_id`. Meta allows one private reply per comment, within 7 days of the comment. The cooldown and comment dedupe in `StateStore` follow from that.
