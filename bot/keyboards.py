"""کیبوردها — دکمه‌های شیشه‌ای رنگی (Bot API 9.4+)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from . import config
from .texts import t


def _btn(text, *, callback_data=None, url=None, style=None):
    base = {"text": text}
    if callback_data is not None:
        base["callback_data"] = callback_data
    if url is not None:
        base["url"] = url
    if config.USE_COLORED_BUTTONS and style:
        try:
            return InlineKeyboardButton(**base, style=style)
        except Exception:
            pass
    return InlineKeyboardButton(**base)


def answer_kb(lang, has_alternatives=False):
    """زیر هر جواب: جواب دیگه + ساخت عکس + صدا + فیدبک."""
    rows = [[
        _btn("🔄 " + t(lang, "btn_regen"), callback_data="regen", style="primary"),
        _btn("🎨 " + t(lang, "btn_image"), callback_data="toimg", style="success"),
    ], [
        _btn("🔊 " + t(lang, "btn_voice"), callback_data="tts", style="primary"),
    ]]
    if has_alternatives:
        rows.append([_btn("📋 جواب‌های دیگه", callback_data="alts", style="primary")])
    rows.append([
        _btn("👍", callback_data="feedback_like", style="success"),
        _btn("👎", callback_data="feedback_dislike", style="danger"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def limit_kb(lang):
    owner = config.OWNER_USERNAME
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("💎 " + t(lang, "btn_buy"), url=f"https://t.me/{owner}", style="success"),
    ]])


def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("کوردی 🟢", callback_data="lang:ku", style="success"),
        _btn("فارسی 🔵", callback_data="lang:fa", style="primary"),
        _btn("English 🔴", callback_data="lang:en", style="danger"),
    ]])


def menu_kb(lang):
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("🌐 " + t(lang, "btn_lang"), callback_data="back:lang"),
    ]])
