"""هسته‌ی پردازش: streaming، context management، quality check."""
import logging
import re
import asyncio
import random
import time

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter, router
from ..keyboards import answer_kb, limit_kb
from ..services import image as image_svc
from ..texts import IDENTITY_REPLY, SYSTEM_PROMPTS, t
from .. import upgrade_chat
from ..prompt_enhancer import enhance_prompt
from ..ttl_dict import TTLDict

log = logging.getLogger("kaysan.core")

_last = TTLDict(ttl_seconds=3600, max_size=5000)
_animation_stopped = TTLDict(ttl_seconds=60, max_size=500)

_LANG_NAMES = {
    "ku": "Kurdish Sorani (کوردی سۆرانی)",
    "fa": "Persian (فارسی)",
    "en": "English",
}

_ANIMATIONS = [
    ["⬜⬜⬜⬜⬜\n⏳ دارم فکر می‌کنم...", "🟦⬜⬜⬜⬜\n⏳ دارم فکر می‌کنم...",
     "🟦🟦⬜⬜⬜\n⏳ دارم فکر می‌کنم...", "🟦🟦🟦🟦⬜\n⏳ دارم فکر می‌کنم...",
     "🟦🟦🟦🟦🟦\n⏳ دارم فکر می‌کنم...", "🟦🟦🟦🟦🟦\n✅ جواب آماده‌ست!"],
    ["🔄\n⏳ دارم فکر می‌کنم...", "🔄🔄\n⏳ دارم فکر می‌کنم...",
     "🔄🔄🔄\n⏳ دارم فکر می‌کنم...", "🔄🔄🔄🔄\n⏳ دارم فکر می‌کنم...",
     "🔄🔄🔄🔄🔄\n⏳ دارم فکر می‌کنم...", "✅\n✅ جواب آماده‌ست!"],
    ["💬\n⏳ دارم فکر می‌کنم...", "💬💬\n⏳ دارم فکر می‌کنم...",
     "💬💬💬\n⏳ دارم فکر می‌کنم...", "💬💬💬💬\n⏳ دارم فکر می‌کنم...",
     "💬💬💬💬💬\n⏳ دارم فکر می‌کنم...", "📝✅\n✅ جواب آماده‌ست!"],
    ["✨\n⏳ دارم فکر می‌کنم...", "✨🪄\n⏳ دارم فکر می‌کنم...",
     "✨🪄⭐\n⏳ دارم فکر می‌کنم...", "✨🪄⭐🌟\n⏳ دارم فکر می‌کنم...",
     "✨🪄⭐🌟💫\n⏳ دارم فکر می‌کنم...", "🔮✨\n✅ جواب آماده‌ست!"],
]

_THINKING_MSGS = [
    "🧠 دارم فکر می‌کنم...",
    "🔍 دارم بررسی می‌کنم...",
    "💭 دارم جواب آماده می‌کنم...",
    "✍️ چند لحظه صبر کن...",
]

async def _animate_thinking(status_msg, lang: str):
    """انیمیشن سینمایی — هر فریم ۱ ثانیه."""
    anim = random.choice(_ANIMATIONS)
    msg_id = status_msg.message_id
    for frame in anim:
        if _animation_stopped.get(msg_id):
            return
        await asyncio.sleep(1)
        if _animation_stopped.get(msg_id):
            return
        try:
            await status_msg.edit_text(frame)
        except Exception:
            pass


async def is_member_of_channel(bot: Bot, user_id: int) -> bool:
    if not config.CHANNEL_USERNAME:
        return True
    try:
        member = await bot.get_chat_member(f"@{config.CHANNEL_USERNAME}", user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        log.warning("channel check failed for %s: %s", user_id, e)
        return True


async def enforce_channel(message: Message) -> bool:
    if await is_member_of_channel(message.bot, message.from_user.id):
        return True
    lang = await db.get_lang(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📢 " + t(lang, "btn_join_channel"),
                             url=f"https://t.me/{config.CHANNEL_USERNAME}"),
    ]])
    await message.answer(t(lang, "join_channel"), reply_markup=kb)
    return False


async def enforce_limit(message, lang) -> bool:
    if await db.can_send(message.from_user.id):
        return True
    await message.answer(
        t(lang, "limit_reached", limit=config.FREE_MESSAGE_LIMIT, owner=config.OWNER_USERNAME),
        parse_mode=ParseMode.HTML, reply_markup=limit_kb(lang),
    )
    return False


_notified = {}
_daily_cost_notified = False
_daily_cost_date = None


async def _notify_owner_limit(bot: Bot, user, lang):
    if not config.OWNER_ID:
        return
    now = time.time()
    last = _notified.get(user.id, 0)
    if now - last < 86400:
        return
    _notified[user.id] = now
    stale = [uid for uid, ts in _notified.items() if now - ts > 604800]
    for uid in stale:
        del _notified[uid]
    try:
        name = ("@" + user.username) if user.username else (user.full_name or str(user.id))
        await bot.send_message(
            config.OWNER_ID,
            t("fa", "notify_owner", uid=user.id, name=name, limit=config.FREE_MESSAGE_LIMIT),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        log.warning("owner notify failed: %s", e)


async def _build_context(uid: int, text: str, lang: str, intent: str) -> list:
    """ساخت context از تاریخچه مکالمه — حداکثر ۱۰ پیام آخر."""
    try:
        history = await db.get_conversation_history(uid, limit=config.MAX_HISTORY_MESSAGES)
        return history if history else []
    except Exception:
        return []


async def _get_status_msg(message: Message, lang: str) -> Message:
    """ارسال پیام وضعیت با انتخاب تصادفی."""
    msg_text = random.choice(_THINKING_MSGS)
    return await message.answer(msg_text)


async def process_text(message, text: str, lang: str, uid: int | None = None):
    """پردازش اصلی — با streaming و quality check."""
    if uid is None:
        uid = message.from_user.id

    if not await db.check_hourly_limit(uid):
        await message.answer(t(lang, "hourly_limit", limit=50))
        return

    intent = router.detect_intent(text)

    if intent == "image":
        await _do_image(message, text, lang)
        return
    if intent == "video":
        await message.answer(t(lang, "video_soon", owner=config.OWNER_USERNAME))
        await db.incr_and_count(uid)
        return

    from .search import _needs_web_search, search_and_answer
    if _needs_web_search(text):
        await search_and_answer(message, text, lang)
        return

    mode = await db.get_mode(uid)
    cached = await db.get_cached_response(text, lang, mode)
    if cached:
        status = await _get_status_msg(message, lang)
        await db.incr_and_count(uid)
        _last[uid] = {"text": text, "intent": intent, "lang": lang, "reply": cached}
        await db.save_last_reply(uid, cached)
        await _send_reply(status, cached, lang, uid)
        return

    mode_prompts = {
        "teacher": "You are a patient, encouraging teacher. Explain concepts clearly with examples.",
        "coder": "You are an expert programmer. Give clean, efficient code with brief explanations.",
        "friend": "You are a close, supportive friend. Be casual, warm, and give personal advice.",
    }

    models = router.models_for(intent)
    status = await _get_status_msg(message, lang)
    await message.bot.send_chat_action(message.chat.id, "typing")

    anim_task = asyncio.create_task(_animate_thinking(status, lang))

    hist = await _build_context(uid, text, lang, intent)
    dates = _get_triple_date()
    date_line = dates.get(lang, dates["en"])
    base_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
    system_prompt = base_prompt.replace("{current_datetime}", f"{dates['short']} {dates['time']} — {date_line}")

    if mode in mode_prompts:
        system_prompt += f"\n\nMODE: {mode_prompts[mode]}"

    enhanced_text = await enhance_prompt(text, lang, intent)
    messages = openrouter.with_system(system_prompt, enhanced_text, hist)

    max_tok = config.MAX_TOKENS_BY_INTENT.get(intent, config.MAX_TOKENS_CHAT)
    temperature = config.TEMP_BY_INTENT.get(intent, 0.7)

    # تلاش با streaming
    if config.ENABLE_STREAMING:
        try:
            current_text = ""
            async for chunk, result in openrouter.chat_stream(messages, models, intent=intent,
                                                               max_tokens=max_tok,
                                                               temperature=temperature):
                if chunk is None and result is not None:
                    anim_task.cancel()
                    reply = current_text
                    usage = result
                    await _finalize_response(message, status, reply, usage, uid, text, intent, lang, mode)
                    return
                if chunk:
                    current_text += chunk
        except asyncio.TimeoutError:
            anim_task.cancel()
            await _handle_error(message, status, lang, uid, "timeout", text)
            return
        except Exception as e:
            log.warning("streaming failed, falling back to non-streaming: %s", e)

    # Fallback: non-streaming
    try:
        reply, usage = await asyncio.wait_for(
            openrouter.chat(messages, models, intent=intent, max_tokens=max_tok,
                           temperature=temperature),
            timeout=90,
        )
    except asyncio.TimeoutError:
        anim_task.cancel()
        await _handle_error(message, status, lang, uid, "timeout", text)
        return
    except Exception as e:
        anim_task.cancel()
        log.warning("chat failed: %s", e)
        await _handle_error(message, status, lang, uid, "chat_failed", text)
        return

    anim_task.cancel()
    retry_count = 0
    needs_retry, reason, confidence = upgrade_chat.smart_retry_needed(reply, intent)
    if needs_retry and retry_count < 2:
        retry_count += 1
        retry_prompt = upgrade_chat.get_retry_prompt(text, reply, lang, confidence)
        if retry_prompt:
            retry_messages = openrouter.with_system(system_prompt, retry_prompt, [])
            try:
                reply2, usage2 = await asyncio.wait_for(
                    openrouter.chat(retry_messages, models, intent=intent,
                                   max_tokens=max_tok, temperature=0.5),
                    timeout=60,
                )
                if reply2 and len(reply2) > len(reply):
                    reply = reply2
                    usage = usage2
            except Exception:
                pass
    reply = upgrade_chat.adaptive_response_length(reply, intent)
    reply = upgrade_chat.format_for_telegram(reply)
    await _finalize_response(message, status, reply, usage, uid, text, intent, lang, mode)


async def _finalize_response(message, status, reply, usage, uid, text, intent, lang, mode,
                            alternatives=None):
    await db.incr_and_count(uid)
    await db.cache_response(text, reply, usage.get("model", ""), lang, mode)
    await db.save_last_reply(uid, reply)
    await db.save_message(uid, "user", text)
    await db.save_message(uid, "assistant", reply)
    _last[uid] = {"text": text, "intent": intent, "lang": lang, "reply": reply,
                   "alternatives": alternatives or [], "model": usage.get("model", "")}

    cost = usage.get("cost", 0)
    if cost == 0:
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        model = usage.get("model", "")
        if "deepseek" in model:
            cost = pt * 0.0000007 + ct * 0.0000028
        elif "gpt-4o-mini" in model:
            cost = pt * 0.00000015 + ct * 0.0000006
        elif "claude" in model:
            cost = pt * 0.000001 + ct * 0.000005
        else:
            cost = pt * 0.000001 + ct * 0.000003
    await db.add_usage(uid, usage.get("prompt_tokens", 0),
                       usage.get("completion_tokens", 0), cost)

    if config.DAILY_COST_LIMIT > 0 and config.OWNER_ID:
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        global _daily_cost_date, _daily_cost_notified
        if _daily_cost_date != today:
            _daily_cost_date = today
            _daily_cost_notified = False
        total = await db.daily_cost()
        if total >= config.DAILY_COST_LIMIT and not _daily_cost_notified:
            _daily_cost_notified = True
            try:
                await message.bot.send_message(
                    config.OWNER_ID,
                    f"⚠️ هزینه روزانه از سقف ${config.DAILY_COST_LIMIT:.2f} رد شد: ${total:.4f}",
                )
            except Exception:
                pass

    await _send_reply(status, reply, lang, uid, alternatives=alternatives)


async def _handle_error(message, status, lang, uid, error_type, text):
    """مدیریت خطا با fallback."""
    try:
        await db.log_error(uid, error_type, text[:100])
        await status.edit_text(t(lang, "error"))
    except Exception:
        try:
            await status.answer(t(lang, "error"))
        except Exception:
            pass


_alternatives = TTLDict(ttl_seconds=300, max_size=1000)


async def _send_reply(status_msg, reply: str, lang: str, uid: int = None,
                      alternatives=None):
    reply = reply or t(lang, "error")

    # توقف انیمیشن قبل از ارسال جواب
    if status_msg and status_msg.message_id:
        _animation_stopped[status_msg.message_id] = True
        await asyncio.sleep(0.1)

    kb = answer_kb(lang, has_alternatives=bool(alternatives))

    clarification = _parse_clarification(reply)
    if clarification and uid:
        main_text, questions = clarification
        kb_buttons = []
        for i, q in enumerate(questions[:6]):
            num = chr(0x0031 + i) if i < 9 else str(i + 1)
            kb_buttons.append([InlineKeyboardButton(text=f"{num}⃣ {q}",
                                                    callback_data=f"clarify:{i}:{q[:80]}")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        try:
            if main_text:
                await status_msg.edit_text(main_text, reply_markup=kb)
            else:
                await status_msg.edit_text(t(lang, "choose_option"), reply_markup=kb)
            return
        except Exception:
            pass

    if len(reply) <= 4000:
        try:
            sent = await status_msg.edit_text(reply, reply_markup=kb)
            if alternatives and sent:
                _alternatives[sent.message_id] = alternatives
            return
        except Exception:
            pass

    try:
        await status_msg.delete()
    except Exception:
        pass

    try:
        sent = await status_msg.answer(reply[:4000], reply_markup=kb)
        if alternatives and sent:
            _alternatives[sent.message_id] = alternatives
        return
    except Exception:
        pass

    chunks = [reply[i:i + 3900] for i in range(0, len(reply), 3900)]
    for i, ch in enumerate(chunks):
        try:
            ch_kb = kb if i == len(chunks) - 1 else None
            sent = await status_msg.answer(ch, reply_markup=ch_kb)
            if alternatives and sent and i == len(chunks) - 1:
                _alternatives[sent.message_id] = alternatives
        except Exception:
            pass


async def _do_image(message, prompt: str, lang: str, uid: int | None = None, style: str = "realistic"):
    if uid is None:
        uid = message.from_user.id
    clean = re.sub(r"(یه|یک|برام|بساز|بکش|نقاشی|عکس|تصویر|draw|image of|picture of|generate)",
                   "", prompt, flags=re.I).strip()
    if len(clean) < 2:
        clean = prompt
    status = await message.answer(t(lang, "drawing"))
    await message.bot.send_chat_action(message.chat.id, "upload_photo")
    try:
        data = await image_svc.generate(clean, style=style)
    except Exception:
        data = None
    if not data:
        await status.edit_text(t(lang, "img_failed"))
        return
    await db.incr_and_count(uid)
    _last[uid] = {"text": prompt, "intent": "image", "lang": lang}
    try:
        await message.answer_photo(
            BufferedInputFile(data, filename="kaysan.png"),
            caption="🧠 Kaysan",
        )
        try:
            await status.delete()
        except Exception:
            pass
    except Exception:
        try:
            await status.edit_text(t(lang, "img_failed"))
        except Exception:
            pass


def get_last(uid):
    return _last.get(uid)


def _parse_clarification(reply: str) -> tuple[str, list[str]] | None:
    lines = reply.strip().split("\n")
    questions = []
    main_lines = []
    for line in lines:
        m = re.match(r"^\s*\d+[\)\.\:]\s*(.+)", line)
        if m and len(m.group(1)) < 100:
            questions.append(m.group(1).strip())
        else:
            main_lines.append(line)
    if len(questions) >= 2:
        main_text = "\n".join(main_lines).strip()
        return main_text, questions
    return None


def _get_triple_date():
    from datetime import datetime
    import jdatetime
    now = datetime.now()
    jd = jdatetime.datetime.fromgregorian(datetime=now)
    fa_months = ["","فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"]
    fa_date = f"{jd.day} {fa_months[jd.month]} {jd.year}"
    miladi = f"{now.year}-{now.month:02d}-{now.day:02d}"
    ku_months = ["خاکەلێوە","گوڵان","جۆزەڕدان","پوشپاڕ","گەلاڕێزان","جۆزەڕدان","بەفرانبار","ڕێبەندان","ڕەشەمە","گەلاڕێزان","سەرماوەز","بەفرانبار"]
    if jd.month <= 3:
        ku_month = jd.month + 9
        ku_year = jd.year - 1
    else:
        ku_month = jd.month - 3
        ku_year = jd.year
    if ku_month > 12:
        ku_month -= 12
        ku_year += 1
    ku_month_name = ku_months[ku_month - 1] if 1 <= ku_month <= 12 else ""
    ku_date = f"{jd.day} {ku_month_name} {ku_year}"
    return {
        "fa": f"📅 امروز {fa_date} ({miladi}) ساعت {now.strftime("%H:%M")}",
        "en": f"📅 Today: {miladi} — {now.strftime("%H:%M")}",
        "ku": f"📅 ئەمڕۆ {ku_date} ({miladi}) کاتژمێر {now.strftime("%H:%M")}",
        "short": miladi,
        "time": now.strftime("%H:%M"),
    }



def _jalali_month(m):
    months = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن","ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]
    return months[m-1] if 1 <= m <= 12 else ""


_PROBE = re.compile(
    r"(کدام مدل|چه مدلی|چه هوش|system prompt|پرامپت(ت| سیستم)|دستورات\s*سیستم|"
    r"openrouter|اوپن\s*روتر|چه api|kudam model|which model|what model|"
    r"what (ai|llm)|ignore (previous|above)|developer mode|jailbreak|"
    r"repeat (the|your)|بکدۆ?ام|چ مۆدێل|پشتت چیه|از چی استفاده)",
    re.I,
)
def _to_kurdish_date(jy, jm, jd):
    ku_months = ["خاکەلېوە","گولان","جوزەڕدان","پوشپاڕ","گەلاڕېزان","جوزەڕدان","بەفرانباڕ","ڕېبەندان","ڕېشەمە","گەلاڕېزان","سەرماوەز","بەفرانباڕ"]
    if jm <= 3:
        ku_month = jm + 9
        ku_year = jy - 1
    else:
        ku_month = jm - 3
        ku_year = jy
    if ku_month > 12:
        ku_month -= 12
        ku_year += 1
    ku_month_name = ku_months[ku_month - 1] if 1 <= ku_month <= 12 else ""
    return ku_year, ku_month, jd, ku_month_name
