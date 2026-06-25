"""Unit tests for bot.database."""
import pytest
import pytest_asyncio
import aiosqlite
from bot import config
from bot.database import (
    init_db, ensure_user, get_lang, set_lang, can_send,
    add_usage, clear_history,
    get_cached_response, cache_response,
    ensure_group, get_group_settings, update_group,
)


@pytest_asyncio.fixture
async def db():
    await init_db()
    yield
    await clear_history(999999)


@pytest.mark.asyncio
async def test_ensure_user(db):
    uid = 999999
    from bot.database import clear_history
    async with aiosqlite.connect(str(config.DB_PATH)) as db_conn:
        await db_conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
        await db_conn.commit()
    await ensure_user(uid, lang="fa", name="test")
    lang = await get_lang(uid)
    assert lang == "fa"


@pytest.mark.asyncio
async def test_set_get_lang(db):
    await ensure_user(999998)
    await set_lang(999998, "ku")
    lang = await get_lang(999998)
    assert lang == "ku"


@pytest.mark.asyncio
async def test_can_send(db):
    await ensure_user(999997)
    can = await can_send(999997)
    assert can is True


@pytest.mark.asyncio
async def test_add_usage(db):
    await ensure_user(999996)
    await add_usage(999996, 100, 50, 0.001)


@pytest.mark.asyncio
async def test_clear_history(db):
    await ensure_user(999995)
    await clear_history(999995)


@pytest.mark.asyncio
async def test_cache(db):
    await cache_response("test_q", "test_r", "model", "ku", "default")
    cached = await get_cached_response("test_q", "ku", "default")
    assert cached == "test_r"
    miss = await get_cached_response("test_q", "en", "default")
    assert miss is None


@pytest.mark.asyncio
async def test_group_settings(db):
    cid = -1007777777777
    await ensure_group(cid, "Test Group")
    s = await get_group_settings(cid)
    assert s is not None
    assert s.get("welcome_on") == 1
    assert s.get("ai_reply") == 0

    await update_group(cid, welcome_text="Hi {name}!")
    s = await get_group_settings(cid)
    assert s.get("welcome_text") == "Hi {name}!"


@pytest.mark.asyncio
async def test_group_settings_validation(db):
    from bot.database import update_group
    with pytest.raises(ValueError):
        await update_group(-100, invalid_field="test")
