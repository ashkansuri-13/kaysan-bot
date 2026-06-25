"""Auth utilities for Telegram WebApp.initData validation + session management."""
import base64
import hashlib
import hmac
import json
import time
import secrets
from urllib.parse import parse_qsl

from . import config


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Validate Telegram WebApp initData using HMAC-SHA256.
    Returns parsed user dict or None if invalid.
    """
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True)
        received_hash = None
        data_check_parts = []

        for key, value in pairs:
            if key == "hash":
                received_hash = value
            else:
                data_check_parts.append(f"{key}={value}")

        if not received_hash:
            return None

        data_check_string = "\n".join(sorted(data_check_parts))

        secret_key = hmac.new(
            bot_token.encode(),
            b"WebAppData",
            hashlib.sha256,
        ).digest()

        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return None

        parsed = dict(pairs)
        user_json = parsed.get("user", "{}")
        user = json.loads(user_json)

        auth_date = int(parsed.get("auth_date", 0))
        if time.time() - auth_date > 86400:
            return None

        return user
    except Exception:
        return None


def create_session_token(user_id: int) -> str:
    """Create a signed session token: base64(user_id:timestamp:hmac_signature)"""
    payload = f"{user_id}:{int(time.time())}"
    secret = config.WEB_SESSION_SECRET.encode()
    sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.b64encode(f"{payload}:{sig}".encode()).decode()


def verify_session_token(token: str) -> int | None:
    """Verify session token, return user_id or None."""
    try:
        decoded = base64.b64decode(token).decode()
        parts = decoded.rsplit(":", 2)
        if len(parts) != 3:
            return None
        user_id_str, timestamp_str, sig = parts
        payload = f"{user_id_str}:{timestamp_str}"
        secret = config.WEB_SESSION_SECRET.encode()
        expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        expiry_hours = getattr(config, "SESSION_EXPIRY_HOURS", 168)
        if time.time() - int(timestamp_str) > expiry_hours * 3600:
            return None
        return int(user_id_str)
    except Exception:
        return None
