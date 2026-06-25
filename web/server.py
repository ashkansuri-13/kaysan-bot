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


async def handle_chat(request):
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
        middlewares=[security_headers_middleware, cors_middleware, rate_limit_middleware]
    )

    app.router.add_get("/", handle_index)
    app.router.add_get("/style.css", handle_css)
    app.router.add_get("/app.js", handle_js)
    app.router.add_get("/logo.png", handle_logo)
    app.router.add_get("/manifest.json", handle_manifest)
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/models", handle_models)
    app.router.add_get("/api/personality", handle_personality_presets)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_post("/api/chat/stream", handle_chat_stream)

    port = int(os.getenv("WEB_PORT", "3000"))
    log.info("Kaysan Web running on http://0.0.0.0:%d", port)
    log.info("API Key: %s...%s", API_KEY[:8], API_KEY[-4:])
    web.run_app(app, host="0.0.0.0", port=port, print=None)


if __name__ == "__main__":
    main()
