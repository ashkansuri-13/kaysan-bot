"""ابزارهای مدیریت خطا — safe_run decorator."""
import functools
import logging

log = logging.getLogger("kaysan.errors")


def safe_run(func):
    """دکوراتور برای اجرای امن توابع async — خطا را می‌گیرد و None برمی‌گرداند."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.warning("safe_run caught: %s in %s", e, func.__name__)
            return None
    return wrapper


def safe_run_sync(func):
    """دکوراتور برای اجرای امن توابع sync — خطا را می‌گیرد و None برمی‌گرداند."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.warning("safe_run_sync caught: %s in %s", e, func.__name__)
            return None
    return wrapper
