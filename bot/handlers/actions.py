"""دکمه‌های زیر جواب: «جواب دیگه»، «به‌صورت عکس»، «صدادار»، «تکمیل سؤال»، «فیدبک»."""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, BufferedInputFile

from .. import database as db
from ..services.tts import text_to_speech
from ..texts import t
from . import core

router = Router()
log = logging.getLogger("kaysan.actions")


@router.callback_query(F.data == "regen")
async def cb_regen(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    last = core.get_last(uid)
    if not last:
        await call.answer()
        return
    if not await db.can_send(uid):
        await call.answer(t(lang, "limit_reached", limit=0), show_alert=True)
        return
    await call.answer()
    await core.process_text(call.message, last["text"], last.get("lang", lang), uid=uid)


@router.callback_query(F.data == "toimg")
async def cb_toimg(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    last = core.get_last(uid)
    if not last:
        await call.answer()
        return
    if not await db.can_send(uid):
        await call.answer(t(lang, "limit_reached", limit=0), show_alert=True)
        return
    await call.answer()
    await core._do_image(call.message, last["text"], last.get("lang", lang), uid=uid)


@router.callback_query(F.data == "tts")
async def cb_tts(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)

    # اول از _last بگیر، بعد از SQLite
    last = core.get_last(uid)
    reply_text = None
    if last and last.get("reply"):
        reply_text = last["reply"]
    else:
        reply_text = await db.get_last_reply(uid)

    if not reply_text:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await call.answer()
    status = await call.message.answer(t(lang, "thinking"))
    audio = await text_to_speech(reply_text[:3000], lang)
    if audio:
        try:
            await status.delete()
            await call.message.answer_voice(
                BufferedInputFile(audio, filename="kaysan_voice.ogg"),
            )
        except Exception:
            await status.edit_text(t(lang, "error"))
    else:
        await status.edit_text(t(lang, "error"))


@router.callback_query(F.data.startswith("clarify:"))
async def cb_clarify(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    parts = call.data.split(":", 2)
    if len(parts) < 3:
        await call.answer()
        return
    selected = parts[2]
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await core.process_text(call.message, selected, lang, uid=uid)


@router.callback_query(F.data == "alts")
async def cb_alternatives(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    alts = core._alternatives.get(call.message.message_id)
    if not alts:
        await call.answer(t(lang, "no_alternatives") if t(lang, "no_alternatives") else "جواب دیگه‌ای نیست", show_alert=True)
        return
    await call.answer()
    lines = []
    for i, alt in enumerate(alts, 1):
        model_short = alt["model"].split("/")[-1] if "/" in alt["model"] else alt["model"]
        lines.append(f"**{i}. {model_short}** (⭐{alt['score']:.1f})\n{alt['reply'][:1500]}")
    text = "\n\n---\n\n".join(lines)
    try:
        await call.message.answer(text[:4000], parse_mode="Markdown")
    except Exception:
        await call.message.answer(text[:4000])


# ============================================================
#  فیدبک — 👍/👎
# ============================================================

@router.callback_query(F.data == "feedback_like")
async def cb_feedback_like(call: CallbackQuery):
    uid = call.from_user.id
    await db.add_feedback(uid, call.message.message_id, 1)
    await call.answer("✅ ممنون از فیدبکت!", show_alert=True)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data == "feedback_dislike")
async def cb_feedback_dislike(call: CallbackQuery):
    uid = call.from_user.id
    await db.add_feedback(uid, call.message.message_id, -1)
    await call.answer("✅ فیدبکت ثبت شد. سعی می‌کنم بهتر بشم!", show_alert=True)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
