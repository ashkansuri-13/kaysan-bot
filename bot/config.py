"""پیکربندی مرکزی Kaysan — از .env خوانده می‌شود."""
import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_DIR / ".env")


def _int(name, default):
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _float(name, default):
    try:
        return float(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _list(name, default=""):
    raw = os.getenv(name, default).strip()
    return [x.strip() for x in raw.split(",") if x.strip()]


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "").strip()
OWNER_ID = _int("OWNER_ID", 0)
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "ashkan_surii").strip().lstrip("@")

DEFAULT_LANG = (os.getenv("DEFAULT_LANG", "ku").strip() or "ku")
FREE_MESSAGE_LIMIT = _int("FREE_MESSAGE_LIMIT", 100)

BOT_API_BASE_URL = os.getenv("BOT_API_BASE_URL", "").strip()
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "/tmp/kaysan").strip())
USE_COLORED_BUTTONS = _bool("USE_COLORED_BUTTONS", True)

PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "").strip()
ROUTER_MODELS = _list("ROUTER_MODELS", "deepseek/deepseek-chat")
CHAT_MODELS = _list("CHAT_MODELS", "deepseek/deepseek-chat")
CODE_MODELS = _list("CODE_MODELS", "deepseek/deepseek-chat")
REASON_MODELS = _list("REASON_MODELS", "deepseek/deepseek-chat")
LONG_MODELS = _list("LONG_MODELS", "deepseek/deepseek-chat")
VISION_MODELS = _list("VISION_MODELS", "openai/gpt-4o-mini")
AUDIO_MODELS = _list("AUDIO_MODELS", "")
PROMPT_ENHANCER_MODEL = _list("PROMPT_ENHANCER_MODEL", "deepseek/deepseek-chat")
IMAGE_MODEL = _list("IMAGE_MODEL", "")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DAILY_COST_LIMIT = float(os.getenv("DAILY_COST_LIMIT", "5.0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "midnight_logs").strip().lstrip("@")

SEARCH_CHANNELS_RAW = os.getenv("SEARCH_CHANNELS", "").strip()
SEARCH_CHANNELS = [c.strip().lstrip("@") for c in SEARCH_CHANNELS_RAW.split(",") if c.strip()]

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

REDIS_URL = os.getenv("REDIS_URL", "").strip()

DB_PATH = Path(__file__).resolve().parent.parent / "kaysan.db"
SUPPORTED_LANGS = ("ku", "fa", "en")

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MODELS_BY_CATEGORY = {
    "chat": CHAT_MODELS,
    "persian": CHAT_MODELS,
    "code": CODE_MODELS,
    "reason": REASON_MODELS,
    "long": LONG_MODELS,
    "vision": VISION_MODELS,
    "audio": AUDIO_MODELS,
    "image": IMAGE_MODEL if isinstance(IMAGE_MODEL, list) else [IMAGE_MODEL] if IMAGE_MODEL else [],
    "router": ROUTER_MODELS,
    "prompt_enhancer": PROMPT_ENHANCER_MODEL,
}

# ===== تنظیمات جدید =====

MAX_HISTORY_MESSAGES = 10

TEMP_CHAT = _float("TEMP_CHAT", 0.8)
TEMP_CODE = _float("TEMP_CODE", 0.2)
TEMP_REASON = _float("TEMP_REASON", 0.3)
TEMP_CREATIVE = _float("TEMP_CREATIVE", 0.9)

MAX_TOKENS_CHAT = _int("MAX_TOKENS_CHAT", 3000)
MAX_TOKENS_CODE = _int("MAX_TOKENS_CODE", 8000)
MAX_TOKENS_REASON = _int("MAX_TOKENS_REASON", 4000)
MAX_TOKENS_LONG = _int("MAX_TOKENS_LONG", 8000)

ENABLE_STREAMING = _bool("ENABLE_STREAMING", True)
ENABLE_QUALITY_CHECK = _bool("ENABLE_QUALITY_CHECK", True)

MIN_REPLY_WORDS = _int("MIN_REPLY_WORDS", 15)

TEMP_BY_INTENT = {
    "chat": TEMP_CHAT,
    "code": TEMP_CODE,
    "reason": TEMP_REASON,
    "creative": TEMP_CREATIVE,
}

MAX_TOKENS_BY_INTENT = {
    "code": MAX_TOKENS_CODE,
    "reason": MAX_TOKENS_REASON,
    "chat": MAX_TOKENS_CHAT,
    "long": MAX_TOKENS_LONG,
}
