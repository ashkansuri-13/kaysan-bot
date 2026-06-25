"""Unit tests for bot.router — intent detection and language detection."""
import pytest
from bot.router import detect_intent, detect_lang, models_for
from bot import config


class TestDetectIntent:
    def test_image_intent(self):
        assert detect_intent("یه عکس از گربه بکش") == "image"

    def test_image_english(self):
        assert detect_intent("draw a cat") == "image"

    def test_code_intent(self):
        assert detect_intent("یه کد پایتون بنویس") == "code"

    def test_code_english(self):
        assert detect_intent("write a python function") == "code"

    def test_video_intent(self):
        assert detect_intent("یه ویدیو بساز") == "video"

    def test_music_intent(self):
        assert detect_intent("یه آهنگ بساز") == "music"

    def test_reason_intent(self):
        assert detect_intent("حل کن این معادله") == "reason"

    def test_chat_intent(self):
        assert detect_intent("سلام چطوری") == "chat"

    def test_empty_text(self):
        assert detect_intent("") == "chat"

    def test_none_text(self):
        assert detect_intent(None) == "chat"


class TestDetectLang:
    def test_kurdish(self):
        assert detect_lang("سڵاو چۆنیت") == "ku"

    def test_persian(self):
        assert detect_lang("سلام حالت چطوره") == "fa"

    def test_english(self):
        assert detect_lang("hello how are you") == "en"

    def test_empty(self):
        assert detect_lang("") == config.DEFAULT_LANG

    def test_none(self):
        assert detect_lang(None) == config.DEFAULT_LANG


class TestModelsFor:
    def test_code_models(self):
        assert models_for("code") == config.CODE_MODELS

    def test_chat_models(self):
        assert models_for("chat") == config.CHAT_MODELS

    def test_unknown_fallback(self):
        assert models_for("unknown") == config.CHAT_MODELS
