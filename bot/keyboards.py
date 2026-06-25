
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


def main_menu_kb(lang="fa"):
    menus = {
        "ku": {"chat": "💬 چت", "image": "🎨 وێنە", "voice": "🎤 دەنگ", "tools": "🔧 ئامرازەکان", "group": "👥 گرووپ", "fun": "🎮 خۆشی", "settings": "⚙️ ڕێکخستن", "help": "📖 ڕێنما", "ai": "🤖 AI", "search": "🔍 گەڕان", "notes": "📌 تێبین", "translate": "🔄 وەرگێڕان", "news": "📰 هەواڵە", "weather": "🌤️ کەش", "stock": "📊 بۆرس", "qr": "📱 QR", "password": "🔑 وشەی نهێنی", "calc": "🧮 حیساب", "meme": "😂 میم", "quiz": "🧠 کوییز", "joke": "😄 لوطیفە", "fal": "🔮 فال", "challenge": "🎯 چالاکی", "expense": "💰 خرج", "habit": "✅ عادت", "travel": "✈️ سەفەر", "recipe": "🍽️ خواردن", "flashcard": "📇 فلش کارت"},
        "fa": {"chat": "💬 چت", "image": "🎨 تصویر", "voice": "🎤 صدا", "tools": "🔧 ابزارها", "group": "👥 گروه", "fun": "🎮 سرگرمی", "settings": "⚙️ تنظیمات", "help": "📖 راهنما", "ai": "🤖 هوش مصنوعی", "search": "🔍 جستجو", "notes": "📌 یادداشت", "translate": "🔄 ترجمه", "news": "📰 اخبار", "weather": "🌤️ آب و هوا", "stock": "📊 بورس", "qr": "📱 QR", "password": "🔑 رمز عبور", "calc": "🧮 ماشین حساب", "meme": "😂 میم", "quiz": "🧠 کوییز", "joke": "😄 لطیفه", "fal": "🔮 فال", "challenge": "🎯 چالش", "expense": "💰 هزینه", "habit": "✅ عادت", "travel": "✈️ سفر", "recipe": "🍽️ غذا", "flashcard": "📇 فلش کارت"},
        "en": {"chat": "💬 Chat", "image": "🎨 Image", "voice": "🎤 Voice", "tools": "🔧 Tools", "group": "👥 Groups", "fun": "🎮 Fun", "settings": "⚙️ Settings", "help": "📖 Guide", "ai": "🤖 AI", "search": "🔍 Search", "notes": "📌 Notes", "translate": "🔄 Translate", "news": "📰 News", "weather": "🌤️ Weather", "stock": "📊 Stocks", "qr": "📱 QR", "password": "🔑 Password", "calc": "🧮 Calculator", "meme": "😂 Meme", "quiz": "🧠 Quiz", "joke": "😄 Jokes", "fal": "🔮 Fortune", "challenge": "🎯 Challenge", "expense": "💰 Expense", "habit": "✅ Habits", "travel": "✈️ Travel", "recipe": "🍽️ Recipes", "flashcard": "📇 Flashcards"}
    }
    m = menus.get(lang, menus["fa"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn(m["chat"], callback_data="menu:chat", style="primary"), _btn(m["image"], callback_data="menu:image", style="success"), _btn(m["voice"], callback_data="menu:voice", style="primary")],
        [_btn(m["search"], callback_data="menu:search", style="primary"), _btn(m["translate"], callback_data="menu:translate", style="success"), _btn(m["notes"], callback_data="menu:notes", style="primary")],
        [_btn(m["quiz"], callback_data="menu:quiz", style="success"), _btn(m["joke"], callback_data="menu:joke", style="primary"), _btn(m["fal"], callback_data="menu:fal", style="success")],
        [_btn(m["tools"], callback_data="menu:tools", style="primary"), _btn(m["group"], callback_data="menu:group", style="success"), _btn(m["fun"], callback_data="menu:fun", style="primary")],
        [_btn(m["weather"], callback_data="menu:weather", style="success"), _btn(m["news"], callback_data="menu:news", style="primary"), _btn(m["stock"], callback_data="menu:stock", style="success")],
        [_btn(m["qr"], callback_data="menu:qr", style="primary"), _btn(m["password"], callback_data="menu:password", style="success"), _btn(m["calc"], callback_data="menu:calc", style="primary")],
        [_btn(m["meme"], callback_data="menu:meme", style="success"), _btn(m["expense"], callback_data="menu:expense", style="primary"), _btn(m["habit"], callback_data="menu:habit", style="success")],
        [_btn(m["travel"], callback_data="menu:travel", style="primary"), _btn(m["recipe"], callback_data="menu:recipe", style="success"), _btn(m["flashcard"], callback_data="menu:flashcard", style="primary")],
        [_btn(m["ai"], callback_data="menu:ai", style="success"), _btn(m["challenge"], callback_data="menu:challenge", style="primary")],
        [_btn(m["settings"], callback_data="menu:settings", style="primary"), _btn(m["help"], callback_data="menu:help", style="success")],
    ])


def tools_menu_kb(lang="fa"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("📱 QR Code", callback_data="tool:qr", style="primary"), _btn("🔗 کوتاه کن", callback_data="tool:short", style="success")],
        [_btn("🧮 ماشین حساب", callback_data="tool:calc", style="primary"), _btn("💱 تبدیل ارز", callback_data="tool:exchange", style="success")],
        [_btn("🔑 رمز عبور", callback_data="tool:password", style="primary"), _btn("📸 اسکرینشات", callback_data="tool:screenshot", style="success")],
        [_btn("📊 قیمت سهام", callback_data="tool:stock", style="primary"), _btn("🌤️ آب و هوا", callback_data="tool:weather", style="success")],
        [_btn("📰 اخبار", callback_data="tool:news", style="primary"), _btn("🔄 ترجمه", callback_data="tool:translate", style="success")],
        [_btn("📝 خلاصه‌سازی", callback_data="tool:summarize", style="primary"), _btn("🍽️ دستور غذا", callback_data="tool:recipe", style="success")],
        [_btn("✈️ برنامه سفر", callback_data="tool:travel", style="primary"), _btn("📇 فلش کارت", callback_data="tool:flashcard", style="success")],
        [_btn("◀️ بازگشت", callback_data="menu:back", style="primary")],
    ])


def image_menu_kb(lang="fa"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("📷 واقعی", callback_data="style:realistic", style="primary"), _btn("🎨 انیمیشنی", callback_data="style:anime", style="success")],
        [_btn("🖌️ کارتونی", callback_data="style:cartoon", style="primary"), _btn("💧 آبرنگ", callback_data="style:watercolor", style="success")],
        [_btn("🖼️ نقاشی روغنی", callback_data="style:oil_painting", style="primary"), _btn("👾 پیکسلی", callback_data="style:pixel_art", style="success")],
        [_btn("🎮 سه بعدی", callback_data="style:3d_render", style="primary"), _btn("📖 کمیک", callback_data="style:comic", style="success")],
        [_btn("✨ مینیمال", callback_data="style:minimalist", style="primary"), _btn("🌆 سایبرپانک", callback_data="style:cyberpunk", style="success")],
        [_btn("🧙 فانتزی", callback_data="style:fantasy", style="primary"), _btn("✏️ اسکچ", callback_data="style:sketch", style="success")],
        [_btn("📸 عکاسی", callback_data="style:photography", style="primary"), _btn("🎬 سینمایی", callback_data="style:cinematic", style="success")],
        [_btn("🎮 دیجیتال", callback_data="style:digital_art", style="primary"), _btn("🔢 رترو", callback_data="style:pixel_retro", style="success")],
        [_btn("🌀 انتزاعی", callback_data="style:abstract", style="primary"), _btn("👤 پرتره", callback_data="style:portrait", style="success")],
        [_btn("🏔️ منظره", callback_data="style:landscape", style="primary"), _btn("🔬 ماکرو", callback_data="style:macro", style="success")],
        [_btn("◀️ بازگشت", callback_data="menu:back", style="primary")],
    ])


def guide_kb(lang="fa"):
    guides = {
        "ku": {"start": "🚀 دەستپێکردن", "chat": "💬 چت کردن", "image": "🎨 دروستکردنی وێنە", "voice": "🎤 ناردنی دەنگ", "tools": "🔧 ئامرازەکان", "group": "👥 بەڕێوبرانەی گرووپ", "back": "◀️ بازگشت"},
        "fa": {"start": "🚀 شروع", "chat": "💬 چت کردن", "image": "🎨 ساخت تصویر", "voice": "🎤 ارسال صدا", "tools": "🔧 ابزارها", "group": "👥 مدیریت گروه", "back": "◀️ بازگشت"},
        "en": {"start": "🚀 Getting Started", "chat": "💬 Chatting", "image": "🎨 Image Generation", "voice": "🎤 Voice Messages", "tools": "🔧 Tools", "group": "👥 Group Management", "back": "◀️ Back"}
    }
    g = guides.get(lang, guides["fa"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn(g["start"], callback_data="guide:start", style="success")],
        [_btn(g["chat"], callback_data="guide:chat", style="primary")],
        [_btn(g["image"], callback_data="guide:image", style="success")],
        [_btn(g["voice"], callback_data="guide:voice", style="primary")],
        [_btn(g["tools"], callback_data="guide:tools", style="success")],
        [_btn(g["group"], callback_data="guide:group", style="primary")],
        [_btn(g["back"], callback_data="menu:back", style="success")],
    ])


def back_kb(lang="fa"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("◀️ بازگشت به منو", callback_data="menu:back", style="primary")]
    ])
