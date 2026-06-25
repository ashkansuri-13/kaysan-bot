"""قابلیت‌های خلاقانه و سرگرمی: تحلیل احساسات، حافظه گروهی، مترجم فرهنگی، جلسه، بازی."""
import asyncio
import json
import logging
import random
from collections import defaultdict

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter
from ..texts import t
from ..ttl_dict import TTLDict

router = Router()
log = logging.getLogger("kaysan.ai_creative")


# ═══════════════════════════════════════════════
#  ۱۱. تشخیص احساسات جمعی (Group Mood)
# ═══════════════════════════════════════════════

@router.message(Command("mood"))
async def cmd_mood(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    from .ai_group import _group_messages
    msgs = _group_messages.get(chat_id, [])

    if len(msgs) < 10:
        await message.answer("📊 حداقل ۱۰ پیام لازمه.")
        return

    recent = msgs[-30:]
    texts = "\n".join(m["text"][:100] for m in recent)

    system = (
        "Analyze the mood/emotion of this group chat. "
        "Reply with:\n"
        "1. Overall mood (1 word: positive/negative/neutral/mixed)\n"
        "2. Mood score (1-10)\n"
        "3. Brief analysis (2 sentences)\n"
        "4. Suggestion to improve mood if negative\n"
        "Reply in the user's language."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Recent messages:\n{texts[:2000]}"},
    ]

    status = await message.answer("😊 در حال تحلیل احساسات...")
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300),
            timeout=15,
        )

        mood_emojis = {
            "positive": "😊", "negative": "😟", "neutral": "😐", "mixed": "🤔"
        }
        mood_word = "neutral"
        for kw in mood_emojis:
            if kw in reply.lower():
                mood_word = kw
                break

        await status.edit_text(
            f"{mood_emojis.get(mood_word, '📊')} <b>حال و هوای گروه:</b>\n\n{reply}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.warning("mood failed: %s", e)
        await status.edit_text("❌ خطا در تحلیل احساسات.")


# ═══════════════════════════════════════════════
#  ۱۲. حافظه گروهی (Group Memory)
# ═══════════════════════════════════════════════

_group_memories: dict[int, list[dict]] = defaultdict(list)


@router.message(Command("remember"))
async def cmd_remember(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        if message.reply_to_message:
            text = message.reply_to_message.text or ""
            if text:
                chat_id = message.chat.id
                _group_memories[chat_id].append({
                    "text": text[:500],
                    "added_by": message.from_user.full_name,
                    "time": message.date.isoformat() if message.date else "",
                })
                await message.answer("✅ پیام در حافظه گروه ذخیره شد!")
            return
        await message.answer(
            "🧠 <b>حافظه گروهی</b>\n\n"
            "بکارهێنان:\n"
            "/remember متن — ذخیره در حافظه\n"
            "یا روی پیام ریپلای کن: /remember\n"
            "/recall جستجو در حافظه\n"
            "/memories لیست حافظه‌ها",
            parse_mode=ParseMode.HTML,
        )
        return

    chat_id = message.chat.id
    _group_memories[chat_id].append({
        "text": parts[1][:500],
        "added_by": message.from_user.full_name,
        "time": message.date.isoformat() if message.date else "",
    })
    await message.answer("✅ در حافظه گروه ذخیره شد!")


@router.message(Command("recall"))
async def cmd_recall(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    memories = _group_memories.get(chat_id, [])

    if not memories:
        await message.answer("🧠 حافظه گروه خالیه.")
        return

    if len(parts) < 2:
        lines = ["🧠 <b>حافظه گروه:</b>\n"]
        for i, mem in enumerate(memories[-5:], 1):
            lines.append(f"{i}. {mem['text'][:80]}...")
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    query = parts[1]
    context = "\n".join(f"[{m['added_by']}] {m['text'][:200]}" for m in memories[-20:])

    system = (
        "Search through the group memory and find relevant entries. "
        "Reply in the user's language. If found, quote the memory and explain context."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Search query: {query}\n\nMemories:\n{context}"},
    ]

    status = await message.answer("🔍 در حال جستجو...")
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=400),
            timeout=15,
        )
        await status.edit_text(f"🧠 <b>نتیجه جستجو:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("recall failed: %s", e)
        await status.edit_text("❌ خطا در جستجو.")


@router.message(Command("memories"))
async def cmd_memories(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    memories = _group_memories.get(chat_id, [])

    if not memories:
        await message.answer("🧠 هنوز حافظه‌ای ذخیره نشده.")
        return

    lines = ["🧠 <b>حافظه گروه:</b>\n"]
    for i, mem in enumerate(memories[-10:], 1):
        lines.append(f"{i}. {mem['text'][:100]}")
        lines.append(f"   📌 توسط {mem['added_by']}")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════
#  ۱۳. مترجم فرهنگی
# ═══════════════════════════════════════════════

@router.message(Command("culture"))
async def cmd_culture(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "🌍 <b>مترجم فرهنگی</b>\n\n"
            "بکارهێنان: /culture اصطلاح یا عبارت\n"
            "مثال: /culture نوروز",
            parse_mode=ParseMode.HTML,
        )
        return

    term = parts[1]
    status = await message.answer("🌍 در حال تحقیق فرهنگی...")

    system = (
        "You are a cultural expert. Explain the cultural context, history, and significance "
        "of the following term/phrase. Include:\n"
        "1. What it means\n"
        "2. Cultural significance\n"
        "3. When/how it's used\n"
        "4. Similar concepts in other cultures\n"
        "Reply in the user's language. Be informative but concise."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Cultural term: {term}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=500),
            timeout=20,
        )
        await status.edit_text(
            f"🌍 <b>تحلیل فرهنگی:</b> {term}\n\n{reply}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.warning("culture failed: %s", e)
        await status.edit_text("❌ خطا در تحلیل فرهنگی.")


# ═══════════════════════════════════════════════
#  ۱۴. مدیر جلسات مجازی
# ═══════════════════════════════════════════════

_group_meetings: dict[int, list[dict]] = defaultdict(list)


@router.message(Command("meeting"))
async def cmd_meeting(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "📅 <b>مدیر جلسات</b>\n\n"
            "بکارهێنان:\n"
            "/meeting propose فردا ساعت ۱۰ — بودجه سالانه\n"
            "/meeting list — لیست جلسات\n"
            "/meeting summary خلاصه جلسه",
            parse_mode=ParseMode.HTML,
        )
        return

    chat_id = message.chat.id
    text = parts[1]

    if text.startswith("propose"):
        topic = text.replace("propose", "").strip()
        if not topic:
            await message.answer("فرمت: /meeting propose زمان — موضوع")
            return

        _group_meetings[chat_id].append({
            "topic": topic,
            "proposer": message.from_user.full_name,
            "time": message.date.isoformat() if message.date else "",
            "status": "proposed",
        })

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ شرکت می‌کنم", callback_data=f"mtg_join:{len(_group_meetings[chat_id])-1}")],
            [InlineKeyboardButton(text="❌ نمیام", callback_data=f"mtg_skip:{len(_group_meetings[chat_id])-1}")],
        ])

        await message.answer(
            f"📅 <b>جلسه پیشنهادی:</b>\n\n"
            f"📌 {topic}\n"
            f"👤 پیشنهاددهنده: {message.from_user.full_name}\n\n"
            f"شرکت می‌کنید؟",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

    elif text.startswith("summary"):
        summary_text = text.replace("summary", "").strip()
        if summary_text:
            await message.answer(f"📋 <b>خلاصه جلسه ذخیره شد.</b>\n\n{summary_text}", parse_mode=ParseMode.HTML)
        else:
            await message.answer("فرمت: /meeting summary متن خلاصه")

    elif text.startswith("list"):
        meetings = _group_meetings.get(chat_id, [])
        if not meetings:
            await message.answer("📅 جلسه‌ای ثبت نشده.")
            return
        lines = ["📅 <b>جلسات پیشنهادی:</b>\n"]
        for i, m in enumerate(meetings[-5:], 1):
            status_icon = "✅" if m["status"] == "confirmed" else "⏳"
            lines.append(f"{i}. {status_icon} {m['topic']}")
            lines.append(f"   👤 {m['proposer']}")
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("mtg_"))
async def cb_meeting(call: CallbackQuery):
    action, idx_str = call.data.split(":")
    try:
        idx = int(idx_str)
    except ValueError:
        await call.answer("خطا!")
        return

    chat_id = call.message.chat.id
    meetings = _group_meetings.get(chat_id, [])

    if idx >= len(meetings):
        await call.answer("جلسه دیگه وجود نداره!", show_alert=True)
        return

    if action == "mtg_join":
        await call.answer(f"✅ {call.from_user.full_name} شرکت می‌کنه!", show_alert=True)
    elif action == "mtg_skip":
        await call.answer("❌ متوجه شدم.", show_alert=True)


# ═══════════════════════════════════════════════
#  ۱۵. بازی‌ساز گروهی
# ═══════════════════════════════════════════════

_story_state = TTLDict(ttl_seconds=600, max_size=500)


@router.message(Command("storygame"))
async def cmd_story_game(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id

    if chat_id in _story_state:
        state = _story_state[chat_id]
        lines = ["📖 <b>داستان تا حالا:</b>\n"]
        for entry in state["story"][-5:]:
            lines.append(f"• {entry}")
        lines.append(f"\n🎯 نوبت: هر کسی یه جمله اضافه کنه!")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ جمله بعدی", callback_data="story:add")],
        ])
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    system = (
        "Create an engaging opening sentence for a group story game. "
        "Make it fun, mysterious, or exciting. "
        "Reply in the user's language. Only ONE sentence."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Start a story game!"},
    ]

    status = await message.answer("📖 در حال ساخت داستان...")
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=100),
            timeout=10,
        )

        _story_state[chat_id] = {
            "story": [reply.strip()],
            "players": [message.from_user.full_name],
        }

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ جمله بعدی", callback_data="story:add")],
        ])

        await status.edit_text(
            f"📖 <b>بازی داستان گروهی!</b>\n\n"
            f"🎯 هر نفر یه جمله اضافه کنه\n"
            f"📝 شروع: {reply.strip()}\n\n"
            f"نوبت: هر کسی دکمه رو بزنه!",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except Exception as e:
        log.warning("storygame failed: %s", e)
        await status.edit_text("❌ خطا در ساخت داستان.")


@router.callback_query(F.data == "story:add")
async def cb_story_add(call: CallbackQuery):
    chat_id = call.message.chat.id
    if chat_id not in _story_state:
        await call.answer("بازی تموم شده! /storygame", show_alert=True)
        return

    state = _story_state[chat_id]
    context = " ".join(state["story"][-3:])

    system = (
        "Continue this group story with ONE short sentence. "
        "Make it engaging and natural. "
        "Reply in the user's language. Only the new sentence, nothing else."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Story so far: {context}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=80),
            timeout=10,
        )

        new_sentence = reply.strip().strip('"').strip("'")
        state["story"].append(new_sentence)
        state["players"].append(call.from_user.full_name)

        lines = ["📖 <b>داستان ادامه دارد:</b>\n"]
        for entry in state["story"][-5:]:
            lines.append(f"• {entry}")
        lines.append(f"\n✍️ توسط: {call.from_user.full_name}")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ جمله بعدی", callback_data="story:add")],
        ])

        await call.message.edit_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        await call.answer()
    except Exception as e:
        log.warning("story add failed: %s", e)
        await call.answer("❌ خطا!", show_alert=True)


# ═══════════════════════════════════════════════
#  ۱۶-۲۰. مشاور شغلی، آشپزخانه، نگهبان حریم خصوصی، خلاق‌یار
# ═══════════════════════════════════════════════

@router.message(Command("career"))
async def cmd_career(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "💼 <b>مشاور شغلی</b>\n\n"
            "بکارهێنان: /career سؤال شغلی\n"
            "مثال: /career چه مهارتی یاد بگیرم؟",
            parse_mode=ParseMode.HTML,
        )
        return

    status = await message.answer("💼 در حال تحلیل...")
    system = (
        "You are a career advisor. Provide practical, actionable career advice. "
        "Reply in the user's language. Be specific and concise."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": parts[1]},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=400),
            timeout=20,
        )
        await status.edit_text(f"💼 <b>مشاوره شغلی:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("career failed: %s", e)
        await status.edit_text("❌ خطا.")


@router.message(Command("cook"))
async def cmd_cook(message: Message):
    parts = message.text.split(maxsplit=1)
    ingredients = parts[1] if len(parts) > 1 else "مواد موجود در یخچال"

    status = await message.answer("🍳 در حال پیشنهاد دستور غذا...")
    system = (
        "You are a chef. Suggest a recipe using available ingredients. "
        "Reply in the user's language. Include: name, ingredients, steps. "
        "Be concise and practical."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Ingredients: {ingredients}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=600),
            timeout=20,
        )
        await status.edit_text(f"🍳 <b>پیشنهاد آشپزی:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("cook failed: %s", e)
        await status.edit_text("❌ خطا.")


@router.message(Command("privacy"))
async def cmd_privacy_check(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    if not message.reply_to_message:
        await message.answer("روی یک پیام ریپلای کن تا بررسی حریم خصوصی بشه.")
        return

    text = message.reply_to_message.text or ""
    issues = []

    phone_pattern = re.compile(r"(\b0\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b)")
    if phone_pattern.search(text):
        issues.append("📱 شماره تلفن")

    id_pattern = re.compile(r"\b\d{10}\b")
    if id_pattern.search(text):
        issues.append("🪪 کد ملی")

    email_pattern = re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b")
    if email_pattern.search(text):
        issues.append("📧 آدرس ایمیل")

    address_pattern = re.compile(r"(خیابان|کوچه|بلوار|پلاک|خ\.|ک\.)")
    if address_pattern.search(text):
        issues.append("🏠 آدرس")

    if issues:
        await message.answer(
            f"🚨 <b>هشدار حریم خصوصی!</b>\n\n"
            f"اطلاعات حساس شناسایی شد:\n"
            + "\n".join(f"  ⚠️ {i}" for i in issues)
            + "\n\nلطفاً این پیام رو حذف کنید.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer("✅ اطلاعات حساسی شناسایی نشد.")


import re


@router.message(Command("brainstorm"))
async def cmd_brainstorm(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "💡 <b>خلاق‌یار</b>\n\n"
            "بکارهێنان: /brainstorm موضوع\n"
            "مثال: /brainstorm ایده برای اپلیکیشن",
            parse_mode=ParseMode.HTML,
        )
        return

    topic = parts[1]
    status = await message.answer("💡 در حال طوف فکری...")

    system = (
        "You are a creative brainstorming partner. Generate 10 diverse, innovative ideas "
        "for the given topic. Reply in the user's language. "
        "Format: numbered list, one idea per line, brief description."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Brainstorm ideas for: {topic}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=600),
            timeout=20,
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👍 عالیه!", callback_data="brainstorm:like")],
            [InlineKeyboardButton(text="🔄 ایده‌های بیشتر", callback_data="brainstorm:more")],
        ])
        await status.edit_text(
            f"💡 <b>طوف فکری:</b> {topic}\n\n{reply}",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except Exception as e:
        log.warning("brainstorm failed: %s", e)
        await status.edit_text("❌ خطا.")


@router.callback_query(F.data.startswith("brainstorm:"))
async def cb_brainstorm(call: CallbackQuery):
    action = call.data.split(":")[1]
    if action == "like":
        await call.answer("🎉 ممنون!", show_alert=True)
    elif action == "more":
        await call.answer()
        await call.message.answer("💡 موضوع جدید بنویس: /brainstorm موضوع")
