"""جستجوی هوشمند — ۲۰ بهبود: وب + تلگرام + Google News + Redis + فیلتر + هوشمندی."""
import asyncio
import hashlib
import logging
import random
import re
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import config, database as db, openrouter, redis_cache as rc, router as rtr
from ..keyboards import answer_kb
from ..texts import SYSTEM_PROMPTS, t
from . import core

router = Router()
log = logging.getLogger("kaysan.search")

# ─────────────────────────────────────────────
#  انیمیشن‌ها
# ─────────────────────────────────────────────
_SEARCH_ANIMS = [
    ["🛰️\n📡 در حال جستجو...", "🛰️📡\n📡 ...", "🛰️📡🌐\n📡 ...",
     "🛰️📡🌐🔍\n📡 ...", "🛰️📡🌐🔍💡\n📡 ...", "🛰️📡🌐🔍💡✅\n📡 پیدا شد!"],
    ["📚\n📖 جستجو...", "📚📖\n📖 ...", "📚📖🔍\n📖 ...",
     "📚📖🔍💡\n📖 ...", "📚📖🔍💡✨\n📖 ...", "📚📖🔍💡✨📝\n📖 پیدا شد!"],
    ["💻\n🖥️ سرچ...", "💻🖥️\n🖥️ ...", "💻🖥️⌨️\n🖥️ ...",
     "💻🖥️⌨️🖱️\n🖥️ ...", "💻🖥️⌨️🖱️🔍\n🖥️ ...", "💻🖥️⌨️🖱️🔍✅\n🖥️ پیدا شد!"],
    ["🔭\n🔭 نگاه...", "🔭🌌\n🔭 ...", "🔭🌌⭐\n🔭 ...",
     "🔭🌌⭐🌟\n🔭 ...", "🔭🌌⭐🌟💫\n🔭 ...", "🔭🌌⭐🌟💫✅\n🔭 پیدا شد!"],
    ["🐝\n🍯 دنبال...", "🐝🌸\n🍯 ...", "🐝🌸🌻\n🍯 ...",
     "🐝🌸🌻🌺\n🍯 ...", "🐝🌸🌻🌺🔍\n🍯 ...", "🐝🌸🌻🌺🔍🍯\n🍯 پیدا شد!"],
]


async def _animate_search(status_msg):
    anim = random.choice(_SEARCH_ANIMS)
    for frame in anim:
        await asyncio.sleep(1)
        try:
            await status_msg.edit_text(frame)
        except Exception:
            pass


# ─────────────────────────────────────────────
#  تشخیص نیاز به سرچ
# ─────────────────────────────────────────────
def _needs_web_search(text: str) -> bool:
    patterns = re.compile(
        r"(قیمت|دلار|یورو|ارز|بورس|سکه|طلا|نتیجه|بازی|آب\s*و\s*هوا|آب‌وهوا|weather|price|score|"
        r"آخرین|جدید|today|news|اکنون|الان|امروز|دیروز|"
        r"ساعت|وقت|زمان|date|time|now|currently|"
        r"کجاست|آدرس|address|map|"
        r"چند|how much|how many|how old|"
        r"کی|when|who|چه کسی|"
        r"چرا|why|چطور|how|"
        r"بهترین|best|"
        r"وضعیت|status|state|"
        r"سیگنال|signal|خرید|فروش|buy|sell|"
        r"پیش‌بینی|predict|forecast|"
        r"روند|trend|تاریخچه|history|"
        r"مقایسه|compare|تفاوت|difference)",
        re.I,
    )
    return bool(patterns.search(text))


# ─────────────────────────────────────────────
#  پیش‌پردازش کوئری
# ─────────────────────────────────────────────
async def _enhance_query(query: str, lang: str) -> list[str]:
    lang_name = core._LANG_NAMES.get(lang, "English")
    system = (
        f"Convert this user question into 2-3 effective search queries. "
        f"Reply in {lang_name}. Format: one query per line, no numbering. "
        f"Keep queries short and keyword-focused."
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": query}]
    try:
        reply, _ = await asyncio.wait_for(
            openrouter.chat(messages, [config.PRIMARY_MODEL] if config.PRIMARY_MODEL else config.CHAT_MODELS, max_tokens=100),
            timeout=10,
        )
        queries = [q.strip() for q in reply.strip().split("\n") if q.strip() and len(q.strip()) > 2]
        return queries[:3] if queries else [query]
    except Exception:
        return [query]


# ─────────────────────────────────────────────
#  فیلتر اسپم
# ─────────────────────────────────────────────
_SPAM_PATTERNS = re.compile(
    r"(کلیک کن|click here|رایگان|free|تخفیف|discount|برنده شو|win|جایزه|prize|"
    r"لینک|link|عضویت|join|فالو|follow|لایک|like|اشتراک|share)",
    re.I,
)

_CREDIBLE_SOURCES = [
    "tgju.org", "iranjib.ir", "mazaneh.net", "talamarket.ir",
    "mofidonline.com", "agah.com", "eghtesadonline.com",
    "bbc.com", "reuters.com", "aljazeera.com",
    "wikipedia.org", "stackoverflow.com", "github.com",
    "khabaronline.ir", "isna.ir", "tabnak.ir",
]


def _is_spam(text: str) -> bool:
    return bool(_SPAM_PATTERNS.search(text))


def _source_credibility(url: str) -> int:
    score = 5
    url_lower = url.lower()
    for src in _CREDIBLE_SOURCES:
        if src in url_lower:
            return 10
    if "t.me" in url_lower:
        score = max(score, 6)
    if any(x in url_lower for x in ["gov", "org", "edu"]):
        score = max(score, 8)
    return score


def _classify_query(text: str) -> str:
    if re.search(r"(قیمت|دلار|ارز|سکه|طلا|بورس|price|buy|sell)", text, re.I):
        return "finance"
    if re.search(r"(خبر|news|رویداد|event|اتفاق)", text, re.I):
        return "news"
    if re.search(r"(علمی|دانش|ویکیپدیا|wikipedia|تاریخچه|history)", text, re.I):
        return "wiki"
    if re.search(r"(آب\s*و\s*هوا|آب‌وهوا|weather|دما|temperature)", text, re.I):
        return "weather"
    if re.search(r"(عکس|تصویر|image|photo|picture|drawing)", text, re.I):
        return "image"
    if re.search(r"(ویدیو|ویدئو|کلیپ|video|clip|آپارات|youtube)", text, re.I):
        return "video"
    return "general"


def _normalize_persian(text: str) -> str:
    replacements = {"٠": "۰", "١": "۱", "٢": "۲", "٣": "۳", "٤": "۴",
                    "٥": "۵", "٦": "۶", "٧": "۷", "٨": "۸", "٩": "۹"}
    for ar, fa in replacements.items():
        text = text.replace(ar, fa)
    return re.sub(r'[^\w\s]', ' ', text).strip()


def _extract_keywords(text: str) -> list[str]:
    text = _normalize_persian(text)
    stop_words = {"چی", "هست", "هسته", "باشه", "بشه", "میشه", "کنه", "بکنه",
                  "چطور", "چطوری", "چگونه", "کجا", "چرا", "چه", "ایا", "آیا",
                  "the", "is", "a", "an", "to", "in", "of", "for", "what", "how"}
    return [w for w in text.split() if len(w) > 1 and w.lower() not in stop_words][:5]


def _get_cache_ttl(query_type: str) -> int:
    """کش هوشمند — هر نوع سؤال TTL متفاوت."""
    return {
        "finance": 300,    # ۵ دقیقه
        "news": 600,       # ۱۰ دقیقه
        "weather": 900,    # ۱۵ دقیقه
        "general": 1800,   # ۳۰ دقیقه
    }.get(query_type, 1800)


# ─────────────────────────────────────────────
#  سرچ وب — چندگانه + فیلتر
# ─────────────────────────────────────────────
async def web_search(query: str, max_results: int = 3) -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    queries = [f"{query} {today}", query, f"{query} سایت معتبر"]
    all_results, seen_urls = [], set()

    for q in queries:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=max_results + 2))
            for r in results:
                url = r.get("href", "")
                if url and url not in seen_urls and not _is_spam(r.get("body", "")):
                    seen_urls.add(url)
                    title = r.get("title", "")
                    body = r.get("body", "")
                    if title or body:
                        all_results.append({
                            "source": url, "title": f"🌐 {title[:60]}",
                            "text": f"{title}\n{body}", "date": today,
                            "url": url, "credibility": _source_credibility(url),
                        })
        except Exception:
            continue
        if len(all_results) >= max_results + 3:
            break

    all_results.sort(key=lambda x: x["credibility"], reverse=True)
    return all_results[:max_results + 3]


# ─────────────────────────────────────────────
#  Google News — اخبار لحظه‌ای
# ─────────────────────────────────────────────
async def google_news_search(query: str, max_results: int = 3) -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    all_results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(f"{query} {today}", max_results=max_results))
        for r in results:
            all_results.append({
                "source": r.get("url", ""),
                "title": f"📰 {r.get('title', '')[:60]}",
                "text": f"{r.get('title', '')}\n{r.get('body', '')}",
                "date": r.get("date", today)[:16],
                "url": r.get("url", ""),
                "credibility": 8,
            })
    except Exception:
        pass
    return all_results[:max_results]


# ─────────────────────────────────────────────
#  سرچ تصاویر
# ─────────────────────────────────────────────
async def image_search(query: str, max_results: int = 3) -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    all_results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(f"{query}", max_results=max_results))
        for r in results:
            all_results.append({
                "source": r.get("image", ""),
                "title": f"🖼️ {r.get('title', '')[:60]}",
                "text": r.get("title", ""),
                "date": today,
                "url": r.get("image", ""),
                "credibility": 5,
            })
    except Exception:
        pass
    return all_results[:max_results]


# ─────────────────────────────────────────────
#  سرچ ویدیو
# ─────────────────────────────────────────────
async def video_search(query: str, max_results: int = 3) -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    all_results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.videos(f"{query}", max_results=max_results))
        for r in results:
            all_results.append({
                "source": r.get("content", ""),
                "title": f"🎬 {r.get('title', '')[:60]}",
                "text": r.get("description", ""),
                "date": today,
                "url": r.get("content", ""),
                "credibility": 6,
            })
    except Exception:
        pass
    return all_results[:max_results]


# ─────────────────────────────────────────────
#  سرچ تلگرام
# ─────────────────────────────────────────────
async def telegram_search(bot, query: str, channels: list[str], max_results: int = 5) -> list[dict]:
    if not channels:
        return []
    keywords = _extract_keywords(query)
    all_results, seen = [], set()

    for channel in channels:
        for q in [query] + keywords[:2]:
            try:
                messages = await bot.search_messages(chat=f"@{channel}", query=q, limit=max_results)
                async for msg in messages:
                    if msg.text and len(msg.text) > 30:
                        text = msg.text[:600]
                        text_hash = text[:80]
                        if text_hash not in seen and not _is_spam(text):
                            seen.add(text_hash)
                            date = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
                            all_results.append({
                                "source": f"@{channel}", "title": f"📱 @{channel}",
                                "text": text, "date": date,
                                "url": f"https://t.me/{channel}/{msg.message_id}",
                                "credibility": 7,
                            })
            except Exception:
                continue

    all_results.sort(key=lambda x: x["date"], reverse=True)
    return all_results[:8]


# ─────────────────────────────────────────────
#  روند قیمت
# ─────────────────────────────────────────────
async def _get_price_trend(item: str) -> str:
    days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    query = f"روند قیمت {item} از {days_ago} تا امروز"
    try:
        results = await web_search(query, max_results=2)
        if results:
            return "\n".join(f"• {r['text'][:200]}" for r in results[:2])
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────
#  سؤالات follow-up
# ─────────────────────────────────────────────
async def _generate_followups(query: str, reply: str, lang: str) -> list[str]:
    lang_name = core._LANG_NAMES.get(lang, "English")
    system = (
        f"Generate 3 short follow-up questions the user might ask next about this topic. "
        f"Reply in {lang_name}. Format: one question per line, no numbering, max 8 words each."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Original: {query}\nAnswer: {reply[:300]}"},
    ]
    try:
        resp, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=150),
            timeout=10,
        )
        return [q.strip() for q in resp.strip().split("\n") if q.strip()][:3]
    except Exception:
        return []


# ─────────────────────────────────────────────
#  جدول مقایسه
# ─────────────────────────────────────────────
async def _generate_comparison(query: str, results: list[dict], lang: str) -> str:
    if not re.search(r"(مقایسه|compare|vs|对比|تفاوت|difference)", query, re.I):
        return ""
    lang_name = core._LANG_NAMES.get(lang, "English")
    combined = "\n".join(f"- {r['text'][:200]}" for r in results[:4])
    system = f"Create a comparison table from these results. Reply in {lang_name}. Use markdown table format."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Compare: {query}\n\nData:\n{combined}"},
    ]
    try:
        resp, _ = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=800),
            timeout=15,
        )
        return resp
    except Exception:
        return ""


# ─────────────────────────────────────────────
#  تابع اصلی
# ─────────────────────────────────────────────
async def search_and_answer(message: Message, text: str, lang: str):
    """جستجوی هوشمند — همه ۲۰ بهبود UX."""
    uid = message.from_user.id
    start_time = datetime.now()

    # ۱. لاگ سرچ + تاریخچه
    await db.log_query(text, uid)
    await db.add_search_history(uid, text, 0)

    # ۲. کش هوشمند (Redis → SQLite)
    query_type = _classify_query(text)
    cache_ttl = _get_cache_ttl(query_type)
    cache_key = hashlib.md5(text.lower().strip().encode()).hexdigest()

    cached = await rc.cache_get(f"search:{cache_key}")
    if cached:
        status = await message.answer("⚡ پاسخ از حافظه...")
        await db.incr_and_count(uid)
        await db.add_search_history(uid, text, 1)
        core._last[uid] = {"text": text, "intent": "chat", "lang": lang, "reply": cached}
        await core._send_reply(status, cached, lang, uid)
        # دکمه ذخیره + تاریخچه
        fav_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ ذخیره", callback_data=f"fav_save:{text[:80]}"),
             InlineKeyboardButton(text="📜 سرچ‌های قبلی", callback_data="fav_history")],
        ])
        try:
            await message.answer("💡 عملیات:", reply_markup=fav_kb)
        except Exception:
            pass
        return

    cached_db = await db.get_search_cache(text)
    if cached_db:
        status = await message.answer("⚡ پاسخ از حافظه...")
        await db.incr_and_count(uid)
        await db.add_search_history(uid, text, 1)
        core._last[uid] = {"text": text, "intent": "chat", "lang": lang, "reply": cached_db["results"]}
        await core._send_reply(status, cached_db["results"], lang, uid)
        fav_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ ذخیره", callback_data=f"fav_save:{text[:80]}"),
             InlineKeyboardButton(text="📜 سرچ‌های قبلی", callback_data="fav_history")],
        ])
        try:
            await message.answer("💡 عملیات:", reply_markup=fav_kb)
        except Exception:
            pass
        return

    status = await message.answer("🔍\n📡 در حال جستجو...")
    await message.bot.send_chat_action(message.chat.id, "typing")
    anim_task = asyncio.create_task(_animate_search(status))

    # ۳. بهبود کوئری
    enhanced_queries = await _enhance_query(text, lang)

    # ۴. سرچ همزمان
    all_tasks = []
    for q in enhanced_queries:
        all_tasks.append(("web", asyncio.create_task(web_search(q, max_results=2))))
    all_tasks.append(("news", asyncio.create_task(google_news_search(text, max_results=2))))
    all_tasks.append(("tg", asyncio.create_task(telegram_search(message.bot, text, config.SEARCH_CHANNELS))))

    if query_type == "image":
        all_tasks.append(("image", asyncio.create_task(image_search(text))))
    if query_type == "video":
        all_tasks.append(("video", asyncio.create_task(video_search(text))))

    results_map = {}
    for source, task in all_tasks:
        try:
            results_map[source] = await asyncio.wait_for(task, timeout=8)
        except (asyncio.TimeoutError, Exception):
            results_map[source] = []

    anim_task.cancel()

    web_results = results_map.get("web", [])
    news_results = results_map.get("news", [])
    tg_results = results_map.get("tg", [])
    image_results = results_map.get("image", [])
    video_results = results_map.get("video", [])
    all_results = tg_results + news_results + web_results + image_results + video_results

    if not all_results:
        await core.process_text(message, text, lang)
        return

    # ۵. نمایش منابع
    sources = []
    if tg_results: sources.append("📱 تلگرام")
    if news_results: sources.append("📰 اخبار")
    if web_results: sources.append("🌐 وب")
    if image_results: sources.append("🖼️ تصویر")
    if video_results: sources.append("🎬 ویدیو")
    try:
        await status.edit_text(f"✅ پیدا شد!\n🔍 منابع: {' + '.join(sources)}\n🧠 دارم نتایج رو بررسی می‌کنم...")
    except Exception:
        pass

    # ۶. روند قیمت + مقایسه
    trend_text = ""
    if query_type == "finance":
        trend_text = await _get_price_trend(text.split()[0] if text.split() else "")
    comparison = await _generate_comparison(text, all_results, lang)

    # ۷. ساخت متن ترکیبی
    combined_lines = []
    if news_results:
        combined_lines.append("📰 Breaking News:")
        for r in news_results[:3]:
            combined_lines.append(f"[{r['date']}] {r['text'][:200]}")
    if tg_results:
        combined_lines.append("\n📱 Telegram:")
        for r in tg_results[:3]:
            combined_lines.append(f"[{r['source']}] {r['date']}\n{r['text'][:200]}")
    if web_results:
        combined_lines.append("\n🌐 Web:")
        for r in web_results[:3]:
            cred = "⭐" * (r.get("credibility", 5) // 2)
            combined_lines.append(f"[{r['title']}] {cred}\n{r['text'][:200]}")
    if image_results:
        combined_lines.append("\n🖼️ Images:")
        for r in image_results[:2]:
            combined_lines.append(f"{r['title']}")
    if video_results:
        combined_lines.append("\n🎬 Videos:")
        for r in video_results[:2]:
            combined_lines.append(f"{r['title']}")
    if trend_text:
        combined_lines.append(f"\n📈 Trend:\n{trend_text}")
    if comparison:
        combined_lines.append(f"\n📊 Comparison:\n{comparison}")

    combined = "\n".join(combined_lines)

    # ۸. system prompt
    enhanced_text = (
        f"User asked: {text}\n"
        f"Query type: {query_type}\n"
        f"Current date/time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"REAL search results (only cite these, NEVER invent):\n{combined}\n\n"
        f"STRICT RULES:\n"
        f"1. ONLY cite sources listed above. NEVER invent channel names, bot names, or URLs.\n"
        f"2. NEVER say 'use @SomeBot' unless it's in the results.\n"
        f"3. If data is incomplete, say what you found AND what's missing.\n"
        f"4. For prices: give the range if available.\n"
        f"5. For news: mention the date.\n"
        f"6. For comparisons: use a clear table.\n"
        f"7. Answer concisely in the user's language.\n"
        f"8. Add 📈 trend info if available."
    )

    dates = core._get_triple_date()
    date_line = dates.get(lang, dates["en"])
    base_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
    system_prompt = base_prompt.replace("{current_datetime}", f"{dates['short']} {dates['time']} — {date_line}")
    messages = openrouter.with_system(system_prompt, enhanced_text)

    try:
        reply, usage = await asyncio.wait_for(
            openrouter.chat(messages, config.CHAT_MODELS, max_tokens=1800),
            timeout=60,
        )
    except Exception as e:
        log.warning("search answer failed: %s", e)
        try:
            await status.edit_text(t(lang, "error"))
        except Exception:
            try:
                await status.answer(t(lang, "error"))
            except Exception:
                pass
        return

    # ۹. ذخیره در کش + لاگ
    await rc.cache_set(f"search:{cache_key}", reply, ttl=cache_ttl)
    await db.save_search_cache(text, reply, len(all_results))
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    await db.log_search(uid, text, len(all_results), duration_ms, "+".join(sources))
    await db.add_search_history(uid, text, len(all_results))

    # ۱۰. ارسال جواب
    await db.incr_and_count(uid)
    core._last[uid] = {"text": text, "intent": "chat", "lang": lang, "reply": reply}

    if len(reply) <= 3800:
        try:
            await status.edit_text(reply, reply_markup=answer_kb(lang))
        except Exception:
            pass
    else:
        await core._send_reply(status, reply, lang, uid)

    # ۱۱. منابع (ساده)
    source_urls = [r for r in all_results[:3] if r.get("url")]
    if source_urls:
        buttons = [[InlineKeyboardButton(text=f"📎 {r.get('title', 'منبع')[:25]}", url=r["url"]) for r in source_urls[:2]]]
        try:
            await message.answer("📎 منابع:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except Exception:
            pass


# ─────────────────────────────────────────────
#  هندلرها
# ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("fu:"))
async def cb_followup(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    question = call.data[3:]
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await core.process_text(call.message, question, lang, uid=uid)


@router.callback_query(F.data.startswith("fav_save:"))
async def cb_fav_save(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)
    query = call.data[9:]
    await db.add_favorite(uid, query)
    await call.answer(t(lang, "saved_to_favorites"), show_alert=True)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data == "fav_history")
async def cb_fav_history(call: CallbackQuery):
    uid = call.from_user.id
    lang = await db.get_lang(uid)

    history = await db.get_search_history(uid, 8)
    favorites = await db.get_favorites(uid)

    lines = []
    if history:
        lines.append(t(lang, "search_history"))
        for i, h in enumerate(history[:5], 1):
            lines.append(f"{i}. {h['query']}")
    if favorites:
        lines.append(f"\n{t(lang, 'search_favorites')}")
        for f in favorites[:5]:
            lines.append(f"⭐ {f['query']}")

    if not lines:
        await call.answer(t(lang, "no_favorites"), show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=q["query"][:40], callback_data=f"fu:{q['query'][:80]}")]
        for q in history[:4]
    ])

    await call.answer()
    try:
        await call.message.edit_text("\n".join(lines), reply_markup=kb)
    except Exception:
        await call.message.answer("\n".join(lines), reply_markup=kb)


@router.callback_query(F.data == "fav_daily")
async def cb_fav_daily(call: CallbackQuery):
    """گزارش روزانه."""
    uid = call.from_user.id
    if uid != config.OWNER_ID:
        await call.answer("فقط سازنده.", show_alert=True)
        return
    summary = await db.get_daily_summary()
    popular = await db.get_popular_queries(5)
    lines = [
        "📊 <b>گزارش روزانه سرچ</b>\n",
        f"🔍 کل سرچ‌ها: {summary.get('queries', 0)}",
        f"👥 کاربران فعال: {summary.get('users', 0)}",
    ]
    if popular:
        lines.append("\n🔥 محبوب‌ترین‌ها:")
        for q in popular:
            lines.append(f"  • {q['query']} ({q['count']})")
    await call.answer()
    await call.message.answer("\n".join(lines), parse_mode="HTML")


# ─────────────────────────────────────────────
#  دستورات
# ─────────────────────────────────────────────
async def cmd_popular_queries():
    return await db.get_popular_queries(10)

async def cmd_search_stats():
    base = await db.get_search_stats(7)
    popular = await db.get_popular_queries(5)
    return {
        "total": base.get("queries", 0),
        "users": base.get("users", 0),
        "avg_duration": 0,
        "avg_results": 0,
        "popular": popular,
    }