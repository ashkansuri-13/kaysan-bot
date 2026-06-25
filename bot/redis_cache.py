"""Redis Cache — کش سریع روی سرور ۲."""
import json
import logging

log = logging.getLogger("kaysan.redis")

_redis = None


async def _get_redis():
    """اتصال به Redis."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        import os
        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            return None
        import aioredis
        _redis = aioredis.from_url(redis_url, decode_responses=True)
        await _redis.ping()
        log.info("✅ Redis connected: %s", redis_url)
        return _redis
    except Exception as e:
        log.warning("⚠️ Redis not available: %s", e)
        _redis = None
        return None


async def cache_get(key: str) -> str | None:
    """دریافت از کش."""
    r = await _get_redis()
    if not r:
        return None
    try:
        return await r.get(f"kaysan:{key}")
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl: int = 1800):
    """ذخیره در کش (پیش‌فرض ۳۰ دقیقه)."""
    r = await _get_redis()
    if not r:
        return
    try:
        await r.set(f"kaysan:{key}", value, ex=ttl)
    except Exception:
        pass


async def cache_delete(key: str):
    """حذف از کش."""
    r = await _get_redis()
    if not r:
        return
    try:
        await r.delete(f"kaysan:{key}")
    except Exception:
        pass


async def cache_stats() -> dict:
    """آمار کش."""
    r = await _get_redis()
    if not r:
        return {"status": "disconnected"}
    try:
        info = await r.info("stats")
        return {
            "status": "connected",
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "keys": await r.dbsize(),
        }
    except Exception:
        return {"status": "error"}
