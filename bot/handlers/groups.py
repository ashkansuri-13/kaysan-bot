"""قابلیت‌های گروه و کانال — ۲۰ امکان هوشمند."""
import asyncio
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, Command
from aiogram.types import CallbackQuery, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter
from ..texts import SYSTEM_PROMPTS, t
from ..ttl_dict import TTLDict

router = Router()
log = logging.getLogger("kaysan.groups")

# ─────────────────────────────────────────────
#  State برای فیچرهای گروهی
# ─────────────────────────────────────────────

_flood_tracker = TTLDict(ttl_seconds=60, max_size=10000)
_last_msg_time = TTLDict(ttl_seconds=3600, max_size=10000)

# فیلتر کلمات نامناسب
_BAD_WORDS_RE = re.compile(
    r"(fuck|shit|bitch|ass|damn|dick|crap|piss)", re.I
)

_SPAM_LINKS_RE = re.compile(
    r"(t\.me/\+|t\.me/joinchat|bit\.ly|tinyurl\.com|shorturl|ad\.fly|goo\.gl|"
    r"free.*gift|win.*prize|click.*here|کلیک.*کن|رایگان.*بگیر|هدیه.*رایگان)", re.I
)

# ─────────────────────────────────────────────
#  ۱. خوش‌آمدگویی اعضا
# ─────────────────────────────────────────────

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_member_join(event: ChatMemberUpdated):
    chat = event.chat
    user = event.new_chat_member.user
    uid = user.id

    await db.ensure_group(chat.id, chat.title or "")

    welcome_texts = {
        "ku": f"🎉 بەخێربێیت <b>{user.full_name}</b>!\n\nبەخێربێیت بۆ گرووپی <b>{chat.title}</b>.\nتکایە ڕێکخراوەکان بخوێنەوە و خۆت خۆش بگرە 😊",
        "fa": f"🎉 خوش اومدی <b>{user.full_name}</b>!\n\nبه گروه <b>{chat.title}</b> خوش اومدی.\nلطفاً قوانین رو بخون و خودت رو راحت کن 😊",
        "en": f"🎉 Welcome <b>{user.full_name}</b>!\n\nWelcome to <b>{chat.title}</b>.\nPlease read the rules and make yourself at home 😊",
    }

    settings = await db.get_group_settings(chat.id)
    if not settings.get("welcome_on", 1):
        return

    lang = settings.get("language", "ku")
    custom = settings.get("welcome_text", "")
    if custom:
        text = custom.replace("{name}", user.full_name).replace("{group}", chat.title or "")
    else:
        text = welcome_texts.get(lang, welcome_texts["en"])

    try:
        await chat.send_message(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("welcome failed: %s", e)


# ─────────────────────────────────────────────
#  ۲. وداع اعضا
# ─────────────────────────────────────────────

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def on_member_leave(event: ChatMemberUpdated):
    chat = event.chat
    user = event.old_chat_member.user

    settings = await db.get_group_settings(chat.id)
    if not settings.get("goodbye_on", 1):
        return

    lang = settings.get("language", "ku")
    texts = {
        "ku": f"👋 <b>{user.full_name}</b> چوونەدەرەوە. سەلامان با!",
        "fa": f"👋 <b>{user.full_name}</b> از گروه رفت. موفق باشی!",
        "en": f"👋 <b>{user.full_name}</b> left the group. Goodbye!",
    }

    try:
        await chat.send_message(texts.get(lang, texts["en"]), parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("goodbye failed: %s", e)


# ─────────────────────────────────────────────
#  ۳. فیلتر اسپم — حذف خودکار لینک‌های اسپم
# ─────────────────────────────────────────────

@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def anti_spam(message: Message):
    if not message.from_user:
        return
    if not message.text:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if await _is_admin(message.bot, chat_id, uid):
        return

    if _SPAM_LINKS_RE.search(message.text):
        try:
            await message.delete()
            await message.answer(
                f"🚫 <b>اسپم حذف شد!</b>\nکاربر {message.from_user.full_name} لینک اسپم ارسال کرد.",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            log.warning("spam delete failed: %s", e)
        return
# ─────────────────────────────────────────────

@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def anti_bad_words(message: Message):
    if not message.from_user:
        return
    if not message.text:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if await _is_admin(message.bot, chat_id, uid):
        return

    if _BAD_WORDS_RE.search(message.text):
        try:
            await message.delete()
            await message.answer(
                f"⚠️ <b>پیام نامناسب حذف شد!</b>\n{message.from_user.full_name}، لطفاً محترمانه صحبت کن.",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            log.warning("badwords delete failed: %s", e)
        return


# ─────────────────────────────────────────────
#  ۵. ضد Flood — جلوگیری از ارسال زیاد
# ─────────────────────────────────────────────

@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def anti_flood(message: Message):
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id
    now = time.time()

    if await _is_admin(message.bot, chat_id, uid):
        return

    _flood_tracker[chat_id][uid].append(now)
    _flood_tracker[chat_id][uid] = [
        t for t in _flood_tracker[chat_id][uid] if now - t < 10
    ]

    if len(_flood_tracker[chat_id][uid]) > 5:
        try:
            await message.delete()
            warn = await message.answer(
                f"⚠️ <b>{message.from_user.full_name}</b>، لطفاً آرام‌تر!",
                parse_mode=ParseMode.HTML,
            )
            await asyncio.sleep(5)
            await warn.delete()
        except Exception as e:
            log.warning("flood warn failed: %s", e)
        return


# ─────────────────────────────────────────────
#  ۶. Slow Mode — حالت آهسته
# ─────────────────────────────────────────────

@router.message(Command("slowmode"))
async def cmd_slowmode(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        await message.answer("فقط ادمین‌ها می‌تونن slow mode رو تنظیم کنن.")
        return

    await db.ensure_group(chat_id, message.chat.title or "")
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("بکارهێنان: /slowmode 30\n(ثانیه بین هر پیام — 0 برای غیرفعال)")
        return

    seconds = int(parts[1])
    if seconds == 0:
        await db.update_group(chat_id, slow_mode=0)
        await message.answer("✅ Slow mode غیرفعال شد.")
    else:
        await db.update_group(chat_id, slow_mode=seconds)
        await message.answer(f"✅ Slow mode: هر {seconds} ثانیه یک پیام")


@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def enforce_slow_mode(message: Message):
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    settings = await db.get_group_settings(chat_id)
    slow_seconds = settings.get("slow_mode", 0)
    if not slow_seconds:
        return
    if await _is_admin(message.bot, chat_id, uid):
        return

    now = time.time()
    last = _last_msg_time.get(chat_id, {}).get(uid, 0)
    remaining = slow_seconds - (now - last)

    if remaining > 0:
        try:
            await message.delete()
            warn = await message.answer(
                f"⏳ <b>{message.from_user.full_name}</b>، صبر کن!\n{int(remaining)} ثانیه دیگه صبر کن.",
                parse_mode=ParseMode.HTML,
            )
            await asyncio.sleep(min(remaining, 5))
            await warn.delete()
        except Exception:
            pass
        return

    _last_msg_time[chat_id][uid] = now


# ─────────────────────────────────────────────
#  ۷. پاسخ خودکار به کلمات کلیدی
# ─────────────────────────────────────────────

_KEYWORD_REPLIES: dict[str, dict[str, str]] = {
    "ku": {
        r"(سلام|سڵاو|هی)": "سڵاو! چۆنیت؟ 😊",
        r"(ممنون|ساگ|سوان)": "خواهیشه! ❤️",
        r"(خسته|هەستەبەر)": "خۆش باشە! 💪",
    },
    "fa": {
        r"(سلام|درود|هی)": "سلام! حالت چطوره؟ 😊",
        r"(ممنون|متشکر)": "خواهش می‌کنم! ❤️",
        r"(خسته|خمیازه)": "خوش باش! 💪",
    },
    "en": {
        r"(hi|hello|hey)": "Hey! How are you? 😊",
        r"(thanks|thx)": "You're welcome! ❤️",
        r"(tired|sleepy)": "Hang in there! 💪",
    },
}


@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def auto_reply_keywords(message: Message):
    if not message.from_user:
        return
    if not message.text:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if await _is_admin(message.bot, chat_id, uid):
        return

    for lang, patterns in _KEYWORD_REPLIES.items():
        for pattern, reply in patterns.items():
            if re.search(pattern, message.text, re.I):
                try:
                    await message.answer(reply)
                except Exception:
                    pass
                return


# ─────────────────────────────────────────────
#  ۸. پاسخ به منشن ربات
# ─────────────────────────────────────────────

@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def on_bot_mention(message: Message):
    if not message.from_user:
        return
    if not message.text:
        return
    bot = message.bot
    me = await bot.get_me()
    mention = f"@{me.username.lower()}"
    text_lower = message.text.lower()
    if mention not in text_lower:
        return

    query = message.text.replace(f"@{me.username}", "").replace(f"@{me.username.lower()}", "").strip()
    if not query:
        await message.answer("بپرس، جواب بدم! 😊")
        return

    try:
        lang = await db.get_lang(message.from_user.id)
        lang_name = {"ku": "Kurdish Sorani", "fa": "Persian", "en": "English"}.get(lang, "English")
        system = f"You are Kaysan AI assistant in a Telegram group. Reply in {lang_name}. Be concise (1-2 sentences max)."
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300),
            timeout=30,
        )
        await message.answer(reply)
    except Exception as e:
        log.warning("group mention failed: %s", e)
        await message.answer("متأسفم، مشکلی پیش اومد.")


# ─────────────────────────────────────────────
#  ۹. آمار گروه
# ─────────────────────────────────────────────

@router.message(Command("groupstats"))
async def cmd_group_stats(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat = message.chat

    try:
        member_count = await chat.get_member_count()
    except Exception:
        member_count = "?"

    texts = {
        "ku": f"📊 <b>ئاماری گرووپ</b>\n\n📝 ناو: {chat.title}\n👥 ژمارەی ئەندامان: {member_count}\n🆔 ID: <code>{chat.id}</code>",
        "fa": f"📊 <b>آمار گروه</b>\n\n📝 نام: {chat.title}\n👥 تعداد اعضا: {member_count}\n🆔 شناسه: <code>{chat.id}</code>",
        "en": f"📊 <b>Group Stats</b>\n\n📝 Name: {chat.title}\n👥 Members: {member_count}\n🆔 ID: <code>{chat.id}</code>",
    }
    lang = await db.get_lang(message.from_user.id)
    await message.answer(texts.get(lang, texts["en"]), parse_mode=ParseMode.HTML)


# ─────────────────────────────────────────────
#  ۱۰. نظرسنجی هوشمند با AI
# ─────────────────────────────────────────────

@router.message(Command("aipoll"))
async def cmd_ai_poll(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    uid = message.from_user.id
    parts = message.text.split(maxsplit=1)

    topic = parts[1] if len(parts) > 1 else None
    if not topic:
        await message.answer("بکارهێنان: /aipoll عنوان\nمثال: /aipoll بهترین زبان برنامه‌نویسی")
        return

    try:
        system = (
            "Generate a poll with exactly 4 options for this topic. "
            "Reply ONLY in JSON: {\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"]}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Topic: {topic}"},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=200),
            timeout=15,
        )
        import json
        data = json.loads(reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        question = data["question"]
        options = data["options"]

        from aiogram.types import PollOption
        await message.answer_poll(
            question=question,
            options=options,
            is_anonymous=True,
        )
    except Exception as e:
        log.warning("ai poll failed: %s", e)
        await message.answer("❌ نتونستم نظرسنجی بسازم.")


# ─────────────────────────────────────────────
#  ۱۱. کوییز گروهی
# ─────────────────────────────────────────────

_GROUP_QUIZ_CACHE: dict[int, dict] = {}


@router.message(Command("groupquiz"))
async def cmd_group_quiz(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    uid = message.from_user.id
    chat_id = message.chat.id

    try:
        system = (
            "Generate a fun trivia question with 4 options (A, B, C, D). "
            "Reply in JSON: {\"question\": \"...\", \"options\": [\"A) ...\", \"B) ...\", \"C) ...\", \"D) ...\"], \"answer\": \"A\"}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "Give me a trivia question about science, history, or geography."},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300),
            timeout=15,
        )
        import json
        data = json.loads(reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))

        _GROUP_QUIZ_CACHE[chat_id] = {"answer": data["answer"][0].upper(), "question": data["question"]}

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"gquiz:{opt[0]}")]
            for opt in data["options"]
        ])
        await message.answer(f"🧠 <b>{data['question']}</b>", reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("group quiz failed: %s", e)
        await message.answer("❌ نتونستم کوییز بسازم.")


@router.callback_query(F.data.startswith("gquiz:"))
async def cb_group_quiz(call: CallbackQuery):
    if not call.from_user:
        return
    chat_id = call.message.chat.id
    chosen = call.data.split(":")[1]
    cached = _GROUP_QUIZ_CACHE.get(chat_id)

    if not cached:
        await call.answer("کوییز تموم شده!", show_alert=True)
        return

    if chosen == cached["answer"]:
        text = f"✅ <b>{call.from_user.full_name}</b> جواب درست داد!"
    else:
        text = f"❌ <b>{call.from_user.full_name}</b> جواب اشتباه بود!\nجواب: {cached['answer']}"

    del _GROUP_QUIZ_CACHE[chat_id]
    await call.message.edit_text(f"🧠 {cached['question']}\n\n{text}", parse_mode=ParseMode.HTML)
    await call.answer()


# ─────────────────────────────────────────────
#  ۱۲. ترجمه خودکار در گروه
# ─────────────────────────────────────────────

@router.message(Command("gtranslate"))
async def cmd_group_translate(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("بکارهێنان: /gtranslate متن\nترجمه متن به ۳ زبان")
        return

    text = parts[1]
    status = await message.answer("🔄 دارم ترجمه می‌کنم...")

    system = (
        "Translate this text to Kurdish Sorani, Persian, and English. "
        "Format:\n🇸🇴 Kurdish:\n...\n\n🇮🇷 Persian:\n...\n\n🇬🇧 English:\n..."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=600),
            timeout=20,
        )
        await status.edit_text(reply)
    except Exception:
        await status.edit_text("❌ ترجمه ناموفق بود.")


# ─────────────────────────────────────────────
#  ۱۳. تبدیل ویس به متن در گروه
# ─────────────────────────────────────────────

@router.message(F.voice | F.audio)
async def group_voice_transcribe(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    from ..services import voice as voice_svc
    status = await message.answer("🎧 دارم گوش می‌دم...")
    try:
        src = message.voice or message.audio
        buf = await message.bot.download(src)
        data = buf.read()
        text = await voice_svc.transcribe(data, fmt="ogg")
        if text:
            await status.edit_text(f"📝 <b>متن ویس:</b>\n{text}", parse_mode=ParseMode.HTML)
        else:
            await status.edit_text("🎧 نتونستم بفهمم.")
    except Exception:
        await status.edit_text("❌ خطا در تبدیل ویس.")


# ─────────────────────────────────────────────
#  ۱۴. تحلیل عکس در گروه
# ─────────────────────────────────────────────

@router.message(F.photo)
async def group_photo_analyze(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    if not message.caption:
        return

    uid = message.from_user.id
    lang = await db.get_lang(uid)
    lang_name = {"ku": "Kurdish Sorani", "fa": "Persian", "en": "English"}.get(lang, "English")

    import base64
    status = await message.answer("👁️ دارم عکس رو می‌بینم...")
    try:
        photo = message.photo[-1]
        buf = await message.bot.download(photo)
        b64 = base64.b64encode(buf.read()).decode()
        data_url = f"data:image/jpeg;base64,{b64}"

        system = f"You are Kaysan AI. Analyze this image. Reply in {lang_name}. Be concise."
        messages = openrouter.vision_message(system, message.caption, data_url)
        reply, _ = await openrouter.chat(messages, config.VISION_MODELS)
        await status.edit_text(reply[:4000])
    except Exception:
        await status.edit_text("❌ نتونستم عکس رو تحلیل کنم.")


# ─────────────────────────────────────────────
#  ۱۵. تحلیل فایل در گروه
# ─────────────────────────────────────────────

@router.message(F.document)
async def group_file_analyze(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    if not message.caption:
        return

    uid = message.from_user.id
    lang = await db.get_lang(uid)
    lang_name = {"ku": "Kurdish Sorani", "fa": "Persian", "en": "English"}.get(lang, "English")

    status = await message.answer("📄 دارم فایل رو می‌خونم...")
    try:
        doc = message.document
        if doc.file_size and doc.file_size > 10 * 1024 * 1024:
            await status.edit_text("❌ فایل خیلی بزرگه (حداکثر 10MB).")
            return

        filename = doc.file_name or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ("txt", "md", "csv", "json", "py", "js", "html", "css"):
            await status.edit_text("❌ فقط فایل‌های متنی پشتیبانی میشن.")
            return

        buf = await message.bot.download(doc)
        text = buf.read().decode("utf-8", errors="ignore")[:6000]

        system = f"You are Kaysan AI. Analyze this file ({filename}). Reply in {lang_name}. Be concise."
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"File: {filename}\n\n{text}\n\n{message.caption}"},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=1500),
            timeout=30,
        )
        await status.edit_text(reply[:4000])
    except Exception:
        await status.edit_text("❌ خطا در تحلیل فایل.")


# ─────────────────────────────────────────────
#  ۱۶. ساعات سکوت
# ─────────────────────────────────────────────

@router.message(Command("silent"))
async def cmd_silent(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        await message.answer("فقط ادمین‌ها می‌تونن تنظیم کنن.")
        return

    await db.ensure_group(chat_id, message.chat.title or "")
    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("بکارهێنان: /silent 23 7\n(ساعت شروع — ساعت پایان)\n/silent off برای غیرفعال")
        return

    start_hour = int(parts[1])
    end_hour = int(parts[2])
    await db.update_group(chat_id, silent_start=start_hour, silent_end=end_hour)
    await message.answer(f"🔇 ساعات سکوت: {start_hour}:00 تا {end_hour}:00")


@router.message(Command("silent_off"))
async def cmd_silent_off(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        return

    await db.update_group(chat_id, silent_start=-1, silent_end=-1)
    await message.answer("🔊 ساعات سکوت غیرفعال شد.")


# ─────────────────────────────────────────────
#  ۱۷. قوانین گروه
# ─────────────────────────────────────────────

@router.message(Command("setrules"))
async def cmd_set_rules(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        await message.answer("فقط ادمین‌ها می‌تونن قوانین تنظیم کنن.")
        return

    await db.ensure_group(chat_id, message.chat.title or "")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("بکارهێنان: /setrules قانون ۱\nقانون ۲\nقانون ۳")
        return

    await db.update_group(chat_id, rules_text=parts[1])
    await message.answer("✅ قوانین گروه ذخیره شد.\nبرای نمایش: /rules")


@router.message(Command("rules"))
async def cmd_rules(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    chat_id = message.chat.id
    settings = await db.get_group_settings(chat_id)
    rules = settings.get("rules_text", "")

    if rules:
        await message.answer(f"📜 <b>قوانین گروه:</b>\n\n{rules}", parse_mode=ParseMode.HTML)
    else:
        await message.answer("📜 قوانینی تنظیم نشده. ادمین‌ها می‌تونن با /setrules قوانین رو اضافه کنن.")


# ─────────────────────────────────────────────
#  ۱۸. گزارش پیام
# ─────────────────────────────────────────────

@router.message(Command("report"))
async def cmd_report(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat = message.chat
    uid = message.from_user.id

    if not message.reply_to_message:
        await message.answer("روی پیام مورد نظر ریپلای کن و /report بزن.")
        return

    reported_msg = message.reply_to_message
    try:
        admins = await chat.get_administrators()
        for admin in admins:
            if admin.user.is_bot:
                continue
            try:
                await message.bot.send_message(
                    admin.user.id,
                    f"🚨 <b>گزارش پیام</b>\n\n"
                    f"گروه: {chat.title}\n"
                    f"گزارش‌دهنده: {message.from_user.full_name} (<code>{uid}</code>)\n"
                    f"فرستنده: {reported_msg.from_user.full_name} (<code>{reported_msg.from_user.id}</code>)\n"
                    f"متن: {reported_msg.text or '(غیر متنی)'}\n"
                    f"لینک: https://t.me/{chat.username or 'c'}/{reported_msg.message_id}",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass
        await message.answer("✅ گزارش به ادمین‌ها ارسال شد.")
    except Exception:
        await message.answer("❌ نتونستم گزارش بدم.")


# ─────────────────────────────────────────────
#  ۱۹. حالت سکوت ربات
# ─────────────────────────────────────────────

@router.message(Command("botmute"))
async def cmd_bot_mute(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        return

    await db.update_group(chat_id, silent_start=0, silent_end=24)
    await message.answer("🔇 ربات در حالت سکوت قرار گرفت. برای فعال‌سازی: /botunmute")


@router.message(Command("botunmute"))
async def cmd_bot_unmute(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        return

    await db.update_group(chat_id, silent_start=-1, silent_end=-1)
    await message.answer("🔊 ربات فعال شد!")


# ─────────────────────────────────────────────
#  ۲۰. ارسال پیام همه اعضا
# ─────────────────────────────────────────────

@router.message(Command("tagall"))
async def cmd_tag_all(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.from_user:
        return
    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin(message.bot, chat_id, uid):
        await message.answer("فقط ادمین‌ها می‌تونن همه رو تگ کنن.")
        return

    try:
        members = []
        async for member in message.chat.get_members():
            if not member.user.is_bot:
                members.append(member.user)

        if not members:
            await message.answer("عضوی پیدا نشد.")
            return

        parts = message.text.split(maxsplit=1)
        prefix = parts[1] if len(parts) > 1 else "پیام مهم"

        tags = " ".join(f"<a href='tg://user?id={m.id}'>.</a>" for m in members)
        await message.answer(
            f"📢 <b>{prefix}</b>\n\n{tags}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.warning("tagall failed: %s", e)
        await message.answer("❌ نتونستم همه رو تگ کنم.")


# ─────────────────────────────────────────────
#  Helper: بررسی ادمین بودن
# ─────────────────────────────────────────────

async def _is_admin(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


# ─────────────────────────────────────────────
#  دستورات راهنما برای گروه
# ─────────────────────────────────────────────

@router.message(Command("grouphelp"))
async def cmd_group_help(message: Message):
    text = (
        "🤖 <b>Kaysan — راهنمای گروه</b>\n\n"
        "<b>دستورات ادمین:</b>\n"
        "/slowmode [ثانیه] — حالت آهسته\n"
        "/silent [شروع] [پایان] — ساعات سکوت\n"
        "/silent_off — غیرفعال کردن سکوت\n"
        "/setrules — تنظیم قوانین\n"
        "/rules — نمایش قوانین\n"
        "/tagall [پیام] — تگ همه اعضا\n"
        "/botmute — سکوت ربات\n"
        "/botunmute — فعال‌سازی ربات\n\n"
        "<b>دستورات عمومی:</b>\n"
        "/groupstats — آمار گروه\n"
        "/aipoll [عنوان] — نظرسنجی هوشمند\n"
        "/groupquiz — کوییز گروهی\n"
        "/gtranslate [متن] — ترجمه ۳ زبانه\n"
        "/report — گزارش پیام\n"
        "/grouphelp — این راهنما\n\n"
        "<b>قابلیت‌های خودکار:</b>\n"
        "✅ خوش‌آمدگویی اعضا\n"
        "✅ وداع اعضا\n"
        "✅ فیلتر اسپم\n"
        "✅ فیلتر کلمات نامناسب\n"
        "✅ ضد Flood\n"
        "✅ پاسخ به منشن ربات\n"
        "✅ تحلیل عکس با کپشن\n"
        "✅ تحلیل فایل با کپشن\n"
        "✅ تبدیل ویس به متن\n"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)
