"""Sentry Error Tracking — ردیابی خطاها."""
import os
import logging

log = logging.getLogger("kaysan.sentry")

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENV = os.getenv("SENTRY_ENVIRONMENT", "production")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))


def init_sentry():
    """Sentry رو مقداردهی اولیه میکنه."""
    if not SENTRY_DSN:
        log.info("Sentry DSN not configured, error tracking disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENV,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            integrations=[sentry_logging],
            attach_stacktrace=True,
            send_default_pii=False,
        )

        log.info("Sentry initialized (env: %s)", SENTRY_ENV)
    except ImportError:
        log.warning("sentry-sdk not installed. Error tracking disabled.")
    except Exception as e:
        log.warning("Sentry init failed: %s", e)


def capture_exception(e: Exception, **kwargs):
    """ارسال خطا به Sentry."""
    if not SENTRY_DSN:
        return
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(e, **kwargs)
    except Exception:
        pass


def capture_message(message: str, level: str = "info"):
    """ارسال پیام به Sentry."""
    if not SENTRY_DSN:
        return
    try:
        import sentry_sdk
        sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass
