"""Unit tests for bot.services.tts."""
import pytest
from bot.services.tts import _VOICE_MAP, text_to_speech


class TestTTS:
    def test_voice_map(self):
        assert "ku" in _VOICE_MAP
        assert "fa" in _VOICE_MAP
        assert "en" in _VOICE_MAP

    def test_text_to_speech_exists(self):
        assert callable(text_to_speech)
