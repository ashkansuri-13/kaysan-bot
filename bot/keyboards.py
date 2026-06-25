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


"""سیستم منوی دکمه‌ای شیشه‌ای برای ربات کیسان."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb(lang: str = "fa") -> InlineKeyboardMarkup:
    """منوی اصلی ربات با دکمه‌های شیشه‌ای."""
    menus = {
        "ku": {
            "title": "ڕێنمای کیسان",
            "chat": "💬 چت",
            "image": "🎨 وێنە",
            "voice": "🎤 دەنگ",
            "tools": "🔧 ئامرازەکان",
            "group": "👥 گرووپ",
            "fun": "🎮 خۆشی",
            "settings": "⚙️ ڕێکخستن",
            "help": "📖 ڕێنما",
            "ai": "🤖 AI",
            "search": "🔍 گەڕان",
            "notes": "📌 تێبین",
            "translate": "🔄 وەرگێڕان",
            "news": "📰 هەواڵە",
            "weather": "🌤️ کەش",
            "stock": "📊 بۆرس",
            "qr": "📱 QR",
            "password": "🔑 وشەی نهێنی",
            "calc": "🧮 حیساب",
            "meme": "😂 میم",
            "quiz": "🧠 کوییز",
            "joke": "😄 لوطیفە",
            "fal": "🔮 فال",
            "challenge": "🎯 چالاکی",
            "expense": "💰 خرج",
            "habit": "✅ عادت",
            "travel": "✈️ سەفەر",
            "recipe": "🍽️ خواردن",
            "flashcard": "📇 فلش کارت",
        },
        "fa": {
            "title": "راهنمای کیسان",
            "chat": "💬 چت",
            "image": "🎨 تصویر",
            "voice": "🎤 صدا",
            "tools": "🔧 ابزارها",
            "group": "👥 گروه",
            "fun": "🎮 سرگرمی",
            "settings": "⚙️ تنظیمات",
            "help": "📖 راهنما",
            "ai": "🤖 هوش مصنوعی",
            "search": "🔍 جستجو",
            "notes": "📌 یادداشت",
            "translate": "🔄 ترجمه",
            "news": "📰 اخبار",
            "weather": "🌤️ آب و هوا",
            "stock": "📊 بورس",
            "qr": "📱 QR",
            "password": "🔑 رمز عبور",
            "calc": "🧮 ماشین حساب",
            "meme": "😂 میم",
            "quiz": "🧠 کوییز",
            "joke": "😄 لطیفه",
            "fal": "🔮 فال",
            "challenge": "🎯 چالش",
            "expense": "💰 هزینه",
            "habit": "✅ عادت",
            "travel": "✈️ سفر",
            "recipe": "🍽️ غذا",
            "flashcard": "📇 فلش کارت",
        },
        "en": {
            "title": "Kaysan Guide",
            "chat": "💬 Chat",
            "image": "🎨 Image",
            "voice": "🎤 Voice",
            "tools": "🔧 Tools",
            "group": "👥 Groups",
            "fun": "🎮 Fun",
            "settings": "⚙️ Settings",
            "help": "📖 Guide",
            "ai": "🤖 AI",
            "search": "🔍 Search",
            "notes": "📌 Notes",
            "translate": "🔄 Translate",
            "news": "📰 News",
            "weather": "🌤️ Weather",
            "stock": "📊 Stocks",
            "qr": "📱 QR",
            "password": "🔑 Password",
            "calc": "🧮 Calculator",
            "meme": "😂 Meme",
            "quiz": "🧠 Quiz",
            "joke": "😄 Jokes",
            "fal": "🔮 Fortune",
            "challenge": "🎯 Challenge",
            "expense": "💰 Expense",
            "habit": "✅ Habits",
            "travel": "✈️ Travel",
            "recipe": "🍽️ Recipes",
            "flashcard": "📇 Flashcards",
        }
    }
    m = menus.get(lang, menus["fa"])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=m["chat"], callback_data="menu:chat"),
         InlineKeyboardButton(text=m["image"], callback_data="menu:image"),
         InlineKeyboardButton(text=m["voice"], callback_data="menu:voice")],
        [InlineKeyboardButton(text=m["search"], callback_data="menu:search"),
         InlineKeyboardButton(text=m["translate"], callback_data="menu:translate"),
         InlineKeyboardButton(text=m["notes"], callback_data="menu:notes")],
        [InlineKeyboardButton(text=m["quiz"], callback_data="menu:quiz"),
         InlineKeyboardButton(text=m["joke"], callback_data="menu:joke"),
         InlineKeyboardButton(text=m["fal"], callback_data="menu:fal")],
        [InlineKeyboardButton(text=m["tools"], callback_data="menu:tools"),
         InlineKeyboardButton(text=m["group"], callback_data="menu:group"),
         InlineKeyboardButton(text=m["fun"], callback_data="menu:fun")],
        [InlineKeyboardButton(text=m["weather"], callback_data="menu:weather"),
         InlineKeyboardButton(text=m["news"], callback_data="menu:news"),
         InlineKeyboardButton(text=m["stock"], callback_data="menu:stock")],
        [InlineKeyboardButton(text=m["qr"], callback_data="menu:qr"),
         InlineKeyboardButton(text=m["password"], callback_data="menu:password"),
         InlineKeyboardButton(text=m["calc"], callback_data="menu:calc")],
        [InlineKeyboardButton(text=m["meme"], callback_data="menu:meme"),
         InlineKeyboardButton(text=m["expense"], callback_data="menu:expense"),
         InlineKeyboardButton(text=m["habit"], callback_data="menu:habit")],
        [InlineKeyboardButton(text=m["travel"], callback_data="menu:travel"),
         InlineKeyboardButton(text=m["recipe"], callback_data="menu:recipe"),
         InlineKeyboardButton(text=m["flashcard"], callback_data="menu:flashcard")],
        [InlineKeyboardButton(text=m["ai"], callback_data="menu:ai"),
         InlineKeyboardButton(text=m["challenge"], callback_data="menu:challenge")],
        [InlineKeyboardButton(text=m["settings"], callback_data="menu:settings"),
         InlineKeyboardButton(text=m["help"], callback_data="menu:help")],
    ])


def tools_menu_kb(lang: str = "fa") -> InlineKeyboardMarkup:
    """منوی ابزارها."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 QR Code", callback_data="tool:qr"),
         InlineKeyboardButton(text="🔗 کوتاه کن", callback_data="tool:short")],
        [InlineKeyboardButton(text="🧮 ماشین حساب", callback_data="tool:calc"),
         InlineKeyboardButton(text="💱 تبدیل ارز", callback_data="tool:exchange")],
        [InlineKeyboardButton(text="🔑 رمز عبور", callback_data="tool:password"),
         InlineKeyboardButton(text="📸 اسکرینشات", callback_data="tool:screenshot")],
        [InlineKeyboardButton(text="📊 قیمت سهام", callback_data="tool:stock"),
         InlineKeyboardButton(text="🌤️ آب و هوا", callback_data="tool:weather")],
        [InlineKeyboardButton(text="📰 اخبار", callback_data="tool:news"),
         InlineKeyboardButton(text="🔄 ترجمه", callback_data="tool:translate")],
        [InlineKeyboardButton(text="📝 خلاصه‌سازی", callback_data="tool:summarize"),
         InlineKeyboardButton(text="🍽️ دستور غذا", callback_data="tool:recipe")],
        [InlineKeyboardButton(text="✈️ برنامه سفر", callback_data="tool:travel"),
         InlineKeyboardButton(text="📇 فلش کارت", callback_data="tool:flashcard")],
        [InlineKeyboardButton(text="◀️ بازگشت", callback_data="menu:back")],
    ])


def image_menu_kb(lang: str = "fa") -> InlineKeyboardMarkup:
    """منوی ساخت تصویر با ۲۰ سبک."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📷 واقعی", callback_data="style:realistic"),
         InlineKeyboardButton(text="🎨 انیمیشنی", callback_data="style:anime")],
        [InlineKeyboardButton(text="🖌️ کارتونی", callback_data="style:cartoon"),
         InlineKeyboardButton(text="💧 آبرنگ", callback_data="style:watercolor")],
        [InlineKeyboardButton(text="🖼️ نقاشی روغنی", callback_data="style:oil_painting"),
         InlineKeyboardButton(text="👾 پیکسلی", callback_data="style:pixel_art")],
        [InlineKeyboardButton(text="🎮 سه بعدی", callback_data="style:3d_render"),
         InlineKeyboardButton(text="📖 کمیک", callback_data="style:comic")],
        [InlineKeyboardButton(text="✨ مینیمال", callback_data="style:minimalist"),
         InlineKeyboardButton(text="🌆 سایبرپانک", callback_data="style:cyberpunk")],
        [InlineKeyboardButton(text="🧙 فانتزی", callback_data="style:fantasy"),
         InlineKeyboardButton(text="✏️ اسکچ", callback_data="style:sketch")],
        [InlineKeyboardButton(text="📸 عکاسی", callback_data="style:photography"),
         InlineKeyboardButton(text="🎬 سینمایی", callback_data="style:cinematic")],
        [InlineKeyboardButton(text="🎮 دیجیتال", callback_data="style:digital_art"),
         InlineKeyboardButton(text="🔢 رترو", callback_data="style:pixel_retro")],
        [InlineKeyboardButton(text="🌀 انتزاعی", callback_data="style:abstract"),
         InlineKeyboardButton(text="👤 پرتره", callback_data="style:portrait")],
        [InlineKeyboardButton(text="🏔️ منظره", callback_data="style:landscape"),
         InlineKeyboardButton(text="🔬 ماکرو", callback_data="style:macro")],
        [InlineKeyboardButton(text="◀️ بازگشت", callback_data="menu:back")],
    ])


def guide_kb(lang: str = "fa") -> InlineKeyboardMarkup:
    """دکمه‌های راهنما."""
    guides = {
        "ku": {
            "start": "🚀 دەستپێکردن",
            "chat": "💬 چت کردن",
            "image": "🎨 دروستکردنی وێنە",
            "voice": "🎤 ناردنی دەنگ",
            "tools": "🔧 ئامرازەکان",
            "group": "👥 بەڕێوبرانەی گرووپ",
            "back": "◀️ بازگشت",
        },
        "fa": {
            "start": "🚀 شروع",
            "chat": "💬 چت کردن",
            "image": "🎨 ساخت تصویر",
            "voice": "🎤 ارسال صدا",
            "tools": "🔧 ابزارها",
            "group": "👥 مدیریت گروه",
            "back": "◀️ بازگشت",
        },
        "en": {
            "start": "🚀 Getting Started",
            "chat": "💬 Chatting",
            "image": "🎨 Image Generation",
            "voice": "🎤 Voice Messages",
            "tools": "🔧 Tools",
            "group": "👥 Group Management",
            "back": "◀️ Back",
        }
    }
    g = guides.get(lang, guides["fa"])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g["start"], callback_data="guide:start")],
        [InlineKeyboardButton(text=g["chat"], callback_data="guide:chat")],
        [InlineKeyboardButton(text=g["image"], callback_data="guide:image")],
        [InlineKeyboardButton(text=g["voice"], callback_data="guide:voice")],
        [InlineKeyboardButton(text=g["tools"], callback_data="guide:tools")],
        [InlineKeyboardButton(text=g["group"], callback_data="guide:group")],
        [InlineKeyboardButton(text=g["back"], callback_data="menu:back")],
    ])


def back_kb(lang: str = "fa") -> InlineKeyboardMarkup:
    """دکمه بازگشت."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ بازگشت به منو", callback_data="menu:back")]
    ])
