"""Health Check — بررسی سلامت ربات."""
import asyncio
import logging
import time
from aiohttp import web

log = logging.getLogger("kaysan.health")

_start_time = time.time()
_health_status = "starting"


async def health_handler(request):
    """هندلر health check."""
    uptime = time.time() - _start_time
    return web.json_response({
        "status": _health_status,
        "uptime_seconds": round(uptime, 1),
        "service": "kaysan-ai-bot",
    })


async def readiness_handler(request):
    """هندلر readiness probe."""
    if _health_status == "healthy":
        return web.json_response({"ready": True})
    return web.json_response({"ready": False}, status=503)


async def start_health_server(port: int = 8080):
    """سرور health check رو شروع میکنه."""
    global _health_status
    try:
        app = web.Application()
        app.router.add_get("/health", health_handler)
        app.router.add_get("/ready", readiness_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        _health_status = "healthy"
        log.info("Health check server started on port %d", port)
    except Exception as e:
        log.warning("Health server failed to start: %s", e)
        _health_status = "degraded"


def mark_unhealthy():
    """علامت‌گذاری ربات به عنوان ناسالم."""
    global _health_status
    _health_status = "unhealthy"
