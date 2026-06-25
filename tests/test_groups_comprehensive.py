"""Comprehensive tests for bot.handlers.groups — mocked Telegram API."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.groups import (
    on_member_join, on_member_leave,
    anti_spam, anti_bad_words, anti_flood,
    cmd_slowmode, enforce_slow_mode,
    auto_reply_keywords, on_bot_mention,
    cmd_group_stats, cmd_ai_poll, cmd_group_quiz,
    cmd_group_translate, group_voice_transcribe,
    group_photo_analyze, group_file_analyze,
    cmd_silent, cmd_silent_off, cmd_set_rules, cmd_rules,
    cmd_report, cmd_bot_mute, cmd_bot_unmute, cmd_tag_all, cmd_group_help,
    _is_admin, _flood_tracker,
    _last_msg_time,
)


def make_chat_member(status="member", is_bot=False):
    member = MagicMock()
    member.user = MagicMock()
    member.user.id = 123
    member.user.full_name = "Test User"
    member.user.is_bot = is_bot
    member.user.username = "testuser"
    member.status = status
    member.new_chat_member = member
    member.old_chat_member = member
    return member


def make_event(chat_id=-100123, user_id=123, status_new="member", status_old="left"):
    event = MagicMock()
    event.chat = MagicMock()
    event.chat.id = chat_id
    event.chat.title = "Test Group"
    event.chat.send_message = AsyncMock()
    event.from_user = MagicMock()
    event.from_user.id = user_id
    event.from_user.full_name = "Test User"
    event.from_user.username = "testuser"
    event.new_chat_member = MagicMock()
    event.new_chat_member.user = event.from_user
    event.new_chat_member.status = status_new
    event.old_chat_member = MagicMock()
    event.old_chat_member.user = event.from_user
    event.old_chat_member.status = status_old
    return event


def make_message(text="/groupstats", user_id=123, chat_id=-100123, chat_type="group"):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.chat = MagicMock()
    msg.chat.type = chat_type
    msg.chat.id = chat_id
    msg.chat.title = "Test Group"
    msg.answer = AsyncMock()
    msg.delete = AsyncMock()
    msg.bot = AsyncMock()
    return msg


class TestIsAdmin:
    @pytest.mark.asyncio
    async def test_is_admin_creator(self):
        bot = AsyncMock()
        member = MagicMock()
        member.status = "creator"
        bot.get_chat_member = AsyncMock(return_value=member)
        assert await _is_admin(bot, -100123, 123) is True

    @pytest.mark.asyncio
    async def test_is_admin_admin(self):
        bot = AsyncMock()
        member = MagicMock()
        member.status = "administrator"
        bot.get_chat_member = AsyncMock(return_value=member)
        assert await _is_admin(bot, -100123, 123) is True

    @pytest.mark.asyncio
    async def test_not_admin(self):
        bot = AsyncMock()
        member = MagicMock()
        member.status = "member"
        bot.get_chat_member = AsyncMock(return_value=member)
        assert await _is_admin(bot, -100123, 123) is False

    @pytest.mark.asyncio
    async def test_admin_exception(self):
        bot = AsyncMock()
        bot.get_chat_member = AsyncMock(side_effect=Exception("error"))
        assert await _is_admin(bot, -100123, 123) is False


class TestWelcomeGoodbye:
    @pytest.mark.asyncio
    async def test_on_member_join(self):
        event = make_event()
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await on_member_join(event)
            event.chat.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_on_member_leave(self):
        event = make_event()
        await on_member_leave(event)
        event.chat.send_message.assert_called()


class TestAntiSpam:
    @pytest.mark.asyncio
    async def test_spam_detected(self):
        msg = make_message("https://t.me/joinchat/abc", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await anti_spam(msg)
            msg.delete.assert_called()

    @pytest.mark.asyncio
    async def test_normal_message(self):
        msg = make_message("hello", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await anti_spam(msg)
            msg.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_message(self):
        msg = make_message("https://t.me/joinchat/abc", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await anti_spam(msg)
            msg.delete.assert_not_called()


class TestAntiBadWords:
    @pytest.mark.asyncio
    async def test_bad_word(self):
        msg = make_message("fuck you", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await anti_bad_words(msg)
            msg.delete.assert_called()

    @pytest.mark.asyncio
    async def test_normal_message(self):
        msg = make_message("hello", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await anti_bad_words(msg)
            msg.delete.assert_not_called()


class TestAntiFlood:
    @pytest.mark.asyncio
    async def test_flood_detected(self):
        msg = make_message("test", chat_type="group")
        _flood_tracker.clear()
        for i in range(6):
            _flood_tracker[msg.chat.id][msg.from_user.id].append(1.0)
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await anti_flood(msg)
        _flood_tracker.clear()

    @pytest.mark.asyncio
    async def test_normal_message(self):
        msg = make_message("hello", chat_type="group")
        _flood_tracker.clear()
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await anti_flood(msg)
            msg.delete.assert_not_called()
        _flood_tracker.clear()


class TestGroupCommands:
    @pytest.mark.asyncio
    async def test_group_stats(self):
        msg = make_message("/groupstats", chat_type="group")
        msg.bot.get_chat_member_count = AsyncMock(return_value=100)
        await cmd_group_stats(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_group_help(self):
        msg = make_message("/grouphelp", chat_type="group")
        await cmd_group_help(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_rules_empty(self):
        msg = make_message("/rules", chat_type="group")
        with patch("bot.handlers.groups.db.get_group_settings", new_callable=AsyncMock, return_value={"rules_text": ""}):
            await cmd_rules(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_rules_exists(self):
        msg = make_message("/rules", chat_type="group")
        with patch("bot.handlers.groups.db.get_group_settings", new_callable=AsyncMock, return_value={"rules_text": "Rule 1\nRule 2"}):
            await cmd_rules(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_set_rules(self):
        msg = make_message("/setrules Rule 1\nRule 2", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await cmd_set_rules(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_set_rules_not_admin(self):
        msg = make_message("/setrules Rule 1", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await cmd_set_rules(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_slowmode(self):
        msg = make_message("/slowmode 30", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await cmd_slowmode(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_silent(self):
        msg = make_message("/silent 23 7", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await cmd_silent(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_silent_off(self):
        msg = make_message("/silent_off", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await cmd_silent_off(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_bot_mute(self):
        msg = make_message("/botmute", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await cmd_bot_mute(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_bot_unmute(self):
        msg = make_message("/botunmute", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            await cmd_bot_unmute(msg)
            msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_report_no_reply(self):
        msg = make_message("/report", chat_type="group")
        msg.reply_to_message = None
        await cmd_report(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_tag_all(self):
        msg = make_message("/tagall Test message", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=True):
            member = MagicMock()
            member.user = MagicMock()
            member.user.id = 123
            member.user.is_bot = False
            msg.chat.get_members = AsyncMock(return_value=[member])
            await cmd_tag_all(msg)
            msg.answer.assert_called()


class TestAutoReply:
    @pytest.mark.asyncio
    async def test_keyword_match(self):
        msg = make_message("hi", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await auto_reply_keywords(msg)

    @pytest.mark.asyncio
    async def test_no_match(self):
        msg = make_message("xyz", chat_type="group")
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False):
            await auto_reply_keywords(msg)


class TestMentionBot:
    @pytest.mark.asyncio
    async def test_bot_mentioned(self):
        msg = make_message("what is python @KaysanAI_Bot", chat_type="group")
        msg.bot.get_me = AsyncMock(return_value=MagicMock(username="KaysanAI_Bot"))
        msg.text = "what is python @KaysanAI_Bot"
        with patch("bot.handlers.groups._is_admin", new_callable=AsyncMock, return_value=False), \
             patch("bot.handlers.groups.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.groups.openrouter.chat", new_callable=AsyncMock, return_value=("Python is a language", {"model": "test"})):
            await on_bot_mention(msg)


class TestGroupHelp:
    @pytest.mark.asyncio
    async def test_grouphelp(self):
        msg = make_message("/grouphelp", chat_type="group")
        await cmd_group_help(msg)
        msg.answer.assert_called()
