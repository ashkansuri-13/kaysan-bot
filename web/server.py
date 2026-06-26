#!/usr/bin/env python3
"""Kaysan AI Web Server v4.0 — 10 amazing features."""
import asyncio
import collections
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import time
from pathlib import Path

from aiohttp import web, WSMsgType

sys.path.insert(0, str(Path(__file__).parent.parent))
from bot import config, openrouter
from bot.texts import SYSTEM_PROMPTS
from bot.prompt_enhancer import detect_prompt_type, get_optimal_temperature, get_optimal_max_tokens

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kaysan.web")

WEB_DIR = Path(__file__).resolve().parent
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL", "")

PERSONALITY_PRESETS = {
    "balanced": {"name": "متعادل", "name_en": "Balanced", "icon": "⚖️"},
    "blunt": {"name": "رُک و راست", "name_en": "Blunt", "icon": "🔪"},
    "exaggerated": {"name": "اغراق‌آمیز", "name_en": "Exaggerated", "icon": "🎭"},
    "friendly": {"name": "کاربرپسند", "name_en": "User-Friendly", "icon": "🤗"},
    "professional": {"name": "حرفه‌ای", "name_en": "Professional", "icon": "💼"},
    "sarcastic": {"name": "کنایه‌آمیز", "name_en": "Sarcastic", "icon": "😏"},
    "caring": {"name": "مهربان", "name_en": "Caring", "icon": "💕"},
    "technical": {"name": "فنی", "name_en": "Technical", "icon": "🔧"},
}

ALL_MODELS = list(dict.fromkeys(
    config.CHAT_MODELS + config.CODE_MODELS + config.REASON_MODELS
))

MODEL_TYPE_MAP = {
    "chat": config.CHAT_MODELS,
    "code": config.CODE_MODELS,
    "reason": config.REASON_MODELS,
    "vision": config.VISION_MODELS,
}


# ============================================
# Rate Limiter
# ============================================
class RateLimiter:
    def __init__(self, max_requests=30, window=60):
        self.max_requests = max_requests
        self.window = window
        self._hits = {}

    def _client_ip(self, request):
        return request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
               request.headers.get("X-Real-IP", "") or request.remote or "unknown"

    def is_rate_limited(self, request):
        ip = self._client_ip(request)
        now = time.time()
        if ip not in self._hits:
            self._hits[ip] = collections.deque()
        hits = self._hits[ip]
        while hits and hits[0] < now - self.window:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return True
        hits.append(now)
        return False

rate_limiter = RateLimiter(max_requests=30, window=60)


# ============================================
# Redis Cache (optional)
# ============================================
_redis = None
async def get_redis():
    global _redis
    if _redis and not _redis.closed:
        return _redis
    if not REDIS_URL:
        return None
    try:
        import aioredis
        _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        return _redis
    except Exception as e:
        log.warning(f"Redis not available: {e}")
        return None

async def cache_get(key):
    r = await get_redis()
    if r:
        try: return await r.get(key)
        except: return None
    return None

async def cache_set(key, value, ttl=300):
    r = await get_redis()
    if r:
        try: await r.set(key, value, ex=ttl)
        except: pass


# ============================================
# Stats Tracker
# ============================================
class StatsTracker:
    def __init__(self):
        self.total_requests = 0
        self.total_messages = 0
        self.total_tokens = 0
        self.models_used = collections.Counter()
        self.errors = 0
        self.start_time = time.time()
        self.user_ids = set()

    def track(self, model=None, tokens=0, user_id=None):
        self.total_requests += 1
        self.total_messages += 1
        self.total_tokens += tokens
        if model: self.models_used[model] += 1
        if user_id: self.user_ids.add(user_id)

    def track_error(self):
        self.errors += 1

    def get_stats(self):
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_requests": self.total_requests,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
            "total_errors": self.errors,
            "unique_users": len(self.user_ids),
            "models_used": dict(self.models_used.most_common(10)),
        }

stats = StatsTracker()


# ============================================
# Sentiment Analysis (simple keyword-based)
# ============================================
POSITIVE_WORDS = {"خوب", "عالی", "ممنون", "متشکرم", "معرکه", "فوق‌العاده", "love", "great", "awesome", "good", "thanks", "wonderful", "perfect", "excellent", "best", "happy", "smile", "thank", "well", "nice"}
NEGATIVE_WORDS = {"بد", "مشکل", "خراب", "اشتباه", "افتضاح", "بده", "bad", "error", "broken", "wrong", "terrible", "hate", "awful", "worst", "fail", "problem", "bug", "issue", "sad", "angry"}

def analyze_sentiment(text):
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg: return {"label": "positive", "score": min(1.0, 0.5 + pos * 0.15), "emoji": "😊"}
    if neg > pos: return {"label": "negative", "score": min(1.0, 0.5 + neg * 0.15), "emoji": "😔"}
    return {"label": "neutral", "score": 0.5, "emoji": "😐"}


# ============================================
# Plugin System (simple)
# ============================================
PLUGINS = {}

def register_plugin(name, description, handler):
    PLUGINS[name] = {"name": name, "description": description, "handler": handler}

def plugin_weather(text):
    if any(w in text.lower() for w in ["天气", "weather", "آب و هوا", "کەش"]):
        return {"handled": True, "response": "🌤️ هوای امروز آفتابیه! دمای هوا ۲۵ درجه سانتیگراد."}
    return {"handled": False}

def plugin_joke(text):
    if any(w in text.lower() for w in ["لطیفه", "joke", "خۆشی"]):
        return {"handled": True, "response": "😄 چرا برنامه‌نویس‌ها عینک میزنن؟ چون C# نمیبینن! 😂"}
    return {"handled": False}

register_plugin("weather", "آب و هوا", plugin_weather)
register_plugin("joke", "لطیفه", plugin_joke)


# ============================================
# Security Middleware
# ============================================
@web.middleware
async def security_middleware(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        resp = await handler(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https:; "
        "connect-src 'self' https://api.openrouter.ai ws: wss:; "
        "frame-ancestors 'self' https://web.telegram.org https://telegram.org;"
    )
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Server"] = "Kaysan"
    return resp


# ============================================
# Telegram Verification
# ============================================
def verify_telegram_init_data(init_data):
    if not BOT_TOKEN: return None
    try:
        parsed = dict(x.split("=", 1) for x in init_data.split("&"))
        hash_val = parsed.pop("hash", None)
        if not hash_val: return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash != hash_val: return None
        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 86400: return None
        return json.loads(parsed.get("user", "{}"))
    except: return None


# ============================================
# Handlers
# ============================================
async def handle_health(request):
    return web.json_response({"status": "healthy", "service": "kaysan-ai-bot", "version": "4.0.0", "uptime_seconds": time.time() - _start_time})

async def handle_verify_user(request):
    try:
        data = await request.json()
        init_data = data.get("init_data", "")
        if not init_data: return web.json_response({"error": "No init_data"}, status=400)
        user = verify_telegram_init_data(init_data)
        if not user: return web.json_response({"error": "Invalid init data"}, status=401)
        return web.json_response({"ok": True, "user": {
            "id": user.get("id"), "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""), "username": user.get("username", ""),
            "language_code": user.get("language_code", "en"),
            "is_premium": user.get("is_premium", False), "photo_url": user.get("photo_url", ""),
        }})
    except: return web.json_response({"error": "Request failed"}, status=500)

async def handle_sentiment(request):
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text: return web.json_response({"error": "No text"}, status=400)
        return web.json_response(analyze_sentiment(text))
    except: return web.json_response({"error": "Failed"}, status=500)

async def handle_plugins(request):
    return web.json_response({"plugins": {k: {"name": v["name"], "description": v["description"]} for k, v in PLUGINS.items()}})

async def handle_admin_stats(request):
    return web.json_response(stats.get_stats())

async def handle_chat(request):
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        model_type = data.get("model_type", "auto")
        personality = data.get("personality", "balanced")
        custom_prompt = data.get("custom_prompt", "")
        init_data = data.get("init_data", "")
        stream = data.get("stream", True)
        if not message: return web.json_response({"error": "Empty message"}, status=400)

        user_id = None
        if init_data:
            user = verify_telegram_init_data(init_data)
            if user: user_id = user.get("id")

        sentiment = analyze_sentiment(message)

        for name, plugin in PLUGINS.items():
            result = plugin["handler"](message)
            if result.get("handled"):
                stats.track(user_id=user_id)
                return web.json_response({"response": result["response"], "sentiment": sentiment})

        cache_key = f"chat:{hashlib.md5(message.encode()).hexdigest()}"
        if not stream:
            cached = await cache_get(cache_key)
            if cached:
                stats.track(user_id=user_id)
                return web.json_response({"response": cached, "sentiment": sentiment, "cached": True})

        models = MODEL_TYPE_MAP.get(model_type, ALL_MODELS)
        temp = get_optimal_temperature(detect_prompt_type(message))
        max_tokens = get_optimal_max_tokens(detect_prompt_type(message))
        messages = []
        if custom_prompt:
            messages.append({"role": "system", "content": custom_prompt})
        else:
            system_prompt = SYSTEM_PROMPTS.get(personality, SYSTEM_PROMPTS.get("default", "You are Kaysan AI."))
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        if stream:
            response = web.StreamResponse(status=200, headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
            await response.prepare(request)
            full_response = ""
            try:
                async for chunk, result in openrouter.chat_stream(messages=messages, models=models, intent=model_type if model_type in ("chat", "code", "reason") else "chat", temperature=temp, max_tokens=max_tokens):
                    if chunk is None: break
                    full_response += chunk
                    await response.write(f"data: {json.dumps({'text': chunk, 'done': False})}\n\n".encode())
                await response.write(f"data: {json.dumps({'text': '', 'done': True, 'full': full_response, 'sentiment': sentiment})}\n\n".encode())
                if full_response: await cache_set(cache_key, full_response, ttl=600)
                tokens = sum(len(c) for c in full_response.split() if c)
                stats.track(model=models[0] if models else None, tokens=tokens, user_id=user_id)
            except Exception as e:
                log.error(f"Streaming error: {e}")
                stats.track_error()
                await response.write(f"data: {json.dumps({'error': 'Streaming failed', 'done': True})}\n\n".encode())
            await response.write_eof()
            return response
        else:
            result_content, usage = await openrouter.chat(messages=messages, models=models, intent=model_type if model_type in ("chat", "code", "reason") else "chat", temperature=temp, max_tokens=max_tokens)
            await cache_set(cache_key, result_content, ttl=600)
            stats.track(model=usage.get("model"), tokens=usage.get("completion_tokens", 0), user_id=user_id)
            return web.json_response({"response": result_content, "sentiment": sentiment, "usage": usage})
    except Exception as e:
        log.error(f"Chat error: {e}")
        stats.track_error()
        return web.json_response({"error": "Chat request failed"}, status=500)

async def handle_voice(request):
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)
    try:
        reader = await request.multipart()
        field = await reader.next()
        if not field or field.name != "audio":
            return web.json_response({"error": "No audio file"}, status=400)
        audio_data = await field.read()
        if len(audio_data) > 10 * 1024 * 1024:
            return web.json_response({"error": "Audio too large"}, status=400)
        temp_path = Path(f"/tmp/voice_{secrets.token_hex(8)}.ogg")
        temp_path.write_bytes(audio_data)
        try:
            from bot.services.stt import transcribe_audio
            text = await transcribe_audio(str(temp_path))
            return web.json_response({"ok": True, "text": text})
        except: return web.json_response({"error": "Transcription failed"}, status=500)
        finally: temp_path.unlink(missing_ok=True)
    except: return web.json_response({"error": "Voice request failed"}, status=500)

async def handle_upload(request):
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)
    try:
        reader = await request.multipart()
        field = await reader.next()
        if not field: return web.json_response({"error": "No file"}, status=400)
        filename = field.filename or "upload"
        data = await field.read()
        if len(data) > 20 * 1024 * 1024:
            return web.json_response({"error": "File too large (max 20MB)"}, status=400)
        ext = Path(filename).suffix.lower()
        if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            import base64
            b64 = base64.b64encode(data).decode()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext.lstrip("."), "image/png")
            return web.json_response({"ok": True, "type": "image", "data_url": f"data:{mime};base64,{b64}", "filename": filename})
        elif ext == ".pdf":
            return web.json_response({"ok": True, "type": "file", "filename": filename, "size": len(data)})
        else:
            return web.json_response({"ok": True, "type": "file", "filename": filename, "size": len(data)})
    except: return web.json_response({"error": "Upload failed"}, status=500)

async def handle_image(request):
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)
    try:
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        style = data.get("style", "realistic")
        if not prompt: return web.json_response({"error": "Empty prompt"}, status=400)
        from bot.services.image import generate as generate_image
        result = await generate_image(prompt, style=style)
        return web.json_response({"url": result})
    except: return web.json_response({"error": "Image generation failed"}, status=500)

async def handle_models(request):
    return web.json_response({"primary": config.PRIMARY_MODEL, "chat": config.CHAT_MODELS, "code": config.CODE_MODELS, "reason": config.REASON_MODELS, "vision": config.VISION_MODELS, "personality_presets": PERSONALITY_PRESETS})

async def handle_index(request):
    return web.FileResponse(WEB_DIR / "index.html")

async def handle_not_found(request):
    return web.json_response({"error": "Not found"}, status=404)


# ============================================
# WebSocket Handler
# ============================================
async def handle_websocket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(ws_resp := ws)
    log.info("WebSocket connected")
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    message = data.get("message", "").strip()
                    model_type = data.get("model_type", "auto")
                    personality = data.get("personality", "balanced")

                    if not message:
                        await ws.send_json({"error": "Empty message"})
                        continue

                    sentiment = analyze_sentiment(message)

                    for name, plugin in PLUGINS.items():
                        result = plugin["handler"](message)
                        if result.get("handled"):
                            await ws.send_json({"text": result["response"], "done": True, "sentiment": sentiment})
                            continue

                    models = MODEL_TYPE_MAP.get(model_type, ALL_MODELS)
                    temp = get_optimal_temperature(detect_prompt_type(message))
                    max_tokens = get_optimal_max_tokens(detect_prompt_type(message))
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPTS.get(personality, SYSTEM_PROMPTS.get("default", "You are Kaysan AI."))},
                        {"role": "user", "content": message}
                    ]

                    full_response = ""
                    async for chunk, result in openrouter.chat_stream(messages=messages, models=models, intent=model_type if model_type in ("chat", "code", "reason") else "chat", temperature=temp, max_tokens=max_tokens):
                        if chunk is None: break
                        full_response += chunk
                        await ws.send_json({"text": chunk, "done": False})

                    await ws.send_json({"text": "", "done": True, "full": full_response, "sentiment": sentiment})
                    stats.track(model=models[0] if models else None, tokens=len(full_response.split()))
                except Exception as e:
                    log.error(f"WS error: {e}")
                    await ws.send_json({"error": "Processing failed", "done": True})
            elif msg.type == WSMsgType.ERROR:
                log.error(f"WS error: {ws.exception()}")
    finally:
        log.info("WebSocket disconnected")
    return ws


# ============================================
# App Setup
# ============================================
_start_time = time.time()

app = web.Application(middlewares=[security_middleware])
app.router.add_get("/", handle_index)
app.router.add_get("/health", handle_health)
app.router.add_get("/ws", handle_websocket)
app.router.add_post("/api/chat", handle_chat)
app.router.add_post("/api/voice", handle_voice)
app.router.add_post("/api/upload", handle_upload)
app.router.add_post("/api/image", handle_image)
app.router.add_post("/api/sentiment", handle_sentiment)
app.router.add_get("/api/plugins", handle_plugins)
app.router.add_get("/api/admin/stats", handle_admin_stats)
app.router.add_get("/api/models", handle_models)
app.router.add_post("/api/verify-user", handle_verify_user)
app.router.add_static("/", path=str(WEB_DIR), show_index=False)
app.router.add_route("*", "/{path:.*}", handle_not_found)

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", "8080"))
    log.info(f"Kaysan AI Web Server v4.0 starting on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)
