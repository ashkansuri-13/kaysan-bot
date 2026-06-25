"""Rate Limiting و Input Validation — محدودسازی و اعتبارسنجی درخواست‌ها."""
import re
import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class RateLimitMiddleware(BaseMiddleware):
    """محدودسازی تعداد درخواست در بازه زمانی."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[int, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()
        super().__init__()

    def _cleanup(self):
        now = time.time()
        if now - self._last_cleanup < 300:
            return
        self._last_cleanup = now
        stale = [uid for uid, ts in self._requests.items()
                 if not ts or now - max(ts) > self.window_seconds * 2]
        for uid in stale:
            del self._requests[uid]

    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id is None:
            return await handler(event, data)

        self._cleanup()
        now = time.time()
        self._requests[user_id] = [
            t for t in self._requests[user_id] if now - t < self.window_seconds
        ]

        if len(self._requests[user_id]) >= self.max_requests:
            if isinstance(event, Message):
                await event.answer("⏰ درخواست‌هات زیاد شده. کمی صبر کن.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏰ صبر کن!", show_alert=True)
            return None

        self._requests[user_id].append(now)
        return await handler(event, data)


class InputValidationMiddleware(BaseMiddleware):
    """اعتبارسنجی ورودی کاربر — جلوگیری از نفوذ و سوءاستفاده."""

    _DANGEROUS_PATTERNS = [
        re.compile(r"__\w+__", re.I),
        re.compile(r"exec\s*\(", re.I),
        re.compile(r"eval\s*\(", re.I),
        re.compile(r"(\/etc\/passwd|\/etc\/shadow)", re.I),
        re.compile(r"(DROP\s+TABLE|DELETE\s+FROM)", re.I),
    ]

    _MAX_MESSAGE_LENGTH = 4000
    _MAX_CALLBACK_LENGTH = 64

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text:
            text = event.text
            if len(text) > self._MAX_MESSAGE_LENGTH:
                await event.answer("❌ پیام خیلی بلنده. کوتاه‌تر بنویس.")
                return None
            for pattern in self._DANGEROUS_PATTERNS:
                if pattern.search(text):
                    await event.answer("❌ محتوای نامعتبر تشخیص داده شد.")
                    return None

        if isinstance(event, CallbackQuery) and event.data:
            if len(event.data) > self._MAX_CALLBACK_LENGTH:
                await event.answer("❌ درخواست نامعتبر.", show_alert=True)
                return None

        return await handler(event, data)
