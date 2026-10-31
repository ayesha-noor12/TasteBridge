"""Environment settings, city config and ranking weights.

Changing the demo city means editing CITY (and providing a matching curated file).
"""

import os
from pathlib import Path

VERSION = "0.1.0"

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
FIXTURES_DIR = BACKEND_DIR / "tests" / "fixtures"
STATIC_DIR = BACKEND_DIR / "static"

# --- City (single demo city, configurable here) ---
CITY = {
    "name": "Toronto",
    "qloo_location_query": "Toronto",
    "curated_file": "curated_toronto.json",
}

# --- Qloo ---
QLOO_TIMEOUT_SECONDS = 20.0
QLOO_MAX_CONCURRENCY = 2
QLOO_RAW_MAX_CHARS = 1500  # truncation for evidence.raw shown in the UI

# --- Sessions ---
SESSION_TTL_SECONDS = 2 * 60 * 60

# --- Input limits (user text is untrusted) ---
MAX_LOVED_ITEMS = 8
MAX_TEXT_LEN = 80
MAX_ORIGIN_LEN = 60

# --- Ranking weights (must sum to 1.0; enforced by tests) ---
WEIGHTS = {
    "taste_match": 0.45,
    "preserve_match": 0.20,
    "affordability": 0.15,
    "proximity": 0.10,
    "social_bonus": 0.10,
}

# Which "preserve" chips a category satisfies.
CATEGORY_PRESERVE = {
    "food": {"food", "familiarity"},
    "music": {"music", "festivals"},
    "social": {"friends", "language"},
    "venue": {"nightlife", "familiarity"},
    "activity": {"festivals", "language"},
}

# --- Planner ---
PLAN_DAYS = 7
MAX_ITEMS_PER_DAY = 2
MAX_PLAN_ITEMS = 9  # one per day, plus up to two weekend extras
# Used only when an item's duration is unknown; the plan notes say so.
DEFAULT_ITEM_HOURS = 1.0

# --- Feedback ---
BUDGET_CUT = 0.30
FAMILIARITY_STEP = 0.25
SOCIAL_BOOST_STEP = 0.5
SOCIAL_BOOST_MAX = 1.5
MIN_SOCIAL_MAX = 4  # guaranteed social items after repeated "not alone" clicks


def qloo_mode() -> str:
    return "live" if os.getenv("QLOO_MODE", "mock").lower() == "live" else "mock"


def qloo_bin() -> str:
    return os.getenv("QLOO_BIN", "qloo")


def cache_dir() -> Path:
    return Path(os.getenv("CACHE_DIR", str(BACKEND_DIR.parent / "cache")))


def llm_mode() -> str:
    on = os.getenv("LLM_MODE", "off").lower() == "on"
    return "on" if on and os.getenv("LLM_API_KEY") else "off"


def llm_settings() -> dict:
    return {
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_BASE_URL") or None,
        "model": os.getenv("LLM_MODEL", ""),
    }


def secret_values() -> list[str]:
    """Env values that must never appear in logs, errors or responses."""
    names = ("QLOO_API_KEY", "LLM_API_KEY")
    return [v for v in (os.getenv(n, "") for n in names) if len(v) >= 4]


def redact(text: str) -> str:
    for secret in secret_values():
        text = text.replace(secret, "[redacted]")
    return text
