"""Comprehensive tests for bot.handlers.search — full coverage."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.search import (
    _needs_web_search, _is_spam, _source_credibility,
    _classify_query, _normalize_persian, _extract_keywords,
    _get_cache_ttl, _enhance_query, _generate_followups,
    _generate_comparison, _get_price_trend,
    web_search, google_news_search, image_search, video_search,
    cb_followup, cb_fav_save, cb_fav_history, cb_fav_daily,
)


def make_callback(data="test", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.message.edit_reply_markup = AsyncMock()
    call.message.answer = AsyncMock()
    call.message.delete = AsyncMock()
    call.answer = AsyncMock()
    return call


class TestSearchFull:
    def test_needs_web_search_various(self):
        assert _needs_web_search("قیمت دلار") is True
        assert _needs_web_search("weather today") is True
        assert _needs_web_search("news") is True
        assert _needs_web_search("hello") is False
        assert _needs_web_search("") is False

    def test_is_spam_various(self):
        assert _is_spam("کلیک کن") is True
        assert _is_spam("click here") is True
        assert _is_spam("سلام") is False

    def test_source_credibility_various(self):
        assert _source_credibility("https://www.bbc.com") >= 8
        assert _source_credibility("https://github.com") >= 8
        assert _source_credibility("https://random.com") >= 5

    def test_classify_query_all(self):
        assert _classify_query("قیمت دلار") == "finance"
        assert _classify_query("news today") == "news"
        assert _classify_query("weather") == "weather"
        assert _classify_query("image of cat") == "image"
        assert _classify_query("video tutorial") == "video"
        assert _classify_query("hello") == "general"

    def test_normalize_persian(self):
        assert _normalize_persian("١٢٣") == "۱۲۳"
        result = _normalize_persian("hello, world!")
        assert "," not in result

    def test_extract_keywords(self):
        keywords = _extract_keywords("قیمت دلار امروز")
        assert len(keywords) > 0

    def test_get_cache_ttl(self):
        assert _get_cache_ttl("finance") == 300
        assert _get_cache_ttl("news") == 600
        assert _get_cache_ttl("weather") == 900
        assert _get_cache_ttl("general") == 1800
        assert _get_cache_ttl("unknown") == 1800

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
        with patch("bot.handlers.search.openrouter.chat", new_callable=AsyncMock, return_value=("comparison", {})):
            result = await _generate_comparison("compare a and b", [{"text": "a"}, {"text": "b"}], "en")
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_generate_comparison_no_match(self):
        result = await _generate_comparison("hello", [], "en")
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_price_trend(self):
        with patch("bot.handlers.search.web_search", new_callable=AsyncMock, return_value=[{"text": "trend"}]):
            result = await _get_price_trend("dollar")
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_price_trend_error(self):
        with patch("bot.handlers.search.web_search", new_callable=AsyncMock, side_effect=Exception("error")):
            result = await _get_price_trend("dollar")
            assert result == ""

    @pytest.mark.asyncio
    async def test_web_search(self):
        result = await web_search("test", max_results=1)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_google_news_search(self):
        result = await google_news_search("test", max_results=1)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_image_search(self):
        result = await image_search("test", max_results=1)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_video_search(self):
        result = await video_search("test", max_results=1)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_cb_followup(self):
        call = make_callback("fu:what is python")
        with patch("bot.handlers.search.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.search.core.process_text", new_callable=AsyncMock):
            await cb_followup(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_fav_save(self):
        call = make_callback("fav_save:test query")
        with patch("bot.handlers.search.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.search.db.add_favorite", new_callable=AsyncMock):
            await cb_fav_save(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_fav_history(self):
        call = make_callback("fav_history")
        with patch("bot.handlers.search.db.get_lang", new_callable=AsyncMock, return_value="en"), \
             patch("bot.handlers.search.db.get_search_history", new_callable=AsyncMock, return_value=[]), \
             patch("bot.handlers.search.db.get_favorites", new_callable=AsyncMock, return_value=[]):
            await cb_fav_history(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_fav_daily(self):
        call = make_callback("fav_daily")
        with patch("bot.handlers.search.config.OWNER_ID", 123), \
             patch("bot.handlers.search.db.get_daily_summary", new_callable=AsyncMock, return_value={"searches": 10, "users": 5, "top_queries": [], "avg_time": 100}):
            await cb_fav_daily(call)
            call.answer.assert_called()
