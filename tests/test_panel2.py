"""Panel handler tests — comprehensive."""
import pytest
from bot.handlers.panel import (
    _clean_state, _set_state, _get_state,
    _toggle, _onoff, _main_kb, _back_kb, _is_group_admin,
)


class TestIsGroupAdmin:
    def test_exists(self):
        assert callable(_is_group_admin)


class TestMainKb:
    def test_returns_keyboard(self):
        kb = _main_kb(-100123, "Test Group")
        assert kb is not None
        assert len(kb.inline_keyboard) > 0


class TestBackKb:
    def test_returns_keyboard(self):
        kb = _back_kb(-100123)
        assert kb is not None
        assert len(kb.inline_keyboard) > 0


class TestStateExtended:
    def test_multiple_states(self):
        _set_state(1, {"action": "a"})
        _set_state(2, {"action": "b"})
        assert _get_state(1)["action"] == "a"
        assert _get_state(2)["action"] == "b"
        _clean_state(1)
        assert _get_state(1) is None
        assert _get_state(2)["action"] == "b"
        _clean_state(2)

    def test_toggle_extended(self):
        assert _toggle(0) == 1
        assert _toggle(1) == 0
        assert _toggle(42) == 0

    def test_onoff_extended(self):
        assert "فعال" in _onoff(1)
        assert "فعال" in _onoff(True)
        assert "غیرفعال" in _onoff(0)
        assert "غیرفعال" in _onoff(False)
