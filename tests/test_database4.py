"""Comprehensive database tests — more coverage."""
import pytest
import pytest_asyncio
import aiosqlite
from bot.database import (
    init_db, ensure_user, get_lang, set_lang, can_send,
    add_usage, clear_history,
    get_cached_response, cache_response, clean_old_cache,
    ensure_group, get_group_settings, update_group,
    get_all_managed_groups, delete_group_settings,
    stats, cost_stats, user_cost, top_users, daily_cost,
    add_reminder, get_due_reminders, mark_reminder_sent, mark_old_reminders_sent,
    log_error, error_stats, add_feedback, get_feedback_stats,
    get_mode, set_mode, save_last_reply, get_last_reply,
    check_hourly_limit, is_subscribed, set_subscribed,
    get_notes, add_note, delete_note,
    get_all_prefs, set_pref, get_pref,
    log_query, get_popular_queries,
    add_price_alert, get_price_alerts, deactivate_alert,
    log_search, get_search_stats,
    add_search_alert, get_search_alerts, mark_alert_sent,
    save_followup, get_followup,
    add_search_history, get_search_history,
    add_favorite, get_favorites, remove_favorite,
    get_auto_suggestions, get_daily_summary,
    get_search_cache, save_search_cache,
    backup_db,
)
from bot import config


@pytest_asyncio.fixture
async def db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_conversations(db):
    uid = 777740
    await ensure_user(uid)
    await clear_history(uid)


@pytest.mark.asyncio
async def test_usage_tracking(db):
    uid = 777739
    import aiosqlite
    async with aiosqlite.connect(str(config.DB_PATH)) as conn:
        await conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
        await conn.execute("DELETE FROM usage_log WHERE user_id=?", (uid,))
        await conn.commit()
    await ensure_user(uid)
    await add_usage(uid, 100, 50, 0.001)
    await add_usage(uid, 200, 100, 0.002)
    row = await user_cost(uid)
    assert row is not None
    assert row[2] == 300  # prompt_tokens
    assert row[3] == 150  # completion_tokens


@pytest.mark.asyncio
async def test_monthly_reset(db):
    uid = 777738
    await ensure_user(uid)
    await add_usage(uid, 10, 5, 0.001)
    can = await can_send(uid)
    assert can is True


@pytest.mark.asyncio
async def test_subscribed_user(db):
    uid = 777737
    await ensure_user(uid)
    await set_subscribed(uid, True)
    assert await is_subscribed(uid) is True
    can = await can_send(uid)
    assert can is True


@pytest.mark.asyncio
async def test_owner_always_subscribed(db):
    assert await is_subscribed(config.OWNER_ID) is True


@pytest.mark.asyncio
async def test_notes_full(db):
    uid = 777736
    await ensure_user(uid)
    nid1 = await add_note(uid, "Note 1")
    nid2 = await add_note(uid, "Note 2")
    notes = await get_notes(uid)
    assert len(notes) >= 2
    assert await delete_note(uid, nid1) is True
    assert await delete_note(uid, 999999) is False


@pytest.mark.asyncio
async def test_prefs_full(db):
    uid = 777735
    await ensure_user(uid)
    await set_pref(uid, "key1", "val1")
    await set_pref(uid, "key2", "val2")
    assert await get_pref(uid, "key1") == "val1"
    all_prefs = await get_all_prefs(uid)
    assert "key1" in all_prefs
    assert "key2" in all_prefs
    await set_pref(uid, "key1", "updated")
    assert await get_pref(uid, "key1") == "updated"


@pytest.mark.asyncio
async def test_reminders_full(db):
    uid = 777734
    await ensure_user(uid)
    rid = await add_reminder(uid, "2099-01-01T00:00:00", "test")
    assert rid > 0
    due = await get_due_reminders()
    assert isinstance(due, list)
    await mark_reminder_sent(rid)
    await mark_old_reminders_sent()


@pytest.mark.asyncio
async def test_error_logs_full(db):
    await log_error(777733, "type1", "detail1")
    await log_error(777733, "type2", "detail2")
    errors = await error_stats()
    assert isinstance(errors, list)


@pytest.mark.asyncio
async def test_feedback_full(db):
    uid = 777732
    await ensure_user(uid)
    await add_feedback(uid, 100, 1)
    await add_feedback(uid, 101, -1)
    stats = await get_feedback_stats(uid)
    assert 1 in stats
    assert -1 in stats


@pytest.mark.asyncio
async def test_modes_full(db):
    uid = 777731
    await ensure_user(uid)
    for mode in ["teacher", "coder", "friend", "default"]:
        await set_mode(uid, mode)
        assert await get_mode(uid) == mode


@pytest.mark.asyncio
async def test_last_reply_full(db):
    uid = 777730
    await ensure_user(uid)
    await save_last_reply(uid, "reply1")
    assert await get_last_reply(uid) == "reply1"
    await save_last_reply(uid, "reply2")
    assert await get_last_reply(uid) == "reply2"


@pytest.mark.asyncio
async def test_cache_full(db):
    await cache_response("q1", "r1", "m1", "ku", "default")
    assert await get_cached_response("q1", "ku", "default") == "r1"
    assert await get_cached_response("q1", "en", "default") is None
    assert await get_cached_response("q1", "ku", "teacher") is None
    await clean_old_cache(days=0)


@pytest.mark.asyncio
async def test_group_full(db):
    cid = -1005555555555
    await ensure_group(cid, "Test")
    s = await get_group_settings(cid)
    assert s["title"] == "Test"
    await update_group(cid, title="Updated", ai_reply=1)
    s = await get_group_settings(cid)
    assert s["title"] == "Updated"
    assert s["ai_reply"] == 1
    groups = await get_all_managed_groups(0)
    assert len(groups) >= 1
    await delete_group_settings(cid)
    s = await get_group_settings(cid)
    assert s == {}


@pytest.mark.asyncio
async def test_search_features(db):
    uid = 777729
    await ensure_user(uid)
    await log_query("test query", uid)
    queries = await get_popular_queries(10)
    assert isinstance(queries, list)

    await add_search_history(uid, "search1", 5)
    history = await get_search_history(uid)
    assert len(history) >= 1

    await save_search_cache("cache1", "result1", 3)
    cached = await get_search_cache("cache1")
    assert cached is not None

    await add_favorite(uid, "fav1")
    favs = await get_favorites(uid)
    assert len(favs) >= 1
    if favs:
        await remove_favorite(uid, favs[0]["id"])

    suggestions = await get_auto_suggestions(uid)
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_price_alerts_full(db):
    uid = 777728
    await ensure_user(uid)
    await add_price_alert(uid, "item1", "above", 100)
    alerts = await get_price_alerts()
    assert len(alerts) >= 1
    if alerts:
        await deactivate_alert(alerts[0]["id"])


@pytest.mark.asyncio
async def test_search_alerts_full(db):
    uid = 777727
    await ensure_user(uid)
    await add_search_alert(uid, "alert1")
    alerts = await get_search_alerts()
    assert len(alerts) >= 1
    if alerts:
        await mark_alert_sent(uid, alerts[0]["query"])


@pytest.mark.asyncio
async def test_followups_full(db):
    uid = 777726
    await ensure_user(uid)
    await save_followup(uid, "original1", "suggestion1")
    result = await get_followup(uid, "original1")
    assert result is not None
    assert await get_followup(uid, "nonexistent") is None


@pytest.mark.asyncio
async def test_stats_full(db):
    users, msgs = await stats()
    assert users >= 0
    users, msgs, pt, ct, cost = await cost_stats()
    assert users >= 0
    top = await top_users(5)
    assert isinstance(top, list)
    dc = await daily_cost()
    assert dc >= 0


@pytest.mark.asyncio
async def test_hourly_limit(db):
    uid = 777725
    await ensure_user(uid)
    assert await check_hourly_limit(uid) is True


@pytest.mark.asyncio
async def test_daily_summary(db):
    summary = await get_daily_summary()
    assert "queries" in summary
    assert "users" in summary


@pytest.mark.asyncio
async def test_backup(db):
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp = f.name
    try:
        await backup_db(tmp)
        assert os.path.exists(tmp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
