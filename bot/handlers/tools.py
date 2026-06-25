"""۲۰ ابزار کاربردی — QR، رمز عبور، تبدیل ارز، ماشین حساب و غیره."""
import asyncio
import hashlib
import io
import json
import logging
import math
import random
import re
import secrets
import string
import struct
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone

import aiohttp
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from .. import config, database as db
from ..ttl_dict import TTLDict

router = Router()
log = logging.getLogger("kaysan.tools")


async def _safe_edit_or_answer(msg, text, **kwargs):
    try:
        await msg.edit_text(text, **kwargs)
    except Exception:
        try:
            await msg.answer(text, **kwargs)
        except Exception:
            pass


# ── state برای ورودی‌ها ──
_tool_state = TTLDict(ttl_seconds=120, max_size=500)


def _clean(uid: int):
    _tool_state.pop(uid, None)


def _set(uid: int, s: dict):
    _tool_state[uid] = s


def _get(uid: int) -> dict | None:
    return _tool_state.get(uid)


# ─────────────────────────────────────────────
#  ۱. QR Code — ساخت بارکد
# ─────────────────────────────────────────────

@router.message(Command("qr"))
async def cmd_qr(message: Message):
    uid = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("بکارهێنان: /qr متن یا لینک\nمثال: /qr https://google.com")
        return

    text = parts[1].strip()
    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        await message.answer_photo(
            BufferedInputFile(buf.read(), filename="qr.png"),
            caption=f"🔲 QR Code برای:\n<code>{text[:100]}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.warning("qr failed: %s", e)
        await message.answer("❌ نتونستم QR Code بسازم.")


# ─────────────────────────────────────────────
#  ۲. لینک کوتاه
# ─────────────────────────────────────────────

@router.message(Command("short"))
async def cmd_short(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("بکارهێنان: /short https://example.com/long-url")
        return

    url = parts[1].strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://api.tinyurl.com/create",
                params={"url": url, "domain": "t.ly"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    short = data.get("data", {}).get("tiny_url", "")
                    if short:
                        await message.answer(f"🔗 لینک کوتاه:\n<code>{short}</code>", parse_mode=ParseMode.HTML)
                        return

        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://is.gd/create.php",
                params={"format": "json", "url": url},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    short = data.get("shorturl", "")
                    if short:
                        await message.answer(f"🔗 لینک کوتاه:\n<code>{short}</code>", parse_mode=ParseMode.HTML)
                        return

        await message.answer("❌ نتونستم لینک رو کوتاه کنم.")
    except Exception as e:
        log.warning("short url failed: %s", e)
        await message.answer("❌ خطا در کوتاه کردن لینک.")


# ─────────────────────────────────────────────
#  ۳. اسکرینشات سایت
# ─────────────────────────────────────────────

@router.message(Command("screenshot"))
async def cmd_screenshot(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("بکارهێنان: /screenshot https://example.com")
        return

    url = parts[1].strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    status = await message.answer("📸 در حال گرفتن اسکرینشات...")
    try:
        api_url = f"https://image.thum.io/get/width/1200/crop/800/{url}"
        async with aiohttp.ClientSession() as s:
            async with s.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                if r.status == 200:
                    data = await r.read()
                    if len(data) > 5000:
                        try:
                            await status.delete()
                        except Exception:
                            pass
                        await message.answer_photo(
                            BufferedInputFile(data, filename="screenshot.png"),
                            caption=f"📸 اسکرینشات:\n<code>{url[:100]}</code>",
                            parse_mode=ParseMode.HTML,
                        )
                        return
        await _safe_edit_or_answer(status, "❌ نتونستم اسکرینشات بگیرم.")
    except Exception as e:
        log.warning("screenshot failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در گرفتن اسکرینشات.")


# ─────────────────────────────────────────────
#  ۴. شناسایی آهنگ (ساده — از متن)
# ─────────────────────────────────────────────

@router.message(Command("whatisthissong"))
async def cmd_what_song(message: Message):
    await message.answer(
        "🎵 <b>شناسایی آهنگ</b>\n\n"
        "تکمیل نشده — نیاز به API تخصصی داره.\n"
        "به‌زودی اضافه میشه!",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────
#  ۵. تبدیل ارز
# ─────────────────────────────────────────────

@router.message(Command("exchange"))
async def cmd_exchange(message: Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer(
            "بکارهێنان: /exchange <مقدار> <از> <به>\n"
            "مثال: /exchange 100 USD IRR\n"
            "ارزها: USD, EUR, IRR, TRY, GBP, KWD"
        )
        return

    try:
        amount = float(parts[1])
        from_cur = parts[2].upper()
        to_cur = parts[3].upper()
    except ValueError:
        await message.answer("❌ مقدار نامعتبر.")
        return

    status = await message.answer("💱 در حال دریافت نرخ...")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://api.exchangerate-api.com/v4/latest/{from_cur}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                if r.status != 200:
                    await _safe_edit_or_answer(status, "❌ نتونستم نرخ ارز رو بگیرم.")
                    return
                data = await r.json()
                rates = data.get("rates", {})
                rate = rates.get(to_cur)
                if not rate:
                    await _safe_edit_or_answer(status, f"❌ ارز {to_cur} پیدا نشد.")
                    return

                result = amount * rate
                await _safe_edit_or_answer(status, 
                    f"💱 <b>تبدیل ارز</b>\n\n"
                    f"{amount:,.2f} {from_cur} = {result:,.2f} {to_cur}\n"
                    f"نرخ: 1 {from_cur} = {rate:,.6f} {to_cur}",
                    parse_mode=ParseMode.HTML,
                )
    except Exception as e:
        log.warning("exchange failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در دریافت نرخ ارز.")


# ─────────────────────────────────────────────
#  ۶. قیمت بورس
# ─────────────────────────────────────────────

@router.message(Command("stock"))
async def cmd_stock(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /stock AAPL\n"
            "مثال: /stock TSLA, /stock BTC"
        )
        return

    symbol = parts[1].upper()
    status = await message.answer("📈 در حال دریافت قیمت...")

    try:
        async with aiohttp.ClientSession() as s:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    await _safe_edit_or_answer(status, f"❌ نماد {symbol} پیدا نشد.")
                    return
                data = await r.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                price = meta.get("regularMarketPrice", 0)
                prev = meta.get("previousClose", 0)
                change = price - prev if prev else 0
                change_pct = (change / prev * 100) if prev else 0
                arrow = "🟢" if change >= 0 else "🔴"

                await _safe_edit_or_answer(status, 
                    f"📈 <b>{symbol}</b>\n\n"
                    f"قیمت: ${price:,.2f}\n"
                    f"تغییر: {arrow} {change:+,.2f} ({change_pct:+.2f}%)\n"
                    f"دیروز: ${prev:,.2f}",
                    parse_mode=ParseMode.HTML,
                )
    except Exception as e:
        log.warning("stock failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در دریافت قیمت سهام.")


# ─────────────────────────────────────────────
#  ۷. ساخت رمز عبور
# ─────────────────────────────────────────────

@router.message(Command("password"))
async def cmd_password(message: Message):
    parts = message.text.split()
    length = 16
    if len(parts) >= 2 and parts[1].isdigit():
        length = min(max(int(parts[1]), 8), 64)

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))

    strength = "ضعیف ❌" if length < 10 else "متوسط 🟡" if length < 14 else "قوی 🟢" if length < 20 else "بسیار قوی 💪"

    await message.answer(
        f"🔑 <b>رمز عبور تصادفی</b>\n\n"
        f"<code>{password}</code>\n\n"
        f"طول: {length} کاراکتر\n"
        f"قدرت: {strength}",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────
#  ۸. متن به عکس
# ─────────────────────────────────────────────

@router.message(Command("text2img"))
async def cmd_text2img(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("بکارهێنان: /text2img متن مورد نظر")
        return

    text = parts[1].strip()
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (800, 400), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

        lines = []
        words = text.split()
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if draw.textlength(test, font=font) < 740:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)

        y = 50
        for l in lines[:10]:
            draw.text((30, y), l, fill=(255, 255, 255), font=font)
            y += 40

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        await message.answer_photo(
            BufferedInputFile(buf.read(), filename="text.png"),
            caption="📝 متن تبدیل شده به عکس",
        )
    except Exception as e:
        log.warning("text2img failed: %s", e)
        await message.answer("❌ خطا در ساخت عکس.")


# ─────────────────────────────────────────────
#  ۹. ماشین حساب
# ─────────────────────────────────────────────

@router.message(Command("calc"))
async def cmd_calc(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /calc 2+2*3\n"
            "پشتیبانی: +, -, *, /, //, %, **, sqrt(), sin(), cos(), pi"
        )
        return

    expr = parts[1].strip()

    if not re.match(r'^[\d\s\+\-\*/%\.\(\),a-zA-Z]+$', expr):
        await message.answer("❌ عبارت نامعتبر.")
        return

    try:
        result = _safe_calc(expr)
        await message.answer(
            f"🧮 <b>ماشین حساب</b>\n\n"
            f"<code>{expr}</code>\n"
            f"= <b>{result}</b>",
            parse_mode=ParseMode.HTML,
        )
    except ZeroDivisionError:
        await message.answer("❌ تقسیم بر صفر!")
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)[:100]}")


def _safe_calc(expr: str):
    """محاسبه امن ریاضی بدون eval."""
    import ast as _ast
    import operator as _op

    _OPS = {
        _ast.Add: _op.add, _ast.Sub: _op.sub, _ast.Mult: _op.mul,
        _ast.Div: _op.truediv, _ast.FloorDiv: _op.floordiv,
        _ast.Mod: _op.mod, _ast.Pow: _op.pow, _ast.USub: _op.neg,
        _ast.UAdd: _op.pos,
    }

    _FUNCS = {
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
        "tan": math.tan, "log": math.log, "log10": math.log10,
        "abs": abs, "round": round, "ceil": math.ceil, "floor": math.floor,
    }

    _CONSTS = {"pi": math.pi, "e": math.e}

    def _eval(node):
        if isinstance(node, _ast.Expression):
            return _eval(node.body)
        if isinstance(node, _ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"نوع ثابت نامعتبر: {type(node.value)}")
        if isinstance(node, _ast.BinOp):
            op_type = type(node.op)
            if op_type not in _OPS:
                raise ValueError(f"عملگر پشتیبانی نمیشه: {op_type.__name__}")
            left = _eval(node.left)
            right = _eval(node.right)
            if op_type in (_ast.Div, _ast.FloorDiv) and right == 0:
                raise ZeroDivisionError("تقسیم بر صفر")
            return _OPS[op_type](left, right)
        if isinstance(node, _ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _OPS:
                raise ValueError(f"عملگر پشتیبانی نمیشه: {op_type.__name__}")
            return _OPS[op_type](_eval(node.operand))
        if isinstance(node, _ast.Call):
            if not isinstance(node.func, _ast.Name):
                raise ValueError("فقط توابع ساده پشتیبانی میشن")
            func_name = node.func.id
            if func_name not in _FUNCS:
                raise ValueError(f"تابع نامعتبر: {func_name}")
            args = [_eval(a) for a in node.args]
            return _FUNCS[func_name](*args)
        if isinstance(node, _ast.Name):
            if node.id in _CONSTS:
                return _CONSTS[node.id]
            raise ValueError(f"متغیر نامعتبر: {node.id}")
        raise ValueError(f"نوع عبارت پشتیبانی نمیشه: {type(node).__name__}")

    tree = _ast.parse(expr, mode="eval")
    return _eval(tree)


# ─────────────────────────────────────────────
#  ۱۰. میم ساز
# ─────────────────────────────────────────────

@router.message(Command("meme"))
async def cmd_meme(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /meme متن بالا | متن پایین\n"
            "مثال: /meme زندگی خوبه | واقعاً؟"
        )
        return

    text = parts[1]
    if "|" in text:
        top, bottom = text.split("|", 1)
        top, bottom = top.strip(), bottom.strip()
    else:
        top, bottom = text.strip(), ""

    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (600, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        except Exception:
            font = ImageFont.load_default()

        draw.text((300 - draw.textlength(top, font=font) // 2, 20), top.upper(), fill=(0, 0, 0), font=font)
        draw.text((300 - draw.textlength(bottom, font=font) // 2, 350), bottom.upper(), fill=(0, 0, 0), font=font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        await message.answer_photo(
            BufferedInputFile(buf.read(), filename="meme.png"),
            caption="📸 میم شما!",
        )
    except Exception as e:
        log.warning("meme failed: %s", e)
        await message.answer("❌ خطا در ساخت میم.")


# ─────────────────────────────────────────────
#  ۱۱. فاکتور
# ─────────────────────────────────────────────

_invoice_state = TTLDict(ttl_seconds=600, max_size=500)


@router.message(Command("invoice"))
async def cmd_invoice(message: Message):
    uid = message.from_user.id
    _invoice_state[uid] = []
    await message.answer(
        "🧾 <b>ساخت فاکتور</b>\n\n"
        "آیتم‌ها رو خط به خط بنویس:\n"
        "<code>نام | قیمت | تعداد</code>\n\n"
        "مثال:\nشیر 10000 | 3\nنان 5000 | 2\n\n"
        "وقتی تموم شد /done بزن.",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("done"))
async def cmd_done(message: Message):
    uid = message.from_user.id
    items = _invoice_state.pop(uid, None)
    if not items:
        await message.answer("❌ آیتمی ثبت نشده.")
        return

    total = sum(p * q for _, p, q in items)
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (500, 300 + len(items) * 35), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except Exception:
            font = ImageFont.load_default()

        y = 20
        draw.text((200, y), "INVOICE", fill=(0, 0, 0), font=font)
        y += 40
        draw.line([(20, y), (480, y)], fill=(0, 0, 0), width=2)
        y += 15

        for name, price, qty in items:
            line_total = price * qty
            draw.text((20, y), f"{name}", fill=(0, 0, 0), font=font)
            draw.text((350, y), f"{line_total:,.0f}", fill=(0, 0, 0), font=font)
            y += 35

        draw.line([(20, y), (480, y)], fill=(0, 0, 0), width=2)
        y += 10
        draw.text((20, y), f"TOTAL: {total:,.0f}", fill=(0, 0, 0), font=font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        await message.answer_photo(
            BufferedInputFile(buf.read(), filename="invoice.png"),
            caption=f"🧾 فاکتور — مبلغ کل: {total:,.0f}",
        )
    except Exception as e:
        log.warning("invoice failed: %s", e)
        await message.answer(f"❌ خطا: {e}")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_invoice_input(message: Message):
    uid = message.from_user.id
    if uid not in _invoice_state:
        return

    text = message.text.strip()
    if not text:
        return

    parts = text.split("|")
    if len(parts) < 2:
        await message.answer("فرمت: نام | قیمت | تعداد (تعداد اختیاری)")
        return

    name = parts[0].strip()
    try:
        price = int(parts[1].strip())
        qty = int(parts[2].strip()) if len(parts) > 2 else 1
    except ValueError:
        await message.answer("❌ قیمت و تعداد باید عدد باشن.")
        return

    _invoice_state[uid].append((name, price, qty))
    await message.answer(f"✅ {name} × {qty} = {price * qty:,.0f}\nآیتم بعدی یا /done")


# ─────────────────────────────────────────────
#  ۱۲. فلش کارت
# ─────────────────────────────────────────────

_flash_cards = TTLDict(ttl_seconds=3600, max_size=500)
_flash_idx = TTLDict(ttl_seconds=3600, max_size=500)


@router.message(Command("flashcard"))
async def cmd_flashcard(message: Message):
    parts = message.text.split(maxsplit=1)
    uid = message.from_user.id

    if len(parts) < 2:
        await message.answer(
            "بکارهێنان:\n"
            "/flashcard add سؤال | جواب\n"
            "/flashcard start\n"
            "/flashcard next\n"
            "/flashcard show"
        )
        return

    sub = parts[1].strip()
    if sub.startswith("add"):
        content = sub[4:].strip()
        if "|" not in content:
            await message.answer("فرمت: /flashcard add سؤال | جواب")
            return
        q, a = content.split("|", 1)
        if uid not in _flash_cards:
            _flash_cards[uid] = []
        _flash_cards[uid].append({"q": q.strip(), "a": a.strip(), "score": 0})
        await message.answer(f"✅ کارت اضافه شد! (کل: {len(_flash_cards[uid])})")

    elif sub.startswith("start"):
        cards = _flash_cards.get(uid, [])
        if not cards:
            await message.answer("❌ هنوز کارتی نداری.")
            return
        _flash_idx[uid] = 0
        card = cards[0]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 نشون بده", callback_data="fc:show")]
        ])
        await message.answer(
            f"📚 <b>کارت 1/{len(cards)}</b>\n\n❓ {card['q']}",
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )

    elif sub.startswith("next"):
        cards = _flash_cards.get(uid, [])
        idx = _flash_idx.get(uid, 0) + 1
        if idx >= len(cards):
            await message.answer("🎉 تموم شد! دوباره /flashcard start بزن.")
            return
        _flash_idx[uid] = idx
        card = cards[idx]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 نشون بده", callback_data="fc:show")]
        ])
        await message.answer(
            f"📚 <b>کارت {idx+1}/{len(cards)}</b>\n\n❓ {card['q']}",
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )

    elif sub.startswith("show"):
        cards = _flash_cards.get(uid, [])
        idx = _flash_idx.get(uid, 0)
        if not cards or idx >= len(cards):
            await message.answer("❌ کارتی نیست.")
            return
        card = cards[idx]
        await message.answer(f"💡 <b>جواب:</b> {card['a']}", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "fc:show")
async def cb_flashcard_show(call: CallbackQuery):
    uid = call.from_user.id
    cards = _flash_cards.get(uid, [])
    idx = _flash_idx.get(uid, 0)
    if not cards or idx >= len(cards):
        await call.answer("کارتی نیست!")
        return
    card = cards[idx]
    await call.answer(f"💡 {card['a']}", show_alert=True)


# ─────────────────────────────────────────────
#  ۱۳. پیگیری عادت‌ها
# ─────────────────────────────────────────────

_habits = TTLDict(ttl_seconds=3600, max_size=500)


@router.message(Command("habit"))
async def cmd_habit(message: Message):
    uid = message.from_user.id
    parts = message.text.split(maxsplit=1)

    if uid not in _habits:
        _habits[uid] = {}

    if len(parts) < 2:
        habits = _habits[uid]
        if not habits:
            await message.answer("بکارهێنان:\n/habit add ورزش\n/habit done ورزش\n/habit list")
            return
        lines = ["✅ <b>عادت‌های امروز:</b>\n"]
        for name, count in habits.items():
            status = "✅" if count > 0 else "❌"
            lines.append(f"{status} {name}: {count} بار")
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    sub = parts[1].strip()
    if sub.startswith("add"):
        name = sub[4:].strip()
        if name:
            _habits[uid][name] = 0
            await message.answer(f"✅ عادت '{name}' اضافه شد!")
        else:
            await message.answer("❌ نام عادت رو بنویس.")

    elif sub.startswith("done"):
        name = sub[5:].strip()
        if name in _habits[uid]:
            _habits[uid][name] += 1
            await message.answer(f"✅ '{name}' انجام شد! ({_habits[uid][name]} بار)")
        else:
            await message.answer(f"❌ عادت '{name}' پیدا نشد.")

    elif sub.startswith("list"):
        habits = _habits.get(uid, {})
        if not habits:
            await message.answer("✅ هنوز عادتی ثبت نشده.")
            return
        lines = ["✅ <b>عادت‌های امروز:</b>\n"]
        for name, count in habits.items():
            status = "✅" if count > 0 else "❌"
            lines.append(f"{status} {name}: {count} بار")
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)


# ─────────────────────────────────────────────
#  ۱۴. ثبت هزینه‌ها
# ─────────────────────────────────────────────

_expenses = TTLDict(ttl_seconds=3600, max_size=500)


@router.message(Command("expense"))
async def cmd_expense(message: Message):
    uid = message.from_user.id
    parts = message.text.split(maxsplit=1)

    if uid not in _expenses:
        _expenses[uid] = []

    if len(parts) < 2:
        exps = _expenses[uid]
        if not exps:
            await message.answer("بکارهێنان:\n/expense 50000 ناهار\n/expense list\n/expense total")
            return
        lines = ["💰 <b>هزینه‌های امروز:</b>\n"]
        total = 0
        for amt, desc in exps[-10:]:
            lines.append(f"• {desc}: {amt:,.0f}")
            total += amt
        lines.append(f"\nجمع: {total:,.0f}")
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    sub = parts[1].strip()
    if sub == "list":
        exps = _expenses.get(uid, [])
        if not exps:
            await message.answer("💰 هنوز هزینه‌ای ثبت نشده.")
            return
        lines = ["💰 <b>هزینه‌های امروز:</b>\n"]
        total = 0
        for amt, desc in exps[-10:]:
            lines.append(f"• {desc}: {amt:,.0f}")
            total += amt
        lines.append(f"\nجمع: {total:,.0f}")
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    if sub == "total":
        total = sum(a for a, _ in _expenses.get(uid, []))
        await message.answer(f"💰 جمع کل: {total:,.0f}")
        return

    sp = sub.split()
    if len(sp) < 1:
        await message.answer("فرمت: /expense <مقدار> <توضیح>")
        return
    try:
        amount = int(sp[0])
        desc = " ".join(sp[1:]) if len(sp) > 1 else "سایر"
    except ValueError:
        await message.answer("❌ مقدار باید عدد باشه.")
        return

    _expenses[uid].append((amount, desc))
    total = sum(a for a, _ in _expenses[uid])
    await message.answer(f"✅ {desc}: {amount:,.0f}\nجمع امروز: {total:,.0f}")


# ─────────────────────────────────────────────
#  ۱۵. برنامه سفر
# ─────────────────────────────────────────────

@router.message(Command("travel"))
async def cmd_travel(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /travel مقصد\n"
            "مثال: /travel اصفهان"
        )
        return

    dest = parts[1].strip()
    status = await message.answer("✈️ دارم برنامه سفر می‌سازم...")
    try:
        from bot import openrouter
        system = (
            f"You are a travel planner. Create a 3-day travel plan for {dest}. "
            "Reply in Persian. Include: morning, afternoon, evening activities. "
            "Be concise and practical."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Plan a 3-day trip to {dest}"},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=1500),
            timeout=30,
        )
        await _safe_edit_or_answer(status, f"✈️ <b>برنامه سفر {dest}:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("travel failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در ساخت برنامه سفر.")


# ─────────────────────────────────────────────
#  ۱۶. دستور غذا
# ─────────────────────────────────────────────

@router.message(Command("recipe"))
async def cmd_recipe(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /recipe مواد موجود\n"
            "مثال: /recipe مرغ، برنج، پیاز"
        )
        return

    ingredients = parts[1].strip()
    status = await message.answer("🍳 دارم دستور غذا پیدا می‌کنم...")
    try:
        from bot import openrouter
        system = (
            "You are a chef. Suggest 2-3 recipes using the given ingredients. "
            "Reply in Persian. For each recipe include: name, ingredients, steps. Be concise."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ingredients: {ingredients}"},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=1000),
            timeout=20,
        )
        await _safe_edit_or_answer(status, f"🍳 <b>دستور غذا:</b>\n\n{reply}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("recipe failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در پیدا کردن دستور غذا.")


# ─────────────────────────────────────────────
#  ۱۷. خلاصه اخبار
# ─────────────────────────────────────────────

@router.message(Command("news"))
async def cmd_news(message: Message):
    parts = message.text.split(maxsplit=1)
    topic = parts[1].strip() if len(parts) > 1 else "today"
    status = await message.answer("📰 دارم اخبار رو جمع‌آوری می‌کنم...")
    try:
        from bot.handlers.search import web_search, google_news_search
        news = await google_news_search(f"{topic} news", max_results=5)
        web = await web_search(f"{topic} latest news", max_results=3)

        lines = [f"📰 <b>خلاصه اخبار {topic}:</b>\n"]
        if news:
            for i, n in enumerate(news[:5], 1):
                lines.append(f"{i}. {n['title'][:80]}")
                lines.append(f"   {n['text'][:120]}\n")
        if web:
            lines.append("\n🌐 <b>منابع وب:</b>")
            for w in web[:3]:
                lines.append(f"• {w['title'][:60]}")

        await _safe_edit_or_answer(status, "\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("news failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در دریافت اخبار.")


# ─────────────────────────────────────────────
#  ۱۸. چالش روزانه
# ─────────────────────────────────────────────

@router.message(Command("challenge"))
async def cmd_challenge(message: Message):
    uid = message.from_user.id
    lang = await db.get_lang(uid)
    status = await message.answer("🎯 دارم چالش روزانه می‌سازم...")
    try:
        from bot import openrouter
        system = (
            "You are a fun challenge generator. Create ONE interesting daily challenge. "
            "Reply in the user's language. Be creative and motivating. "
            "Include: challenge name, description, difficulty (easy/medium/hard)."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "Give me today's challenge"},
        ]
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=300),
            timeout=15,
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ انجام دادم!", callback_data="challenge_done")],
            [InlineKeyboardButton(text="⏭️ چالش بعدی", callback_data="challenge_next")],
        ])
        await _safe_edit_or_answer(status, f"🎯 <b>چالش روزانه:</b>\n\n{reply}", parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        log.warning("challenge failed: %s", e)
        await _safe_edit_or_answer(status, "❌ خطا در ساخت چالش.")


@router.callback_query(F.data == "challenge_done")
async def cb_challenge_done(call: CallbackQuery):
    await call.answer("آفرین! 🎉 ادامه بده!", show_alert=True)


@router.callback_query(F.data == "challenge_next")
async def cb_challenge_next(call: CallbackQuery):
    await call.answer()
    await cmd_challenge(call.message)


# ─────────────────────────────────────────────
#  ۱۹. نظرسنجی پیشرفته
# ─────────────────────────────────────────────

@router.message(Command("advancedpoll"))
async def cmd_advanced_poll(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "بکارهێنان: /advancedpoll عنوان | گزینه۱, گزینه۲, گزینه۳\n"
            "مثال: /advancedpoll بهترین شهر | تهران, اصفهان, شیراز"
        )
        return

    text = parts[1]
    if "|" not in text:
        await message.answer("❌ فرمت: عنوان | گزینه۱, گزینه۲")
        return

    title, options_str = text.split("|", 1)
    options = [o.strip() for o in options_str.split(",") if o.strip()]

    if len(options) < 2 or len(options) > 10:
        await message.answer("❌ تعداد گزینه باید بین 2 تا 10 باشه.")
        return

    await message.answer_poll(
        question=title.strip(),
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False,
    )


# ─────────────────────────────────────────────
#  ۲۰. بازی حدس عدد
# ─────────────────────────────────────────────

_guess_games = TTLDict(ttl_seconds=120, max_size=500)


@router.message(Command("guess"))
async def cmd_guess(message: Message):
    uid = message.from_user.id
    target = random.randint(1, 100)
    _guess_games[uid] = {"target": target, "tries": 0, "max": 7}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(n), callback_data=f"guess:{n}")]
        for n in range(1, 10)
    ] + [
        [InlineKeyboardButton(text=str(n), callback_data=f"guess:{n}")]
        for n in range(10, 20)
    ])

    await message.answer(
        "🎮 <b>بازی حدس عدد</b>\n\n"
        "یه عدد بین ۱ تا ۱۰۰ حدس بزن!\n"
        "۷ بار فرصت داری.\n\n"
        "عدد رو بنویس یا از دکمه‌ها استفاده کن.",
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("guess:"))
async def cb_guess(call: CallbackQuery):
    uid = call.from_user.id
    game = _guess_games.get(uid)
    if not game:
        await call.answer("بازی شروع نشده! /guess", show_alert=True)
        return

    num = int(call.data.split(":")[1])
    game["tries"] += 1
    target = game["target"]

    if num == target:
        del _guess_games[uid]
        await call.message.edit_text(
            f"🎉 <b>آفرین!</b>\n\n"
            f"عدد {num} درست بود!\n"
            f"تعداد تلاش: {game['tries']}/{game['max']}",
            parse_mode=ParseMode.HTML,
        )
        await call.answer("بردی! 🎉", show_alert=True)
    elif game["tries"] >= game["max"]:
        del _guess_games[uid]
        await call.message.edit_text(
            f"😔 <b>باختی!</b>\n\n"
            f"عدد {target} بود.\n"
            f"تعداد تلاش: {game['tries']}/{game['max']}",
            parse_mode=ParseMode.HTML,
        )
        await call.answer("باختی! 😔", show_alert=True)
    else:
        remaining = game["max"] - game["tries"]
        hint = "بیشتره 📈" if num < target else "کمتره 📉"
        await call.answer(f"{hint} | {remaining} بار مونده")
