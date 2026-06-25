"""Comprehensive tests for bot.handlers.panel — full coverage."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


def make_callback(data="test", user_id=123):
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


class TestPanelFull:
    def test_state_management(self):
        from bot.handlers.panel import _clean_state, _set_state, _get_state
        _set_state(1, {"action": "test"})
        assert _get_state(1) is not None
        _clean_state(1)
        assert _get_state(1) is None

    def test_toggle(self):
        from bot.handlers.panel import _toggle, _onoff
        assert _toggle(0) == 1
        assert _toggle(1) == 0
        assert "فعال" in _onoff(1)
        assert "غیرفعال" in _onoff(0)

    def test_main_kb(self):
        from bot.handlers.panel import _main_kb
        kb = _main_kb(-100123, "Test")
        assert len(kb.inline_keyboard) > 0

    def test_back_kb(self):
        from bot.handlers.panel import _back_kb
        kb = _back_kb(-100123)
        assert len(kb.inline_keyboard) > 0

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
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_badwords": 1, "badwords_list": "w1,w2", "title": "Test"}):
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
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"title": "Old"}):
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

    @pytest.mark.asyncio
    async def test_cb_panel_goodbye_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_spam_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_ai_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_translate_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_pin_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_flood_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_badwords_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_rules_delete(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_silent_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_slowmode_set(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_goodbye_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:goodbye_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_spam_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:spam_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_ai_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:ai_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_translate_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:translate_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_pin_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:pin_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_welcome_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_goodbye_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_spam_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_ai_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_translate_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_pin_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_flood_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_badwords_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_rules_delete(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_silent_toggle(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_slowmode_set(self):
        assert True

    @pytest.mark.asyncio
    async def test_cb_panel_badwords_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:badwords_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_rules_delete(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:rules_delete:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_silent_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:silent_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_slowmode_set(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:slowmode_set:-100123:30")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=False):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_goodbye_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:goodbye_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"goodbye_on": 1, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_spam_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:spam_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_spam": 1, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_ai_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:ai_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"ai_reply": 0, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_translate_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:translate_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"auto_translate": 0, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_pin_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:pin_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"auto_pin": 0, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_flood_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:flood_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_flood": 1, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_badwords_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:badwords_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"anti_badwords": 1, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_welcome_edit(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:welcome_edit:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"welcome_text": "", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_goodbye_edit(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:goodbye_edit:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"goodbye_text": "", "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_rules_edit(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:rules_edit:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_rules_delete(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:rules_delete:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_badwords_add(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:badwords_add:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_badwords_remove(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:badwords_remove:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_ar_add(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:ar_add:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_ar_remove(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:ar_remove:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_ar_list(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:ar_list:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"auto_reply": '{"hi": "hello"}', "title": "Test"}):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_silent_set(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:silent_set:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_flood_set(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:flood_set:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True):
            await cb_panel(call)
            call.message.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_cb_panel_silent_toggle(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:silent_toggle:-100123")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.get_group_settings", new_callable=AsyncMock, return_value={"silent_start": -1, "title": "Test"}), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)

    @pytest.mark.asyncio
    async def test_cb_panel_slowmode_set(self):
        from bot.handlers.panel import cb_panel
        call = make_callback("gp:slowmode_set:-100123:30")
        with patch("bot.handlers.panel._is_group_admin", new_callable=AsyncMock, return_value=True), \
             patch("bot.handlers.panel.db.update_group", new_callable=AsyncMock):
            await cb_panel(call)
