"""Comprehensive tests for bot.handlers.actions — full coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.actions import (
    cb_regen, cb_toimg, cb_tts, cb_clarify,
    cb_feedback_like, cb_feedback_dislike,
)


def make_callback(data="test", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.message.edit_reply_markup = AsyncMock()
    call.message.answer = AsyncMock()
    call.message.delete = AsyncMock()
    call.answer = AsyncMock()
    return call


class TestActionsFull:
    @pytest.mark.asyncio
    async def test_regen_no_last(self):
        call = make_callback("regen")
        with patch("bot.handlers.actions.core.get_last", return_value=None):
            await cb_regen(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_regen_no_limit(self):
        call = make_callback("regen")
        with patch("bot.handlers.actions.core.get_last", return_value={"text": "test", "lang": "en"}), \
             patch("bot.handlers.actions.db.can_send", new_callable=AsyncMock, return_value=False):
            await cb_regen(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_regen_ok(self):
        call = make_callback("regen")
        with patch("bot.handlers.actions.core.get_last", return_value={"text": "test", "lang": "en"}), \
             patch("bot.handlers.actions.db.can_send", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.actions.core.process_text", new_callable=AsyncMock):
            await cb_regen(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_toimg_no_last(self):
        call = make_callback("toimg")
        with patch("bot.handlers.actions.core.get_last", return_value=None):
            await cb_toimg(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_toimg_no_limit(self):
        call = make_callback("toimg")
        with patch("bot.handlers.actions.core.get_last", return_value={"text": "test", "lang": "en"}), \
             patch("bot.handlers.actions.db.can_send", new_callable=AsyncMock, return_value=False):
            await cb_toimg(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_toimg_ok(self):
        call = make_callback("toimg")
        with patch("bot.handlers.actions.core.get_last", return_value={"text": "test", "lang": "en"}), \
             patch("bot.handlers.actions.db.can_send", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.actions.core._do_image", new_callable=AsyncMock):
            await cb_toimg(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_tts_no_reply(self):
        call = make_callback("tts")
        with patch("bot.handlers.actions.core.get_last", return_value=None), \
             patch("bot.handlers.actions.db.get_last_reply", new_callable=AsyncMock, return_value=None):
            await cb_tts(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_tts_with_last(self):
        call = make_callback("tts")
        with patch("bot.handlers.actions.core.get_last", return_value={"reply": "test reply"}), \
             patch("bot.handlers.actions.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.actions.db.can_send", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.actions.text_to_speech", new_callable=AsyncMock, return_value=b"audio"):
            await cb_tts(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_clarify_short(self):
        call = make_callback("clarify:0:question")
        with patch("bot.handlers.actions.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.actions.core.process_text", new_callable=AsyncMock):
            await cb_clarify(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_clarify_invalid(self):
        call = make_callback("clarify:")
        await cb_clarify(call)
        call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_feedback_like(self):
        call = make_callback("feedback_like")
        with patch("bot.handlers.actions.db.add_feedback", new_callable=AsyncMock):
            await cb_feedback_like(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_feedback_dislike(self):
        call = make_callback("feedback_dislike")
        with patch("bot.handlers.actions.db.add_feedback", new_callable=AsyncMock):
            await cb_feedback_dislike(call)
            call.answer.assert_called()
