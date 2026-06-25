"""Unit tests for bot.config."""
import pytest
from bot.config import (
    BOT_TOKEN, OPENROUTER_KEY, OWNER_ID, DEFAULT_LANG,
    FREE_MESSAGE_LIMIT, DAILY_COST_LIMIT, DB_PATH,
    SUPPORTED_LANGS, CHAT_MODELS, CODE_MODELS,
    REASON_MODELS, VISION_MODELS, MODELS_BY_CATEGORY,
)


class TestConfig:
    def test_bot_token_type(self):
        assert isinstance(BOT_TOKEN, str)

    def test_owner_id_type(self):
        assert isinstance(OWNER_ID, int)

    def test_default_lang(self):
        assert DEFAULT_LANG in ("ku", "fa", "en")

    def test_free_message_limit(self):
        assert FREE_MESSAGE_LIMIT > 0

    def test_daily_cost_limit(self):
        assert DAILY_COST_LIMIT > 0

    def test_db_path(self):
        assert str(DB_PATH).endswith(".db")

    def test_supported_langs(self):
        assert "ku" in SUPPORTED_LANGS
        assert "fa" in SUPPORTED_LANGS
        assert "en" in SUPPORTED_LANGS

    def test_models_by_category(self):
        assert "chat" in MODELS_BY_CATEGORY
        assert "code" in MODELS_BY_CATEGORY
        assert "vision" in MODELS_BY_CATEGORY

    def test_chat_models(self):
        assert len(CHAT_MODELS) > 0

    def test_code_models(self):
        assert len(CODE_MODELS) > 0
