"""Unit tests for bot.health and bot.logging_config."""
import pytest
from bot.health import _start_time, _health_status, mark_unhealthy
from bot.logging_config import StructuredFormatter, setup_logging


class TestHealth:
    def test_start_time(self):
        assert _start_time > 0

    def test_mark_unhealthy(self):
        mark_unhealthy()
        from bot.health import _health_status
        assert _health_status == "unhealthy"


class TestLogging:
    def test_formatter(self):
        formatter = StructuredFormatter()
        import logging
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        output = formatter.format(record)
        assert "test message" in output
        assert "INFO" in output
