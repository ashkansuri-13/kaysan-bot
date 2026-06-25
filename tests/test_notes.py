"""Unit tests for bot.handlers.notes."""
import pytest
import pytest_asyncio
from bot.database import init_db, ensure_user, add_note, get_notes, delete_note


@pytest_asyncio.fixture
async def db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_add_note(db):
    await ensure_user(888888)
    note_id = await add_note(888888, "Test note content")
    assert note_id > 0


@pytest.mark.asyncio
async def test_get_notes(db):
    await ensure_user(888887)
    await add_note(888887, "Note 1")
    await add_note(888887, "Note 2")
    notes = await get_notes(888887)
    assert len(notes) >= 2


@pytest.mark.asyncio
async def test_delete_note(db):
    await ensure_user(888886)
    note_id = await add_note(888886, "To be deleted")
    deleted = await delete_note(888886, note_id)
    assert deleted is True
    notes = await get_notes(888886)
    assert len(notes) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent(db):
    deleted = await delete_note(888885, 999999)
    assert deleted is False
