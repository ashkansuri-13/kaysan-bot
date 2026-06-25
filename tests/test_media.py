"""Unit tests for bot.handlers.media."""
import pytest
from bot.handlers.media import on_voice, on_photo


class TestMediaHandlers:
    def test_on_voice_exists(self):
        assert callable(on_voice)

    def test_on_photo_exists(self):
        assert callable(on_photo)
