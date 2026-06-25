"""هندلرهای پایه: start/help/lang و دستور /image."""
import base64
import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from .. import config, database as db, openrouter
from ..keyboards import lang_kb, menu_kb
from ..services.image import _detect_style
from ..texts import SYSTEM_PROMPTS, t
from ..ttl_dict import TTLDict
from . import core

router = Router()
log = logging.getLogger("kaysan.start")


async def _get_user_profile(bot, user) -> dict:
    """اطلاعات پروفایل کاربر را جمع‌آوری می‌کند."""
    info = {
        "name": user.full_name or user.first_name or "Unknown",
        "username": user.username or "",
        "bio": "",
        "photos": [],
    }

    try:
        chat = await bot.get_chat(user.id)
        if chat.bio:
            info["bio"] = chat.bio
    except Exception:
        pass

    try:
        photos = await bot.get_user_profile_photos(user.id, limit=3)
        for photo_group in photos.photos:
            largest = photo_group[-1]
            buf = await bot.download(largest)
            b64 = base64.b64encode(buf.read()).decode()
            info["photos"].append(f"data:image/jpeg;base64,{b64}")
    except Exception:
        pass

    return info


async def _analyze_profile(info: dict, lang: str) -> tuple[str, str]:
    """تحلیل شخصیت بر اساس پروفایل. (analysis, compliment)"""
    parts = []
    parts.append(f"Name: {info['name']}")
    if info["username"]:
        parts.append(f"Username: @{info['username']}")
    if info["bio"]:
        parts.append(f"Bio: {info['bio']}")
    parts.append(f"Number of profile photos: {len(info['photos'])}")

    profile_text = "\n".join(parts)

    lang_instruction = {
        "ku": "IMPORTANT: You MUST reply in Kurdish Sorani (کوردی سۆرانی). Do NOT reply in English or any other language. Write everything in Kurdish Sorani script.",
        "fa": "IMPORTANT: You MUST reply in Persian (فارسی). Do NOT reply in English or any other language. Write everything in Persian script.",
        "en": "Reply in English.",
    }.get(lang, "Reply in English.")

    system = (
        "You are Kaysan, a warm and friendly AI assistant. "
        "Analyze the user's Telegram profile and give a brief, positive personality analysis. "
        f"{lang_instruction} "
        "Write 2-4 short sentences about what their profile tells you about them. "
        "Be warm, genuine, and complimentary but not over-the-top. "
        "Mention specific details from their name, bio, or photos. "
        "After the analysis, write one short motivational/positive sentence as a compliment on a new line."
    )

    messages = [{"role": "system", "content": system}]

    if info["photos"]:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"Analyze this user's profile:\n\n{profile_text}\n\nHere are their profile photos:"},
                *[{"type": "image_url", "image_url": {"url": p}} for p in info["photos"]],
            ],
        })
    else:
        messages.append({"role": "user", "content": f"Analyze this user's profile:\n\n{profile_text}"})

    # اول با مدل پولی (بهتر) امتحان کن، بعد رایگان
    models = [config.PRIMARY_MODEL] if config.PRIMARY_MODEL else []
    models.extend(config.VISION_MODELS if info["photos"] else config.CHAT_MODELS)

    try:
        reply, _ = await openrouter.chat(messages, models, max_tokens=400)
        lines = reply.strip().split("\n")
        analysis = "\n".join(lines[:-1]).strip() if len(lines) > 1 else reply.strip()
        compliment = lines[-1].strip() if len(lines) > 1 else ""
        if not compliment or len(compliment) < 5:
            analysis = reply.strip()
            compliment = ""
        return analysis, compliment
    except Exception as e:
        log.warning("profile analysis failed: %s", e)
        return "", ""


@router.message(CommandStart())
async def cmd_start(message: Message):
    uid = message.from_user.id
    user = message.from_user
    await db.ensure_user(uid, name=user.full_name)
    if not await core.enforce_channel(message):
        return
    lang = await db.get_lang(uid)

    # دکمه‌های سریع برای کاربر جدید
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    quick_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 از من بپرس", callback_data="quick:ask"),
         InlineKeyboardButton(text="🎨 عکس بساز", callback_data="quick:image")],
        [InlineKeyboardButton(text="🔄 ترجمه کن", callback_data="quick:translate"),
         InlineKeyboardButton(text="🧠 کوییز", callback_data="quick:quiz")],
        [InlineKeyboardButton(text="😄 لطیفه بگو", callback_data="quick:joke"),
         InlineKeyboardButton(text="📌 یادداشت", callback_data="quick:note")],
    ])

    welcome = t(lang, "welcome")
    await message.answer(welcome, parse_mode=ParseMode.HTML, reply_markup=quick_kb)


@router.callback_query(F.data.startswith("quick:"))
async def cb_quick(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    action = call.data.split(":")[1]
    await call.answer()

    prompts = {
        "ask": "هی Kaysan! یه سؤال دارم...",
        "image": "/image یه منظره زیبا",
        "translate": "/translate سلام حالت چطوره",
        "quiz": "/quiz",
        "joke": "/joke",
        "note": "/note اولین یادداشت من",
    }
    if action in prompts:
        try:
            await call.message.delete()
        except Exception:
            pass
        await core.process_text(call.message, prompts[action], lang, uid=uid)


@router.message(Command("help"))
async def cmd_help(message: Message):
    lang = await db.get_lang(message.from_user.id)
    await message.answer(t(lang, "help"), parse_mode=ParseMode.HTML)


@router.message(Command("lang"))
async def cmd_lang(message: Message):
    lang = await db.get_lang(message.from_user.id)
    await message.answer(t(lang, "choose_lang"), reply_markup=lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(call: CallbackQuery):
    lang = call.data.split(":", 1)[1]
    if lang not in config.SUPPORTED_LANGS:
        lang = config.DEFAULT_LANG
    await db.set_lang(call.from_user.id, lang)
    await call.message.edit_text(t(lang, "lang_set"))
    await call.message.answer(t(lang, "welcome"), parse_mode=ParseMode.HTML,
                              reply_markup=menu_kb(lang))
    await call.answer()


@router.callback_query(F.data == "back:lang")
async def cb_back_lang(call: CallbackQuery):
    await call.message.answer(t(await db.get_lang(call.from_user.id), "choose_lang"),
                              reply_markup=lang_kb())
    await call.answer()


_style_state = TTLDict(ttl_seconds=300, max_size=500)


@router.callback_query(F.data.startswith("style:"))
async def cb_style(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    style = call.data.split(":", 1)[1]
    _style_state[uid] = style

    style_names = {
        "anime": "🎨 انیمیشنی",
        "realistic": "📷 واقعی",
        "cartoon": "🖌️ کارتونی",
        "watercolor": "💧 آبرنگ",
        "oil_painting": "🖼️ نقاشی روغنی",
        "pixel_art": "👾 پیکسلی",
        "3d_render": "🔮 سه‌بعدی",
        "comic": "💥 کمیک",
        "minimalist": "✨ مینیمال",
        "cyberpunk": "🌃 سایبرپانک",
        "fantasy": "🧙 فانتزی",
        "sketch": "✏️ اسکچ",
    }
    style_name = style_names.get(style, style)

    await call.answer(f"سبک: {style_name}")
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"✅ سبک: **{style_name}**\n\nحالا توضیح عکست رو بنویس:",
        parse_mode=ParseMode.HTML,
    )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_image_style_input(message: Message):
    uid = message.from_user.id
    style = _style_state.pop(uid, None)
    if not style:
        return

    await core._do_image(message, message.text, await db.get_lang(uid), style=style)
    await message.stop_propagation()


@router.message(Command("image"))
async def cmd_image(message: Message):
    uid = message.from_user.id
    await db.ensure_user(uid, name=message.from_user.full_name)
    lang = await db.get_lang(uid)
    if not await core.enforce_limit(message, lang):
        return
    prompt = message.text.split(maxsplit=1)
    if len(prompt) < 2:
        from ..services.image import get_style_keyboard
        usage = {
            "ku": "🎨 <b>ساخت عکس</b>\n\nتکایە سبک هەڵبژێرە:",
            "fa": "🎨 <b>ساخت تصویر</b>\n\nلطفاً سبک رو انتخاب کن:",
            "en": "🎨 <b>Generate Image</b>\n\nPlease choose a style:",
        }
        kb = get_style_keyboard()
        await message.answer(usage.get(lang, usage["en"]), reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    style, clean_prompt = _detect_style(prompt[1])
    await core._do_image(message, clean_prompt, lang, style=style)


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    uid = message.from_user.id
    await db.clear_history(uid)
    lang = await db.get_lang(uid)
    texts = {
        "ku": "✅ تاریخچه‌ی گفتگو پاک کرا.",
        "fa": "✅ تاریخچه گفتگو پاک شد.",
        "en": "✅ Conversation history cleared.",
    }
    await message.answer(texts.get(lang, texts["en"]))
