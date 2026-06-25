"""هندلر رسانه: ویس → متن → روتر | عکس → مدل vision."""
import base64
import asyncio

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message

from .. import config, database as db, openrouter, router as rtr
from ..keyboards import answer_kb
from ..services import voice as voice_svc
from ..texts import SYSTEM_PROMPTS, t
from . import core

router = Router()

_LANG_NAMES = {
    "ku": "Kurdish Sorani (کوردی سۆرانی)",
    "fa": "Persian (فارسی)",
    "en": "English",
}


async def _safe_edit_or_answer(msg, text, **kwargs):
    try:
        await msg.edit_text(text, **kwargs)
    except Exception:
        try:
            await msg.answer(text, **kwargs)
        except Exception:
            pass


@router.message(F.voice | F.audio)
async def on_voice(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    if not await core.enforce_channel(message):
        return
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    status = await message.answer(t(lang, "listening"))
    src = message.voice or message.audio
    try:
        buf = await message.bot.download(src)
        data = buf.read()
    except Exception:
        await _safe_edit_or_answer(status, t(lang, "error"))
        return

    text = await voice_svc.transcribe(data, fmt="ogg")
    if not text:
        await _safe_edit_or_answer(status, t(lang, "voice_failed"))
        return

    try:
        await status.delete()
    except Exception:
        pass
    await core.process_text(message, text, lang)


@router.message(F.photo)
async def on_photo(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    if not await core.enforce_channel(message):
        return
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    status = await message.answer(t(lang, "looking"))
    try:
        photo = message.photo[-1]
        buf = await message.bot.download(photo)
        b64 = base64.b64encode(buf.read()).decode()
        data_url = f"data:image/jpeg;base64,{b64}"
    except Exception:
        await _safe_edit_or_answer(status, t(lang, "error"))
        return

    caption = message.caption or "Describe this image and answer any question in it."
    from .core import _get_triple_date
    dates = _get_triple_date()
    date_line = dates.get(lang, dates["en"])
    base_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
    system_prompt = base_prompt.replace(
        "{current_datetime}", f"{dates['short']} {dates['time']} — {date_line}")
    messages = openrouter.vision_message(system_prompt, caption, data_url)
    try:
        reply, usage = await openrouter.chat(messages, config.VISION_MODELS, intent="chat")
    except Exception:
        await _safe_edit_or_answer(status, t(lang, "error"))
        return
    await db.incr_and_count(uid)
    core._last[uid] = {"text": f"[photo] {caption}", "intent": "image", "lang": lang, "reply": reply}
    await core._send_reply(status, reply, lang, uid)
