"""Additional unit tests for bot.database — more coverage."""
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
    check_hourly_limit,
)


@pytest_asyncio.fixture
async def db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_stats(db):
    users, msgs = await stats()
    assert users >= 0
    assert msgs >= 0


@pytest.mark.asyncio
async def test_cost_stats(db):
    users, msgs, pt, ct, cost = await cost_stats()
    assert users >= 0


@pytest.mark.asyncio
async def test_user_cost(db):
    await ensure_user(777770)
    row = await user_cost(777770)
    assert row is not None


@pytest.mark.asyncio
async def test_top_users(db):
    result = await top_users(5)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_daily_cost(db):
    cost = await daily_cost()
    assert cost >= 0


@pytest.mark.asyncio
async def test_reminders(db):
    await ensure_user(777769)
    rid = await add_reminder(777769, "2099-01-01T00:00:00", "test reminder")
    assert rid > 0
    await mark_reminder_sent(rid)


@pytest.mark.asyncio
async def test_error_logs(db):
    await log_error(777768, "test_error", "test details")
    errors = await error_stats()
    assert isinstance(errors, list)


@pytest.mark.asyncio
async def test_feedback(db):
    await ensure_user(777767)
    await add_feedback(777767, 12345, 1)
    stats = await get_feedback_stats(777767)
    assert isinstance(stats, dict)


@pytest.mark.asyncio
async def test_modes(db):
    await ensure_user(777766)
    await set_mode(777766, "teacher")
    mode = await get_mode(777766)
    assert mode == "teacher"


@pytest.mark.asyncio
async def test_last_reply(db):
    await ensure_user(777765)
    await save_last_reply(777765, "test reply")
    reply = await get_last_reply(777765)
    assert reply == "test reply"


@pytest.mark.asyncio
async def test_hourly_limit(db):
    await ensure_user(777764)
    can = await check_hourly_limit(777764)
    assert can is True


@pytest.mark.asyncio
async def test_clean_old_cache(db):
    await cache_response("test_to_clean", "value", "model", "ku", "default")
    cached = await get_cached_response("test_to_clean", "ku", "default")
    assert cached == "value"
    await clean_old_cache(days=30)
    cached2 = await get_cached_response("test_to_clean", "ku", "default")
    assert cached2 == "value"


@pytest.mark.asyncio
async def test_delete_group(db):
    cid = -1006666666666
    await ensure_group(cid, "To Delete")
    await delete_group_settings(cid)
    s = await get_group_settings(cid)
    assert s == {}
