"""Comprehensive tests for bot.handlers.core — full coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.core import (
    _parse_clarification, _get_triple_date, _to_kurdish_date,
    _jalali_month, _LANG_NAMES, _last, _PROBE,
    is_member_of_channel, enforce_channel, enforce_limit,
    _notify_owner_limit, _send_reply, _do_image, get_last,
)


def make_message(text="/test", user_id=123, chat_id=-100123, chat_type="private"):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.from_user.username = "testuser"
    msg.chat = MagicMock()
    msg.chat.type = chat_type
    msg.chat.id = chat_id
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.bot = AsyncMock()
    return msg


class TestCoreFull:
    def test_get_last(self):
        _last[123] = {"text": "test"}
        assert get_last(123) is not None
        assert get_last(999) is None
        _last.pop(123, None)

    def test_jalali_month(self):
        months = ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
                  "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"]
        for i in range(1, 13):
            assert _jalali_month(i) == months[i-1]
        assert _jalali_month(0) == ""
        assert _jalali_month(13) == ""

    def test_to_kurdish_date(self):
        ky, km, kd, name = _to_kurdish_date(1403, 1, 15)
        assert 1 <= km <= 12
        assert len(name) > 0

    def test_get_triple_date(self):
        dates = _get_triple_date()
        assert "fa" in dates
        assert "en" in dates
        assert "ku" in dates
        assert "short" in dates
        assert "time" in dates

    def test_parse_clarification(self):
        result = _parse_clarification("Info\n1) Q1\n2) Q2\n3) Q3")
        assert result is not None
        assert len(result[1]) == 3

    def test_parse_clarification_no_questions(self):
        result = _parse_clarification("Just text")
        assert result is None

    def test_parse_clarification_empty(self):
        result = _parse_clarification("")
        assert result is None

    @pytest.mark.asyncio
    async def test_is_member_of_channel(self):
        bot = AsyncMock()
        member = MagicMock()
        member.status = "member"
        bot.get_chat_member = AsyncMock(return_value=member)
        with patch("bot.handlers.core.config.CHANNEL_USERNAME", "test"):
            assert await is_member_of_channel(bot, 123) is True

    @pytest.mark.asyncio
    async def test_is_member_no_channel(self):
        bot = AsyncMock()
        with patch("bot.handlers.core.config.CHANNEL_USERNAME", ""):
            assert await is_member_of_channel(bot, 123) is True

    @pytest.mark.asyncio
    async def test_enforce_channel_ok(self):
        msg = make_message()
        with patch("bot.handlers.core.is_member_of_channel", new_callable=AsyncMock, return_value=True):
            assert await enforce_channel(msg) is True

    @pytest.mark.asyncio
    async def test_enforce_channel_fail(self):
        msg = make_message()
        with patch("bot.handlers.core.is_member_of_channel", new_callable=AsyncMock, return_value=False), \
             patch("bot.handlers.core.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.core.t", return_value="Join channel"):
            assert await enforce_channel(msg) is False

    @pytest.mark.asyncio
    async def test_enforce_limit_ok(self):
        msg = make_message()
        with patch("bot.handlers.core.db.can_send", new_callable=AsyncMock, return_value=True):
            assert await enforce_limit(msg, "en") is True

    @pytest.mark.asyncio
    async def test_enforce_limit_fail(self):
        msg = make_message()
        with patch("bot.handlers.core.db.can_send", new_callable=AsyncMock, return_value=False), \
             patch("bot.handlers.core.t", return_value="Limit reached"):
            assert await enforce_limit(msg, "en") is False

    @pytest.mark.asyncio
    async def test_notify_owner_limit(self):
        bot = AsyncMock()
        user = MagicMock()
        user.id = 123
        user.full_name = "Test"
        user.username = "test"
        from bot.handlers.core import _notified
        _notified.clear()
        with patch("bot.handlers.core.config.OWNER_ID", 999):
            await _notify_owner_limit(bot, user, "en")
        _notified.clear()

    @pytest.mark.asyncio
    async def test_send_reply_short(self):
        status = AsyncMock()
        await _send_reply(status, "Hello", "en", 123)
        status.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_send_reply_long(self):
        status = AsyncMock()
        await _send_reply(status, "x" * 5000, "en", 123)
        status.delete.assert_called()

    @pytest.mark.asyncio
    async def test_send_reply_empty(self):
        status = AsyncMock()
        await _send_reply(status, "", "en", 123)
        status.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_send_reply_clarification(self):
        status = AsyncMock()
        reply = "Info\n1) Option A\n2) Option B\n3) Option C"
        await _send_reply(status, reply, "en", 123)
        status.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_do_image(self):
        msg = make_message()
        with patch("bot.handlers.core.db.ensure_user", new_callable=AsyncMock), \
             patch("bot.handlers.core.image_svc.generate", new_callable=AsyncMock, return_value=b"image_data"), \
             patch("bot.handlers.core.db.incr_and_count", new_callable=AsyncMock):
            await _do_image(msg, "cat", "en")
            msg.answer_photo.assert_called()
