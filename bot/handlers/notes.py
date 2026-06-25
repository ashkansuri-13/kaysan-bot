"""یادداشت‌های شخصی — /note /notes /delnote."""
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from .. import database as db
from ..texts import t

router = Router()
log = logging.getLogger("kaysan.notes")


@router.message(Command("note"))
async def cmd_note(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t(lang, "note_usage"))
        return

    note_id = await db.add_note(uid, parts[1])
    await message.answer(t(lang, "note_saved", id=note_id))


@router.message(Command("notes"))
async def cmd_notes(message: Message):
    uid = message.from_user.id
    lang = await db.get_lang(uid)

    notes = await db.get_notes(uid)
    if not notes:
        await message.answer(t(lang, "notes_empty"))
        return

    lines = [t(lang, "notes_header")]
    for n in notes:
        content = n["content"][:80] + ("..." if len(n["content"]) > 80 else "")
        lines.append(f"📌 <code>{n['id']}</code>: {content}")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


@router.message(Command("delnote"))
async def cmd_delnote(message: Message):
    uid = message.from_user.id
    lang = await db.get_lang(uid)

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(t(lang, "delnote_usage"))
        return

    note_id = int(parts[1])
    deleted = await db.delete_note(uid, note_id)
    if deleted:
        await message.answer(t(lang, "note_deleted", id=note_id))
    else:
        await message.answer(t(lang, "note_not_found", id=note_id))
