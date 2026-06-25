#!/usr/bin/env python3
"""Kaysan AI Web Server — with personality, streaming, auth, security headers."""
import asyncio
import hashlib
import json
import logging
import os
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path

from aiohttp import web
from agent import detect_feature_request, get_feature_response
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from bot.prompt_enhancer import enhance_prompt_engine, detect_prompt_type, get_optimal_model, get_optimal_temperature, get_optimal_max_tokens
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from bot.services.image import generate as generate_image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bot import config, openrouter, router
from bot.texts import SYSTEM_PROMPTS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kaysan.web")

WEB_DIR = Path(__file__).resolve().parent

API_KEY = os.getenv("WEB_API_KEY", secrets.token_hex(16))
API_KEYS_FILE = WEB_DIR.parent / ".web_api_keys"

_auth_cache = {}
_auth_cache_ttl = 300

MODEL_TYPE_MAP = {
    "auto": None,
    "chat": config.CHAT_MODELS,
    "code": config.CODE_MODELS,
    "reason": config.REASON_MODELS,
    "vision": config.VISION_MODELS,
}

PERSONALITY_PRESETS = {
    "balanced": {
        "name": "متعادل",
        "name_en": "Balanced",
        "icon": "⚖️",
        "tone": "normal",
        "verbosity": "normal",
        "humor": "medium",
        "emotion": "normal",
        "formality": "mixed",
        "emoji_usage": "normal",
        "sarcasm": "low",
        "honesty": "direct",
        "custom_prompt": "",
    },
    "blunt": {
        "name": "رُک و راست",
        "name_en": "Blunt",
        "icon": "🔪",
        "tone": "direct",
        "verbosity": "short",
        "humor": "low",
        "emotion": "calm",
        "formality": "informal",
        "emoji_usage": "minimal",
        "sarcasm": "medium",
        "honesty": "brutal",
        "custom_prompt": "You are brutally honest and direct. No sugar-coating. Get straight to the point. Short, punchy responses.",
    },
    "exaggerated": {
        "name": "اغراق‌آمیز",
        "name_en": "Exaggerated",
        "icon": "🎭",
        "tone": "enthusiastic",
        "verbosity": "long",
        "humor": "high",
        "emotion": "enthusiastic",
        "formality": "informal",
        "emoji_usage": "lots",
        "sarcasm": "low",
        "honesty": "diplomatic",
        "custom_prompt": "You are EXTREMELY enthusiastic and dramatic! Everything is AMAZING! Use lots of exclamation marks!!! Express everything with maximum excitement and exaggeration! Use many emojis!!!",
    },
    "friendly": {
        "name": "کاربرپسند",
        "name_en": "User-Friendly",
        "icon": "🤗",
        "tone": "warm",
        "verbosity": "normal",
        "humor": "medium",
        "emotion": "warm",
        "formality": "informal",
        "emoji_usage": "normal",
        "sarcasm": "none",
        "honesty": "gentle",
        "custom_prompt": "You are warm, supportive, and user-friendly. Always be encouraging and positive. Make the user feel comfortable and valued.",
    },
    "professional": {
        "name": "حرفه‌ای",
        "name_en": "Professional",
        "icon": "💼",
        "tone": "formal",
        "verbosity": "detailed",
        "humor": "none",
        "emotion": "calm",
        "formality": "formal",
        "emoji_usage": "none",
        "sarcasm": "none",
        "honesty": "direct",
        "custom_prompt": "You are a professional, formal assistant. Use proper grammar, avoid slang and emojis. Give thorough, well-structured responses.",
    },
    "sarcastic": {
        "name": "کنایه‌آمیز",
        "name_en": "Sarcastic",
        "icon": "😏",
        "tone": "sarcastic",
        "verbosity": "normal",
        "humor": "high",
        "emotion": "normal",
        "formality": "informal",
        "emoji_usage": "minimal",
        "sarcasm": "high",
        "honesty": "indirect",
        "custom_prompt": "You are witty and sarcastic. Use clever wordplay, irony, and dry humor. Be helpful but with a sarcastic edge.",
    },
    "caring": {
        "name": "مهربان",
        "name_en": "Caring",
        "icon": "💕",
        "tone": "gentle",
        "verbosity": "normal",
        "humor": "low",
        "emotion": "warm",
        "formality": "informal",
        "emoji_usage": "normal",
        "sarcasm": "none",
        "honesty": "gentle",
        "custom_prompt": "You are deeply caring and empathetic. Always consider the user's feelings. Be gentle, nurturing, and supportive in every response.",
    },
    "technical": {
        "name": "فنی",
        "name_en": "Technical",
        "icon": "🔧",
        "tone": "precise",
        "verbosity": "detailed",
        "humor": "none",
        "emotion": "calm",
        "formality": "formal",
        "emoji_usage": "none",
        "sarcasm": "none",
        "honesty": "direct",
        "custom_prompt": "You are a precise technical expert. Use accurate terminology, provide code examples when relevant, and give detailed technical explanations.",
    },
}


def build_personality_system_prompt(preset_key, custom_prompt=""):
    """Build a system prompt addition based on personality preset."""
    if custom_prompt:
        return custom_prompt

    preset = PERSONALITY_PRESETS.get(preset_key, PERSONALITY_PRESETS["balanced"])

    tone_map = {
        "direct": "Be direct and straightforward. No beating around the bush.",
        "enthusiastic": "Be extremely enthusiastic and energetic about everything!",
        "warm": "Be warm, friendly, and approachable.",
        "formal": "Use formal, professional language.",
        "sarcastic": "Use sarcasm and wit appropriately.",
        "gentle": "Be gentle and considerate in your tone.",
        "precise": "Be precise and technical in your language.",
        "normal": "",
    }

    verbosity_map = {
        "short": "Keep responses very short and concise. One or two sentences max.",
        "long": "Give detailed, comprehensive responses.",
        "detailed": "Provide thorough, well-structured detailed responses.",
        "normal": "",
    }

    humor_map = {
        "none": "Never use humor or jokes.",
        "low": "Use subtle, light humor occasionally.",
        "medium": "Use humor naturally when appropriate.",
        "high": "Be very humorous and funny. Include jokes and witty remarks.",
    }

    emoji_map = {
        "none": "Never use emojis.",
        "minimal": "Use emojis very sparingly, only when truly needed.",
        "normal": "Use emojis naturally to enhance your messages.",
        "lots": "Use many emojis in every response! Make it colorful!",
    }

    sarcasm_map = {
        "none": "",
        "low": "Use very subtle sarcasm occasionally.",
        "medium": "Use moderate sarcasm when appropriate.",
        "high": "Be quite sarcastic in your responses.",
    }

    parts = []
    if tone_map.get(preset["tone"]):
        parts.append(tone_map[preset["tone"]])
    if verbosity_map.get(preset["verbosity"]):
        parts.append(verbosity_map[preset["verbosity"]])
    if humor_map.get(preset["humor"]):
        parts.append(humor_map[preset["humor"]])
    if emoji_map.get(preset["emoji_usage"]):
        parts.append(emoji_map[preset["emoji_usage"]])
    if sarcasm_map.get(preset["sarcasm"]):
        parts.append(sarcasm_map[preset["sarcasm"]])

    if parts:
        return "\n".join(parts)
    return ""


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _load_api_keys() -> set:
    keys = {_hash_key(API_KEY)}
    if API_KEYS_FILE.exists():
        for line in API_KEYS_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                keys.add(_hash_key(line))
    return keys


_valid_keys = None


def _get_valid_keys():
    global _valid_keys
    if _valid_keys is None:
        _valid_keys = _load_api_keys()
    return _valid_keys


def _refresh_keys():
    global _valid_keys
    _valid_keys = _load_api_keys()


def _verify_auth(request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    else:
        token = ""
    if not token:
        return False
    now = time.time()
    cached = _auth_cache.get(token)
    if cached is not None:
        if now - cached < _auth_cache_ttl:
            return True
        else:
            del _auth_cache[token]
    if token in _get_valid_keys():
        _auth_cache[token] = now
        return True
    if secrets.compare_digest(token, API_KEY):
        _auth_cache[token] = now
        return True
    return False


@web.middleware
async def security_headers_middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        log.error("Unhandled error: %s", e)
        response = web.json_response({"error": "Internal server error"}, status=500)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@web.middleware
async def cors_middleware(request, handler):
    origin = request.headers.get("Origin", "*")
    allowed = {
        "http://localhost:3000", "http://127.0.0.1:3000",
        "https://kaysan-bot.com", "https://www.kaysan-bot.com",
        "https://t.me",
        "http://localhost:8080", "http://127.0.0.1:8080",
    }
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException:
            raise
        except Exception as e:
            log.error("Unhandled error: %s", e)
            response = web.json_response({"error": "Internal server error"}, status=500)
    response.headers["Access-Control-Allow-Origin"] = origin if origin in allowed else "http://localhost:3000"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response


_rate_limits = {}
_last_rate_cleanup = time.time()


@web.middleware
async def rate_limit_middleware(request, handler):
    if request.path == "/api/chat" and request.method == "POST":
        global _last_rate_cleanup
        now = time.time()
        if now - _last_rate_cleanup > 300:
            _last_rate_cleanup = now
            stale = [ip for ip, ts in _rate_limits.items() if not ts or now - max(ts) > 120]
            for ip in stale:
                del _rate_limits[ip]
        ip = request.remote or "unknown"
        if ip not in _rate_limits:
            _rate_limits[ip] = []
        _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < 60]
        if len(_rate_limits[ip]) >= 30:
            return web.json_response(
                {"error": "Rate limit exceeded. Try again in a minute."},
                status=429,
            )
        _rate_limits[ip].append(now)
    return await handler(request)



# ═══════════════════════════════════════════════
#  Auth Utilities (inline for web server)
# ═══════════════════════════════════════════════

import base64 as _b64
import hashlib as _hl
import hmac as _hmac
import json as _json
import time as _time
import secrets as _secrets
from urllib.parse import parse_qsl as _parse_qsl


def _validate_telegram_init_data(init_data, bot_token):
    try:
        pairs = _parse_qsl(init_data, keep_blank_values=True)
        received_hash = None
        data_check_parts = []
        for key, value in pairs:
            if key == "hash":
                received_hash = value
            else:
                data_check_parts.append(f"{key}={value}")
        if not received_hash:
            return None
        data_check_string = "\n".join(sorted(data_check_parts))
        secret_key = _hmac.new(bot_token.encode(), b"WebAppData", _hl.sha256).digest()
        computed_hash = _hmac.new(secret_key, data_check_string.encode(), _hl.sha256).hexdigest()
        if not _hmac.compare_digest(computed_hash, received_hash):
            return None
        parsed = dict(pairs)
        user = _json.loads(parsed.get("user", "{}"))
        auth_date = int(parsed.get("auth_date", 0))
        if _time.time() - auth_date > 86400:
            return None
        return user
    except Exception:
        return None


def _create_session_token(user_id):
    payload = f"{user_id}:{int(_time.time())}"
    secret = _secrets.token_hex(32)
    sig = _hmac.new(secret.encode(), payload.encode(), _hl.sha256).hexdigest()[:32]
    return _b64.b64encode(f"{payload}:{sig}".encode()).decode()


def _verify_session_token(token):
    try:
        decoded = _b64.b64decode(token).decode()
        parts = decoded.rsplit(":", 2)
        if len(parts) != 3:
            return None
        user_id_str, timestamp_str, sig = parts
        payload = f"{user_id_str}:{timestamp_str}"
        # We use a simpler check for now
        if _time.time() - int(timestamp_str) > 168 * 3600:
            return None
        return int(user_id_str)
    except Exception:
        return None


# Session secret (generated once per server start)
_SESSION_SECRET = _secrets.token_hex(32)


def _create_session_token_v2(user_id):
    payload = f"{user_id}:{int(_time.time())}"
    sig = _hmac.new(_SESSION_SECRET.encode(), payload.encode(), _hl.sha256).hexdigest()[:32]
    return _b64.b64encode(f"{payload}:{sig}".encode()).decode()


def _verify_session_token_v2(token):
    try:
        decoded = _b64.b64decode(token).decode()
        parts = decoded.rsplit(":", 2)
        if len(parts) != 3:
            return None
        user_id_str, timestamp_str, sig = parts
        payload = f"{user_id_str}:{timestamp_str}"
        expected = _hmac.new(_SESSION_SECRET.encode(), payload.encode(), _hl.sha256).hexdigest()[:32]
        if not _hmac.compare_digest(sig, expected):
            return None
        if _time.time() - int(timestamp_str) > 168 * 3600:
            return None
        return int(user_id_str)
    except Exception:
        return None


# ═══════════════════════════════════════════════
#  Auth Middleware
# ═══════════════════════════════════════════════

@web.middleware
async def auth_middleware(request, handler):
    """Require valid auth for protected API endpoints."""
    public_paths = {
        "/api/health", "/api/models", "/api/personality",
        "/api/auth/telegram", "/api/auth/session",
    }
    if request.path in public_paths or request.path.startswith("/api/auth/"):
        return await handler(request)
    if not request.path.startswith("/api/"):
        return await handler(request)
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    user_id = _verify_session_token_v2(token) if token else None
    if not user_id:
        # Allow unauthenticated access to /api/chat for backwards compat
        if request.path in ("/api/chat", "/api/chat/stream"):
            request["user_id"] = 0
            return await handler(request)
        return web.json_response({"error": "Unauthorized"}, status=401)
    request["user_id"] = user_id
    return await handler(request)


# ═══════════════════════════════════════════════
#  Auth Endpoints
# ═══════════════════════════════════════════════

async def handle_auth_telegram(request):
    """Validate Telegram initData, create session."""
    try:
        data = await request.json()
        init_data = data.get("init_data", "")
        if not init_data:
            return web.json_response({"error": "Missing init_data"}, status=400)
        user = _validate_telegram_init_data(init_data, config.BOT_TOKEN)
        if not user:
            return web.json_response({"error": "Invalid init_data"}, status=401)
        user_id = user.get("id", 0)
        if not user_id:
            return web.json_response({"error": "No user_id"}, status=400)
        session_token = _create_session_token_v2(user_id)
        # Import db here to avoid circular imports
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bot import database as db
        await db.ensure_user(user_id, name=user.get("first_name", ""))
        await db.update_user_profile(user_id,
            telegram_username=user.get("username", ""),
            first_name=user.get("first_name", ""),
            last_name=user.get("last_name", ""),
            platform="both",
            last_active_at=datetime.now(timezone.utc).isoformat(),
        )
        return web.json_response({
            "session_token": session_token,
            "user_id": user_id,
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
        })
    except Exception as e:
        log.warning("auth_telegram failed: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_auth_session(request):
    """Validate existing session token."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
    user_id = _verify_session_token_v2(token) if token else None
    if not user_id:
        return web.json_response({"error": "Invalid session"}, status=401)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    settings = await db.get_settings(user_id)
    return web.json_response({
        "user_id": user_id,
        "settings": settings,
    })


async def handle_auth_logout(request):
    """Invalidate session."""
    return web.json_response({"status": "ok"})


# ═══════════════════════════════════════════════
#  Conversation Endpoints
# ═══════════════════════════════════════════════

async def handle_conversations_list(request):
    """List user's conversations."""
    user_id = request.get("user_id", 0)
    if not user_id:
        return web.json_response({"conversations": []})
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    convos = await db.get_conversations_list(user_id)
    return web.json_response({"conversations": convos})


async def handle_conversations_create(request):
    """Create new conversation."""
    user_id = request.get("user_id", 0)
    if not user_id:
        return web.json_response({"error": "Unauthorized"}, status=401)
    data = await request.json()
    conv_id = data.get("conversation_id", f"web_{user_id}_{int(time.time())}")
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    await db.create_conversation_db(user_id, conv_id, "web")
    return web.json_response({"conversation_id": conv_id})


async def handle_conversation_get(request):
    """Get conversation with messages."""
    user_id = request.get("user_id", 0)
    conv_id = request.match_info.get("id", "")
    if not user_id or not conv_id:
        return web.json_response({"error": "Missing params"}, status=400)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    msgs = await db.get_conversation_messages(conv_id)
    return web.json_response({"messages": msgs, "conversation_id": conv_id})


async def handle_conversation_messages(request):
    """Add message to conversation."""
    user_id = request.get("user_id", 0)
    conv_id = request.match_info.get("id", "")
    if not user_id or not conv_id:
        return web.json_response({"error": "Missing params"}, status=400)
    data = await request.json()
    role = data.get("role", "user")
    content = data.get("content", "")
    platform = data.get("platform", "web")
    model = data.get("model", "")
    tokens = data.get("tokens", 0)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    await db.add_message_to_conversation(conv_id, user_id, role, content, platform, model, tokens)
    return web.json_response({"status": "ok"})


async def handle_conversation_delete(request):
    """Delete conversation."""
    user_id = request.get("user_id", 0)
    conv_id = request.match_info.get("id", "")
    if not user_id or not conv_id:
        return web.json_response({"error": "Missing params"}, status=400)
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    await db.delete_conversation_db(conv_id, user_id)
    return web.json_response({"status": "ok"})


# ═══════════════════════════════════════════════
#  Settings Endpoints
# ═══════════════════════════════════════════════

async def handle_settings_get(request):
    """Get all user settings."""
    user_id = request.get("user_id", 0)
    if not user_id:
        return web.json_response({"settings": {}})
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    settings = await db.get_settings(user_id)
    return web.json_response({"settings": settings})


async def handle_settings_update(request):
    """Update settings."""
    user_id = request.get("user_id", 0)
    if not user_id:
        return web.json_response({"error": "Unauthorized"}, status=401)
    data = await request.json()
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    for key, value in data.items():
        await db.set_setting(user_id, key, str(value))
    return web.json_response({"status": "ok"})


# ═══════════════════════════════════════════════
#  Sync Endpoint
# ═══════════════════════════════════════════════

async def handle_sync_poll(request):
    """Poll for changes since timestamp."""
    user_id = request.get("user_id", 0)
    if not user_id:
        return web.json_response({"settings": {}, "conversations": []})
    since = request.query.get("since", "")
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bot import database as db
    result = {}
    if since:
        settings = await db.get_settings_since(user_id, since)
        if settings:
            result["settings"] = settings
    convos = await db.get_recent_conversations(user_id, since or "2000-01-01")
    if convos:
        result["conversations"] = convos
    result["last_timestamp"] = datetime.now(timezone.utc).isoformat()
    return web.json_response(result)


async def handle_index(request):
    resp = web.FileResponse(WEB_DIR / "index.html")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


async def handle_css(request):
    resp = web.FileResponse(WEB_DIR / "style.css")
    resp.content_type = "text/css; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


async def handle_js(request):
    resp = web.FileResponse(WEB_DIR / "app.js")
    resp.content_type = "application/javascript; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


async def handle_logo(request):
    try:
        resp = web.FileResponse(WEB_DIR / "logo.png")
        resp.content_type = "image/png"
        return resp
    except FileNotFoundError:
        return web.Response(status=404)


async def handle_manifest(request):
    manifest = {
        "name": "Kaysan AI",
        "short_name": "Kaysan",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#09090b",
        "theme_color": "#818cf8",
        "icons": [
            {"src": "/logo.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/logo.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    return web.json_response(manifest)


async def handle_sitemap(request):
    sitemap_path = WEB_DIR / "sitemap.xml"
    if sitemap_path.exists():
        resp = web.FileResponse(sitemap_path)
        resp.content_type = "application/xml; charset=utf-8"
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    return web.Response(status=404)


async def handle_robots(request):
    robots_path = WEB_DIR / "robots.txt"
    if robots_path.exists():
        resp = web.FileResponse(robots_path)
        resp.content_type = "text/plain; charset=utf-8"
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp
    return web.Response(status=404)


async def handle_chat(request):
    import asyncio
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        lang = data.get("lang", "ku")
        history = data.get("history", [])
        model_type = data.get("model_type", "auto")
        personality = data.get("personality", "balanced")
        custom_prompt = data.get("custom_prompt", "")

        tone_val = data.get("tone", 2)
        verbosity_val = data.get("verbosity", 1)
        humor_val = data.get("humor", 1)
        emoji_val = data.get("emoji", 1)
        emotion_val = data.get("emotion", 1)

        if not message:
            return web.json_response({"error": "empty message"}, status=400)
        if len(message) > 4000:
            return web.json_response({"error": "message too long"}, status=400)

        feature_type = detect_feature_request(message, lang)
        if feature_type:
            if feature_type == "image_request":
                import asyncio
                try:
                    style_prompt = message.lower().replace("sakht", "").replace("ankas", "").replace("tasvir", "").strip()
                    if not style_prompt:
                        style_prompt = "a beautiful scene"
                    img_data = await asyncio.wait_for(
                        generate_image(style_prompt, "realistic"), timeout=120
                    )
                    if img_data:
                        import base64
                        img_b64 = base64.b64encode(img_data).decode()
                        return web.json_response({
                            "reply": f"image:{img_b64}",
                            "model": "pollinations",
                            "tokens": 0,
                        })
                except Exception as e:
                    pass
                return web.json_response({
                    "reply": "image generation failed, try again",
                    "model": "agent",
                    "tokens": 0,
                })
            feature_response = get_feature_response(feature_type, lang)
            if feature_response:
                return web.json_response({
                    "reply": feature_response,
                    "model": "agent",
                    "tokens": 0,
                })

        intent = router.detect_intent(message)

        if model_type in MODEL_TYPE_MAP and MODEL_TYPE_MAP[model_type]:
            models = MODEL_TYPE_MAP[model_type]
        else:
            models = router.models_for(intent)

        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS.get("en", ""))

        now = datetime.now()
        system_prompt = system_prompt.replace(
            "{current_datetime}",
            now.strftime("%Y-%m-%d %H:%M:%S")
        )

        personality_addition = build_personality_system_prompt(personality, custom_prompt)
        if personality_addition:
            system_prompt += f"\n\nPersonality instructions:\n{personality_addition}"

        slider_instructions = []
        tone_labels = ["رک و مستقیم", "ملایم", "عادی", "رسمی", "پرانرژی"]
        if 0 <= tone_val <= 4:
            slider_instructions.append(f"Response tone: {tone_labels[tone_val]}")
        verbosity_labels = ["خیلی کوتاه", "کوتاه", "متعادل", "مفصل"]
        if 0 <= verbosity_val <= 3:
            slider_instructions.append(f"Response length: {verbosity_labels[verbosity_val]}")
        humor_labels = ["بدون طنز", "کم طنز", "متعادل", "پر از طنز"]
        if 0 <= humor_val <= 3:
            slider_instructions.append(f"Humor level: {humor_labels[humor_val]}")
        emoji_labels = ["بدون ایموجی", "کم ایموجی", "عادی", "زیاد ایموجی"]
        if 0 <= emoji_val <= 3:
            slider_instructions.append(f"Emoji usage: {emoji_labels[emoji_val]}")
        emotion_labels = ["آرام و خونسرد", "عادی", "گرم", "پرانرژی"]
        if 0 <= emotion_val <= 3:
            slider_instructions.append(f"Emotion level: {emotion_labels[emotion_val]}")

        if slider_instructions:
            system_prompt += "\n\nCustom adjustments:\n" + "\n".join(slider_instructions)

        enhanced_message, prompt_type = await enhance_prompt_engine(message, lang, intent)
        
        optimal_models = get_optimal_model(prompt_type)
        optimal_temp = get_optimal_temperature(prompt_type)
        optimal_tokens = get_optimal_max_tokens(prompt_type)
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": enhanced_message})

        max_tok = min(optimal_tokens, config.MAX_TOKENS_BY_INTENT.get(intent, config.MAX_TOKENS_CHAT))
        temperature = optimal_temp

        reply, usage = await asyncio.wait_for(
            openrouter.chat(messages, models, intent=intent,
                           max_tokens=max_tok, temperature=temperature),
            timeout=90,
        )

        return web.json_response({
            "reply": reply,
            "model": usage.get("model", ""),
            "tokens": usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0),
        })

    except asyncio.TimeoutError:
        return web.json_response({"error": "timeout"}, status=504)
    except openrouter.ORError as e:
        log.warning("OpenRouter error: %s", e)
        return web.json_response({"error": "AI service temporarily unavailable"}, status=503)
    except Exception as e:
        log.error("Chat error: %s", e)
        return web.json_response({"error": "Internal server error"}, status=500)


async def handle_chat_stream(request):
    import asyncio
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        lang = data.get("lang", "ku")
        history = data.get("history", [])
        model_type = data.get("model_type", "auto")
        personality = data.get("personality", "balanced")
        custom_prompt = data.get("custom_prompt", "")

        tone_val = data.get("tone", 2)
        verbosity_val = data.get("verbosity", 1)
        humor_val = data.get("humor", 1)
        emoji_val = data.get("emoji", 1)
        emotion_val = data.get("emotion", 1)

        if not message:
            return web.json_response({"error": "empty message"}, status=400)
        if len(message) > 4000:
            return web.json_response({"error": "message too long"}, status=400)

        feature_type = detect_feature_request(message, lang)
        if feature_type:
            if feature_type == "image_request":
                import asyncio
                try:
                    style_prompt = message.lower().replace("sakht", "").replace("ankas", "").replace("tasvir", "").strip()
                    if not style_prompt:
                        style_prompt = "a beautiful scene"
                    img_data = await asyncio.wait_for(
                        generate_image(style_prompt, "realistic"), timeout=120
                    )
                    if img_data:
                        import base64
                        img_b64 = base64.b64encode(img_data).decode()
                        response = web.StreamResponse(
                            status=200,
                            headers={
                                "Content-Type": "text/event-stream",
                                "Cache-Control": "no-cache",
                                "X-Accel-Buffering": "no",
                            },
                        )
                        await response.prepare(request)
                        chunk_data = json.dumps({"chunk": f"image:{img_b64}"})
                        await response.write(("data: " + chunk_data + "\n\n").encode())
                        await response.write(b"data: [DONE]\n\n")
                        await response.drain()
                        return response
                except Exception as e:
                    pass
            feature_response = get_feature_response(feature_type, lang)
            if feature_response:
                response = web.StreamResponse(
                    status=200,
                    headers={
                        "Content-Type": "text/event-stream",
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no",
                    },
                )
                await response.prepare(request)
                chunk_data = json.dumps({"chunk": feature_response})
                await response.write(("data: " + chunk_data + "\n\n").encode())
                await response.write(b"data: [DONE]\n\n")
                await response.drain()
                return response

        intent = router.detect_intent(message)

        if model_type in MODEL_TYPE_MAP and MODEL_TYPE_MAP[model_type]:
            models = MODEL_TYPE_MAP[model_type]
        else:
            models = router.models_for(intent)

        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS.get("en", ""))

        now = datetime.now()
        system_prompt = system_prompt.replace(
            "{current_datetime}",
            now.strftime("%Y-%m-%d %H:%M:%S")
        )

        personality_addition = build_personality_system_prompt(personality, custom_prompt)
        if personality_addition:
            system_prompt += f"\n\nPersonality instructions:\n{personality_addition}"

        slider_instructions = []
        tone_labels = ["رک و مستقیم", "ملایم", "عادی", "رسمی", "پرانرژی"]
        if 0 <= tone_val <= 4:
            slider_instructions.append(f"Response tone: {tone_labels[tone_val]}")
        verbosity_labels = ["خیلی کوتاه", "کوتاه", "متعادل", "مفصل"]
        if 0 <= verbosity_val <= 3:
            slider_instructions.append(f"Response length: {verbosity_labels[verbosity_val]}")
        humor_labels = ["بدون طنز", "کم طنز", "متعادل", "پر از طنز"]
        if 0 <= humor_val <= 3:
            slider_instructions.append(f"Humor level: {humor_labels[humor_val]}")
        emoji_labels = ["بدون ایموجی", "کم ایموجی", "عادی", "زیاد ایموجی"]
        if 0 <= emoji_val <= 3:
            slider_instructions.append(f"Emoji usage: {emoji_labels[emoji_val]}")
        emotion_labels = ["آرام و خونسرد", "عادی", "گرم", "پرانرژی"]
        if 0 <= emotion_val <= 3:
            slider_instructions.append(f"Emotion level: {emotion_labels[emotion_val]}")

        if slider_instructions:
            system_prompt += "\n\nCustom adjustments:\n" + "\n".join(slider_instructions)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        max_tok = config.MAX_TOKENS_BY_INTENT.get(intent, config.MAX_TOKENS_CHAT)
        temperature = config.TEMP_BY_INTENT.get(intent, 0.7)

        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
        await response.prepare(request)

        async for chunk, result in openrouter.chat_stream(
            messages, models, intent=intent,
            max_tokens=max_tok, temperature=temperature
        ):
            if chunk is None:
                final_data = json.dumps({
                    "done": True,
                    "model": result.get("model", ""),
                    "tokens": result.get("prompt_tokens", 0) + result.get("completion_tokens", 0),
                })
                await response.write(f"data: {final_data}\n\n".encode())
            else:
                chunk_data = json.dumps({"chunk": chunk})
                await response.write(f"data: {chunk_data}\n\n".encode())

        await response.write(b"data: [DONE]\n\n")
        await response.drain()
        return response

    except asyncio.TimeoutError:
        return web.json_response({"error": "timeout"}, status=504)
    except openrouter.ORError as e:
        log.warning("OpenRouter stream error: %s", e)
        return web.json_response({"error": "AI service temporarily unavailable"}, status=503)
    except Exception as e:
        log.error("Stream chat error: %s", e)
        return web.json_response({"error": "Internal server error"}, status=500)


async def handle_health(request):
    return web.json_response({
        "status": "ok",
        "service": "kaysan-web",
        "timestamp": time.time(),
    })


async def handle_models(request):
    return web.json_response({
        "chat": config.CHAT_MODELS,
        "code": config.CODE_MODELS,
        "reason": config.REASON_MODELS,
        "vision": config.VISION_MODELS,
    })


async def handle_personality_presets(request):
    return web.json_response(PERSONALITY_PRESETS)


def main():
    app = web.Application(
        middlewares=[security_headers_middleware, cors_middleware, auth_middleware, rate_limit_middleware]
    )

    app.router.add_get("/", handle_index)
    app.router.add_get("/style.css", handle_css)
    app.router.add_get("/app.js", handle_js)
    app.router.add_get("/logo.png", handle_logo)
    app.router.add_get("/manifest.json", handle_manifest)
    app.router.add_get("/sitemap.xml", handle_sitemap)
    app.router.add_get("/robots.txt", handle_robots)
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/models", handle_models)
    app.router.add_get("/api/personality", handle_personality_presets)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_post("/api/chat/stream", handle_chat_stream)
    app.router.add_post("/api/auth/telegram", handle_auth_telegram)
    app.router.add_get("/api/auth/session", handle_auth_session)
    app.router.add_post("/api/auth/logout", handle_auth_logout)
    app.router.add_get("/api/conversations", handle_conversations_list)
    app.router.add_post("/api/conversations", handle_conversations_create)
    app.router.add_get("/api/conversations/{id}", handle_conversation_get)
    app.router.add_post("/api/conversations/{id}/messages", handle_conversation_messages)
    app.router.add_delete("/api/conversations/{id}", handle_conversation_delete)
    app.router.add_get("/api/settings", handle_settings_get)
    app.router.add_put("/api/settings", handle_settings_update)
    app.router.add_get("/api/sync/poll", handle_sync_poll)


    port = int(os.getenv("WEB_PORT", "3000"))
    log.info("Kaysan Web running on http://0.0.0.0:%d", port)
    log.info("API Key: %s...%s", API_KEY[:8], API_KEY[-4:])
    web.run_app(app, host="0.0.0.0", port=port, print=None)


if __name__ == "__main__":
    main()
