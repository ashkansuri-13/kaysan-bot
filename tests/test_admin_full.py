"""Comprehensive tests for bot.handlers.admin — full coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.admin import (
    cmd_grant, cmd_revoke, cmd_stats, cmd_testmodels,
    cmd_searchchannels, cmd_testsearch, cmd_popular,
    cmd_searchstats, cmd_alert, cmd_cost, _is_owner,
)


def make_message(text="/test", user_id=123):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.answer = AsyncMock()
    msg.bot = AsyncMock()
    return msg


class TestAdminFull:
    @pytest.mark.asyncio
    async def test_grant_no_args(self):
        msg = make_message("/grant")
        with patch("bot.handlers.admin._is_owner", return_value=True):
            await cmd_grant(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_grant_invalid(self):
        msg = make_message("/grant abc")
        with patch("bot.handlers.admin._is_owner", return_value=True):
            await cmd_grant(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_grant_ok(self):
        msg = make_message("/grant 123")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.admin.db.set_subscribed", new_callable=AsyncMock), \
             patch("bot.handlers.admin.db.get_lang", new_callable=AsyncMock, return_value="en"):
            await cmd_grant(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_no_args(self):
        msg = make_message("/revoke")
        with patch("bot.handlers.admin._is_owner", return_value=True):
            await cmd_revoke(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_ok(self):
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
    async def test_testmodels(self):
        msg = make_message("/testmodels")
        with patch("bot.handlers.admin._is_owner", return_value=True):
            await cmd_testmodels(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_searchchannels(self):
        msg = make_message("/searchchannels")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.config.SEARCH_CHANNELS", ["ch1"]):
            await cmd_searchchannels(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_searchchannels_empty(self):
        msg = make_message("/searchchannels")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.config.SEARCH_CHANNELS", []):
            await cmd_searchchannels(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_popular(self):
        msg = make_message("/popular")
        with patch("bot.handlers.admin._is_owner", return_value=True):
            await cmd_popular(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_searchstats(self):
        msg = make_message("/searchstats")
        with patch("bot.handlers.admin._is_owner", return_value=True):
            await cmd_searchstats(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_alert_no_args(self):
        msg = make_message("/alert")
        await cmd_alert(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_alert_invalid(self):
        msg = make_message("/alert invalid format")
        await cmd_alert(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_alert_ok(self):
        msg = make_message("/alert dollar above 60000")
        with patch("bot.handlers.admin.db.add_price_alert", new_callable=AsyncMock):
            await cmd_alert(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cost_no_args(self):
        msg = make_message("/cost")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.cost_stats", new_callable=AsyncMock, return_value=(10, 100, 1000, 500, 0.5)), \
             patch("bot.handlers.admin.db.top_users", new_callable=AsyncMock, return_value=[]), \
             patch("bot.handlers.admin.db.error_stats", new_callable=AsyncMock, return_value=[]):
            await cmd_cost(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cost_with_user(self):
        msg = make_message("/cost 123")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.user_cost", new_callable=AsyncMock, return_value=("name", 10, 100, 50, 0.1)):
            await cmd_cost(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cost_user_not_found(self):
        msg = make_message("/cost 999")
        with patch("bot.handlers.admin._is_owner", return_value=True), \
             patch("bot.handlers.admin.db.user_cost", new_callable=AsyncMock, return_value=None):
            await cmd_cost(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_not_owner(self):
        msg = make_message("/stats")
        with patch("bot.handlers.admin._is_owner", return_value=False):
            await cmd_stats(msg)
            msg.answer.assert_called()

    def test_is_owner_true(self):
        msg = make_message()
        msg.from_user.id = 6278069364
        with patch("bot.handlers.admin.config.OWNER_ID", 6278069364):
            assert _is_owner(msg) is True

    def test_is_owner_false(self):
        msg = make_message()
        msg.from_user.id = 999
        with patch("bot.handlers.admin.config.OWNER_ID", 6278069364):
            assert _is_owner(msg) is False
