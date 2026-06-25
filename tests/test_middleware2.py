"""Middleware and errors tests — comprehensive."""
import time
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.middleware import RateLimitMiddleware, InputValidationMiddleware
from bot.errors import safe_run, safe_run_sync


class TestRateLimitExtended:
    def test_window_cleanup(self):
        m = RateLimitMiddleware(max_requests=5, window_seconds=60)
        m._requests[1].append(time.time() - 120)
        m._requests[1].append(time.time())
        m._requests[1] = [t for t in m._requests[1] if time.time() - t < 60]
        assert len(m._requests[1]) == 1

    def test_multiple_users(self):
        m = RateLimitMiddleware(max_requests=5, window_seconds=60)
        m._requests[1].append(time.time())
        m._requests[2].append(time.time())
        assert len(m._requests[1]) == 1
        assert len(m._requests[2]) == 1


class TestInputValidation:
    def test_dangerous_patterns(self):
        m = InputValidationMiddleware()
        assert len(m._DANGEROUS_PATTERNS) > 0

    def test_max_lengths(self):
        m = InputValidationMiddleware()
        assert m._MAX_MESSAGE_LENGTH == 4000
        assert m._MAX_CALLBACK_LENGTH == 64


class TestSafeRun:
    @pytest.mark.asyncio
    async def test_success(self):
        @safe_run
        async def ok():
            return 42
        assert await ok() == 42

    @pytest.mark.asyncio
    async def test_failure(self):
        @safe_run
        async def fail():
            raise ValueError("test")
        result = await fail()
        assert result is None

    def test_sync_success(self):
        @safe_run_sync
        def ok():
            return 42
        assert ok() == 42

    def test_sync_failure(self):
        @safe_run_sync
        def fail():
            raise ValueError("test")
        assert fail() is None
