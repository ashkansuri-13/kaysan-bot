"""Tests for new modules — metrics, sentry, pool, circuit_breaker, backup."""
import pytest
from bot.metrics import (
    record_message, record_callback, record_error, record_api_call,
    _metrics, _format_prometheus, metrics_handler,
)
from bot.sentry_config import init_sentry, capture_exception, capture_message
from bot.pool import ConnectionPool, get_pool
from bot.circuit_breaker import CircuitBreaker, CircuitState, get_breaker, circuit_protected
from bot.backup import BackupManager, backup_loop


class TestMetrics:
    def test_record_message(self):
        _metrics["messages_total"] = 0
        record_message(123)
        assert _metrics["messages_total"] == 1
        assert 123 in _metrics["active_users"]

    def test_record_callback(self):
        _metrics["callbacks_total"] = 0
        record_callback(456)
        assert _metrics["callbacks_total"] == 1

    def test_record_error(self):
        _metrics["errors_total"] = 0
        record_error()
        assert _metrics["errors_total"] == 1

    def test_record_api_call(self):
        _metrics["api_calls_total"] = 0
        _metrics["api_latency_sum"] = 0
        _metrics["api_latency_count"] = 0
        record_api_call(0.5)
        assert _metrics["api_calls_total"] == 1
        assert _metrics["api_latency_sum"] == 0.5

    def test_format_prometheus(self):
        output = _format_prometheus()
        assert "kaysan_uptime_seconds" in output
        assert "kaysan_messages_total" in output


class TestSentry:
    def test_init_sentry_no_dsn(self):
        import os
        os.environ.pop("SENTRY_DSN", None)
        init_sentry()

    def test_capture_exception(self):
        capture_exception(ValueError("test"))

    def test_capture_message(self):
        capture_message("test message")


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_failure_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        import time
        time.sleep(0.1)
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_get_breaker(self):
        cb = get_breaker("test_breaker", failure_threshold=5)
        assert isinstance(cb, CircuitBreaker)

    def test_circuit_protected_decorator(self):
        from bot.circuit_breaker import _breakers
        _breakers.pop("test_protected3", None)

        @circuit_protected("test_protected3", failure_threshold=1, recovery_timeout=0)
        async def test_func():
            return 42

        async def run():
            return await test_func()

        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(run())
            assert result == 42
        finally:
            loop.close()


class TestConnectionPool:
    def test_get_pool(self):
        pool = get_pool(":memory:")
        assert isinstance(pool, ConnectionPool)
        assert pool.max_connections == 5

    @pytest.mark.asyncio
    async def test_acquire_release(self):
        pool = get_pool(":memory:")
        conn = await pool.acquire()
        assert conn is not None
        await pool.release(conn)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        pool = get_pool(":memory:")
        async with pool.connection() as conn:
            assert conn is not None


class TestBackupManager:
    def test_create_backup(self):
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"test data")
            db_path = f.name
        try:
            manager = BackupManager(db_path, backup_dir=tempfile.mkdtemp())
            result = manager.create_backup()
            assert result is not None
            assert os.path.exists(result)
        finally:
            os.unlink(db_path)

    def test_list_backups(self):
        import tempfile
        manager = BackupManager(":memory:", backup_dir=tempfile.mkdtemp())
        backups = manager.list_backups()
        assert isinstance(backups, list)
