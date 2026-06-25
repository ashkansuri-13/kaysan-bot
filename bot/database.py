"""دیتابیس SQLite — کاربر، زبان، شمارش پیام، اشتراک، و تمام توابع مورد نیاز."""
import asyncio
import hashlib
from datetime import datetime, timedelta, timezone

import aiosqlite

from . import config

_DB = str(config.DB_PATH)

from contextlib import asynccontextmanager

_DB_POOL: aiosqlite.Connection | None = None
_DB_LOCK = asyncio.Lock()


@asynccontextmanager
async def _get_db():
    """اتصال SQLite با WAL mode — singleton connection."""
    global _DB_POOL
    if _DB_POOL is None:
        async with _DB_LOCK:
            if _DB_POOL is None:
                _DB_POOL = await aiosqlite.connect(_DB)
                await _DB_POOL.execute('PRAGMA journal_mode=WAL')
                await _DB_POOL.execute('PRAGMA synchronous=NORMAL')
                _DB_POOL.row_factory = aiosqlite.Row
    try:
        yield _DB_POOL
    except Exception:
        try:
            await _DB_POOL.close()
        except Exception:
            pass
        _DB_POOL = None
        raise


async def init_db():
    async with _get_db() as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY,
                lang      TEXT DEFAULT 'ku',
                msg_count INTEGER DEFAULT 0,
                subscribed INTEGER DEFAULT 0,
                name      TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS user_prefs (
                user_id INTEGER,
                key TEXT,
                value TEXT,
                PRIMARY KEY (user_id, key)
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                remind_at TEXT,
                text TEXT,
                sent INTEGER DEFAULT 0,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                error_type TEXT,
                details TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS response_cache (
                query_hash TEXT PRIMARY KEY,
                response TEXT,
                model TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS last_replies (
                user_id INTEGER PRIMARY KEY,
                text TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS search_cache (
                query_hash TEXT PRIMARY KEY,
                results TEXT,
                source_count INTEGER,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS search_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                result_count INTEGER,
                duration_ms INTEGER,
                source TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS followups (
                user_id INTEGER,
                original_query TEXT,
                suggestions TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                result_count INTEGER,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                cost REAL,
                created_at TEXT
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                welcome_on INTEGER DEFAULT 1,
                welcome_text TEXT DEFAULT '',
                goodbye_on INTEGER DEFAULT 1,
                goodbye_text TEXT DEFAULT '',
                anti_spam INTEGER DEFAULT 1,
                anti_badwords INTEGER DEFAULT 1,
                anti_flood INTEGER DEFAULT 1,
                flood_limit INTEGER DEFAULT 5,
                flood_window INTEGER DEFAULT 60,
                slow_mode INTEGER DEFAULT 0,
                silent_start INTEGER DEFAULT -1,
                silent_end INTEGER DEFAULT -1,
                rules_text TEXT DEFAULT '',
                auto_reply INTEGER DEFAULT 0,
                badwords_list TEXT DEFAULT '',
                ai_reply INTEGER DEFAULT 0,
                auto_translate INTEGER DEFAULT 0,
                auto_pin INTEGER DEFAULT 0,
                created_at TEXT
            )"""
        )
        await db.commit()


async def ensure_user(user_id, lang=None, name=None):
    async with _get_db() as db:
        cur = await db.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        if await cur.fetchone() is None:
            await db.execute(
                "INSERT INTO users (user_id, lang, name, created_at) VALUES (?,?,?,?)",
                (user_id, lang or config.DEFAULT_LANG, name or "",
                 datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()


async def get_lang(user_id):
    async with _get_db() as db:
        cur = await db.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row and row[0] else config.DEFAULT_LANG


async def set_lang(user_id, lang):
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO users (user_id, lang, created_at) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
            (user_id, lang, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def is_subscribed(user_id):
    if user_id == config.OWNER_ID:
        return True
    async with _get_db() as db:
        cur = await db.execute("SELECT subscribed FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return bool(row and row[0])


async def set_subscribed(user_id, value):
    async with _get_db() as db:
        await db.execute("UPDATE users SET subscribed=? WHERE user_id=?",
                         (1 if value else 0, user_id))
        await db.commit()


async def incr_and_count(user_id):
    async with _get_db() as db:
        await db.execute("UPDATE users SET msg_count = msg_count + 1 WHERE user_id=?", (user_id,))
        await db.commit()
        cur = await db.execute("SELECT msg_count FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def get_count(user_id):
    async with _get_db() as db:
        cur = await db.execute("SELECT msg_count FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def can_send(user_id):
    if await is_subscribed(user_id):
        return True
    return (await get_count(user_id)) < config.FREE_MESSAGE_LIMIT


async def stats():
    async with _get_db() as db:
        c1 = await db.execute("SELECT COUNT(*) FROM users")
        users = (await c1.fetchone())[0]
        c2 = await db.execute("SELECT COALESCE(SUM(msg_count),0) FROM users")
        msgs = (await c2.fetchone())[0]
        return users, msgs


# ===== Hourly Limit =====

async def check_hourly_limit(user_id):
    """آیا کاربر از سقف ساعتی رد شده؟"""
    if await is_subscribed(user_id):
        return True
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM usage_log WHERE user_id=? AND created_at>?",
            (user_id, cutoff),
        )
        row = await cur.fetchone()
        count = row[0] if row else 0
        return count < 50


# ===== User Profile =====

async def get_user_profile(user_id):
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT user_id, lang, msg_count, name FROM users WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return {"user_id": user_id, "lang": "ku", "msg_count": 0, "name": "", "topics": [], "style": "casual"}
        topics = []
        try:
            rows = await db.execute_fetchall(
                "SELECT content FROM conversations WHERE user_id=? AND role='user' ORDER BY id DESC LIMIT 10",
                (user_id,),
            )
            for r in rows:
                ct = r[0] if r else ""
                if ct and len(ct) > 5:
                    words = ct.split()[:5]
                    topics.extend(words)
        except Exception:
            pass
        style = "formal" if row[3] and len(row[3]) > 20 else "casual"
        return {
            "user_id": row[0],
            "lang": row[1] or "ku",
            "msg_count": row[2] or 0,
            "name": row[3] or "",
            "topics": list(set(topics))[:10],
            "style": style,
        }


async def get_conversation_summary(user_id, max_messages=20):
    async with _get_db() as db:
        try:
            rows = await db.execute_fetchall(
                "SELECT role, content FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, max_messages),
            )
            if not rows:
                return ""
            messages = []
            for role, content_text in reversed(rows):
                if content_text and role in ("user", "assistant"):
                    prefix = "User" if role == "user" else "Kaysan"
                    messages.append(prefix + ": " + content_text[:100])
            return "\n".join(messages[-10:])
        except Exception:
            return ""


# ===== User Mode =====

async def get_user_mode(user_id):
    async with _get_db() as db:
        try:
            cur = await db.execute(
                "SELECT value FROM user_prefs WHERE user_id=? AND key='mode'",
                (user_id,),
            )
            row = await cur.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
    return "default"


async def set_user_mode(user_id, mode):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_prefs (user_id, key, value) VALUES (?, 'mode', ?)",
            (user_id, mode),
        )
        await db.commit()


# Alias for extras.py compatibility
async def get_mode(user_id):
    return await get_user_mode(user_id)


async def set_mode(user_id, mode):
    await set_user_mode(user_id, mode)


# ===== User Prefs =====

async def set_pref(user_id, key, value):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_prefs (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, str(value)),
        )
        await db.commit()


async def get_pref(user_id, key, default=None):
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT value FROM user_prefs WHERE user_id=? AND key=?",
            (user_id, key),
        )
        row = await cur.fetchone()
        return row[0] if row else default



# ===== Cache =====

def _cache_key(query, lang, mode):
    raw = f"{query}|{lang}|{mode or ''}"
    return hashlib.md5(raw.encode()).hexdigest()


async def get_cached_response(query, lang, mode):
    key = _cache_key(query, lang, mode)
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT response FROM response_cache WHERE query_hash=?", (key,),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def cache_response(query, response, model, lang, mode):
    key = _cache_key(query, lang, mode)
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO response_cache (query_hash, response, model, created_at) VALUES (?, ?, ?, ?)",
            (key, response[:4000], model, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


# ===== Last Reply =====

async def save_last_reply(user_id, text):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO last_replies (user_id, text) VALUES (?, ?)",
            (user_id, text[:4000]),
        )
        await db.commit()


async def get_last_reply(user_id):
    async with _get_db() as db:
        cur = await db.execute("SELECT text FROM last_replies WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else None


# ===== Usage & Cost =====

async def add_usage(user_id, prompt_tokens, completion_tokens, cost):
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO usage_log (user_id, prompt_tokens, completion_tokens, cost, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, prompt_tokens, completion_tokens, cost, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def daily_cost():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT COALESCE(SUM(cost), 0) FROM usage_log WHERE created_at >= ?",
            (today,),
        )
        row = await cur.fetchone()
        return row[0] if row else 0.0


# ===== Error Logs =====

async def log_error(user_id, error_type, details=""):
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO error_logs (user_id, error_type, details, created_at) VALUES (?, ?, ?, ?)",
            (user_id, error_type, details[:500], datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


# ===== Reminders =====

async def add_reminder(user_id, remind_at, text):
    async with _get_db() as db:
        cur = await db.execute(
            "INSERT INTO reminders (user_id, remind_at, text, sent, created_at) VALUES (?, ?, ?, 0, ?)",
            (user_id, remind_at, text, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_due_reminders():
    now = datetime.now(timezone.utc).isoformat()
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id, user_id, text FROM reminders WHERE sent=0 AND remind_at <= ?",
            (now,),
        )
        return [{"id": r[0], "user_id": r[1], "text": r[2]} for r in rows]


async def mark_reminder_sent(reminder_id):
    async with _get_db() as db:
        await db.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
        await db.commit()


async def mark_old_reminders_sent():
    """علامت‌گذاری یادآوری‌های قدیمی‌تر از ۷ روز به عنوان ارسال شده."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    async with _get_db() as db:
        await db.execute(
            "UPDATE reminders SET sent=1 WHERE sent=0 AND remind_at < ?",
            (cutoff,),
        )
        await db.commit()


# ===== Notes =====

async def add_note(user_id, content):
    async with _get_db() as db:
        cur = await db.execute(
            "INSERT INTO notes (user_id, content, created_at) VALUES (?, ?, ?)",
            (user_id, content, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_notes(user_id, limit=20):
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id, content FROM notes WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [{"id": r[0], "content": r[1]} for r in rows]


async def delete_note(user_id, note_id):
    async with _get_db() as db:
        cur = await db.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
        await db.commit()
        return cur.rowcount > 0


# ===== Search =====

def _search_key(query):
    return hashlib.md5(query.lower().strip().encode()).hexdigest()


async def log_query(query, user_id):
    pass


async def clear_history(user_id):
    async with _get_db() as db:
        await db.execute("DELETE FROM conversations WHERE user_id=?", (user_id,))
        await db.commit()


async def add_feedback(user_id, message_id, value):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_prefs (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, f"feedback_{message_id}", str(value)),
        )
        await db.commit()


async def add_price_alert(user_id, item, condition, price):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_prefs (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, f"alert_{item}", f"{condition}:{price}"),
        )
        await db.commit()


async def user_cost(user_id):
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT name, msg_count, "
            "COALESCE((SELECT SUM(prompt_tokens) FROM usage_log WHERE user_id=?),0), "
            "COALESCE((SELECT SUM(completion_tokens) FROM usage_log WHERE user_id=?),0), "
            "COALESCE((SELECT SUM(cost) FROM usage_log WHERE user_id=?),0) "
            "FROM users WHERE user_id=?",
            (user_id, user_id, user_id, user_id),
        )
        return await cur.fetchone()


async def cost_stats():
    async with _get_db() as db:
        c1 = await db.execute("SELECT COUNT(*) FROM users")
        users = (await c1.fetchone())[0]
        c2 = await db.execute("SELECT COALESCE(SUM(msg_count),0) FROM users")
        msgs = (await c2.fetchone())[0]
        c3 = await db.execute("SELECT COALESCE(SUM(prompt_tokens),0) FROM usage_log")
        pt = (await c3.fetchone())[0]
        c4 = await db.execute("SELECT COALESCE(SUM(completion_tokens),0) FROM usage_log")
        ct = (await c4.fetchone())[0]
        c5 = await db.execute("SELECT COALESCE(SUM(cost),0) FROM usage_log")
        cost = (await c5.fetchone())[0]
        return users, msgs, pt, ct, cost


async def top_users(limit=5):
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT u.user_id, u.name, u.msg_count, "
            "COALESCE((SELECT SUM(cost) FROM usage_log WHERE user_id=u.user_id),0) as total_cost "
            "FROM users u WHERE u.msg_count > 0 ORDER BY total_cost DESC LIMIT ?",
            (limit,),
        )
        return [(r[0], r[1], r[2], r[3]) for r in rows]


async def error_stats():
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT error_type, COUNT(*) as cnt FROM error_logs "
            "WHERE created_at >= datetime('now', '-7 days') "
            "GROUP BY error_type ORDER BY cnt DESC LIMIT 10"
        )
        return [{"type": r[0], "count": r[1]} for r in rows]


async def clean_old_cache(days=7):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    async with _get_db() as db:
        await db.execute("DELETE FROM response_cache WHERE created_at < ?", (cutoff,))
        await db.execute("DELETE FROM search_cache WHERE created_at < ?", (cutoff,))
        await db.commit()


async def get_all_prefs(user_id):
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT key, value FROM user_prefs WHERE user_id=?", (user_id,)
        )
        return {r[0]: r[1] for r in rows}


async def get_price_alerts(user_id=None):
    async with _get_db() as db:
        if user_id:
            rows = await db.execute_fetchall(
                "SELECT key, value FROM user_prefs WHERE user_id=? AND key LIKE 'alert_%'",
                (user_id,),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT key, value FROM user_prefs WHERE key LIKE 'alert_%'",
            )
        results = []
        for key, val in rows:
            item = key.replace("alert_", "", 1)
            parts = val.split(":")
            if len(parts) == 2:
                results.append({"id": item, "item": item, "condition": parts[0], "price": float(parts[1])})
        return results


async def deactivate_alert(alert_id=None, user_id=None, item=None):
    async with _get_db() as db:
        if alert_id and not user_id:
            await db.execute(
                "DELETE FROM user_prefs WHERE key=?",
                (f"alert_{alert_id}",),
            )
        elif user_id and item:
            await db.execute(
                "DELETE FROM user_prefs WHERE user_id=? AND key=?",
                (user_id, f"alert_{item}"),
            )
        await db.commit()


async def add_search_alert(user_id, query, target_value=""):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_prefs (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, f"search_alert_{query}", str(target_value)),
        )
        await db.commit()


async def get_search_alerts(user_id=None):
    async with _get_db() as db:
        if user_id:
            rows = await db.execute_fetchall(
                "SELECT key, value FROM user_prefs WHERE user_id=? AND key LIKE 'search_alert_%'",
                (user_id,),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT key, value FROM user_prefs WHERE key LIKE 'search_alert_%'",
            )
        return [{"query": r[0].replace("search_alert_", "", 1), "target": r[1]} for r in rows]


async def mark_alert_sent(user_id, query):
    async with _get_db() as db:
        await db.execute(
            "DELETE FROM user_prefs WHERE user_id=? AND key=?",
            (user_id, f"search_alert_{query}"),
        )
        await db.commit()


async def save_message(user_id, role, text):
    async with _get_db() as db:
        try:
            await db.execute(
                "INSERT INTO conversations (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, text, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()
        except Exception:
            pass


async def get_conversation_history(user_id, limit=20):
    async with _get_db() as db:
        try:
            rows = await db.execute_fetchall(
                "SELECT role, content FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
        except Exception:
            return []


async def get_followup(user_id, original_query=None):
    async with _get_db() as db:
        if original_query:
            cur = await db.execute(
                "SELECT original_query, suggestions FROM followups WHERE user_id=? AND original_query=? ORDER BY rowid DESC LIMIT 1",
                (user_id, original_query[:200]),
            )
        else:
            cur = await db.execute(
                "SELECT original_query, suggestions FROM followups WHERE user_id=? ORDER BY rowid DESC LIMIT 1",
                (user_id,),
            )
        row = await cur.fetchone()
        if row:
            return {"original_query": row[0], "suggestions": row[1]}
        return None


async def remove_favorite(user_id, query_or_id):
    async with _get_db() as db:
        if isinstance(query_or_id, int):
            cur = await db.execute(
                "DELETE FROM favorites WHERE id=? AND user_id=?",
                (query_or_id, user_id),
            )
        else:
            cur = await db.execute(
                "DELETE FROM favorites WHERE user_id=? AND query=?",
                (user_id, query_or_id),
            )
        await db.commit()
        return cur.rowcount > 0


async def get_auto_suggestions(user_id, limit=5):
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT query FROM search_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [{"query": r[0]} for r in rows]


async def backup_db(backup_path):
    import shutil
    try:
        shutil.copy2(_DB, backup_path)
        return True
    except Exception:
        return False


async def get_search_cache(query):
    key = _search_key(query)
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT results, source_count FROM search_cache WHERE query_hash=?", (key,),
        )
        row = await cur.fetchone()
        if row:
            return {"results": row[0], "source_count": row[1]}
    return None


async def save_search_cache(query, results, source_count):
    key = _search_key(query)
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO search_cache (query_hash, results, source_count, created_at) VALUES (?, ?, ?, ?)",
            (key, results[:4000], source_count, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def log_search(user_id, query, result_count, duration_ms, source):
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO search_log (user_id, query, result_count, duration_ms, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, query, result_count, duration_ms, source, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def add_search_history(user_id, query, result_count):
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO search_history (user_id, query, result_count, created_at) VALUES (?, ?, ?, ?)",
            (user_id, query[:200], result_count, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def get_search_history(user_id, limit=10):
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT query, result_count FROM search_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [{"query": r[0], "result_count": r[1]} for r in rows]


async def save_followup(user_id, original_query, suggestions):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO followups (user_id, original_query, suggestions) VALUES (?, ?, ?)",
            (user_id, original_query[:200], suggestions),
        )
        await db.commit()


async def add_favorite(user_id, query):
    async with _get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, query, created_at) VALUES (?, ?, ?)",
            (user_id, query[:200], datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def get_favorites(user_id, limit=10):
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id, query FROM favorites WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [{"id": r[0], "query": r[1]} for r in rows]


async def get_daily_summary():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(DISTINCT user_id), COUNT(*) FROM search_log WHERE created_at >= ?",
            (today,),
        )
        row = await cur.fetchone()
        return {"users": row[0], "queries": row[1], "searches": row[1]}


async def get_popular_queries(limit=10):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    async with _get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT query, COUNT(*) as cnt FROM search_log WHERE created_at >= ? GROUP BY query ORDER BY cnt DESC LIMIT ?",
            (today, limit),
        )
        return [{"query": r[0], "count": r[1]} for r in rows]


async def get_search_stats(days=7):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT COUNT(DISTINCT user_id), COUNT(*) FROM search_log WHERE created_at >= ?",
            (cutoff,),
        )
        row = await cur.fetchone()
        return {"users": row[0], "queries": row[1], "total": row[1]}


# ===== Group Settings =====

async def ensure_group(chat_id, title):
    async with _get_db() as db:
        cur = await db.execute("SELECT 1 FROM group_settings WHERE chat_id=?", (chat_id,))
        if await cur.fetchone() is None:
            await db.execute(
                "INSERT INTO group_settings (chat_id, title, created_at) VALUES (?, ?, ?)",
                (chat_id, title, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()


async def get_group_settings(chat_id):
    async with _get_db() as db:
        cur = await db.execute("SELECT * FROM group_settings WHERE chat_id=?", (chat_id,))
        row = await cur.fetchone()
        if not row:
            return {}
        cols = ["chat_id", "title", "welcome_on", "welcome_text", "goodbye_on", "goodbye_text",
                "anti_spam", "anti_badwords", "anti_flood", "flood_limit", "flood_window",
                "slow_mode", "silent_start", "silent_end", "rules_text", "auto_reply",
                "badwords_list", "ai_reply", "auto_translate", "auto_pin", "created_at"]
        return dict(zip(cols, row))


async def update_group(chat_id, **kwargs):
    if not kwargs:
        return
    valid_columns = {
        "chat_id", "title", "welcome_on", "welcome_text", "goodbye_on", "goodbye_text",
        "anti_spam", "anti_badwords", "anti_flood", "flood_limit", "flood_window",
        "slow_mode", "silent_start", "silent_end", "rules_text", "auto_reply",
        "badwords_list", "ai_reply", "auto_translate", "auto_pin",
    }
    invalid = set(kwargs.keys()) - valid_columns
    if invalid:
        raise ValueError(f"Invalid columns: {', '.join(invalid)}")
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [chat_id]
    async with _get_db() as db:
        await db.execute(f"UPDATE group_settings SET {sets} WHERE chat_id=?", vals)
        await db.commit()


async def get_all_managed_groups(user_id):
    """گروه‌هایی که ربات در اونا ادمینه — فقط owner."""
    if user_id != config.OWNER_ID:
        return []
    async with _get_db() as db:
        rows = await db.execute_fetchall("SELECT chat_id, title FROM group_settings")
        return [{"chat_id": r[0], "title": r[1]} for r in rows]


async def delete_group_settings(chat_id):
    async with _get_db() as db:
        await db.execute("DELETE FROM group_settings WHERE chat_id=?", (chat_id,))
        await db.commit()


async def save_message(user_id: int, role: str, content: str):
    """ذخیره پیام در conversations table."""
    async with _get_db() as db:
        await db.execute(
            "INSERT INTO conversations (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def get_conversation_history(user_id: int, limit: int = 10):
    """دریافت آخرین پیام‌های کاربر."""
    async with _get_db() as db:
        cur = await db.execute(
            """SELECT role, content, created_at FROM conversations 
               WHERE user_id=? ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        )
        rows = await cur.fetchall()
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in reversed(rows)]


async def get_feedback_stats(user_id):
    async with _get_db() as db:
        cur = await db.execute(
            "SELECT key, value FROM user_prefs WHERE user_id=? AND key LIKE 'feedback_%'",
            (user_id,),
        )
        rows = await cur.fetchall()
        stats = {}
        for _, v in rows:
            val = int(v)
            stats[val] = stats.get(val, 0) + 1
        return stats
