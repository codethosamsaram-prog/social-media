"""Environment loader for the @code_tho_samsaram reel factory.

Every module imports ``settings`` from here. Values come from the process
environment, with an optional ``.env`` file next to this module filling in
anything that is not already set (real environment variables always win, so
Render / GitHub Actions secrets override a stale local file).
"""

from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# Vercel (serverless): the deployment bundle is read-only, only /tmp is writable, and nothing
# runs between requests. Runtime state goes to /tmp and webhook DMs are sent inline.
SERVERLESS = bool(os.environ.get("VERCEL"))
RUNTIME_DIR = Path("/tmp/reel-factory") if SERVERLESS else BASE_DIR


def _load_dotenv(path: Path) -> None:
    """Minimal .env parser: KEY=value, optional quotes, # comments, `export` prefix."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name) or default)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name).lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _graph_host(token: str) -> str:
    """Instagram-Login tokens (IGAA...) live on graph.instagram.com; Facebook-Login
    page tokens (EAA...) live on graph.facebook.com. GRAPH_API_HOST overrides."""
    explicit = _env("GRAPH_API_HOST")
    if explicit:
        return explicit.replace("https://", "").rstrip("/")
    if token and not token.startswith("IG"):
        return "graph.facebook.com"
    return "graph.instagram.com"


@dataclass(frozen=True)
class Settings:
    # --- required by the spec -------------------------------------------------
    google_search_api_key: str
    pexels_api_key: str
    instagram_access_token: str
    instagram_user_id: str
    verify_token: str
    # --- optional extras --------------------------------------------------------
    google_search_cx: str
    gemini_api_key: str
    gemini_model: str
    meta_app_secret: str
    facebook_page_id: str
    graph_api_version: str
    graph_api_host: str
    dashboard_token: str
    github_token: str
    account_handle: str
    tts_voice: str
    tts_rate: str
    tts_pitch: str
    day_one: dt.date
    day_number_override: int
    whisper_model: str
    dm_rate_per_hour: int
    dm_cooldown_hours: int
    public_reply_enabled: bool
    public_reply_text: str
    est_views_per_comment: int
    # --- paths -------------------------------------------------------------------
    base_dir: Path
    queue_file: Path
    data_dir: Path
    output_dir: Path
    assets_dir: Path
    static_dir: Path

    @classmethod
    def load(cls) -> "Settings":
        token = _env("INSTAGRAM_ACCESS_TOKEN")
        data_dir = Path(_env("DATA_DIR") or RUNTIME_DIR / "data")
        output_dir = Path(_env("OUTPUT_DIR") or RUNTIME_DIR / "output")
        assets_dir = Path(_env("ASSETS_DIR") or RUNTIME_DIR / "assets")
        for folder in (data_dir, output_dir, assets_dir):
            folder.mkdir(parents=True, exist_ok=True)
        queue_file = Path(_env("QUEUE_FILE") or BASE_DIR / "topics_queue.json")
        if SERVERLESS and not _env("QUEUE_FILE"):
            # Writable copy of the bundled queue; edits made here last only as long as the instance.
            tmp_queue = RUNTIME_DIR / "topics_queue.json"
            if not tmp_queue.exists() and queue_file.exists():
                tmp_queue.write_bytes(queue_file.read_bytes())
            queue_file = tmp_queue
        return cls(
            google_search_api_key=_env("GOOGLE_SEARCH_API_KEY"),
            pexels_api_key=_env("PEXELS_API_KEY"),
            instagram_access_token=token,
            instagram_user_id=_env("INSTAGRAM_USER_ID"),
            verify_token=_env("VERIFY_TOKEN"),
            google_search_cx=_env("GOOGLE_SEARCH_CX"),
            gemini_api_key=_env("GEMINI_API_KEY"),
            gemini_model=_env("GEMINI_MODEL", "gemini-flash-latest"),
            meta_app_secret=_env("META_APP_SECRET"),
            facebook_page_id=_env("FACEBOOK_PAGE_ID"),
            graph_api_version=_env("GRAPH_API_VERSION", "v23.0"),
            graph_api_host=_graph_host(token),
            dashboard_token=_env("DASHBOARD_TOKEN"),
            github_token=_env("GITHUB_TOKEN"),
            account_handle=_env("ACCOUNT_HANDLE", "code_tho_samsaram").lstrip("@"),
            tts_voice=_env("TTS_VOICE", "en-US-AndrewNeural"),   # warm, gentle (was the deep ChristopherNeural)
            tts_rate=_env("TTS_RATE", "+4%"),
            tts_pitch=_env("TTS_PITCH", "+6Hz"),
            day_one=dt.date.fromisoformat(_env("DAY_ONE", "2026-11-04")),
            day_number_override=_env_int("DAY_NUMBER", 0),
            whisper_model=_env("WHISPER_MODEL", "base"),
            dm_rate_per_hour=max(1, _env_int("DM_RATE_PER_HOUR", 180)),
            dm_cooldown_hours=max(0, _env_int("DM_COOLDOWN_HOURS", 24)),
            public_reply_enabled=_env_bool("PUBLIC_REPLY_ENABLED", True),
            public_reply_text=_env("PUBLIC_REPLY_TEXT", "Sent! Check your DMs 📩🔥"),
            est_views_per_comment=max(1, _env_int("EST_VIEWS_PER_COMMENT", 100)),
            base_dir=BASE_DIR,
            queue_file=queue_file,
            data_dir=data_dir,
            output_dir=output_dir,
            assets_dir=assets_dir,
            static_dir=BASE_DIR / "static",
        )

    @property
    def graph_base(self) -> str:
        return f"https://{self.graph_api_host}/{self.graph_api_version}"

    @property
    def instagram_ready(self) -> bool:
        return bool(self.instagram_access_token and self.instagram_user_id)

    def require(self, *names: str) -> None:
        """Raise a readable error listing every missing setting (by env-var name)."""
        missing = [n.upper() for n in names if not getattr(self, n)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    def status(self) -> dict[str, bool]:
        """Which integrations are configured, for the dashboard (never exposes values)."""
        return {
            "instagram": self.instagram_ready,
            "verify_token": bool(self.verify_token),
            "signature_check": bool(self.meta_app_secret),
            "pexels": bool(self.pexels_api_key),
            "google_search": bool(self.google_search_api_key and self.google_search_cx),
            "gemini": bool(self.gemini_api_key),
            "dashboard_auth": bool(self.dashboard_token),
        }


settings = Settings.load()
