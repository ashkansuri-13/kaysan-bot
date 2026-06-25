"""Unit tests for bot.handlers.chat."""
import pytest
from bot.handlers.chat import on_text


class TestChatHandler:
    def test_on_text_exists(self):
        assert callable(on_text)
