"""Unit tests for bot.handlers.admin."""
import pytest
from bot.handlers.admin import _is_owner
from bot import config


class TestIsOwner:
    def test_owner(self):
        class FakeMsg:
            class FromUser:
                id = config.OWNER_ID
            from_user = FromUser()
        msg = FakeMsg()
        assert _is_owner(msg) is True

    def test_not_owner(self):
        class FakeMsg:
            class FromUser:
                id = 999999999
            from_user = FromUser()
        msg = FakeMsg()
        assert _is_owner(msg) is False
