"""Additional database tests for better coverage."""
import pytest
import pytest_asyncio
from bot.database import (
    init_db, ensure_user, get_lang, set_lang, can_send,
    add_usage, clear_history,
    get_cached_response, cache_response, clean_old_cache,
    ensure_group, get_group_settings, update_group,
    get_all_managed_groups, delete_group_settings,
    stats, cost_stats, user_cost, top_users, daily_cost,
    add_reminder, get_due_reminders, mark_reminder_sent,
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
    get_auto_suggestions, get_daily_summary, get_search_cache, save_search_cache,
)


@pytest_asyncio.fixture
async def db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_is_subscribed(db):
    uid = 777760
    import aiosqlite
    from bot import config
    async with aiosqlite.connect(str(config.DB_PATH)) as conn:
        await conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
        await conn.commit()
    await ensure_user(uid)
    assert await is_subscribed(uid) is False
    await set_subscribed(uid, True)
    assert await is_subscribed(uid) is True


@pytest.mark.asyncio
async def test_notes(db):
    await ensure_user(777759)
    nid = await add_note(777759, "Test note")
    assert nid > 0
    notes = await get_notes(777759)
    assert len(notes) >= 1
    assert await delete_note(777759, nid) is True


@pytest.mark.asyncio
async def test_prefs(db):
    await ensure_user(777758)
    await set_pref(777758, "theme", "dark")
    val = await get_pref(777758, "theme")
    assert val == "dark"
    all_prefs = await get_all_prefs(777758)
    assert "theme" in all_prefs


@pytest.mark.asyncio
async def test_popular_queries(db):
    await log_query("test query", 777757)
    queries = await get_popular_queries(10)
    assert isinstance(queries, list)


@pytest.mark.asyncio
async def test_price_alerts(db):
    await ensure_user(777756)
    await add_price_alert(777756, "dollar", "above", 60000)
    alerts = await get_price_alerts()
    assert len(alerts) >= 1
    if alerts:
        await deactivate_alert(alerts[0]["id"])


@pytest.mark.asyncio
async def test_search_stats(db):
    stats = await get_search_stats(7)
    assert isinstance(stats, dict)
    assert "total" in stats


@pytest.mark.asyncio
async def test_search_alerts(db):
    await ensure_user(777755)
    await add_search_alert(777755, "test alert")
    alerts = await get_search_alerts()
    assert len(alerts) >= 1


@pytest.mark.asyncio
async def test_followups(db):
    await ensure_user(777754)
    await save_followup(777754, "original", "suggestion1\nsuggestion2")
    result = await get_followup(777754, "original")
    assert result is not None


@pytest.mark.asyncio
async def test_search_history(db):
    await ensure_user(777753)
    await add_search_history(777753, "test search", 5)
    history = await get_search_history(777753)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_favorites(db):
    await ensure_user(777752)
    await add_favorite(777752, "test fav")
    favs = await get_favorites(777752)
    assert len(favs) >= 1
    if favs:
        assert await remove_favorite(777752, favs[0]["id"]) is True


@pytest.mark.asyncio
async def test_auto_suggestions(db):
    await ensure_user(777751)
    await add_search_history(777751, "suggestion test", 1)
    suggestions = await get_auto_suggestions(777751)
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_daily_summary(db):
    summary = await get_daily_summary()
    assert isinstance(summary, dict)
    assert "searches" in summary


@pytest.mark.asyncio
async def test_search_cache(db):
    await save_search_cache("cache test", "result", 3)
    cached = await get_search_cache("cache test")
    assert cached is not None
    assert cached["results"] == "result"
