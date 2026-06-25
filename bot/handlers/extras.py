"""آب‌وهوا، تبدیل واحد، فال حافظ، حالت‌ها، بازی حدس کلمه."""
import logging
import random
import re

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter
from ..texts import SYSTEM_PROMPTS, t
from . import core

router = Router()
log = logging.getLogger("kaysan.extras")


# ============================================================
#  آب‌وهوا — /weather
# ============================================================

@router.message(Command("weather"))
async def cmd_weather(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t(lang, "weather_usage", city=""))
        return

    city = parts[1].strip()
    status = await message.answer(t(lang, "thinking"))
    await message.bot.send_chat_action(message.chat.id, "typing")

    from ..handlers.search import web_search
    results = await web_search(f"weather {city} today", max_results=2)

    if results:
        lang_name = core._LANG_NAMES.get(lang, "English")
        system = f"Summarize this weather info in {lang_name}. Be concise (2-3 sentences)."
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": results},
        ]
        try:
            reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=200)
            try:
                await status.edit_text(t(lang, "weather_result", city=city, result=reply))
            except Exception:
                await status.answer(t(lang, "weather_result", city=city, result=reply))
        except Exception:
            try:
                await status.edit_text(results[:2000])
            except Exception:
                await status.answer(results[:2000])
    else:
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            await status.answer(t(lang, "error"))


# ============================================================
#  تبدیل واحد — /convert
# ============================================================

@router.message(Command("convert"))
async def cmd_convert(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t(lang, "convert_usage"))
        return

    query = parts[1].strip()
    status = await message.answer(t(lang, "thinking"))
    await message.bot.send_chat_action(message.chat.id, "typing")

    lang_name = core._LANG_NAMES.get(lang, "English")
    system = f"You are a unit converter. Convert the given value. Reply in {lang_name}. Be concise."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]

    try:
        reply, _ = await openrouter.chat(messages, config.CHAT_MODELS, max_tokens=200)
        await db.incr_and_count(uid)
        try:
            await status.edit_text(t(lang, "convert_result", result=reply))
        except Exception:
            await status.answer(t(lang, "convert_result", result=reply))
    except Exception:
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            await status.answer(t(lang, "error"))


# ============================================================
#  فال حافظ — /fal
# ============================================================

_HAFEZ_POEMS = [
    ("اِلٰهی به روزیِ فردام\nختمِ کارِ من بکن\nگر چه با من سرِ کینه‌ای\nزین عالم به درم بکن", "صبر پیشه کن. دوران سختی زود گذر است و به زودی خبر خوشی به تو می‌رسد."),
    ("مرا به رندی و عشق آموزند مغان\nچه نسبت است به کودکان درس نادان", "عشق و عاشقی راهی است که باید با جان و دل طی کنی. نترس."),
    ("ز کوی تو چون پرگار در آمدم\nچه چیز آید ز این ماجرا به ختم", "سفری در پیش داری که زندگی‌ات را عوض می‌کند. آماده باش."),
    ("شب تاریک و بیم موج و گردابی چنین هایل\nکجا دانند حال ما سبکباران ساحل‌ها", "در سختی‌های زندگی صبور باش. به ساحل نجات خواهی رسید."),
    ("دل من در هوایت بی‌قرار است\n灵魂م بی‌تو بی‌قرار است", "دلتنگی طبیعی است. صبر کن، وصال نزدیک است."),
    ("بیا که قصر امل سخت سست بنیاد است\nفریبِ خوش خیالِ گذرِ عمر در خواب است", "از آرزوهای بی‌پایه دست بردار. زندگی کن و لحظه‌ها رو دریاب."),
    ("گل در بر و می در کف و معشوق به کام است\nسلطانِ جهانم چه نعمت‌هاست این ایام", "روزهای خوبی در راه است. از زندگی لذت ببر."),
    ("مرا عهدیست با جانان که تا جان در بدن دارم\nهزاران جان فدای جانان که آن جان شیرین‌تر است", "عاشقی واقعی ارزش فداکاری دارد. عشق خود را حفظ کن."),
]


@router.message(Command("fal"))
async def cmd_fal(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    poem, interp = random.choice(_HAFEZ_POEMS)
    await message.answer(
        t(lang, "fal_result", poem=poem, interpretation=interp),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
#  حالت‌ها — /mode
# ============================================================

_MODES = {
    "teacher": {"ku": "معلم", "fa": "معلم", "en": "Teacher"},
    "coder": {"ku": "برنامەنویس", "fa": "برنامه‌نویس", "en": "Coder"},
    "friend": {"ku": "دوست", "fa": "دوست", "en": "Friend"},
    "default": {"ku": "عادی", "fa": "عادی", "en": "Default"},
}

_MODE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📚 معلم / Teacher", callback_data="mode:teacher"),
     InlineKeyboardButton(text="💻 کدنویس / Coder", callback_data="mode:coder")],
    [InlineKeyboardButton(text="🤝 دوست / Friend", callback_data="mode:friend"),
     InlineKeyboardButton(text="🤖 عادی / Default", callback_data="mode:default")],
])


@router.message(Command("mode"))
async def cmd_mode(message: Message):
    uid = message.from_user.id
    lang = await db.get_lang(uid)
    await message.answer("یک حالت انتخاب کن / Choose a mode:", reply_markup=_MODE_KEYBOARD)


@router.callback_query(F.data.startswith("mode:"))
async def cb_mode(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    mode = call.data.split(":")[1]
    if mode not in _MODES:
        await call.answer()
        return

    await db.set_mode(uid, mode)
    mode_name = _MODES[mode].get(lang, mode)
    await call.answer(t(lang, "mode_set", mode=mode_name))

    # پیام تأیید
    confirm_texts = {
        "teacher": t(lang, "mode_teacher"),
        "coder": t(lang, "mode_coder"),
        "friend": t(lang, "mode_friend"),
        "default": t(lang, "mode_default"),
    }
    await call.message.edit_text(confirm_texts.get(mode, confirm_texts["default"]))
    await call.answer()


# ============================================================
#  بازی حدس کلمه — /wordle (ساده)
# ============================================================

_WORDLE_WORDS = [
    "کتاب", "گل", "آسمان", "باغ", "ستاره", "ماه", "خورشید", "آب",
    "برد", "خانه", "درخت", "سنگ", "آتش", "باد", "ابر", "باران",
    "cat", "dog", "sun", "moon", "star", "tree", "book", "fish",
    "house", "water", "fire", "wind", "rain", "snow", "love", "hope",
]


@router.message(Command("wordle"))
async def cmd_wordle(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)

    word = random.choice(_WORDLE_WORDS)
    hidden = word[0] + "░" * (len(word) - 1)
    await db.set_pref(uid, "wordle_word", word)
    await db.set_pref(uid, "wordle_tries", "0")

    await message.answer(
        f"🎮 <b>بازی حدس کلمه</b>\n\n"
        f"کلمه: <code>{hidden}</code>\n"
        f"تعداد حروف: {len(word)}\n\n"
        f"کلمه رو حدس بزن!",
        parse_mode=ParseMode.HTML,
    )
