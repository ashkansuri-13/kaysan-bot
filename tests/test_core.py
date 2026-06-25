"""Unit tests for bot.handlers.core — heart of the bot."""
import pytest
from bot.handlers.core import (
    _parse_clarification, _get_triple_date, _to_kurdish_date,
    _LANG_NAMES, _last,
)
from bot.router import detect_intent as router_detect


class TestParseClarification:
    def test_with_questions(self):
        reply = "Here is some info:\n1) What topic?\n2) What language?\n3) What style?"
        result = _parse_clarification(reply)
        assert result is not None
        main, questions = result
        assert len(questions) == 3
        assert "What topic?" in questions[0]

    def test_no_questions(self):
        reply = "This is a normal reply without questions."
        result = _parse_clarification(reply)
        assert result is None

    def test_single_question(self):
        reply = "Info\n1) Just one question"
        result = _parse_clarification(reply)
        assert result is None

    def test_empty(self):
        result = _parse_clarification("")
        assert result is None


class TestGetTripleDate:
    def test_returns_dict(self):
        dates = _get_triple_date()
        assert isinstance(dates, dict)
        assert "fa" in dates
        assert "en" in dates
        assert "ku" in dates
        assert "short" in dates
        assert "time" in dates

    def test_format(self):
        dates = _get_triple_date()
        assert "-" in dates["short"]
        assert ":" in dates["time"]


class TestToKurdishDate:
    def test_basic(self):
        ky, km, kd, name = _to_kurdish_date(1403, 1, 1)
        assert ky == 1402
        assert km == 10
        assert kd == 1
        assert len(name) > 0

    def test_month_range(self):
        for m in range(1, 13):
            ky, km, kd, name = _to_kurdish_date(1403, m, 15)
            assert 1 <= km <= 12


class TestLangNames:
    def test_all_languages(self):
        assert "ku" in _LANG_NAMES
        assert "fa" in _LANG_NAMES
        assert "en" in _LANG_NAMES


class TestLast:
    def test_get_last_empty(self):
        from bot.handlers.core import get_last
        result = get_last(999999999)
        assert result is None

    def test_set_get_last(self):
        from bot.handlers.core import get_last
        _last[12345] = {"text": "test", "intent": "chat", "lang": "fa", "reply": "response"}
        result = get_last(12345)
        assert result is not None
        assert result["text"] == "test"
        del _last[12345]
