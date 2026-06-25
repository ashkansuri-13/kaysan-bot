"""Unit tests for bot.handlers.translate."""
import pytest
from bot.texts import t


class TestTextsTranslation:
    def test_ku_welcome(self):
        assert len(t("ku", "welcome")) > 10

    def test_fa_welcome(self):
        assert len(t("fa", "welcome")) > 10

    def test_en_welcome(self):
        assert len(t("en", "welcome")) > 10

    def test_ku_help(self):
        assert len(t("ku", "help")) > 50

    def test_fa_help(self):
        assert len(t("fa", "help")) > 50

    def test_en_help(self):
        assert len(t("en", "help")) > 50

    def test_ku_error(self):
        assert len(t("ku", "error")) > 5

    def test_fa_error(self):
        assert len(t("fa", "error")) > 5

    def test_en_error(self):
        assert len(t("en", "error")) > 5

    def test_format_limit(self):
        result = t("en", "limit_reached", limit=50)
        assert "50" in result

    def test_format_remind(self):
        result = t("en", "remind_usage")
        assert "remind" in result.lower()
