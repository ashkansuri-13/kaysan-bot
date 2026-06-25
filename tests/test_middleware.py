"""Unit tests for bot.middleware — rate limiting."""
import time
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.middleware import RateLimitMiddleware


class TestRateLimitMiddleware:
    def test_init(self):
        middleware = RateLimitMiddleware(max_requests=10, window_seconds=60)
        assert middleware.max_requests == 10
        assert middleware.window_seconds == 60

    def test_requests_tracking(self):
        middleware = RateLimitMiddleware(max_requests=5, window_seconds=60)
        middleware._requests[123].append(time.time())
        assert len(middleware._requests[123]) == 1
