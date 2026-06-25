"""Circuit Breaker — الگوی مقاوم در برابر خطا."""
# NOTE: This module is currently unused (not imported anywhere). Kept for potential future use.
import time
import logging
from enum import Enum
from functools import wraps

log = logging.getLogger("kaysan.cb")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            log.warning("circuit breaker OPEN after %d failures", self.failure_count)

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def reset(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED


_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(**kwargs)
    return _breakers[name]


def circuit_protected(name: str, **kwargs):
    """دکوراتور circuit breaker برای توابع async."""
    def decorator(func):
        breaker = get_breaker(name, **kwargs)

        @wraps(func)
        async def wrapper(*args, **kw):
            if not breaker.can_execute():
                raise RuntimeError(f"circuit breaker '{name}' is OPEN")
            try:
                result = await func(*args, **kw)
                breaker.record_success()
                return result
            except Exception:
                breaker.record_failure()
                raise
        return wrapper
    return decorator
