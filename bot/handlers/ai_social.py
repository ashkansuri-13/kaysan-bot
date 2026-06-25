"""قابلیت‌های اجتماعی و مدیریتی: مذاکره‌کننده، پیش‌بینی روند، تصمیم‌گیری، حسابدار، معلم."""
import asyncio
import json
import logging
from collections import defaultdict

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter
from ..texts import t

router = Router()
log = logging.getLogger("kaysan.ai_social")


# ═══════════════════════════════════════════════
#  ۶. مذاکره‌کننده هوشمند
# ═══════════════════════════════════════════════

@router.message(Command("mediator"))
async def cmd_mediator(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    if not message.reply_to_message:
        await message.answer(
            "🤝 <b>مذاکره‌کننده هوشمند</b>\n\n"
            "روی پیامی که می‌خوای درباره‌ش نظر بده ریپلای کن.",
            parse_mode=ParseMode.HTML,
        )
        return

    replied = message.reply_to_message
    original_text = replied.text or "(پیام غیرمتنی)"
    original_user = replied.from_user.full_name if replied.from_user else "ناشناخته"

    context_parts = [f"[{original_user}]: {original_text[:300]}"]
    if replied.reply_to_message:
        rt = replied.reply_to_message
        context_parts.insert(0, f"[{rt.from_user.full_name if rt.from_user else '?'}]: {(rt.text or '')[:300]}")

    context = "\n".join(context_parts)

    system = (
        "You are a wise mediator in a Telegram group discussion. "
        "Analyze the viewpoints and provide a balanced perspective. "
        "Be neutral, fair, and suggest compromise solutions. "
        "Reply in the user's language. Be concise (3-4 sentences max)."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Discussion context:\n{context}\n\nWhat's your mediation?"},
    ]

    status = await message.answer("🤝 در حال تحلیل...")
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=400),
            timeout=20,
        )
        await status.edit_text(f"🤝 <b>نظر مذاکره‌کننده:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("mediator failed: %s", e)
        await status.edit_text("❌ نتونستم تحلیل کنم.")


# ═══════════════════════════════════════════════
#  ۷. پیش‌بینی روند (Trend Predictor)
# ═══════════════════════════════════════════════

@router.message(Command("trend"))
async def cmd_trend(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    from .ai_group import _group_messages
    msgs = _group_messages.get(chat_id, [])

    if len(msgs) < 20:
        await message.answer("📊 حداقل ۲۰ پیام لازمه برای تحلیل روند.")
        return

    status = await message.answer("📈 در حال تحلیل روندها...")

    recent = msgs[-50:]
    older = msgs[-100:-50] if len(msgs) > 50 else []

    recent_words = defaultdict(int)
    older_words = defaultdict(int)

    for m in recent:
        for w in m["text"].lower().split():
            if len(w) > 3:
                recent_words[w] += 1

    for m in older:
        for w in m["text"].lower().split():
            if len(w) > 3:
                older_words[w] += 1

    rising = []
    for word, count in recent_words.items():
        old_count = older_words.get(word, 0)
        if count > old_count + 2:
            rising.append((word, count - old_count))

    rising.sort(key=lambda x: x[1], reverse=True)

    if not rising:
        await status.edit_text("📈 روند خاصی مشاهده نمیشه.")
        return

    system = (
        "You are a trend analyst for a Telegram group. "
        "Based on rising topics, predict what the group will discuss next. "
        "Reply in the user's language. Be concise and insightful."
    )
    topics = ", ".join(f"{w}({c})" for w, c in rising[:8])
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Rising topics in the group: {topics}\n\nWhat will they discuss next?"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300),
            timeout=15,
        )
        lines = ["📈 <b>روندهای گروه:</b>\n"]
        for word, count in rising[:5]:
            lines.append(f"  🔺 {word}: +{count}")
        lines.append(f"\n🔮 <b>پیش‌بینی:</b>\n{reply}")
        await status.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("trend failed: %s", e)
        await status.edit_text("❌ خطا در تحلیل روند.")


# ═══════════════════════════════════════════════
#  ۸. دستیار تصمیم‌گیری گروهی
# ═══════════════════════════════════════════════

@router.message(Command("decide"))
async def cmd_decide(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /decide کجا بریم شام؟\n"
            "مثال: /decide چه پروژه‌ای شروع کنیم؟"
        )
        return

    question = parts[1]
    status = await message.answer("🤔 در حال تحلیل گزینه‌ها...")

    system = (
        "You are a group decision assistant. Analyze the decision question. "
        "Reply in the user's language with:\n"
        "1. A brief analysis (2-3 sentences)\n"
        "2. 3-4 options with pros/cons\n"
        "3. Your recommendation (1 sentence)\n"
        "Be practical and concise."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Decision needed: {question}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=500),
            timeout=20,
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👍 موافقم", callback_data="decide:agree")],
            [InlineKeyboardButton(text="👎 نظر دیگه", callback_data="decide:disagree")],
            [InlineKeyboardButton(text="📊 نظرسنجی بزن", callback_data="decide:poll")],
        ])

        await status.edit_text(
            f"🤔 <b>تصمیم‌گیری:</b> {question}\n\n{reply}",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except Exception as e:
        log.warning("decide failed: %s", e)
        await status.edit_text("❌ خطا در تحلیل.")


@router.callback_query(F.data.startswith("decide:"))
async def cb_decide(call: CallbackQuery):
    action = call.data.split(":")[1]
    if action == "agree":
        await call.answer("✅ ممنون از نظرت!", show_alert=True)
    elif action == "disagree":
        await call.answer("💡 نظرت چیه؟ بنویس!", show_alert=True)
    elif action == "poll":
        await call.answer()
        await call.message.answer("📊 برای نظرسنجی از /aipoll استفاده کن.")


# ═══════════════════════════════════════════════
#  ۹. حسابدار گروهی
# ═══════════════════════════════════════════════

_group_expenses: dict[int, list[dict]] = defaultdict(list)


@router.message(Command("split"))
async def cmd_split(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        exps = _group_expenses.get(chat_id, [])
        if not exps:
            await message.answer(
                "💰 <b>حسابدار گروهی</b>\n\n"
                "بکارهێنان:\n"
                "/split 50000 ناهار علی\n"
                "/split list — لیست هزینه‌ها\n"
                "/split total — جمع کل\n"
                "/split settle — تسویه حساب",
                parse_mode=ParseMode.HTML,
            )
            return

        action = parts[0]
        if action == "list":
            lines = ["💰 <b>هزینه‌های گروه:</b>\n"]
            total = 0
            for e in exps[-10:]:
                lines.append(f"  • {e['name']}: {e['amount']:,.0f} توسط {e['payer']}")
                total += e["amount"]
            lines.append(f"\nجمع: {total:,.0f}")
            await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
            return

        if action == "total":
            total = sum(e["amount"] for e in exps)
            await message.answer(f"💰 جمع کل: {total:,.0f}")
            return

        if action == "settle":
            if not exps:
                await message.answer("💰 هزینه‌ای ثبت نشده.")
                return
            totals = defaultdict(float)
            for e in exps:
                totals[e["payer"]] += e["amount"]
            total_all = sum(totals.values())
            per_person = total_all / len(totals) if totals else 0

            lines = ["💰 <b>تسویه حساب:</b>\n"]
            for name, amount in totals.items():
                diff = amount - per_person
                if diff > 0:
                    lines.append(f"  📈 {name} باید بگیره: {diff:,.0f}")
                elif diff < 0:
                    lines.append(f"  📉 {name} باید بده: {abs(diff):,.0f}")
                else:
                    lines.append(f"  ✅ {name}: تسویه")
            await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
            return

    text = parts[1]
    sp = text.split()
    if len(sp) < 2:
        await message.answer("فرمت: /split <مقدار> <توضیح>")
        return

    try:
        amount = int(sp[0])
        name = " ".join(sp[1:])
    except ValueError:
        await message.answer("❌ مقدار باید عدد باشه.")
        return

    payer = message.from_user.full_name
    _group_expenses[chat_id].append({
        "amount": amount,
        "name": name,
        "payer": payer,
        "time": message.date.isoformat() if message.date else "",
    })

    total = sum(e["amount"] for e in _group_expenses[chat_id])
    await message.answer(f"✅ {name}: {amount:,.0f} توسط {payer}\nجمع گروه: {total:,.0f}")


# ═══════════════════════════════════════════════
#  ۱۰. معلم گروهی
# ═══════════════════════════════════════════════

@router.message(Command("teach"))
async def cmd_teach(message: Message):
    if not message.chat or message.chat.type == "private":
        return

    if not message.reply_to_message:
        await message.answer(
            "🎓 <b>معلم گروهی</b>\n\n"
            "روی پیامی که می‌خوای توضیح داده بشه ریپلای کن.",
            parse_mode=ParseMode.HTML,
        )
        return

    replied = message.reply_to_message
    text = replied.text or "(پیام غیرمتنی)"

    status = await message.answer("🎓 در حال توضیح...")

    system = (
        "You are a knowledgeable teacher in a Telegram group. "
        "Explain the following message in a clear, educational way. "
        "Reply in the user's language. "
        "Include: what it means, why it matters, and an example if relevant. "
        "Be concise but thorough (3-5 sentences)."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Explain this:\n{text[:500]}"},
    ]

    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=500),
            timeout=20,
        )
        await status.edit_text(
            f"🎓 <b>توضیح:</b>\n\n{reply}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.warning("teach failed: %s", e)
        await status.edit_text("❌ نتونستم توضیح بدم.")
