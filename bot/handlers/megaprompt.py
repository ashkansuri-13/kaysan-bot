"""Mega Prompt API — نوشتن پرامپت حرفه‌ای و ارسال به مدل‌ها."""
import logging
import asyncio

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from .. import config, database as db, openrouter
from ..texts import SYSTEM_PROMPTS, t
from ..ttl_dict import TTLDict
from . import core

router = Router()
log = logging.getLogger("kaysan.megaprompt")

_MEGA_SYSTEM = """You are a MEGA PROMPT ENGINEER — the world's best AI prompt architect.

Your job:
1. Take the user's simple request
2. Write a DETAILED, PROFESSIONAL mega prompt that will get the BEST possible result from an AI model
3. Then EXECUTE that prompt and give the final answer

MEGA PROMPT RULES:
- Be extremely specific and detailed
- Include context, constraints, examples, format requirements
- Add role assignment, tone, style, audience
- Include edge cases and fallback instructions
- Add evaluation criteria
- Write in the same language as the user

OUTPUT FORMAT:
First, show the mega prompt you created (in a code block).
Then, execute it and give the final answer.

Example structure:
📋 **Mega Prompt:**
```
[detailed prompt here]
```

✅ **Result:**
[executed answer]"""


@router.message(Command("mega"))
async def cmd_mega(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        usage = {
            "ku": "بکارهێنان: /mega پرسیارەکەت\nمثال: /mega ڕێنمایی بۆ فێربوونی پای썬",
            "fa": "استفاده: /mega سوال شما\nمثال: /mega راهنمای یادگیری پایتون",
            "en": "Usage: /mega your question\nExample: /mega guide to learning Python",
        }
        await message.answer(usage.get(lang, usage["en"]))
        return

    user_text = parts[1]
    status = await message.answer(core.random.choice(core._THINKING_MSGS))
    await message.bot.send_chat_action(message.chat.id, "typing")

    anim_task = asyncio.create_task(core._animate_thinking(status, lang))

    dates = core._get_triple_date()
    date_line = dates.get(lang, dates["en"])
    base_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
    system_prompt = base_prompt.replace(
        "{current_datetime}", f"{dates['short']} {dates['time']} — {date_line}"
    ) + "\n\n" + _MEGA_SYSTEM

    messages = openrouter.with_system(system_prompt, user_text)

    try:
        reply, usage_data = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, intent="code", max_tokens=4000),
            timeout=120,
        )
    except asyncio.TimeoutError:
        anim_task.cancel()
        await core._handle_error(message, status, lang, uid, "timeout", user_text)
        return
    except Exception as e:
        anim_task.cancel()
        log.warning("mega prompt failed: %s", e)
        await core._handle_error(message, status, lang, uid, "chat_failed", user_text)
        return

    anim_task.cancel()
    await db.incr_and_count(uid)

    cost = usage_data.get("cost", 0)
    if cost == 0:
        pt = usage_data.get("prompt_tokens", 0)
        ct = usage_data.get("completion_tokens", 0)
        cost = pt * 0.0000007 + ct * 0.0000028
    await db.add_usage(uid, usage_data.get("prompt_tokens", 0),
                       usage_data.get("completion_tokens", 0), cost)

    core._last[uid] = {"text": user_text, "intent": "chat", "lang": lang, "reply": reply}
    await db.save_last_reply(uid, reply)

    await core._send_reply(status, reply, lang, uid)


@router.message(Command("prompt"))
async def cmd_prompt_only(message: Message):
    """فقط mega prompt می‌نویسه بدون اجرا."""
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        usage = {
            "ku": "بکارهێنان: /prompt پرسیارەکەت\nتەنها پرامپت دروست دەکات بێ ئەنجام.",
            "fa": "استفاده: /prompt سوال شما\nفقط پرامپت می‌نویسد بدون نتیجه.",
            "en": "Usage: /prompt your question\nWrites only the prompt, no execution.",
        }
        await message.answer(usage.get(lang, usage["en"]))
        return

    user_text = parts[1]
    status = await message.answer("📝 در حال نوشتن پرامپت...")
    await message.bot.send_chat_action(message.chat.id, "typing")

    system = """You are a MEGA PROMPT ENGINEER. Write ONLY a detailed, professional prompt for an AI model.

RULES:
- Be extremely specific and detailed
- Include role, context, constraints, format, examples
- Write in the user's language
- Output ONLY the prompt in a code block, nothing else
- Make it ready to copy-paste into any AI model"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, intent="code", max_tokens=2000),
            timeout=60,
        )
        await db.incr_and_count(uid)
        try:
            await status.edit_text(f"📝 **Mega Prompt:**\n\n```\n{reply}\n```",
                                   parse_mode=ParseMode.HTML)
        except Exception:
            await status.answer(f"📝 **Mega Prompt:**\n\n```\n{reply}\n```",
                                parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("prompt only failed: %s", e)
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            pass


@router.message(Command("apiprompt"))
async def cmd_api_prompt(message: Message):
    """پرامپت + ارسال مستقیم به API مدل انتخابی."""
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧠 MiMo", callback_data="api_model:mimo/mimo-auto"),
             InlineKeyboardButton(text="🤖 DeepSeek", callback_data="api_model:deepseek/deepseek-chat")],
            [InlineKeyboardButton(text="💡 GPT-4o", callback_data="api_model:openai/gpt-4o-mini"),
             InlineKeyboardButton(text="🎭 Claude", callback_data="api_model:anthropic/claude-haiku-4.5")],
            [InlineKeyboardButton(text="🔮 Gemini", callback_data="api_model:google/gemini-2.5-flash")],
        ])
        usage = {
            "ku": "بکارهێنان: /apiprompt مۆدێل | پرسیار\nیا مۆدێل هەڵبژێرە:",
            "fa": "استفاده: /apiprompt مدل | سوال\nیا مدل رو انتخاب کن:",
            "en": "Usage: /apiprompt model | question\nOr choose a model:",
        }
        await message.answer(usage.get(lang, usage["en"]), reply_markup=kb)
        return

    text = parts[1]
    if "|" in text:
        model_name, question = text.split("|", 1)
        model_name = model_name.strip()
        question = question.strip()
        model_map = {
            "mimo": "mimo/mimo-auto",
            "deepseek": "deepseek/deepseek-chat",
            "gpt": "openai/gpt-4o-mini",
            "gpt4o": "openai/gpt-4o-mini",
            "claude": "anthropic/claude-haiku-4.5",
            "gemini": "google/gemini-2.5-flash",
            "qwen": "qwen/qwen3-coder:free",
        }
        selected_model = model_map.get(model_name.lower(), model_name)
    else:
        selected_model = config.CHAT_MODELS[0] if config.CHAT_MODELS else "deepseek/deepseek-chat"
        question = text

    status = await message.answer(f"🚀 ارسال به `{selected_model}`...")
    await message.bot.send_chat_action(message.chat.id, "typing")

    mega_system = """You are a MEGA PROMPT ENGINEER. 
1. First, write a detailed mega prompt for the user's question
2. Then execute it and give the best possible answer
Be thorough and professional."""

    messages = openrouter.with_system(mega_system, question)

    try:
        reply, usage_data = await asyncio.wait_for(
            openrouter.chat(messages, [selected_model], intent="chat", max_tokens=4000),
            timeout=120,
        )
        await db.incr_and_count(uid)

        try:
            await status.edit_text(reply[:4000], parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await status.answer(reply[:4000], parse_mode=ParseMode.HTML)
            except Exception:
                chunks = [reply[i:i+3900] for i in range(0, len(reply), 3900)]
                for ch in chunks:
                    await message.answer(ch)

    except Exception as e:
        log.warning("api prompt failed: %s", e)
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            pass


@router.callback_query(F.data.startswith("api_model:"))
async def cb_api_model(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    model = call.data.split(":", 1)[1]
    _mega_state[uid] = {"model": model}
    await call.answer()
    await call.message.edit_text(
        "✨ مدل انتخاب شد!\n\nحالا سوالت رو بنویس:",
        parse_mode=ParseMode.HTML,
    )


_mega_state = TTLDict(ttl_seconds=300, max_size=1000)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_mega_input(message: Message):
    uid = message.from_user.id
    state = _mega_state.get(uid)
    if not state:
        return

    model = state.pop("model")
    question = message.text

    status = await message.answer(f"🚀 ارسال به `{model}`...")
    await message.bot.send_chat_action(message.chat.id, "typing")

    mega_system = """You are a MEGA PROMPT ENGINEER.
1. First, write a detailed mega prompt for the user's question
2. Then execute it and give the best possible answer
Be thorough and professional."""

    messages = openrouter.with_system(mega_system, question)

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, [model], intent="chat", max_tokens=4000),
            timeout=120,
        )
        await db.incr_and_count(uid)
        try:
            await status.edit_text(reply[:4000], parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await status.answer(reply[:4000], parse_mode=ParseMode.HTML)
            except Exception:
                chunks = [reply[i:i+3900] for i in range(0, len(reply), 3900)]
                for ch in chunks:
                    await message.answer(ch)
    except Exception as e:
        log.warning("mega input failed: %s", e)
        try:
            await status.edit_text(t("ku", "error"))
        except Exception:
            pass

    await message.stop_propagation()
