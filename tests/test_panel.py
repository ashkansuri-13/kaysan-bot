"""Unit tests for bot.handlers.panel."""
import pytest
import json
from bot.handlers.panel import (
    _clean_state, _set_state, _get_state,
    _toggle, _onoff,
)


class TestStateManagement:
    def test_set_get(self):
        _set_state(123, {"action": "test", "chat_id": 456})
        state = _get_state(123)
        assert state is not None
        assert state["action"] == "test"

    def test_clean(self):
        _set_state(123, {"action": "test"})
        _clean_state(123)
        assert _get_state(123) is None

    def test_get_nonexistent(self):
        assert _get_state(999999) is None


class TestToggle:
    def test_on_to_off(self):
        assert _toggle(1) == 0

    def test_off_to_on(self):
        assert _toggle(0) == 1


class TestOnOff:
    def test_on(self):
        assert "فعال" in _onoff(1)

    def test_off(self):
        assert "غیرفعال" in _onoff(0)
