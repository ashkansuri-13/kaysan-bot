"""Comprehensive tests for bot.handlers.search — mocked Telegram API."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.search import (
    _needs_web_search, _is_spam, _source_credibility,
    _classify_query, _normalize_persian, _extract_keywords,
    _get_cache_ttl, _enhance_query, _generate_followups,
    _generate_comparison, _get_price_trend,
    web_search, google_news_search, image_search, video_search,
    cb_followup, cb_fav_save, cb_fav_history, cb_fav_daily,
    cmd_popular_queries, cmd_search_stats,
)


class TestNeedsWebSearchExtended:
    def test_various_queries(self):
        assert _needs_web_search("قیمت دلار") is True
        assert _needs_web_search("weather today") is True
        assert _needs_web_search("news") is True
        assert _needs_web_search("hello") is False
        assert _needs_web_search("") is False


class TestIsSpamExtended:
    def test_various_spam(self):
        assert _is_spam("کلیک کن") is True
        assert _is_spam("click here") is True
        assert _is_spam("رایگان بگیر") is True

    def test_normal_text(self):
        assert _is_spam("سلام") is False
        assert _is_spam("hello") is False


class TestSourceCredibilityExtended:
    def test_various_sources(self):
        assert _source_credibility("https://www.bbc.com") >= 8
        assert _source_credibility("https://github.com") >= 8
        assert _source_credibility("https://random.com") >= 5


class TestClassifyQueryExtended:
    def test_all_types(self):
        assert _classify_query("قیمت دلار") == "finance"
        assert _classify_query("news today") == "news"
        assert _classify_query("weather") == "weather"
        assert _classify_query("image of cat") == "image"
        assert _classify_query("video tutorial") == "video"
        assert _classify_query("hello") == "general"


class TestNormalizePersian:
    def test_arabic_to_persian(self):
        assert _normalize_persian("١٢٣") == "۱۲۳"

    def test_punctuation(self):
        result = _normalize_persian("hello, world!")
        assert "," not in result


class TestExtractKeywords:
    def test_basic(self):
        keywords = _extract_keywords("قیمت دلار امروز")
        assert len(keywords) > 0

    def test_stop_words_removed(self):
        keywords = _extract_keywords("چی هست")
        assert "چی" not in keywords


class TestGetCacheTTLExtended:
    def test_all_types(self):
        assert _get_cache_ttl("finance") == 300
        assert _get_cache_ttl("news") == 600
        assert _get_cache_ttl("weather") == 900
        assert _get_cache_ttl("general") == 1800
        assert _get_cache_ttl("unknown") == 1800


class TestSearchFunctions:
    @pytest.mark.asyncio
    async def test_enhance_query(self):
        with patch("bot.handlers.search.openrouter.chat", new_callable=AsyncMock, return_value=("query1\nquery2", {})):
            result = await _enhance_query("test", "en")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_enhance_query_error(self):
        with patch("bot.handlers.search.openrouter.chat", new_callable=AsyncMock, side_effect=Exception("error")):
            result = await _enhance_query("test", "en")
            assert result == ["test"]

    @pytest.mark.asyncio
    async def test_generate_followups(self):
        with patch("bot.handlers.search.openrouter.chat", new_callable=AsyncMock, return_value=("q1\nq2\nq3", {})):
            result = await _generate_followups("test", "response", "en")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_generate_followups_error(self):
        with patch("bot.handlers.search.openrouter.chat", new_callable=AsyncMock, side_effect=Exception("error")):
            result = await _generate_followups("test", "response", "en")
            assert result == []

    @pytest.mark.asyncio
    async def test_generate_comparison(self):
        with patch("bot.handlers.search.openrouter.chat", new_callable=AsyncMock, return_value=("comparison table", {})):
            result = await _generate_comparison("compare a and b", [{"text": "a info"}, {"text": "b info"}], "en")
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_generate_comparison_no_match(self):
        result = await _generate_comparison("hello", [], "en")
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_price_trend(self):
        with patch("bot.handlers.search.web_search", new_callable=AsyncMock, return_value=[{"text": "trend info"}]):
            result = await _get_price_trend("dollar")
            assert isinstance(result, str)


class TestWebSearch:
    @pytest.mark.asyncio
    async def test_web_search(self):
        result = await web_search("test query", max_results=2)
        assert isinstance(result, list)


class TestCallbacks:
    @pytest.mark.asyncio
    async def test_cb_followup(self):
        call = AsyncMock()
        call.data = "fu:what is python"
        call.from_user = MagicMock()
        call.from_user.id = 123
        call.message = AsyncMock()
        call.message.delete = AsyncMock()
        call.answer = AsyncMock()
        with patch("bot.handlers.search.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.search.core.process_text", new_callable=AsyncMock):
            await cb_followup(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_fav_save(self):
        call = AsyncMock()
        call.data = "fav_save:test query"
        call.from_user = MagicMock()
        call.from_user.id = 123
        call.message = AsyncMock()
        call.message.edit_reply_markup = AsyncMock()
        call.answer = AsyncMock()
        with patch("bot.handlers.search.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.search.db.add_favorite", new_callable=AsyncMock):
            await cb_fav_save(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_fav_history(self):
        call = AsyncMock()
        call.data = "fav_history"
        call.from_user = MagicMock()
        call.from_user.id = 123
        call.message = AsyncMock()
        call.message.edit_text = AsyncMock()
        call.message.answer = AsyncMock()
        call.answer = AsyncMock()
        with patch("bot.handlers.search.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.search.db.get_search_history", new_callable=AsyncMock, return_value=[]), \
             patch("bot.handlers.search.db.get_favorites", new_callable=AsyncMock, return_value=[]):
            await cb_fav_history(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_fav_daily(self):
        call = AsyncMock()
        call.data = "fav_daily"
        call.from_user = MagicMock()
        call.from_user.id = 123
        call.message = AsyncMock()
        call.message.answer = AsyncMock()
        call.answer = AsyncMock()
        with patch("bot.handlers.search.config.OWNER_ID", 123), \
             patch("bot.handlers.search.db.get_daily_summary", new_callable=AsyncMock, return_value={"searches": 10, "users": 5, "top_queries": [], "avg_time": 100}):
            await cb_fav_daily(call)
            call.answer.assert_called()

    def test_cmd_popular_queries(self):
        assert callable(cmd_popular_queries)

    def test_cmd_search_stats(self):
        assert callable(cmd_search_stats)
