"""Unit tests for bot.texts — internationalization."""
import pytest
from bot.texts import t, TEXTS


class TestTexts:
    def test_ku_welcome(self):
        assert len(t("ku", "welcome")) > 10

    def test_fa_welcome(self):
        assert len(t("fa", "welcome")) > 10

    def test_en_welcome(self):
        assert len(t("en", "welcome")) > 10

    def test_ku_error(self):
        assert len(t("ku", "error")) > 5

    def test_fa_error(self):
        assert len(t("fa", "error")) > 5

    def test_en_error(self):
        assert len(t("en", "error")) > 5

    def test_ku_help(self):
        assert len(t("ku", "help")) > 50

    def test_fa_help(self):
        assert len(t("fa", "help")) > 50

    def test_en_help(self):
        assert len(t("en", "help")) > 50

    def test_fallback_to_en(self):
        result = t("xx", "welcome")
        assert len(result) > 10

    def test_unknown_key(self):
        result = t("ku", "nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_format_kwargs(self):
        result = t("en", "limit_reached", limit=100)
        assert "100" in result

    def test_no_tuple_values(self):
        for lang, entries in TEXTS.items():
            for key, val in entries.items():
                assert not isinstance(val, tuple), f"{lang}.{key} is a tuple"

    def test_all_languages_have_required_keys(self):
        required = ["welcome", "error", "help", "thinking", "limit_reached"]
        for lang in ["ku", "fa", "en"]:
            for key in required:
                assert key in TEXTS[lang], f"{lang} missing {key}"
