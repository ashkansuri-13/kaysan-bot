"""Prometheus Metrics — متریک‌های مانیتورینگ."""
import time
import logging
from collections import defaultdict
from aiohttp import web

log = logging.getLogger("kaysan.metrics")

_start_time = time.time()
_metrics = {
    "messages_total": 0,
    "callbacks_total": 0,
    "errors_total": 0,
    "api_calls_total": 0,
    "api_latency_sum": 0.0,
    "api_latency_count": 0,
    "active_users": set(),
}


def record_message(user_id: int = 0):
    """ثبت پیام جدید."""
    _metrics["messages_total"] += 1
    if user_id:
        _metrics["active_users"].add(user_id)


def record_callback(user_id: int = 0):
    """ثبت callback جدید."""
    _metrics["callbacks_total"] += 1
    if user_id:
        _metrics["active_users"].add(user_id)


def record_error():
    """ثبت خطا."""
    _metrics["errors_total"] += 1


def record_api_call(latency: float):
    """ثبت فراخوانی API."""
    _metrics["api_calls_total"] += 1
    _metrics["api_latency_sum"] += latency
    _metrics["api_latency_count"] += 1


def _format_prometheus() -> str:
    """فرمت‌دهی متریک‌ها برای Prometheus."""
    uptime = time.time() - _start_time
    avg_latency = (
        _metrics["api_latency_sum"] / _metrics["api_latency_count"]
        if _metrics["api_latency_count"] > 0
        else 0
    )

    lines = [
        "# HELP kaysan_uptime_seconds Bot uptime in seconds",
        "# TYPE kaysan_uptime_seconds gauge",
        f"kaysan_uptime_seconds {uptime:.1f}",
        "",
        "# HELP kaysan_messages_total Total messages processed",
        "# TYPE kaysan_messages_total counter",
        f"kaysan_messages_total {_metrics['messages_total']}",
        "",
        "# HELP kaysan_callbacks_total Total callbacks processed",
        "# TYPE kaysan_callbacks_total counter",
        f"kaysan_callbacks_total {_metrics['callbacks_total']}",
        "",
        "# HELP kaysan_errors_total Total errors",
        "# TYPE kaysan_errors_total counter",
        f"kaysan_errors_total {_metrics['errors_total']}",
        "",
        "# HELP kaysan_api_calls_total Total API calls",
        "# TYPE kaysan_api_calls_total counter",
        f"kaysan_api_calls_total {_metrics['api_calls_total']}",
        "",
        "# HELP kaysan_api_latency_seconds Average API latency",
        "# TYPE kaysan_api_latency_seconds gauge",
        f"kaysan_api_latency_seconds {avg_latency:.3f}",
        "",
        "# HELP kaysan_active_users Number of unique active users",
        "# TYPE kaysan_active_users gauge",
        f"kaysan_active_users {len(_metrics['active_users'])}",
    ]

    return "\n".join(lines)


async def metrics_handler(request):
    """هندلر Prometheus metrics."""
    return web.Response(
        text=_format_prometheus(),
        content_type="text/plain",
    )


async def start_metrics_server(port: int = 9090):
    """سرور متریک‌ها رو شروع میکنه."""
    try:
        app = web.Application()
        app.router.add_get("/metrics", metrics_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        log.info("Metrics server started on port %d", port)
    except Exception as e:
        log.warning("Metrics server failed to start: %s", e)
