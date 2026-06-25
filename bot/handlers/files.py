"""آپلود و تحلیل فایل — PDF, DOCX, TXT."""
import io
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message

from .. import config, database as db, openrouter
from ..texts import SYSTEM_PROMPTS, t
from . import core

router = Router()
log = logging.getLogger("kaysan.files")

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _extract_text_from_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = [p.extract_text() or "" for p in reader.pages[:10]]
        return "\n".join(pages)[:8000]
    except Exception as e:
        log.warning("PDF extraction failed: %s", e)
        return ""


def _extract_text_from_docx(data: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs[:200])
        return text[:8000]
    except Exception as e:
        log.warning("DOCX extraction failed: %s", e)
        return ""


@router.message(F.document)
async def on_document(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    if not await core.enforce_channel(message):
        return
    if not await core.enforce_limit(message, lang):
        return

    doc = message.document
    if doc.file_size and doc.file_size > _MAX_FILE_SIZE:
        await message.answer(t(lang, "file_too_large"))
        return

    filename = doc.file_name or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("pdf", "docx", "doc", "txt", "md", "csv", "json", "py", "js", "html", "css"):
        await message.answer(t(lang, "file_not_supported"))
        return

    status = await message.answer(t(lang, "thinking"))
    await message.bot.send_chat_action(message.chat.id, "upload_document")

    try:
        buf = await message.bot.download(doc)
        data = buf.read()
    except Exception:
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            await status.answer(t(lang, "error"))
        return

    if ext == "pdf":
        text = _extract_text_from_pdf(data)
    elif ext in ("docx", "doc"):
        text = _extract_text_from_docx(data)
    else:
        try:
            text = data.decode("utf-8", errors="ignore")[:8000]
        except Exception:
            text = ""

    if not text or len(text.strip()) < 10:
        try:
            await status.edit_text(t(lang, "file_empty"))
        except Exception:
            await status.answer(t(lang, "file_empty"))
        return

    caption = message.caption or "Summarize and analyze this file. Answer any questions about its content."

    lang_name = core._LANG_NAMES.get(lang, "English")
    system = (
        f"You are Kaysan. The user uploaded a file ({filename}). "
        f"Analyze and summarize it. Reply in {lang_name}. "
        f"Be concise but thorough. Include key points."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"File: {filename}\n\nContent:\n{text}\n\n{caption}"},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=2000)
        await db.incr_and_count(uid)
        core._last[uid] = {"text": f"[file: {filename}] {caption}", "intent": "chat", "lang": lang, "reply": reply}
        await core._send_reply(status, reply, lang, uid)
    except Exception as e:
        log.warning("file analysis failed: %s", e)
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            await status.answer(t(lang, "error"))
