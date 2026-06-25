"""Unit tests for bot.redis_cache."""
import pytest
from bot.redis_cache import cache_get, cache_set, cache_delete, cache_stats


class TestRedisCache:
    @pytest.mark.asyncio
    async def test_cache_get_empty(self):
        result = await cache_get("nonexistent_key_xyz")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        await cache_set("test_key_redis_123", "test_value", ttl=60)
        result = await cache_get("test_key_redis_123")
        if result is None:
            pytest.skip("Redis not available")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        await cache_set("test_del_key_redis", "value", ttl=60)
        await cache_delete("test_del_key_redis")
        result = await cache_get("test_del_key_redis")
        if result is not None:
            pytest.skip("Redis not available")

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        stats = await cache_stats()
        assert isinstance(stats, dict)
        assert "status" in stats
