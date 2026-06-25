"""Unit tests for bot.handlers.actions — callback handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.actions import (
    cb_regen, cb_toimg, cb_tts, cb_clarify,
    cb_feedback_like, cb_feedback_dislike,
)


class TestCallbacks:
    def test_regen_exists(self):
        assert callable(cb_regen)

    def test_toimg_exists(self):
        assert callable(cb_toimg)

    def test_tts_exists(self):
        assert callable(cb_tts)

    def test_clarify_exists(self):
        assert callable(cb_clarify)

    def test_feedback_like_exists(self):
        assert callable(cb_feedback_like)

    def test_feedback_dislike_exists(self):
        assert callable(cb_feedback_dislike)
