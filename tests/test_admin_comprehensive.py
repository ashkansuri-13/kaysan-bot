"""Comprehensive tests for bot.handlers.admin — mocked Telegram API."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.admin import (
    cmd_grant, cmd_revoke, cmd_stats, cmd_testmodels,
    cmd_searchchannels, cmd_testsearch, cmd_popular,
    cmd_searchstats, cmd_alert, cmd_cost, _is_owner,
)


def make_message(text="/stats", user_id=123):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.answer = AsyncMock()
    msg.bot = AsyncMock()
    return msg


class TestIsOwner:
    def test_owner(self):
        msg = make_message()
        msg.from_user.id = 6278069364
        with patch("bot.handlers.admin.config.OWNER_ID", 6278069364):
            assert _is_owner(msg) is True

    def test_not_owner(self):
        msg = make_message()
        msg.from_user.id = 999
        with patch("bot.handlers.admin.config.OWNER_ID", 6278069364):
            assert _is_owner(msg) is False


class TestAdminCommands:
    @pytest.mark.asyncio
    async def test_grant(self):
        msg = make_message("/grant 123")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.admin.db.set_subscribed", new_callable=AsyncMock), \
             patch("bot.handlers.admin.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.admin.t", return_value="granted"):
            await cmd_grant(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_revoke(self):
        msg = make_message("/revoke 123")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.set_subscribed", new_callable=AsyncMock):
            await cmd_revoke(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_stats(self):
        msg = make_message("/stats")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.stats", new_callable=AsyncMock, return_value=(10, 100)):
            await cmd_stats(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_searchchannels(self):
        msg = make_message("/searchchannels")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.config.SEARCH_CHANNELS", ["ch1", "ch2"]):
            await cmd_searchchannels(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cost(self):
        msg = make_message("/cost")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.cost_stats", new_callable=AsyncMock, return_value=(10, 100, 1000, 500, 0.5)), \
             patch("bot.handlers.admin.db.top_users", new_callable=AsyncMock, return_value=[]), \
             patch("bot.handlers.admin.db.error_stats", new_callable=AsyncMock, return_value=[]):
            await cmd_cost(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_alert(self):
        msg = make_message("/alert دلار بالای 60000")
        with patch("bot.handlers.admin.db.add_price_alert", new_callable=AsyncMock):
            await cmd_alert(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_not_owner(self):
        msg = make_message("/stats")
        with patch("bot.handlers.admin._is_owner", return_value=False):
            await cmd_stats(msg)
            msg.answer.assert_called()
