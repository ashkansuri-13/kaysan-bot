"""ترجمه و خلاصه‌سازی."""
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from .. import config, database as db, openrouter
from ..texts import SYSTEM_PROMPTS, t
from . import core

router = Router()
log = logging.getLogger("kaysan.translate")


@router.message(Command("translate"))
async def cmd_translate(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t(lang, "translate_usage"))
        return

    text = parts[1]
    status = await message.answer(t(lang, "thinking"))
    await message.bot.send_chat_action(message.chat.id, "typing")

    system = (
        "You are a professional translator. Translate the following text to ALL of these languages: "
        "Kurdish Sorani (کوردی سۆرانی), Persian (فارسی), and English. "
        "Format the output as:\n"
        "🇸🇴 Kurdish:\n[translation]\n\n"
        "🇮🇷 Persian:\n[translation]\n\n"
        "🇬🇧 English:\n[translation]"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=800)
        await db.incr_and_count(uid)
        try:
            await status.edit_text(reply, parse_mode=ParseMode.HTML)
        except Exception:
            await status.answer(reply, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("translate failed: %s", e)
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            await status.answer(t(lang, "error"))


@router.message(Command("summarize"))
async def cmd_summarize(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t(lang, "summarize_usage"))
        return

    text = parts[1]
    status = await message.answer(t(lang, "thinking"))
    await message.bot.send_chat_action(message.chat.id, "typing")

    lang_name = core._LANG_NAMES.get(lang, "English")
    system = (
        f"Summarize the following text in a clear, concise way. "
        f"Reply in {lang_name}. "
        f"Keep the summary short (3-5 sentences max) and include only key points."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=500)
        await db.incr_and_count(uid)
        try:
            await status.edit_text(reply)
        except Exception:
            await status.answer(reply)
    except Exception as e:
        log.warning("summarize failed: %s", e)
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            await status.answer(t(lang, "error"))
