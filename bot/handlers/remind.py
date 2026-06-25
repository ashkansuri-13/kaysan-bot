"""یادآوری — /remind."""
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from .. import config, database as db
from ..texts import t

router = Router()
log = logging.getLogger("kaysan.remind")


def _parse_time(text: str) -> tuple[timedelta | None, str]:
    """زمان و متن یادآوری را پارس می‌کند."""
    m = re.match(
        r"(\d+)\s*(s|sec|second|m|min|minute|h|hr|hour|d|day|w|week)"
        r"\s+(.+)",
        text.strip(),
        re.I,
    )
    if not m:
        return None, ""
    amount = int(m.group(1))
    unit = m.group(2).lower()
    msg = m.group(3)

    multipliers = {
        "s": 1, "sec": 1, "second": 1,
        "m": 60, "min": 60, "minute": 60,
        "h": 3600, "hr": 3600, "hour": 3600,
        "d": 86400, "day": 86400,
        "w": 604800, "week": 604800,
    }
    seconds = amount * multipliers.get(unit, 60)
    return timedelta(seconds=seconds), msg


async def _reminder_loop(bot):
    """چرخه بررسی یادآوری‌ها."""
    await db.mark_old_reminders_sent()
    while True:
        try:
            due = await db.get_due_reminders()
            for r in due:
                try:
                    await bot.send_message(
                        r["user_id"],
                        f"⏰ <b>یادآوری:</b>\n{r['text']}",
                        parse_mode="HTML",
                    )
                    await db.mark_reminder_sent(r["id"])
                except Exception as e:
                    log.warning("reminder send failed: %s", e)
                    await db.mark_reminder_sent(r["id"])
        except Exception as e:
            log.warning("reminder loop error: %s", e)
        await asyncio.sleep(30)


@router.message(Command("remind"))
async def cmd_remind(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t(lang, "remind_usage"))
        return

    delta, text = _parse_time(parts[1])
    if delta is None:
        await message.answer(t(lang, "remind_usage"))
        return

    remind_at = (datetime.now(timezone.utc) + delta).isoformat()
    await db.add_reminder(uid, remind_at, text)

    units = {
        (86400, "day"): ("روز", "day"),
        (3600, "hour"): ("ساعت", "hour"),
        (60, "minute"): ("دقیقه", "minute"),
    }
    total_seconds = int(delta.total_seconds())
    display = ""
    for sec_val, unit_en in units.keys():
        if total_seconds >= sec_val:
            count = total_seconds // sec_val
            display = f"{count} {units[(sec_val, unit_en)][0]}"
            break
    if not display:
        display = f"{total_seconds} ثانیه"

    confirm = {
        "ku": f"✅ یادآوری لە {display}دا دامەزرێت: {text}",
        "fa": f"✅ یادآوری بعد از {display}: {text}",
        "en": f"✅ Reminder set for {display}: {text}",
    }
    await message.answer(confirm.get(lang, confirm["en"]))
