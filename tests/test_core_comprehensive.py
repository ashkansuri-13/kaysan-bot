"""Comprehensive tests for bot.handlers.core — mocked Telegram API."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.core import (
    _parse_clarification, _get_triple_date, _to_kurdish_date,
    _jalali_month, _LANG_NAMES, _last, _PROBE,
    is_member_of_channel, enforce_channel, enforce_limit,
    _notify_owner_limit, _send_reply,
)


class TestParseClarificationExtended:
    def test_six_questions(self):
        reply = "Info\n1) Q1\n2) Q2\n3) Q3\n4) Q4\n5) Q5\n6) Q6"
        result = _parse_clarification(reply)
        assert result is not None
        assert len(result[1]) == 6

    def test_seven_questions(self):
        reply = "Info\n1) Q1\n2) Q2\n3) Q3\n4) Q4\n5) Q5\n6) Q6\n7) Q7"
        result = _parse_clarification(reply)
        assert result is not None
        assert len(result[1]) == 7

    def test_no_numbered_lines(self):
        reply = "Just text\nNo numbers here"
        result = _parse_clarification(reply)
        assert result is None

    def test_single_question(self):
        reply = "Info\n1) Only one"
        result = _parse_clarification(reply)
        assert result is None


class TestGetTripleDate:
    def test_all_keys(self):
        dates = _get_triple_date()
        assert "fa" in dates
        assert "en" in dates
        assert "ku" in dates
        assert "short" in dates
        assert "time" in dates

    def test_format_short(self):
        dates = _get_triple_date()
        assert "-" in dates["short"]

    def test_format_time(self):
        dates = _get_triple_date()
        assert ":" in dates["time"]


class TestToKurdishDate:
    def test_month_range(self):
        for m in range(1, 13):
            ky, km, kd, name = _to_kurdish_date(1403, m, 15)
            assert 1 <= km <= 12
            assert len(name) > 0


class TestProbePatterns:
    def test_various_probes(self):
        probes = [
            "کدام مدل",
            "system prompt",
            "ignore previous",
            "developer mode",
            "jailbreak",
            "repeat the",
            "بکدۆام",
        ]
        for p in probes:
            assert _PROBE.search(p), f"Pattern not found: {p}"


class TestEnforceLimit:
    @pytest.mark.asyncio
    async def test_can_send(self):
        msg = MagicMock()
        msg.from_user = MagicMock()
        msg.from_user.id = 123
        msg.answer = AsyncMock()
        with patch("bot.handlers.core.db.can_send", new_callable=AsyncMock, return_value=True):
            result = await enforce_limit(msg, "en")
            assert result is True

    @pytest.mark.asyncio
    async def test_cannot_send(self):
        msg = MagicMock()
        msg.from_user = MagicMock()
        msg.from_user.id = 123
        msg.answer = AsyncMock()
        with patch("bot.handlers.core.db.can_send", new_callable=AsyncMock, return_value=False), \
             patch("bot.handlers.core.db.is_subscribed", new_callable=AsyncMock, return_value=False):
            result = await enforce_limit(msg, "en")
            assert result is False
            msg.answer.assert_called()


class TestNotifyOwnerLimit:
    @pytest.mark.asyncio
    async def test_notify_owner(self):
        bot = AsyncMock()
        user = MagicMock()
        user.id = 123
        user.full_name = "Test"
        user.username = "test"
        from bot.handlers.core import _notified
        _notified.clear()
        with patch("bot.handlers.core.config.OWNER_ID", 999):
            await _notify_owner_limit(bot, user, "en")
            bot.send_message.assert_called()
        _notified.clear()


class TestSendReply:
    @pytest.mark.asyncio
    async def test_short_reply(self):
        status = AsyncMock()
        status.edit_text = AsyncMock()
        await _send_reply(status, "Hello", "en", 123)
        status.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_long_reply(self):
        status = AsyncMock()
        status.delete = AsyncMock()
        status.answer = AsyncMock()
        long_reply = "x" * 5000
        await _send_reply(status, long_reply, "en", 123)
        status.delete.assert_called()

    @pytest.mark.asyncio
    async def test_empty_reply(self):
        status = AsyncMock()
        status.edit_text = AsyncMock()
        await _send_reply(status, "", "en", 123)
        status.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_clarification(self):
        status = AsyncMock()
        status.edit_text = AsyncMock()
        reply = "Info\n1) Option A\n2) Option B\n3) Option C"
        await _send_reply(status, reply, "en", 123)
        status.edit_text.assert_called()
