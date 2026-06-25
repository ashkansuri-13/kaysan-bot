"""Web App (Mini App) handler for Kaysan AI."""
import asyncio
import json
import logging
from aiogram import Router, F
from aiogram.types import Message

from .. import config, openrouter, router as router_mod
from ..texts import SYSTEM_PROMPTS

log = logging.getLogger("kaysan.webapp")
router = Router()


@router.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """Handle data sent from Telegram Mini App."""
    try:
        data = json.loads(message.web_app_data.data)
        text = data.get("message", "").strip()
        lang = data.get("lang", "ku")
        history = data.get("history", [])

        if not text:
            await message.answer("تکایە پەیامێک بنووسە.")
            return

        intent = router_mod.detect_intent(text)
        models = router_mod.models_for(intent)

        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS.get("en", ""))
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": text})

        max_tok = config.MAX_TOKENS_BY_INTENT.get(intent, config.MAX_TOKENS_CHAT)
        temperature = config.TEMP_BY_INTENT.get(intent, 0.7)

        reply, usage = await asyncio.wait_for(
            openrouter.chat(messages, models, intent=intent,
                           max_tokens=max_tok, temperature=temperature),
            timeout=60,
        )

        await message.answer(reply)

    except asyncio.TimeoutError:
        await message.answer("⏱️ کات تەواو بوو — تکایە دوبارە هەوڵ بدە.")
    except Exception as e:
        log.error("WebApp error: %s", e)
        await message.answer(f"❌ هەڵە: {str(e)[:100]}")
