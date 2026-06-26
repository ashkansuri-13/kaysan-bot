#!/usr/bin/env python3
"""Kaysan AI Web Server — Telegram Mini App with full UI/UX (2026)."""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path

from aiohttp import web

sys.path.insert(0, str(Path(__file__).parent.parent))
from bot import config, openrouter, router
from bot.texts import SYSTEM_PROMPTS
from bot.prompt_enhancer import enhance_prompt_engine, detect_prompt_type, get_optimal_model, get_optimal_temperature, get_optimal_max_tokens

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kaysan.web")

WEB_DIR = Path(__file__).resolve().parent
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

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
    "balanced": {"name": "متعادل", "name_en": "Balanced", "icon": "⚖️"},
    "blunt": {"name": "رُک و راست", "name_en": "Blunt", "icon": "🔪"},
    "exaggerated": {"name": "اغراق‌آمیز", "name_en": "Exaggerated", "icon": "🎭"},
    "friendly": {"name": "کاربرپسند", "name_en": "User-Friendly", "icon": "🤗"},
    "professional": {"name": "حرفه‌ای", "name_en": "Professional", "icon": "💼"},
    "sarcastic": {"name": "کنایه‌آمیز", "name_en": "Sarcastic", "icon": "😏"},
    "caring": {"name": "مهربان", "name_en": "Caring", "icon": "💕"},
    "technical": {"name": "فنی", "name_en": "Technical", "icon": "🔧"},
}


def verify_telegram_init_data(init_data: str) -> dict | None:
    """Verify Telegram Mini App init data using HMAC-SHA256."""
    if not BOT_TOKEN:
        return None

    try:
        parsed = dict(x.split("=", 1) for x in init_data.split("&"))
        hash_val = parsed.pop("hash", None)
        if not hash_val:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        secret_key = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if calculated_hash != hash_val:
            return None

        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            return None

        user_data = json.loads(parsed.get("user", "{}"))
        return user_data
    except Exception as e:
        log.warning(f"Telegram init data verification failed: {e}")
        return None


async def handle_verify_user(request: web.Request) -> web.Response:
    """Verify Telegram Mini App user and return user info."""
    try:
        data = await request.json()
        init_data = data.get("init_data", "")

        if not init_data:
            return web.json_response({"error": "No init_data"}, status=400)

        user = verify_telegram_init_data(init_data)
        if not user:
            return web.json_response({"error": "Invalid init data"}, status=401)

        return web.json_response({
            "ok": True,
            "user": {
                "id": user.get("id"),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "username": user.get("username", ""),
                "language_code": user.get("language_code", "en"),
                "is_premium": user.get("is_premium", False),
                "photo_url": user.get("photo_url", ""),
            }
        })
    except Exception as e:
        log.error(f"Verify user error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "healthy",
        "service": "kaysan-ai-bot",
        "version": "3.0.0",
        "uptime_seconds": time.time() - _start_time,
    })


async def handle_chat(request: web.Request) -> web.Response:
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

        personality_config = PERSONALITY_PRESETS.get(personality, PERSONALITY_PRESETS["balanced"])

        models = MODEL_TYPE_MAP.get(model_type)
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
                async for chunk in openrouter.stream_chat(
                    messages=messages,
                    models=models,
                    temperature=temp,
                    max_tokens=max_tokens,
                ):
                    if isinstance(chunk, dict):
                        text = chunk.get("content", "")
                    else:
                        text = str(chunk)
                    full_response += text
                    await response.write(f"data: {json.dumps({'text': text, 'done': False})}\n\n".encode())

                await response.write(f"data: {json.dumps({'text': '', 'done': True, 'full': full_response})}\n\n".encode())
            except Exception as e:
                log.error(f"Streaming error: {e}")
                await response.write(f"data: {json.dumps({'error': str(e), 'done': True})}\n\n".encode())

            await response.write_eof()
            return response
        else:
            result = await openrouter.chat(
                messages=messages,
                models=models,
                temperature=temp,
                max_tokens=max_tokens,
            )
            return web.json_response({"response": result})

    except Exception as e:
        log.error(f"Chat error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_image(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        prompt = data.get("prompt", "").strip()
        style = data.get("style", "realistic")

        if not prompt:
            return web.json_response({"error": "Empty prompt"}, status=400)

        from bot.services.image import generate as generate_image
        result = await generate_image(prompt, style=style)
        return web.json_response({"url": result})

    except Exception as e:
        log.error(f"Image error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_models(request: web.Request) -> web.Response:
    return web.json_response({
        "primary": config.PRIMARY_MODEL,
        "chat": config.CHAT_MODELS,
        "code": config.CODE_MODELS,
        "reason": config.REASON_MODELS,
        "vision": config.VISION_MODELS,
        "personality_presets": PERSONALITY_PRESETS,
    })


_start_time = time.time()

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/api/chat", handle_chat)
app.router.add_post("/api/image", handle_image)
app.router.add_get("/api/models", handle_models)
app.router.add_post("/api/verify-user", handle_verify_user)
app.router.add_static("/", path=str(WEB_DIR), show_index=False)

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", "8080"))
    log.info(f"Kaysan AI Web Server starting on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)
