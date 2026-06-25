"""Structured Logging — لاگ ساختاریافته."""
import json
import logging
import sys
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """فرمت‌دهنده لاگ ساختاریافته JSON."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO"):
    """تنظیم لاگ ساختاریافته."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root.handlers = [handler]

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
