"""Comprehensive error handling tests."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.errors import safe_run, safe_run_sync
from bot.middleware import RateLimitMiddleware, InputValidationMiddleware
from bot.circuit_breaker import CircuitBreaker, CircuitState


class TestSafeRun:
    @pytest.mark.asyncio
    async def test_success_return(self):
        @safe_run
        async def func():
            return 42
        assert await func() == 42

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        @safe_run
        async def func():
            raise ValueError("error")
        assert await func() is None

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_not_caught(self):
        @safe_run
        async def func():
            raise KeyboardInterrupt()
        with pytest.raises(KeyboardInterrupt):
            await func()

    def test_sync_success(self):
        @safe_run_sync
        def func():
            return 42
        assert func() == 42

    def test_sync_exception(self):
        @safe_run_sync
        def func():
            raise ValueError("error")
        assert func() is None


class TestRateLimitEdgeCases:
    def test_zero_requests(self):
        m = RateLimitMiddleware(max_requests=0, window_seconds=60)
        assert m.max_requests == 0

    def test_large_window(self):
        m = RateLimitMiddleware(max_requests=100, window_seconds=3600)
        assert m.window_seconds == 3600

    def test_cleanup_old_entries(self):
        import time
        m = RateLimitMiddleware(max_requests=5, window_seconds=1)
        m._requests[1] = [time.time() - 10, time.time() - 5, time.time()]
        m._requests[1] = [t for t in m._requests[1] if time.time() - t < 1]
        assert len(m._requests[1]) == 1


class TestInputValidationEdgeCases:
    def test_long_message(self):
        m = InputValidationMiddleware()
        assert m._MAX_MESSAGE_LENGTH == 4000

    def test_long_callback(self):
        m = InputValidationMiddleware()
        assert m._MAX_CALLBACK_LENGTH == 64

    def test_dangerous_patterns_count(self):
        m = InputValidationMiddleware()
        assert len(m._DANGEROUS_PATTERNS) > 0


class TestCircuitBreakerEdgeCases:
    def test_multiple_failures(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_after_failure(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_recovery_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        import time
        time.sleep(0.01)
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        import time
        time.sleep(0.01)
        cb.can_execute()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        import time
        time.sleep(0.01)
        cb.can_execute()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
