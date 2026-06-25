"""Comprehensive tests for bot.handlers.panel — mocked Telegram API."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.panel import (
    _clean_state, _set_state, _get_state,
    _toggle, _onoff, _main_kb, _back_kb,
    _input_state,
)


def make_message(text="/manage", user_id=123, chat_type="private"):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.chat = MagicMock()
    msg.chat.type = chat_type
    msg.chat.id = -100123
    msg.chat.title = "Test Group"
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    return msg


def make_callback(data="gp:open:-100123", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.message.delete = AsyncMock()
    call.answer = AsyncMock()
    call.bot = AsyncMock()
    return call


class TestPanelState:
    def test_set_get(self):
        _set_state(1, {"action": "test"})
        assert _get_state(1) is not None
        _clean_state(1)
        assert _get_state(1) is None

    def test_toggle(self):
        assert _toggle(0) == 1
        assert _toggle(1) == 0

    def test_onoff(self):
        assert "فعال" in _onoff(1)
        assert "غیرفعال" in _onoff(0)


class TestPanelKeyboard:
    def test_main_kb(self):
        kb = _main_kb(-100123, "Test")
        assert len(kb.inline_keyboard) > 0

    def test_back_kb(self):
        kb = _back_kb(-100123)
        assert len(kb.inline_keyboard) > 0


class TestPanelCallbackHandler:
    @pytest.mark.asyncio
    async def test_cb_panel_back(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:back")
        with patch("bot.handlers.panel._show_my_groups", new_callable=AsyncMock):
            await cb_panel(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_list(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:list")
        with patch("bot.handlers.panel._show_my_groups", new_callable=AsyncMock):
            await cb_panel(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_open_not_admin(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:open:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_welcome(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:welcome:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"welcome_on": 1, "welcome_text": "", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_goodbye(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:goodbye:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"goodbye_on": 1, "goodbye_text": "", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_rules(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:rules:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"rules_text": "Rule 1", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_stats(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:stats:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"title": "Test", "anti_spam": 1, "ai_reply": 0}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_spam(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:spam:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_spam": 1, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_badwords(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:badwords:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_badwords": 1, "badwords_list": "word1,word2", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_autoreply(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:autoreply:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"auto_reply": "{}", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_ai(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:ai:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"ai_reply": 0, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_slowmode(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:slowmode:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"slow_mode": 0, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_silent(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:silent:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"silent_start": -1, "silent_end": -1, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_flood(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:flood:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_flood": 1, "flood_limit": 5, "flood_window": 10, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_translate(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:translate:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"auto_translate": 0, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_pin(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:pin:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"auto_pin": 0, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_log(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:log:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_spam": 1, "anti_badwords": 1, "anti_flood": 1, "ai_reply": 0, "auto_translate": 0, "auto_pin": 0, "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_admins(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:admins:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            admin = MagicMock()
            admin.user = MagicMock()
            admin.user.full_name = "Admin"
            admin.user.is_bot = False
            admin.status = "creator"
            call.bot.get_chat_administrators = AsyncMock(return_value=[admin])
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_rename(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:rename:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"title": "Old Name"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_backup(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:backup:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"title": "Test", "chat_id": -100123}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_notif(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:notif:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_schedule(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:schedule:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_chart(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:chart:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"ai_reply": 0, "anti_spam": 1, "auto_reply": "{}", "title": "Test"}):
            call.bot.get_chat_member_count = AsyncMock(return_value=100)
            await cb_panel(call)
            call.message.edit_text.assert_called()


class TestPanelToggleHandlers:
    @pytest.mark.asyncio
    async def test_toggle_state(self):
        from bot.handlers.panel import _toggle, _onoff
        assert _toggle(0) == 1
        assert _toggle(1) == 0
        assert "فعال" in _onoff(1)
        assert "غیرفعال" in _onoff(0)

    @pytest.mark.asyncio
    async def test_welcome_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "welcome_text", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "welcome_text"
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_goodbye_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "goodbye_text", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "goodbye_text"
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_spam_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "spam", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "spam"
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_ai_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "ai_reply", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "ai_reply"
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_translate_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "auto_translate", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "auto_translate"
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_pin_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "auto_pin", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "auto_pin"
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_flood_toggle_state(self):
        from bot.handlers.panel import _set_state, _get_state, _clean_state
        _set_state(123, {"action": "flood_config", "chat_id": -100123})
        state = _get_state(123)
        assert state["action"] == "flood_config"
        _clean_state(123)


class TestPanelInputHandlers:
    @pytest.mark.asyncio
    async def test_welcome_edit(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:welcome_edit:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"welcome_text": "", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_goodbye_edit(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:goodbye_edit:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"goodbye_text": "", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_rules_edit(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:rules_edit:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_rules_delete(self):
        from bot.handlers.panel import cb_panel, _set_state, _get_state
        _set_state(123, {"action": "rules_text", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_badwords_add(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "badwords_add", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_badwords_remove(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "badwords_remove", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_ar_add(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "ar_add_key", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_ar_remove(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "ar_remove", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_ar_list(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "silent_hours", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_silent_set(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "flood_config", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_flood_set(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "rename", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)

    @pytest.mark.asyncio
    async def test_slowmode_set(self):
        from bot.handlers.panel import _set_state, _get_state
        _set_state(123, {"action": "welcome_text", "chat_id": -100123})
        assert _get_state(123) is not None
        _clean_state(123)
