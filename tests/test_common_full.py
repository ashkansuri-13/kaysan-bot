"""Comprehensive tests for bot.handlers.common — full coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.common import (
    cmd_start, cmd_help, cmd_lang, cb_lang,
    cb_back_lang, cmd_image, cmd_clear, cb_quick,
    _get_user_profile, _analyze_profile,
)


def make_message(text="/test", user_id=123):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.from_user.username = "testuser"
    msg.answer = AsyncMock()
    msg.bot = AsyncMock()
    return msg


def make_callback(data="test", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.message.answer = AsyncMock()
    call.message.delete = AsyncMock()
    call.answer = AsyncMock()
    return call


class TestCommonFull:
    @pytest.mark.asyncio
    async def test_start(self):
        msg = make_message("/start")
        with patch("bot.handlers.common.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.common.core.enforce_channel", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.common.t", return_value="Welcome"):
            await cmd_start(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_help(self):
        msg = make_message("/help")
        with patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.common.t", return_value="Help"):
            await cmd_help(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_lang(self):
        msg = make_message("/lang")
        with patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"):
            await cmd_lang(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_lang(self):
        call = make_callback("lang:en")
        with patch("bot.handlers.common.db.set_lang", new_callable=AsyncMock), \
             patch("bot.handlers.common.t", return_value="Language set"):
            await cb_lang(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_back_lang(self):
        call = make_callback("back:lang")
        with patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.common.t", return_value="Choose lang"):
            await cb_back_lang(call)
            call.message.answer.assert_called()

    @pytest.mark.asyncio
    async def test_image(self):
        msg = make_message("/image cat")
        with patch("bot.handlers.common.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.common.core.enforce_limit", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.common.core._do_image", new_callable=AsyncMock):
            await cmd_image(msg)

    @pytest.mark.asyncio
    async def test_image_no_args(self):
        msg = make_message("/image")
        with patch("bot.handlers.common.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.common.core.enforce_limit", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.common.t", return_value="Enter prompt"):
            await cmd_image(msg)

    @pytest.mark.asyncio
    async def test_clear(self):
        msg = make_message("/clear")
        with patch("bot.handlers.common.db.clear_history", new_callable=AsyncMock), \
             patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"):
            await cmd_clear(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_quick(self):
        call = make_callback("quick:joke")
        with patch("bot.handlers.common.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.common.core.process_text", new_callable=AsyncMock):
            await cb_quick(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        bot = AsyncMock()
        user = MagicMock()
        user.id = 123
        user.full_name = "Test"
        user.username = "test"
        bot.get_chat = AsyncMock(return_value=MagicMock(bio="Test bio"))
        bot.get_user_profile_photos = AsyncMock(return_value=MagicMock(photos=[]))
        result = await _get_user_profile(bot, user)
        assert result["name"] == "Test"
        assert result["bio"] == "Test bio"

    @pytest.mark.asyncio
    async def test_analyze_profile(self):
        info = {"name": "Test", "username": "test", "bio": "bio", "photos": []}
        with patch("bot.handlers.common.openrouter.chat", new_callable=AsyncMock, return_value=("Analysis\nCompliment", {})):
            analysis, compliment = await _analyze_profile(info, "en")
            assert len(analysis) > 0
