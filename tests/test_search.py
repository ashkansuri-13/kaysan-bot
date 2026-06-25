"""Unit tests for bot.handlers.search."""
import pytest
from bot.handlers.search import (
    _needs_web_search, _is_spam, _source_credibility,
    _classify_query, _normalize_persian, _extract_keywords,
    _get_cache_ttl, _SPAM_PATTERNS, _CREDIBLE_SOURCES,
)


class TestNeedsWebSearch:
    def test_price_query(self):
        assert _needs_web_search("قیمت دلار") is True

    def test_weather_query(self):
        assert _needs_web_search("آب و هوای تهران") is True

    def test_normal_chat(self):
        assert _needs_web_search("ممنون متشکرم") is False

    def test_empty(self):
        assert _needs_web_search("") is False


class TestIsSpam:
    def test_spam(self):
        assert _is_spam("کلیک کن برای برد") is True

    def test_normal(self):
        assert _is_spam("ممنون متشکرم") is False


class TestSourceCredibility:
    def test_credible_source(self):
        score = _source_credibility("https://www.bbc.com/news")
        assert score >= 8

    def test_gov_source(self):
        score = _source_credibility("https://gov.ir")
        assert score >= 8

    def test_unknown_source(self):
        score = _source_credibility("https://random-blog.com")
        assert score >= 5


class TestClassifyQuery:
    def test_finance(self):
        assert _classify_query("قیمت دلار") == "finance"

    def test_news(self):
        assert _classify_query("news today") == "news"

    def test_weather(self):
        assert _classify_query("آب و هوا") == "weather"

    def test_general(self):
        assert _classify_query("سلام") == "general"


class TestNormalizePersian:
    def test_arabic_numbers(self):
        result = _normalize_persian("١٢٣٤٥")
        assert result == "۱۲۳۴۵"

    def test_normal_text(self):
        result = _normalize_persian("hello")
        assert result == "hello"


class TestExtractKeywords:
    def test_basic(self):
        keywords = _extract_keywords("قیمت دلار امروز")
        assert len(keywords) > 0

    def test_stop_words(self):
        keywords = _extract_keywords("چی هست")
        assert len(keywords) <= 2


class TestGetCacheTTL:
    def test_finance(self):
        assert _get_cache_ttl("finance") == 300

    def test_news(self):
        assert _get_cache_ttl("news") == 600

    def test_general(self):
        assert _get_cache_ttl("general") == 1800

    def test_unknown(self):
        assert _get_cache_ttl("unknown") == 1800
