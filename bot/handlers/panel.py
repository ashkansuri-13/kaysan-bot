"""پنل مدیریت گروه از پی‌وی — ۲۰ قابلیت."""
import json
import logging
import re
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db
from ..ttl_dict import TTLDict

router = Router()
log = logging.getLogger("kaysan.panel")

# ── حالت‌های ورودی کاربر ──
_input_state = TTLDict(ttl_seconds=300, max_size=1000)


def _clean_state(uid: int):
    _input_state.pop(uid, None)


def _set_state(uid: int, state: dict):
    _input_state[uid] = state


def _get_state(uid: int) -> dict | None:
    return _input_state.get(uid)


# ─────────────────────────────────────────────
#  هسته پنل
# ─────────────────────────────────────────────

async def _is_group_admin(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


def _main_kb(chat_id: int, title: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 پیام خوش‌آمد", callback_data=f"gp:welcome:{chat_id}"),
         InlineKeyboardButton(text="👋 پیام وداع", callback_data=f"gp:goodbye:{chat_id}")],
        [InlineKeyboardButton(text="📜 قوانین", callback_data=f"gp:rules:{chat_id}"),
         InlineKeyboardButton(text="📊 آمار", callback_data=f"gp:stats:{chat_id}")],
        [InlineKeyboardButton(text="🚫 فیلتر اسپم", callback_data=f"gp:spam:{chat_id}"),
         InlineKeyboardButton(text="⚠️ کلمات ممنوع", callback_data=f"gp:badwords:{chat_id}")],
        [InlineKeyboardButton(text="💬 پاسخ خودکار", callback_data=f"gp:autoreply:{chat_id}"),
         InlineKeyboardButton(text="🤖 حالت AI", callback_data=f"gp:ai:{chat_id}")],
        [InlineKeyboardButton(text="⏳ Slow Mode", callback_data=f"gp:slowmode:{chat_id}"),
         InlineKeyboardButton(text="🔇 ساعات سکوت", callback_data=f"gp:silent:{chat_id}")],
        [InlineKeyboardButton(text="🔒 ضد Flood", callback_data=f"gp:flood:{chat_id}"),
         InlineKeyboardButton(text="🔄 ترجمه خودکار", callback_data=f"gp:translate:{chat_id}")],
        [InlineKeyboardButton(text="📌 پین خودکار", callback_data=f"gp:pin:{chat_id}"),
         InlineKeyboardButton(text="📋 لاگ فعالیت", callback_data=f"gp:log:{chat_id}")],
        [InlineKeyboardButton(text="🛡️ ادمین‌ها", callback_data=f"gp:admins:{chat_id}"),
         InlineKeyboardButton(text="🏷️ نام گروه", callback_data=f"gp:rename:{chat_id}")],
        [InlineKeyboardButton(text="💾 بکاپ", callback_data=f"gp:backup:{chat_id}"),
         InlineKeyboardButton(text="🔔 اعلان‌ها", callback_data=f"gp:notif:{chat_id}")],
        [InlineKeyboardButton(text="⏰ زمان‌بندی", callback_data=f"gp:schedule:{chat_id}"),
         InlineKeyboardButton(text="📊 نمودار", callback_data=f"gp:chart:{chat_id}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="gp:back")],
    ])


def _back_kb(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به پنل", callback_data=f"gp:open:{chat_id}")]
    ])


def _toggle(val: int) -> int:
    return 0 if val else 1


def _onoff(val: int) -> str:
    return "فعال ✅" if val else "غیرفعال ❌"


# ─────────────────────────────────────────────
#  /manage — شروع
# ─────────────────────────────────────────────

@router.message(Command("manage"))
@router.message(F.text.func(lambda t: t and t.lower() in ("مدیریت گروه", "manage", "manage group", "گروهم", "manage my group")))
async def cmd_manage(message: Message):
    uid = message.from_user.id
    lang = await db.get_lang(uid)
    _clean_state(uid)

    text = {
        "ku": "🔧 <b>پنل مدیریت گروه</b>\n\nگروهی که میخوای مدیریت کنی رو انتخاب کن.\nاگه ربات هنوز به گروه اضافه نشده، اول اضافه‌اش کن.",
        "fa": "🔧 <b>پنل مدیریت گروه</b>\n\nگروهی که میخوای مدیریت کنی رو انتخاب کن.\nاگه ربات هنوز به گروه اضافه نشده، اول اضافه‌اش کن.",
        "en": "🔧 <b>Group Management Panel</b>\n\nSelect the group you want to manage.\nIf the bot isn't in the group yet, add it first.",
    }.get(lang, "en")

    add_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن ربات به گروه", url=f"https://t.me/{config.OWNER_USERNAME or 'KaysanAI_Bot'}?startgroup=true")],
    ])

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=add_kb)
    await _show_my_groups(message, uid)


async def _show_my_groups(message: Message, uid: int):
    groups = await db.get_all_managed_groups(uid)
    if not groups:
        await message.answer("📌 هنوز هیچ گروهی ثبت نشده.\nربات رو به گروه اضافه کن، بعد اینجا مدیریتش کن.")
        return

    lines = ["📌 <b>گروه‌های شما:</b>\n"]
    kb_buttons = []
    for g in groups:
        lines.append(f"• {g['title']} (<code>{g['chat_id']}</code>)")
        kb_buttons.append([InlineKeyboardButton(
            text=f"⚙️ {g['title']}",
            callback_data=f"gp:open:{g['chat_id']}"
        )])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)


# ─────────────────────────────────────────────
#  تشخیص اضافه شدن ربات به گروه
# ─────────────────────────────────────────────

@router.my_chat_member(F.new_chat_member.status.in_({"administrator", "member"}))
async def on_bot_added(event):
    chat = event.chat
    added_by = event.from_user
    if chat.type not in ("group", "supergroup"):
        return

    await db.ensure_group(chat.id, chat.title or "")

    try:
        await chat.send_message(
            f"✅ <b>Kaysan AI به گروه اضافه شد!</b>\n\n"
            f" add_by <b>{added_by.full_name}</b> اضافه شد.\n"
            f"برای مدیریت گروه از پی‌وی من استفاده کن:\n"
            f"/manage",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    try:
        await added_by.send_message(
            f"✅ ربات به گروه <b>{chat.title}</b> اضافه شد!\n"
            f"برای مدیریت: /manage",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
#  هندلر مرکزی callback
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("gp:"))
async def cb_panel(call: CallbackQuery):
    uid = call.from_user.id
    parts = call.data.split(":")

    if len(parts) < 2:
        await call.answer()
        return

    action = parts[1]
    chat_id = int(parts[2]) if len(parts) > 2 and parts[2].lstrip("-").isdigit() else None

    if action == "back":
        _clean_state(uid)
        await call.message.delete()
        await call.answer()
        await _show_my_groups(call.message, uid)
        return

    if action == "list":
        _clean_state(uid)
        await call.answer()
        await _show_my_groups(call.message, uid)
        return

    if action == "open" and chat_id:
        if not await _is_group_admin(call.bot, chat_id, uid):
            await call.answer("شما ادمین این گروه نیستید!", show_alert=True)
            return
        await _show_group_panel(call, chat_id)
        return

    if chat_id and not await _is_group_admin(call.bot, chat_id, uid):
        await call.answer("دسترسی غیرمجاز!", show_alert=True)
        return

    await _handle_feature(call, uid, action, chat_id, parts)


# ─────────────────────────────────────────────
#  نمایش پنل گروه
# ─────────────────────────────────────────────

async def _show_group_panel(call: CallbackQuery, chat_id: int):
    settings = await db.get_group_settings(chat_id)
    title = settings.get("title", str(chat_id))

    text = (
        f"⚙️ <b>{title}</b>\n\n"
        f"🎨 خوش‌آمد: {_onoff(settings.get('welcome_on', 1))}\n"
        f"👋 وداع: {_onoff(settings.get('goodbye_on', 1))}\n"
        f"🚫 اسپم: {_onoff(settings.get('anti_spam', 1))}\n"
        f"⚠️ کلمات ممنوع: {_onoff(settings.get('anti_badwords', 1))}\n"
        f"🔒 ضد Flood: {_onoff(settings.get('anti_flood', 1))}\n"
        f"⏳ Slow Mode: {settings.get('slow_mode', 0)} ثانیه\n"
        f"🔇 سکوت: {'فعال' if settings.get('silent_start', -1) >= 0 else 'غیرفعال'}\n"
        f"🤖 AI: {_onoff(settings.get('ai_reply', 0))}\n"
        f"🔄 ترجمه: {_onoff(settings.get('auto_translate', 0))}\n"
        f"📌 پین: {_onoff(settings.get('auto_pin', 0))}\n"
    )

    await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_main_kb(chat_id, title))
    await call.answer()


# ─────────────────────────────────────────────
#  ۱. پیام خوش‌آمد
# ─────────────────────────────────────────────

# ۲. پیام وداع
# ─────────────────────────────────────────────

async def _refresh_feature(call: CallbackQuery, feature: str, chat_id: int):
    """بازخوانی نمای یک قابلیت بعد از تغییر — بدون ساخت CallbackQuery جعلی."""
    await _handle_feature(call, call.from_user.id, feature, chat_id, [f"gp:{feature}:{chat_id}"])


async def _handle_feature(call: CallbackQuery, uid: int, action: str, chat_id: int, parts: list):
    settings = await db.get_group_settings(chat_id)
    title = settings.get("title", str(chat_id))

    # ── ۱. پیام خوش‌آمد ──
    if action == "welcome":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('welcome_on', 1))}",
                callback_data=f"gp:welcome_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="✏️ ویرایش متن", callback_data=f"gp:welcome_edit:{chat_id}")],
            [InlineKeyboardButton(text="👁️ پیش‌نمایش", callback_data=f"gp:welcome_preview:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"🎨 <b>پیام خوش‌آمد</b>\n\n"
            f"وضعیت: {_onoff(settings.get('welcome_on', 1))}\n"
            f"متن فعلی:\n<code>{settings.get('welcome_text', '(پیش‌فرض)')[:200]}</code>\n\n"
            f"متغیرها:\n"
            f"{{name}} — نام کاربر\n"
            f"{{group}} — نام گروه"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "welcome_toggle":
        new_val = _toggle(settings.get("welcome_on", 1))
        await db.update_group(chat_id, welcome_on=new_val)
        await call.answer(f"خوش‌آمد: {_onoff(new_val)}")
        await _refresh_feature(call, "welcome", chat_id)

    elif action == "welcome_edit":
        _set_state(uid, {"action": "welcome_text", "chat_id": chat_id})
        await call.message.edit_text(
            "✏️ متن خوش‌آمد جدید رو بنویس:\n\n"
            "متغیرها: {name} = نام کاربر، {group} = نام گروه\n"
            "برای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    elif action == "welcome_preview":
        settings = await db.get_group_settings(chat_id)
        text = settings.get("welcome_text", "")
        if not text:
            text = "🎉 بخێربێیت {name}!\nبەخێربێیت بۆ {group} 😊"
        preview = text.replace("{name}", "علی").replace("{group}", title)
        await call.answer(f"پیش‌نمایش: {preview[:100]}", show_alert=True)

    # ── ۲. پیام وداع ──
    elif action == "goodbye":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('goodbye_on', 1))}",
                callback_data=f"gp:goodbye_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="✏️ ویرایش متن", callback_data=f"gp:goodbye_edit:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"👋 <b>پیام وداع</b>\n\n"
            f"وضعیت: {_onoff(settings.get('goodbye_on', 1))}\n"
            f"متن فعلی:\n<code>{settings.get('goodbye_text', '(پیش‌فرض)')[:200]}</code>"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "goodbye_toggle":
        new_val = _toggle(settings.get("goodbye_on", 1))
        await db.update_group(chat_id, goodbye_on=new_val)
        await call.answer(f"وداع: {_onoff(new_val)}")
        await _refresh_feature(call, "goodbye", chat_id)

    elif action == "goodbye_edit":
        _set_state(uid, {"action": "goodbye_text", "chat_id": chat_id})
        await call.message.edit_text(
            "✏️ متن وداع جدید رو بنویس:\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    # ── ۳. قوانین ──
    elif action == "rules":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ ویرایش قوانین", callback_data=f"gp:rules_edit:{chat_id}")],
            [InlineKeyboardButton(text="🗑️ حذف قوانین", callback_data=f"gp:rules_delete:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        rules = settings.get("rules_text", "")
        text = (
            f"📜 <b>قوانین گروه</b>\n\n"
            f"{rules if rules else 'هنوز قوانینی تنظیم نشده.'}"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "rules_edit":
        _set_state(uid, {"action": "rules_text", "chat_id": chat_id})
        await call.message.edit_text(
            "📜 قوانین جدید رو بنویس:\nهر خط یک قانون.\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    elif action == "rules_delete":
        await db.update_group(chat_id, rules_text="")
        await call.answer("قوانین حذف شد!")
        await _refresh_feature(call, "rules", chat_id)

    # ── ۴. آمار ──
    elif action == "stats":
        member_count = "?"
        try:
            m = await call.bot.get_chat_member_count(chat_id)
            member_count = m
        except Exception:
            pass
        text = (
            f"📊 <b>آمار گروه</b>\n\n"
            f"📝 نام: {title}\n"
            f"👥 اعضا: {member_count}\n"
            f"🆔 شناسه: <code>{chat_id}</code>\n"
            f"🚫 اسپم: {_onoff(settings.get('anti_spam', 1))}\n"
            f"⚠️ کلمات ممنوع: {_onoff(settings.get('anti_badwords', 1))}\n"
            f"🔒 ضد Flood: {_onoff(settings.get('anti_flood', 1))}\n"
            f"🤖 AI: {_onoff(settings.get('ai_reply', 0))}\n"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۵. فیلتر اسپم ──
    elif action == "spam":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('anti_spam', 1))}",
                callback_data=f"gp:spam_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = f"🚫 <b>فیلتر اسپم</b>\n\nوضعیت: {_onoff(settings.get('anti_spam', 1))}\n\nلینک‌های اسپم خودکار حذف میشن."
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "spam_toggle":
        new_val = _toggle(settings.get("anti_spam", 1))
        await db.update_group(chat_id, anti_spam=new_val)
        await call.answer(f"اسپم: {_onoff(new_val)}")
        await _refresh_feature(call, "spam", chat_id)

    # ── ۶. کلمات ممنوع ──
    elif action == "badwords":
        words = settings.get("badwords_list", "")
        word_list = words.split(",") if words else []
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('anti_badwords', 1))}",
                callback_data=f"gp:badwords_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="➕ اضافه کردن", callback_data=f"gp:badwords_add:{chat_id}")],
            [InlineKeyboardButton(text="➖ حذف کردن", callback_data=f"gp:badwords_remove:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"⚠️ <b>کلمات ممنوع</b>\n\n"
            f"وضعیت: {_onoff(settings.get('anti_badwords', 1))}\n"
            f"تعداد: {len(word_list)}\n"
            f"لیست: {', '.join(word_list[:20]) if word_list else '(خالی)'}"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "badwords_toggle":
        new_val = _toggle(settings.get("anti_badwords", 1))
        await db.update_group(chat_id, anti_badwords=new_val)
        await call.answer(f"کلمات ممنوع: {_onoff(new_val)}")
        await _refresh_feature(call, "badwords", chat_id)

    elif action == "badwords_add":
        _set_state(uid, {"action": "badwords_add", "chat_id": chat_id})
        await call.message.edit_text(
            "⚠️ کلمات ممنوع رو بنویس (با کاما جدا کن):\nمثال: فحش, بی‌احترامی, توهین\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    elif action == "badwords_remove":
        _set_state(uid, {"action": "badwords_remove", "chat_id": chat_id})
        await call.message.edit_text(
            "⚠️ کلمه‌ای که میخوای حذف کنی رو بنویس:\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    # ── ۷. پاسخ خودکار ──
    elif action == "autoreply":
        ar = json.loads(settings.get("auto_reply") or "{}")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ اضافه کردن", callback_data=f"gp:ar_add:{chat_id}")],
            [InlineKeyboardButton(text="➖ حذف کردن", callback_data=f"gp:ar_remove:{chat_id}")],
            [InlineKeyboardButton(text="📋 لیست", callback_data=f"gp:ar_list:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"💬 <b>پاسخ خودکار</b>\n\n"
            f"تعداد: {len(ar)}\n"
            f"وقتی کاربر کلمه‌ای بنویسه، ربات خودکار جواب بده."
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "ar_add":
        _set_state(uid, {"action": "ar_add_key", "chat_id": chat_id})
        await call.message.edit_text(
            "💬 کلمه/عبارت مورد نظر رو بنویس:\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    elif action == "ar_remove":
        _set_state(uid, {"action": "ar_remove", "chat_id": chat_id})
        await call.message.edit_text(
            "💬 کلمه‌ای که میخوای حذف کنی رو بنویس:\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    elif action == "ar_list":
        ar = json.loads(settings.get("auto_reply") or "{}")
        if not ar:
            text = "💬 لیست خالیه."
        else:
            lines = ["💬 <b>لیست پاسخ خودکار:</b>\n"]
            for k, v in list(ar.items())[:20]:
                lines.append(f"• <code>{k}</code> → {v[:40]}")
            text = "\n".join(lines)
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۸. حالت AI ──
    elif action == "ai":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('ai_reply', 0))}",
                callback_data=f"gp:ai_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"🤖 <b>حالت AI</b>\n\n"
            f"وضعیت: {_onoff(settings.get('ai_reply', 0))}\n\n"
            f"وقتی فعال باشه، ربات به پیام‌هایی که منشن بشه جواب هوشمند میده."
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "ai_toggle":
        new_val = _toggle(settings.get("ai_reply", 0))
        await db.update_group(chat_id, ai_reply=new_val)
        await call.answer(f"AI: {_onoff(new_val)}")
        await _refresh_feature(call, "ai", chat_id)

    # ── ۹. Slow Mode ──
    elif action == "slowmode":
        sm = settings.get("slow_mode", 0)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="۰ ثانیه (غیرفعال)", callback_data=f"gp:slowmode_set:{chat_id}:0")],
            [InlineKeyboardButton(text="۱۵ ثانیه", callback_data=f"gp:slowmode_set:{chat_id}:15")],
            [InlineKeyboardButton(text="۳۰ ثانیه", callback_data=f"gp:slowmode_set:{chat_id}:30")],
            [InlineKeyboardButton(text="۶۰ ثانیه", callback_data=f"gp:slowmode_set:{chat_id}:60")],
            [InlineKeyboardButton(text="۱۲۰ ثانیه", callback_data=f"gp:slowmode_set:{chat_id}:120")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = f"⏳ <b>Slow Mode</b>\n\nوضعیت فعلی: {sm} ثانیه"
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "slowmode_set":
        seconds = int(parts[3]) if len(parts) > 3 else 0
        await db.update_group(chat_id, slow_mode=seconds)
        await call.answer(f"Slow mode: {seconds} ثانیه")
        await _refresh_feature(call, "slowmode", chat_id)

    # ── ۱۰. ساعات سکوت ──
    elif action == "silent":
        ss = settings.get("silent_start", -1)
        se = settings.get("silent_end", -1)
        active = ss >= 0
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {'فعال ✅' if active else 'غیرفعال ❌'}",
                callback_data=f"gp:silent_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="⏰ تنظیم ساعت", callback_data=f"gp:silent_set:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"🔇 <b>ساعات سکوت</b>\n\n"
            f"وضعیت: {'فعال ✅' if active else 'غیرفعال ❌'}\n"
            f"ساعت: {ss}:00 تا {se}:00" if active else "ساعت: تنظیم نشده"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "silent_toggle":
        if settings.get("silent_start", -1) >= 0:
            await db.update_group(chat_id, silent_start=-1, silent_end=-1)
            await call.answer("سکوت غیرفعال شد")
        else:
            await db.update_group(chat_id, silent_start=23, silent_end=7)
            await call.answer("سکوت فعال شد (23-7)")
        await _refresh_feature(call, "silent", chat_id)

    elif action == "silent_set":
        _set_state(uid, {"action": "silent_hours", "chat_id": chat_id})
        await call.message.edit_text(
            "🔇 ساعت شروع و پایان سکوت رو بنویس:\n"
            "مثال: 23 7\n(یعنی از ساعت 23 تا 7 صبح)\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    # ── ۱۱. ضد Flood ──
    elif action == "flood":
        fl = settings.get("flood_limit", 5)
        fw = settings.get("flood_window", 10)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('anti_flood', 1))}",
                callback_data=f"gp:flood_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="⚙️ تنظیم", callback_data=f"gp:flood_set:{chat_id}")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"🔒 <b>ضد Flood</b>\n\n"
            f"وضعیت: {_onoff(settings.get('anti_flood', 1))}\n"
            f"حداکثر: {fl} پیام در {fw} ثانیه"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "flood_toggle":
        new_val = _toggle(settings.get("anti_flood", 1))
        await db.update_group(chat_id, anti_flood=new_val)
        await call.answer(f"ضد Flood: {_onoff(new_val)}")
        await _refresh_feature(call, "flood", chat_id)

    elif action == "flood_set":
        _set_state(uid, {"action": "flood_config", "chat_id": chat_id})
        await call.message.edit_text(
            "🔒 حداکثر پیام و بازه زمانی رو بنویس:\n"
            "مثال: 5 10\n(یعنی 5 پیام در 10 ثانیه)\nبرای بازگشت: /cancel",
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    # ── ۱۲. ترجمه خودکار ──
    elif action == "translate":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('auto_translate', 0))}",
                callback_data=f"gp:translate_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = (
            f"🔄 <b>ترجمه خودکار</b>\n\n"
            f"وضعیت: {_onoff(settings.get('auto_translate', 0))}\n\n"
            f"وقتی فعال باشه، پیام‌های انگلیسی خودکار به فارسی ترجمه میشن."
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "translate_toggle":
        new_val = _toggle(settings.get("auto_translate", 0))
        await db.update_group(chat_id, auto_translate=new_val)
        await call.answer(f"ترجمه: {_onoff(new_val)}")
        await _refresh_feature(call, "translate", chat_id)

    # ── ۱۳. پین خودکار ──
    elif action == "pin":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"وضعیت: {_onoff(settings.get('auto_pin', 0))}",
                callback_data=f"gp:pin_toggle:{chat_id}"
            )],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"gp:open:{chat_id}")]
        ])
        text = f"📌 <b>پین خودکار</b>\n\nوضعیت: {_onoff(settings.get('auto_pin', 0))}\n\nوقتی فعال باشه، پیام‌های مهم خودکار پین میشن."
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        await call.answer()

    elif action == "pin_toggle":
        new_val = _toggle(settings.get("auto_pin", 0))
        await db.update_group(chat_id, auto_pin=new_val)
        await call.answer(f"پین: {_onoff(new_val)}")
        await _refresh_feature(call, "pin", chat_id)

    # ── ۱۴. لاگ فعالیت ──
    elif action == "log":
        text = (
            f"📋 <b>لاگ فعالیت اخیر</b>\n\n"
            f"آخرین تنظیمات:\n"
            f"• اسپم: {_onoff(settings.get('anti_spam', 1))}\n"
            f"• کلمات ممنوع: {_onoff(settings.get('anti_badwords', 1))}\n"
            f"• ضد Flood: {_onoff(settings.get('anti_flood', 1))}\n"
            f"• AI: {_onoff(settings.get('ai_reply', 0))}\n"
            f"• ترجمه: {_onoff(settings.get('auto_translate', 0))}\n"
            f"• پین: {_onoff(settings.get('auto_pin', 0))}\n"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۱۵. ادمین‌ها ──
    elif action == "admins":
        try:
            admins = []
            async for member in call.bot.get_chat_administrators(chat_id):
                if not member.user.is_bot:
                    admins.append(f"• {member.user.full_name} ({member.status})")
            text = f"🛡️ <b>ادمین‌های گروه:</b>\n\n" + "\n".join(admins) if admins else "ادمینی پیدا نشد."
        except Exception:
            text = "❌ نتونستم لیست ادمین‌ها رو بگیرم."
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۱۶. نام گروه ──
    elif action == "rename":
        _set_state(uid, {"action": "rename", "chat_id": chat_id})
        await call.message.edit_text(
            f"🏷️ نام فعلی: <b>{title}</b>\n\nنام جدید رو بنویس:\nبرای بازگشت: /cancel",
            parse_mode=ParseMode.HTML,
            reply_markup=_back_kb(chat_id)
        )
        await call.answer()

    # ── ۱۷. بکاپ ──
    elif action == "backup":
        settings = await db.get_group_settings(chat_id)
        backup = json.dumps(settings, ensure_ascii=False, indent=2)
        text = (
            f"💾 <b>بکاپ تنظیمات</b>\n\n"
            f"<code>{backup[:1500]}</code>\n\n"
            f"این تنظیمات رو ذخیره کن تا بعداً بازیابی کنی."
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۱۸. اعلان‌ها ──
    elif action == "notif":
        text = (
            f"🔔 <b>تنظیمات اعلان‌ها</b>\n\n"
            f"اعلان‌ها به ادمین‌ها ارسال میشه:\n"
            f"• هنگام اسپم\n"
            f"• هنگام فیلتر کلمات\n"
            f"• هنگام Flood\n"
            f"• عضویت/خروج اعضا"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۱۹. زمان‌بندی ──
    elif action == "schedule":
        text = (
            f"⏰ <b>زمان‌بندی پیام</b>\n\n"
            f"برای ارسال خودکار پیام در ساعت مشخص:\n"
            f"از دستور /schedule استفاده کن.\n\n"
            f"مثال: /schedule 09:00 سلام روز بخیر"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    # ── ۲۰. نمودار ──
    elif action == "chart":
        try:
            member_count = await call.bot.get_chat_member_count(chat_id)
        except Exception:
            member_count = "?"
        text = (
            f"📊 <b>نمودار فعالیت</b>\n\n"
            f"👥 اعضا: {member_count}\n"
            f"🤖 AI: {_onoff(settings.get('ai_reply', 0))}\n"
            f"🚫 اسپم: {_onoff(settings.get('anti_spam', 1))}\n"
            f"💬 پاسخ خودکار: {len(json.loads(settings.get('auto_reply', '{}')))} عدد\n"
        )
        await call.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_kb(chat_id))
        await call.answer()

    else:
        await call.answer()


# ─────────────────────────────────────────────
#  پردازش ورودی کاربر
# ─────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    uid = message.from_user.id
    _clean_state(uid)
    await message.answer("لغو شد. ✅")


def _has_panel_state(message: Message) -> bool:
    return _get_state(message.from_user.id) is not None


@router.message(F.text & ~F.text.startswith("/"), _has_panel_state)
async def handle_input(message: Message):
    uid = message.from_user.id
    state = _get_state(uid)

    action = state["action"]
    chat_id = state["chat_id"]
    text = message.text.strip()

    if action == "welcome_text":
        await db.update_group(chat_id, welcome_text=text)
        _clean_state(uid)
        await message.answer("✅ متن خوش‌آمد ذخیره شد!")

    elif action == "goodbye_text":
        await db.update_group(chat_id, goodbye_text=text)
        _clean_state(uid)
        await message.answer("✅ متن وداع ذخیره شد!")

    elif action == "rules_text":
        await db.update_group(chat_id, rules_text=text)
        _clean_state(uid)
        await message.answer("✅ قوانین ذخیره شد!")

    elif action == "badwords_add":
        settings = await db.get_group_settings(chat_id)
        existing = settings.get("badwords_list", "")
        new_words = [w.strip() for w in text.split(",") if w.strip()]
        all_words = list(set(existing.split(",") + new_words)) if existing else new_words
        await db.update_group(chat_id, badwords_list=",".join(all_words))
        _clean_state(uid)
        await message.answer(f"✅ {len(new_words)} کلمه اضافه شد! (کل: {len(all_words)})")

    elif action == "badwords_remove":
        settings = await db.get_group_settings(chat_id)
        existing = settings.get("badwords_list", "")
        if existing:
            words = [w.strip() for w in existing.split(",") if w.strip() and w.strip() != text]
            await db.update_group(chat_id, badwords_list=",".join(words))
        _clean_state(uid)
        await message.answer(f"✅ کلمه '{text}' حذف شد!")

    elif action == "ar_add_key":
        _set_state(uid, {"action": "ar_add_val", "chat_id": chat_id, "key": text})
        await message.answer(f"💬 حالا جواب '{text}' رو بنویس:")

    elif action == "ar_add_val":
        settings = await db.get_group_settings(chat_id)
        ar = json.loads(settings.get("auto_reply") or "{}")
        ar[state["key"]] = text
        await db.update_group(chat_id, auto_reply=json.dumps(ar, ensure_ascii=False))
        _clean_state(uid)
        await message.answer(f"✅ پاسخ خودکار ذخیره شد: '{state['key']}' → '{text}'")

    elif action == "ar_remove":
        settings = await db.get_group_settings(chat_id)
        ar = json.loads(settings.get("auto_reply") or "{}")
        if text in ar:
            del ar[text]
            await db.update_group(chat_id, auto_reply=json.dumps(ar, ensure_ascii=False))
            _clean_state(uid)
            await message.answer(f"✅ '{text}' حذف شد!")
        else:
            await message.answer(f"❌ '{text}' پیدا نشد.")

    elif action == "silent_hours":
        parts = text.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            start = int(parts[0])
            end = int(parts[1])
            if 0 <= start <= 23 and 0 <= end <= 23:
                await db.update_group(chat_id, silent_start=start, silent_end=end)
                _clean_state(uid)
                await message.answer(f"✅ ساعات سکوت: {start}:00 تا {end}:00")
            else:
                await message.answer("❌ ساعت باید بین 0 تا 23 باشه.")
        else:
            await message.answer("❌ فرمت اشتباه. مثال: 23 7")

    elif action == "flood_config":
        parts = text.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            limit = int(parts[0])
            window = int(parts[1])
            if 1 <= limit <= 100 and 1 <= window <= 300:
                await db.update_group(chat_id, flood_limit=limit, flood_window=window)
                _clean_state(uid)
                await message.answer(f"✅ ضد Flood: {limit} پیام در {window} ثانیه")
            else:
                await message.answer("❌ مقادیر نامعتبر.")
        else:
            await message.answer("❌ فرمت اشتباه. مثال: 5 10")

    elif action == "rename":
        if len(text) < 2 or len(text) > 100:
            await message.answer("❌ نام باید بین 2 تا 100 کاراکتر باشه.")
        else:
            await db.update_group(chat_id, title=text)
            _clean_state(uid)
            await message.answer(f"✅ نام گروه به '{text}' تغییر کرد!")
