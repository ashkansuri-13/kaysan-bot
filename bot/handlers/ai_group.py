"""قابلیت‌های هوشمند گروهی: یادگیری، کارآگاه پیام، ترجمه لحظه‌ای، تقویم هوشمند، وکیل قوانین."""
import asyncio
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter
from ..texts import t
from ..ttl_dict import TTLDict

router = Router()
log = logging.getLogger("kaysan.ai_group")


# ═══════════════════════════════════════════════
#  ۱. خودآموزی گروهی (Group Learning)
# ═══════════════════════════════════════════════

_group_messages: dict[int, list[dict]] = defaultdict(list)
_GROUP_MSG_MAX = 500


@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def collect_group_message(message: Message):
    chat_id = message.chat.id
    _group_messages[chat_id].append({
        "user_id": message.from_user.id,
        "name": message.from_user.full_name,
        "text": message.text[:500] if message.text else "",
        "time": message.date.isoformat() if message.date else datetime.now(timezone.utc).isoformat(),
    })
    if len(_group_messages[chat_id]) > _GROUP_MSG_MAX:
        _group_messages[chat_id] = _group_messages[chat_id][-_GROUP_MSG_MAX:]


@router.message(Command("grouplearn"))
async def cmd_group_learn(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    chat_id = message.chat.id
    msgs = _group_messages.get(chat_id, [])

    if len(msgs) < 10:
        await message.answer("📊 هنوز پیام کافی نیست. حداقل ۱۰ پیام لازمه.")
        return

    status = await message.answer("🧠 در حال تحلیل مکالمات گروه...")

    topic_count = defaultdict(int)
    user_count = defaultdict(int)
    hourly = defaultdict(int)
    for m in msgs:
        user_count[m["name"]] += 1
        words = m["text"].split()
        for w in words:
            if len(w) > 3:
                topic_count[w.lower()] += 1
        try:
            hour = datetime.fromisoformat(m["time"]).hour
            hourly[hour] += 1
        except Exception:
            pass

    top_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:10]
    top_users = sorted(user_count.items(), key=lambda x: x[1], reverse=True)[:5]
    peak_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)[:3]

    lines = ["📊 <b>گزارش هوشمند گروه</b>\n"]

    lines.append("👥 <b>فعال‌ترین اعضا:</b>")
    for name, count in top_users:
        lines.append(f"  • {name}: {count} پیام")

    lines.append("\n🔥 <b>موضوعات داغ:</b>")
    for word, count in top_topics:
        lines.append(f"  • {word}: {count} بار")

    lines.append(f"\n⏰ <b>ساعات فعال:</b>")
    for hour, count in peak_hours:
        lines.append(f"  • ساعت {hour}:00 — {count} پیام")

    lines.append(f"\n📝 <b>کل پیام‌ها:</b> {len(msgs)}")

    await status.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════
#  ۲. کارآگاه پیام (Message Detective)
# ═══════════════════════════════════════════════

@router.message(Command("detect"))
async def cmd_detect(message: Message):
    if not message.chat or message.chat.type == "private":
        return
    if not message.reply_to_message:
        await message.answer("روی یک پیام ریپلای کن و /detect بزن.")
        return

    replied = message.reply_to_message
    chat_id = message.chat.id
    msgs = _group_messages.get(chat_id, [])

    replied_text = replied.text or ""
    replied_user = replied.from_user.full_name if replied.from_user else "ناشناخته"

    context_msgs = []
    for m in reversed(msgs):
        if m["text"] == replied_text and m["name"] == replied_user:
            continue
        context_msgs.append(m)
        if len(context_msgs) >= 5:
            break

    if not context_msgs:
        await message.answer("🔍 اطلاعات بیشتری درباره این پیام پیدا نکردم.")
        return

    context_text = "\n".join(
        f"[{m['name']}] {m['text'][:150]}" for m in reversed(context_msgs)
    )

    system = (
        "You are a message detective in a Telegram group. "
        "Analyze the context and explain what the replied message is about. "
        "Reply in the user's language. Be concise (2-3 sentences max)."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Replied message: [{replied_user}] {replied_text[:300]}\n\nContext:\n{context_text}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300),
            timeout=20,
        )
        await message.answer(f"🔍 <b>تحلیل پیام:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("detect failed: %s", e)
        await message.answer("❌ نتونستم تحلیل کنم.")


# ═══════════════════════════════════════════════
#  ۳. ترجمه لحظه‌ای گروهی (Live Group Translation)
# ═══════════════════════════════════════════════

_live_translate_enabled = TTLDict(ttl_seconds=3600, max_size=1000)
_live_translate_langs: dict[int, list[str]] = defaultdict(lambda: ["fa", "en"])


@router.message(Command("livetranslate"))
async def cmd_live_translate(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    uid = message.from_user.id

    if not await _is_admin_group(message.bot, chat_id, uid):
        await message.answer("فقط ادمین‌ها می‌تونن ترجمه لحظه‌ای رو فعال کنن.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        current = "فعال ✅" if _live_translate_enabled.get(chat_id) else "غیرفعال ❌"
        await message.answer(
            f"🔄 <b>ترجمه لحظه‌ای:</b> {current}\n\n"
            "بکارهێنان:\n"
            "/livetranslate on — فعال‌سازی\n"
            "/livetranslate off — غیرفعال\n"
            "/livetranslate langs fa,en — زبان‌ها",
            parse_mode=ParseMode.HTML,
        )
        return

    action = parts[1].lower()
    if action == "on":
        _live_translate_enabled[chat_id] = True
        await message.answer("✅ ترجمه لحظه‌ای فعال شد!")
    elif action == "off":
        _live_translate_enabled[chat_id] = False
        await message.answer("❌ ترجمه لحظه‌ای غیرفعال شد.")
    elif action == "langs" and len(parts) >= 3:
        langs = [l.strip() for l in parts[2].split(",") if l.strip() in ("ku", "fa", "en")]
        if langs:
            _live_translate_langs[chat_id] = langs
            await message.answer(f"✅ زبان‌ها: {', '.join(langs)}")
        else:
            await message.answer("❌ زبان نامعتبر. فقط ku, fa, en")


@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def auto_translate_message(message: Message):
    if not message.text:
        return
    chat_id = message.chat.id
    if not _live_translate_enabled.get(chat_id):
        return

    text = message.text
    if len(text) < 10 or text.startswith("/"):
        return

    target_langs = _live_translate_langs.get(chat_id, ["fa", "en"])

    lang_names = {"ku": "Kurdish Sorani", "fa": "Persian", "en": "English"}
    targets = [lang_names.get(l, "English") for l in target_langs]

    system = (
        f"Translate the following text to: {', '.join(targets)}. "
        "Format: one translation per language, prefixed with language name and flag. "
        "Keep translations short and natural. If text is already in a target language, skip it."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text[:500]},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, [config.CHAT_MODELS[0]], max_tokens=400),
            timeout=15,
        )
        if reply and len(reply) > 5:
            flags = {"ku": "🇸🇴", "fa": "🇮🇷", "en": "🇬🇧"}
            header = " ".join(f"{flags.get(l, '🌐')}" for l in target_langs)
            await message.answer(
                f"{header} <b>ترجمه خودکار:</b>\n{reply[:1500]}",
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.message_id,
            )
    except Exception:
        pass


# ═══════════════════════════════════════════════
#  ۴. تقویم هوشمند گروهی
# ═══════════════════════════════════════════════

_smart_events: dict[int, list[dict]] = defaultdict(list)


@router.message(Command("addevent"))
async def cmd_add_event(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /addevent 2025-01-15 تولد علی\n"
            "یا: /addevent فردا جلسه تیم"
        )
        return

    chat_id = message.chat.id
    uid = message.from_user.id
    text = parts[1]

    date_match = re.match(r"(\d{4}-\d{2}-\d{2})\s+(.+)", text)
    if date_match:
        event_date = date_match.group(1)
        event_text = date_match.group(2)
    else:
        event_date = "auto"
        event_text = text

    _smart_events[chat_id].append({
        "date": event_date,
        "text": event_text,
        "added_by": message.from_user.full_name,
        "added_at": datetime.now(timezone.utc).isoformat(),
    })

    await message.answer(f"✅ رویداد ذخیره شد: {event_text}")


@router.message(Command("events"))
async def cmd_events(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    events = _smart_events.get(chat_id, [])

    if not events:
        await message.answer("📅 هنوز رویدادی ثبت نشده.")
        return

    lines = ["📅 <b>رویدادهای گروه:</b>\n"]
    for i, e in enumerate(events[-10:], 1):
        lines.append(f"{i}. 📌 {e['text']}")
        lines.append(f"   📆 {e['date']} — اضافه شده توسط {e['added_by']}")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def rule_enforcement(message: Message):
    if not message.text or message.text.startswith("/"):
        return

    chat_id = message.chat.id
    uid = message.from_user.id
    settings = await db.get_group_settings(chat_id)
    rules = settings.get("rules_text", "")

    if not rules:
        return

    if await _is_admin_group(message.bot, chat_id, uid):
        return

    text = message.text.lower()
    rule_keywords = {
        "اسپم": ["link", "t.me", "bit.ly", "free", "win", "click"],
        "تبلیغ": ["follow", "subscribe", "join", "عضویت", "لایک"],
    }

    for rule_name, keywords in rule_keywords.items():
        for kw in keywords:
            if kw in text:
                try:
                    await message.delete()
                    await message.answer(
                        f"⚠️ <b>{message.from_user.full_name}</b>، قوانین گروه رعایت نشد!\n\n"
                        f"📋 قانون مرتبط: <i>ممنوعیت {rule_name}</i>\n"
                        f"📜 قوانین کامل: /rules",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass
                return


# ═══════════════════════════════════════════════
#  Helper
# ═══════════════════════════════════════════════

async def _is_admin_group(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False
