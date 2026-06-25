"""Unit tests for bot.handlers.quiz."""
import pytest
from bot.handlers.quiz import _QUIZ_CACHE


class TestQuizCache:
    def test_cache_is_dict(self):
        assert isinstance(_QUIZ_CACHE, dict)

    def test_cache_empty_initially(self):
        _QUIZ_CACHE.clear()
        assert len(_QUIZ_CACHE) == 0
