"""Unit tests for bot.keyboards."""
import pytest
from bot.keyboards import answer_kb, lang_kb, limit_kb


class TestAnswerKb:
    def test_ku(self):
        kb = answer_kb("ku")
        assert kb is not None
        assert len(kb.inline_keyboard) > 0

    def test_fa(self):
        kb = answer_kb("fa")
        assert kb is not None

    def test_en(self):
        kb = answer_kb("en")
        assert kb is not None


class TestLangKb:
    def test_basic(self):
        kb = lang_kb()
        assert kb is not None
        assert len(kb.inline_keyboard) == 1
        assert len(kb.inline_keyboard[0]) == 3


class TestLimitKb:
    def test_basic(self):
        kb = limit_kb("fa")
        assert kb is not None
        assert len(kb.inline_keyboard) == 1
