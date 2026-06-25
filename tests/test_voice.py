"""Unit tests for bot.services.voice."""
import pytest
from bot.services.voice import _FFMPEG_AVAILABLE


class TestVoice:
    def test_ffmpeg_check(self):
        assert isinstance(_FFMPEG_AVAILABLE, bool)
