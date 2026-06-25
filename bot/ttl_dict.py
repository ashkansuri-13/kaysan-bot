"""دیکشنری با TTL خودکار — جلوگیری از نشت حافظه."""
import time
from collections.abc import MutableMapping


class TTLDict(MutableMapping):
    """دیکشنری که بعد از مدت مشخصی آنتی‌اکسپایر میشه."""

    def __init__(self, ttl_seconds=3600, max_size=10000):
        self._data: dict = {}
        self._expires: dict = {}
        self._ttl = ttl_seconds
        self._max_size = max_size

    def __setitem__(self, key, value):
        now = time.monotonic()
        self._data[key] = value
        self._expires[key] = now + self._ttl
        if len(self._data) > self._max_size:
            self._evict()

    def __getitem__(self, key):
        if key in self._expires and time.monotonic() > self._expires[key]:
            del self[key]
        return self._data[key]

    def __delitem__(self, key):
        self._data.pop(key, None)
        self._expires.pop(key, None)

    def __contains__(self, key):
        if key in self._expires and time.monotonic() > self._expires[key]:
            del self[key]
        return key in self._data

    def __iter__(self):
        now = time.monotonic()
        expired = [k for k, exp in self._expires.items() if now > exp]
        for k in expired:
            del self[k]
        return iter(self._data)

    def __len__(self):
        self._evict()
        return len(self._data)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def _evict(self):
        now = time.monotonic()
        expired = [k for k, exp in self._expires.items() if now > exp]
        for k in expired:
            self._data.pop(k, None)
            self._expires.pop(k, None)
