"""Comprehensive tests for bot.handlers.extras, quiz, remind, translate, notes — full coverage."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.extras import (
    cmd_weather, cmd_convert, cmd_fal, cmd_mode, cb_mode, cmd_wordle,
    _HAFEZ_POEMS, _WORDLE_WORDS, _MODES, _MODE_KEYBOARD,
)
from bot.handlers.quiz import cmd_quiz, cb_quiz, cmd_riddle, cmd_joke, _QUIZ_CACHE
from bot.handlers.remind import cmd_remind, _parse_time
from bot.handlers.translate import cmd_translate, cmd_summarize
from bot.handlers.notes import cmd_note, cmd_notes, cmd_delnote
from bot.handlers.media import on_voice, on_photo


def make_message(text="/test", user_id=123):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.bot = AsyncMock()
    msg.caption = None
    return msg


def make_callback(data="test:1", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.message.edit_reply_markup = AsyncMock()
    call.answer = AsyncMock()
    return call


class TestExtrasFull:
    @pytest.mark.asyncio
    async def test_weather_no_args(self):
        msg = make_message("/weather")
        await cmd_weather(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_convert_no_args(self):
        msg = make_message("/convert")
        await cmd_convert(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_fal(self):
        msg = make_message("/fal")
        await cmd_fal(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_mode(self):
        msg = make_message("/mode")
        await cmd_mode(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_mode(self):
        call = make_callback("mode:teacher")
        with patch("bot.handlers.extras.db.set_mode", new_callable=AsyncMock), \
             patch("bot.handlers.extras.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.extras.t", return_value="Mode set"):
            await cb_mode(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_mode_invalid(self):
        call = make_callback("mode:invalid")
        await cb_mode(call)
        call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_wordle(self):
        msg = make_message("/wordle")
        with patch("bot.handlers.extras.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.extras.db.set_pref", new_callable=AsyncMock):
            await cmd_wordle(msg)
            msg.answer.assert_called()

    def test_hafez_poems(self):
        assert len(_HAFEZ_POEMS) > 0
        for poem, interp in _HAFEZ_POEMS:
            assert len(poem) > 10
            assert len(interp) > 10

    def test_wordle_words(self):
        assert len(_WORDLE_WORDS) > 0

    def test_modes(self):
        assert "teacher" in _MODES
        assert "coder" in _MODES
        assert "friend" in _MODES
        assert "default" in _MODES


class TestQuizFull:
    @pytest.mark.asyncio
    async def test_quiz(self):
        msg = make_message("/quiz")
        with patch("bot.handlers.quiz.openrouter.chat", new_callable=AsyncMock, return_value=('{"question":"Q?","options":["A) x","B) y","C) z","D) w"],"answer":"A"}', {})):
            await cmd_quiz(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_quiz_error(self):
        msg = make_message("/quiz")
        with patch("bot.handlers.quiz.openrouter.chat", new_callable=AsyncMock, side_effect=Exception("error")):
            await cmd_quiz(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_riddle(self):
        msg = make_message("/riddle")
        with patch("bot.handlers.quiz.openrouter.chat", new_callable=AsyncMock, return_value=("Riddle\nAnswer: test", {})):
            await cmd_riddle(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_riddle_error(self):
        msg = make_message("/riddle")
        with patch("bot.handlers.quiz.openrouter.chat", new_callable=AsyncMock, side_effect=Exception("error")):
            await cmd_riddle(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_joke(self):
        msg = make_message("/joke")
        with patch("bot.handlers.quiz.openrouter.chat", new_callable=AsyncMock, return_value=("Joke", {})):
            await cmd_joke(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_joke_error(self):
        msg = make_message("/joke")
        with patch("bot.handlers.quiz.openrouter.chat", new_callable=AsyncMock, side_effect=Exception("error")):
            await cmd_joke(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_quiz_correct(self):
        _QUIZ_CACHE[123] = {"answer": "A", "question": "Q?"}
        call = make_callback("quiz:A")
        await cb_quiz(call)
        call.message.edit_text.assert_called()
        _QUIZ_CACHE.pop(123, None)

    @pytest.mark.asyncio
    async def test_cb_quiz_wrong(self):
        _QUIZ_CACHE[123] = {"answer": "A", "question": "Q?"}
        call = make_callback("quiz:B")
        await cb_quiz(call)
        call.message.edit_text.assert_called()
        _QUIZ_CACHE.pop(123, None)

    @pytest.mark.asyncio
    async def test_cb_quiz_no_cache(self):
        call = make_callback("quiz:A")
        await cb_quiz(call)
        call.answer.assert_called()


class TestRemindFull:
    @pytest.mark.asyncio
    async def test_remind_no_args(self):
        msg = make_message("/remind")
        await cmd_remind(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_remind_invalid(self):
        msg = make_message("/remind invalid")
        await cmd_remind(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_remind_valid(self):
        msg = make_message("/remind 5m test")
        with patch("bot.handlers.remind.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.remind.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.remind.db.add_reminder", new_callable=AsyncMock, return_value=1):
            await cmd_remind(msg)
            msg.answer.assert_called()

    def test_parse_time_all_units(self):
        d, m = _parse_time("30s hello")
        assert d.seconds == 30
        d, m = _parse_time("5m test")
        assert d.seconds == 300
        d, m = _parse_time("2h test")
        assert d.seconds == 7200
        d, m = _parse_time("1d test")
        assert d.days == 1
        d, m = _parse_time("1w test")
        assert d.days == 7

    def test_parse_time_invalid(self):
        d, m = _parse_time("invalid")
        assert d is None


class TestTranslateFull:
    @pytest.mark.asyncio
    async def test_translate_no_args(self):
        msg = make_message("/translate")
        await cmd_translate(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_summarize_no_args(self):
        msg = make_message("/summarize")
        await cmd_summarize(msg)
        msg.answer.assert_called()


class TestNotesFull:
    @pytest.mark.asyncio
    async def test_note_no_args(self):
        msg = make_message("/note")
        with patch("bot.handlers.notes.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"):
            await cmd_note(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_note_add(self):
        msg = make_message("/note test note")
        with patch("bot.handlers.notes.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.notes.db.add_note", new_callable=AsyncMock, return_value=1):
            await cmd_note(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_notes_empty(self):
        msg = make_message("/notes")
        with patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.notes.db.get_notes", new_callable=AsyncMock, return_value=[]):
            await cmd_notes(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_notes_list(self):
        msg = make_message("/notes")
        with patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.notes.db.get_notes", new_callable=AsyncMock, return_value=[{"id": 1, "content": "test", "created_at": "2024-01-01"}]):
            await cmd_notes(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_delnote_no_args(self):
        msg = make_message("/delnote")
        with patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"):
            await cmd_delnote(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_delnote_invalid(self):
        msg = make_message("/delnote abc")
        with patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"):
            await cmd_delnote(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_delnote_not_found(self):
        msg = make_message("/delnote 999")
        with patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.notes.db.delete_note", new_callable=AsyncMock, return_value=False):
            await cmd_delnote(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_delnote_success(self):
        msg = make_message("/delnote 1")
        with patch("bot.handlers.notes.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.notes.db.delete_note", new_callable=AsyncMock, return_value=True):
            await cmd_delnote(msg)
            msg.answer.assert_called()


class TestMediaFull:
    @pytest.mark.asyncio
    async def test_on_photo_no_caption(self):
        msg = make_message("/test")
        msg.caption = None
        msg.photo = [MagicMock()]
        with patch("bot.handlers.media.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.media.core.enforce_channel", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.media.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.media.core.enforce_limit", new_callable=AsyncMock, return_value=True):
            await on_photo(msg)
