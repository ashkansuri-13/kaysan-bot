"""هندلر چت: هر پیام متنی → هسته‌ی پردازش."""
from aiogram import F, Router
from aiogram.types import Message

from .. import database as db, router as rtr
from . import core

router = Router()


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    if not await core.enforce_channel(message):
        return
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return
    await core.process_text(message, message.text, lang)
