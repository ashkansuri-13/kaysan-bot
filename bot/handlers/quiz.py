"""کوییز، معما، لطیفه — /quiz /riddle /joke."""
import json
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter
from ..texts import t
from . import core

router = Router()
log = logging.getLogger("kaysan.quiz")

_QUIZ_CACHE: dict[int, dict] = {}


@router.message(Command("quiz"))
async def cmd_quiz(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    system = (
        "Generate a fun trivia question with 4 multiple choice options (A, B, C, D). "
        "Reply in the user's language. "
        "Format your reply as JSON:\n"
        '{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A"}'
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Give me a trivia question about science, history, or geography."},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300)
        data = json.loads(reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        question = data["question"]
        options = data["options"]
        correct = data["answer"][0].upper()

        _QUIZ_CACHE[uid] = {"answer": correct, "question": question}

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"quiz:{opt[0]}")]
            for opt in options
        ])

        await message.answer(f"🧠 <b>{question}</b>", reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("quiz failed: %s", e)
        await message.answer(t(lang, "error"))


@router.callback_query(F.data.startswith("quiz:"))
async def cb_quiz(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    chosen = call.data.split(":")[1]
    cached = _QUIZ_CACHE.get(uid)

    if not cached:
        await call.answer(t(lang, "error"), show_alert=True)
        return

    if chosen == cached["answer"]:
        text = t(lang, "quiz_correct")
    else:
        text = t(lang, "quiz_wrong", answer=cached["answer"])

    del _QUIZ_CACHE[uid]
    await call.message.edit_text(
        f"🧠 {cached['question']}\n\n{text}",
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.message(Command("riddle"))
async def cmd_riddle(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    lang_name = {"ku": "Kurdish Sorani", "fa": "Persian", "en": "English"}.get(lang, "English")
    system = f"You are a riddle master. Give a fun riddle in {lang_name}. Format: riddle on first line, then 'Answer:' on next line."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Give me a riddle."},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=200)
        await message.answer(reply, parse_mode=ParseMode.HTML)
    except Exception:
        await message.answer(t(lang, "error"))


@router.message(Command("joke"))
async def cmd_joke(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    lang_name = {"ku": "Kurdish Sorani", "fa": "Persian", "en": "English"}.get(lang, "English")
    system = f"You are a funny comedian. Tell a short, clean, funny joke in {lang_name}."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Tell me a joke."},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=200)
        await message.answer(reply)
    except Exception:
        await message.answer(t(lang, "error"))
