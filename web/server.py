#!/usr/bin/env python3
"""Kaysan AI Web Server v3.2 — All issues fixed."""
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

from aiohttp import web

sys.path.insert(0, str(Path(__file__).parent.parent))
from bot import config, openrouter
from bot.texts import SYSTEM_PROMPTS
from bot.prompt_enhancer import detect_prompt_type, get_optimal_temperature, get_optimal_max_tokens

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kaysan.web")

WEB_DIR = Path(__file__).resolve().parent
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

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
    def __init__(self, max_requests: int = 30, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self._hits: dict[str, collections.deque] = {}

    def _client_ip(self, request: web.Request) -> str:
        return request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
               request.headers.get("X-Real-IP", "") or \
               request.remote or "unknown"

    def is_rate_limited(self, request: web.Request) -> bool:
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
# Middleware: Security Headers + CORS + Hide Server
# ============================================
@web.middleware
async def security_middleware(request: web.Request, handler):
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
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' https://api.openrouter.ai; "
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
def verify_telegram_init_data(init_data: str) -> dict | None:
    if not BOT_TOKEN:
        return None
    try:
        parsed = dict(x.split("=", 1) for x in init_data.split("&"))
        hash_val = parsed.pop("hash", None)
        if not hash_val:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash != hash_val:
            return None
        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            return None
        return json.loads(parsed.get("user", "{}"))
    except Exception as e:
        log.warning(f"Telegram verify failed: {e}")
        return None


# ============================================
# Handlers
# ============================================
async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "healthy",
        "service": "kaysan-ai-bot",
        "version": "3.2.0",
        "uptime_seconds": time.time() - _start_time,
    })


async def handle_verify_user(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        init_data = data.get("init_data", "")
        if not init_data:
            return web.json_response({"error": "No init_data"}, status=400)
        user = verify_telegram_init_data(init_data)
        if not user:
            return web.json_response({"error": "Invalid init data"}, status=401)
        return web.json_response({"ok": True, "user": {
            "id": user.get("id"),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "username": user.get("username", ""),
            "language_code": user.get("language_code", "en"),
            "is_premium": user.get("is_premium", False),
            "photo_url": user.get("photo_url", ""),
        }})
    except Exception:
        return web.json_response({"error": "Request failed"}, status=500)


async def handle_chat(request: web.Request) -> web.Response:
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded. Try again later."}, status=429)

    try:
        data = await request.json()
        message = data.get("message", "").strip()
        model_type = data.get("model_type", "auto")
        personality = data.get("personality", "balanced")
        custom_prompt = data.get("custom_prompt", "")
        init_data = data.get("init_data", "")
        stream = data.get("stream", True)

        if not message:
            return web.json_response({"error": "Empty message"}, status=400)

        user_name = "کاربر"
        if init_data:
            user = verify_telegram_init_data(init_data)
            if user:
                user_name = user.get("first_name", "کاربر")

        models = MODEL_TYPE_MAP.get(model_type, ALL_MODELS)
        temp = get_optimal_temperature(detect_prompt_type(message))
        max_tokens = get_optimal_max_tokens(detect_prompt_type(message))

        messages = []
        if custom_prompt:
            messages.append({"role": "system", "content": custom_prompt})
        else:
            system_prompt = SYSTEM_PROMPTS.get(personality, SYSTEM_PROMPTS.get("default", "You are Kaysan AI, a helpful assistant."))
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        if stream:
            response = web.StreamResponse(
                status=200,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
            await response.prepare(request)

            full_response = ""
            try:
                async for chunk, result in openrouter.chat_stream(
                    messages=messages,
                    models=models,
                    intent=model_type if model_type in ("chat", "code", "reason") else "chat",
                    temperature=temp,
                    max_tokens=max_tokens,
                ):
                    if chunk is None:
                        break
                    full_response += chunk
                    await response.write(f"data: {json.dumps({'text': chunk, 'done': False})}\n\n".encode())

                await response.write(f"data: {json.dumps({'text': '', 'done': True, 'full': full_response})}\n\n".encode())
            except Exception as e:
                log.error(f"Streaming error: {e}")
                await response.write(f"data: {json.dumps({'error': 'Streaming failed', 'done': True})}\n\n".encode())

            await response.write_eof()
            return response
        else:
            result_content, usage = await openrouter.chat(
                messages=messages,
                models=models,
                intent=model_type if model_type in ("chat", "code", "reason") else "chat",
                temperature=temp,
                max_tokens=max_tokens,
            )
            return web.json_response({"response": result_content})

    except Exception as e:
        log.error(f"Chat error: {e}")
        return web.json_response({"error": "Chat request failed"}, status=500)


async def handle_voice(request: web.Request) -> web.Response:
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)

    try:
        reader = await request.multipart()
        field = await reader.next()
        if not field or field.name != "audio":
            return web.json_response({"error": "No audio file"}, status=400)

        audio_data = await field.read()
        if len(audio_data) > 10 * 1024 * 1024:
            return web.json_response({"error": "Audio too large (max 10MB)"}, status=400)

        temp_path = Path(f"/tmp/voice_{secrets.token_hex(8)}.ogg")
        temp_path.write_bytes(audio_data)

        try:
            from bot.services.stt import transcribe_audio
            text = await transcribe_audio(str(temp_path))
            return web.json_response({"ok": True, "text": text})
        except Exception as e:
            log.error(f"STT error: {e}")
            return web.json_response({"error": "Transcription failed"}, status=500)
        finally:
            temp_path.unlink(missing_ok=True)

    except Exception as e:
        log.error(f"Voice error: {e}")
        return web.json_response({"error": "Voice request failed"}, status=500)


async def handle_image(request: web.Request) -> web.Response:
    if rate_limiter.is_rate_limited(request):
        return web.json_response({"error": "Rate limit exceeded"}, status=429)

    try:
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        style = data.get("style", "realistic")
        if not prompt:
            return web.json_response({"error": "Empty prompt"}, status=400)
        from bot.services.image import generate as generate_image
        result = await generate_image(prompt, style=style)
        return web.json_response({"url": result})
    except Exception:
        return web.json_response({"error": "Image generation failed"}, status=500)


async def handle_models(request: web.Request) -> web.Response:
    return web.json_response({
        "primary": config.PRIMARY_MODEL,
        "chat": config.CHAT_MODELS,
        "code": config.CODE_MODELS,
        "reason": config.REASON_MODELS,
        "vision": config.VISION_MODELS,
        "personality_presets": PERSONALITY_PRESETS,
    })


async def handle_index(request: web.Request) -> web.Response:
    return web.FileResponse(WEB_DIR / "index.html")


async def handle_not_found(request: web.Request) -> web.Response:
    return web.json_response({"error": "Not found"}, status=404)


_start_time = time.time()

app = web.Application(middlewares=[security_middleware])
app.router.add_get("/", handle_index)
app.router.add_get("/health", handle_health)
app.router.add_post("/api/chat", handle_chat)
app.router.add_post("/api/voice", handle_voice)
app.router.add_post("/api/image", handle_image)
app.router.add_get("/api/models", handle_models)
app.router.add_post("/api/verify-user", handle_verify_user)
app.router.add_static("/", path=str(WEB_DIR), show_index=False)
app.router.add_route("*", "/{path:.*}", handle_not_found)

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", "8080"))
    log.info(f"Kaysan AI Web Server v3.2 starting on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)
