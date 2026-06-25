"""دستورات سازنده: /grant /revoke /stats /testmodels /cost."""
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from .. import config, database as db, openrouter
from ..texts import t

router = Router()


def _is_owner(message: Message) -> bool:
    return message.from_user.id == config.OWNER_ID


@router.message(Command("grant"))
async def cmd_grant(message: Message):
    lang = await db.get_lang(message.from_user.id)
    if not _is_owner(message):
        await message.answer(t(lang, "owner_only"))
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("Usage: /grant <user_id>")
        return
    uid = int(parts[1])
    await db.ensure_user(uid)
    await db.set_subscribed(uid, True)
    await message.answer(f"✅ granted: {uid}")
    try:
        ulang = await db.get_lang(uid)
        await message.bot.send_message(uid, t(ulang, "granted"))
    except Exception:
        pass


@router.message(Command("revoke"))
async def cmd_revoke(message: Message):
    lang = await db.get_lang(message.from_user.id)
    if not _is_owner(message):
        await message.answer(t(lang, "owner_only"))
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("Usage: /revoke <user_id>")
        return
    uid = int(parts[1])
    await db.set_subscribed(uid, False)
    await message.answer(f"✅ revoked: {uid}")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    lang = await db.get_lang(message.from_user.id)
    if not _is_owner(message):
        await message.answer(t(lang, "owner_only"))
        return
    users, msgs = await db.stats()
    await message.answer(t(lang, "stats", users=users, msgs=msgs))


@router.message(Command("testmodels"))
async def cmd_testmodels(message: Message):
    if not _is_owner(message):
        await message.answer("فقط سازنده.")
        return
    status = await message.answer("🔍 در حال تست مدل‌ها...")
    results = []
    categories = {
        "ROUTER": config.ROUTER_MODELS,
        "CHAT": config.CHAT_MODELS,
        "CODE": config.CODE_MODELS,
        "REASON": config.REASON_MODELS,
        "VISION": config.VISION_MODELS,
        "AUDIO": config.AUDIO_MODELS,
    }
    test_msg = [{"role": "user", "content": "Say hi in one word."}]
    for cat, models in categories.items():
        for model in models:
            try:
                out, _ = await openrouter._call(model, test_msg, max_tokens=10)
                results.append(f"✅ {cat}: {model}")
            except Exception as e:
                results.append(f"❌ {cat}: {model} → {str(e)[:60]}")
    await status.edit_text("<b>نتیجه تست مدل‌ها:</b>\n\n" + "\n".join(results),
                           parse_mode=ParseMode.HTML)


@router.message(Command("searchchannels"))
async def cmd_searchchannels(message: Message):
    if not _is_owner(message):
        await message.answer("فقط سازنده.")
        return
    channels = config.SEARCH_CHANNELS
    if not channels:
        await message.answer(
            "<b>📱 کانال‌های جستجو:</b>\n\n"
            "هیچ کانالی تنظیم نشده.\n"
            "برای اضافه کردن، این خط رو به .env اضافه کن:\n"
            "<code>SEARCH_CHANNELS=channel1,channel2,channel3</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    lines = ["<b>📱 کانال‌های جستجوی فعال:</b>\n"]
    for i, ch in enumerate(channels, 1):
        lines.append(f"{i}. @{ch}")
    lines.append(f"\n总计: {len(channels)} کانال")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("testsearch"))
async def cmd_testsearch(message: Message):
    if not _is_owner(message):
        await message.answer("فقط سازنده.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /testsearch query")
        return
    status = await message.answer("🔍 در حال تست جستجو...")
    from ..handlers.search import web_search, telegram_search
    web = await web_search(parts[1], max_results=2)
    tg = await telegram_search(message.bot, parts[1], config.SEARCH_CHANNELS, max_results=2)
    lines = []
    if tg:
        lines.append("<b>📱 تلگرام:</b>")
        for r in tg[:2]:
            lines.append(f"  {r['source']} — {r['text'][:100]}")
    if web:
        lines.append("\n<b>🌐 وب:</b>")
        for r in web[:2]:
            cred = "⭐" * (r.get('credibility', 5) // 2)
            lines.append(f"  {cred} {r['title'][:40]}")
    if not lines:
        lines.append("❌ نتیجه‌ای پیدا نشد.")
    await status.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("popular"))
async def cmd_popular(message: Message):
    if not _is_owner(message):
        await message.answer("فقط سازنده.")
        return
    from ..handlers.search import cmd_popular_queries
    queries = await cmd_popular_queries()
    if not queries:
        await message.answer("❌ هنوز سؤالی ثبت نشده.")
        return
    lines = ["<b>📊 سؤالات پرتکرار:</b>\n"]
    for i, q in enumerate(queries, 1):
        lines.append(f"{i}. {q['query']} ({q['count']} بار)")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("searchstats"))
async def cmd_searchstats(message: Message):
    if not _is_owner(message):
        await message.answer("فقط سازنده.")
        return
    from ..handlers.search import cmd_search_stats
    stats = await cmd_search_stats()
    lines = [
        "<b>📊 آمار سرچ (۷ روز اخیر):</b>\n",
        f"🔍 کل سرچ‌ها: {stats['total']}",
        f"⏱️ میانگین زمان: {stats['avg_duration']}ms",
        f"📋 میانگین نتایج: {stats['avg_results']}",
    ]
    if stats['popular']:
        lines.append("\n<b>🔥 پرتکرارها:</b>")
        for q in stats['popular'][:5]:
            lines.append(f"  • {q['query']} ({q['count']})")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("alert"))
async def cmd_alert(message: Message):
    uid = message.from_user.id
    lang = await db.get_lang(uid)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Usage: /alert دلار بالای 60000\n"
            "یا: /alert سکه زیر 30000000",
        )
        return
    text = parts[1]
    import re
    m = re.match(r"(\S+)\s+(بالای|زیر|بیشتر|کمتر|above|below)\s+([\d,]+)", text)
    if not m:
        await message.answer("فرمت اشتباه. مثال: /alert دلار بالای 60000")
        return
    item = m.group(1)
    condition = "above" if m.group(2) in ("بالای", "بیشتر", "above") else "below"
    price = float(m.group(3).replace(",", ""))
    await db.add_price_alert(uid, item, condition, price)
    cond_fa = "بالای" if condition == "above" else "زیر"
    await message.answer(f"✅ هشدار تنظیم شد:\nوقتی قیمت {item} از {cond_fa} {price:,.0f} رد شد، بهت خبر میدم.")


@router.message(Command("cost"))
async def cmd_cost(message: Message):
    if not _is_owner(message):
        await message.answer("فقط سازنده.")
        return

    parts = message.text.split()
    if len(parts) >= 2 and parts[1].lstrip("-").isdigit():
        uid = int(parts[1])
        row = await db.user_cost(uid)
        if not row:
            await message.answer(f"کاربر {uid} یافت نشد.")
            return
        name, msgs, pt, ct, cost = row
        await message.answer(
            f"<b>هزینه کاربر {uid}</b>\n"
            f"نام: {name or '—'}\n"
            f"پیام: {msgs}\n"
            f"توکن ورودی: {pt:,}\n"
            f"توکن خروجی: {ct:,}\n"
            f"هزینه: ${cost:.6f}",
            parse_mode=ParseMode.HTML,
        )
        return

    users, msgs, pt, ct, cost = await db.cost_stats()
    top = await db.top_users(5)
    errors = await db.error_stats()

    lines = [
        f"<b>📊 آمار کل ربات</b>",
        f"",
        f"کاربران: {users}",
        f"پیام‌ها: {msgs}",
        f"توکن ورودی: {pt:,}",
        f"توکن خروجی: {ct:,}",
        f"هزینه کل: ${cost:.6f}",
    ]

    if top:
        lines.append("")
        lines.append("<b>🔝 ۵ کاربر پرمصرف:</b>")
        for i, (uid, name, msgs, ucost) in enumerate(top, 1):
            label = f"@{name}" if name and not name.startswith(("Id:", "User ")) else str(uid)
            lines.append(f"  {i}. {label} — {msgs} msgs — ${ucost:.6f}")

    if errors:
        lines.append("")
        lines.append("<b>⚠️ خطاهای اخیر:</b>")
        for e in errors[:5]:
            lines.append(f"  • {e['type']}: {e['count']} بار")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
