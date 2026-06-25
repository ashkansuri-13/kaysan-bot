"""Unit tests for bot.handlers.extras."""
import pytest
from bot.handlers.extras import _HAFEZ_POEMS, _WORDLE_WORDS, _MODES


class TestHafezPoems:
    def test_poems_exist(self):
        assert len(_HAFEZ_POEMS) > 0

    def test_poem_structure(self):
        for poem, interp in _HAFEZ_POEMS:
            assert len(poem) > 10
            assert len(interp) > 10


class TestWordleWords:
    def test_words_exist(self):
        assert len(_WORDLE_WORDS) > 0

    def test_words_are_strings(self):
        for word in _WORDLE_WORDS:
            assert isinstance(word, str)
            assert len(word) > 0


class TestModes:
    def test_modes_exist(self):
        assert "teacher" in _MODES
        assert "coder" in _MODES
        assert "friend" in _MODES
        assert "default" in _MODES

    def test_modes_have_languages(self):
        for mode, texts in _MODES.items():
            assert "ku" in texts
            assert "fa" in texts
            assert "en" in texts
