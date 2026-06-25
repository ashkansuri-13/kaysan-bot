"""Database Migration — سیستم مهاجرت دیتابیس."""
import logging
from datetime import datetime, timezone

import aiosqlite

from . import config

log = logging.getLogger("kaysan.migration")

_DB = str(config.DB_PATH)

MIGRATIONS = [
    {
        "version": 1,
        "name": "initial_schema",
        "sql": """
            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
        """,
    },
]


async def get_current_version() -> int:
    """نسخه فعلی دیتابیس رو برمیگرداند."""
    try:
        async with aiosqlite.connect(_DB) as db:
            cur = await db.execute("SELECT MAX(version) FROM migrations")
            row = await cur.fetchone()
            return row[0] if row and row[0] else 0
    except Exception:
        return 0


async def run_migrations():
    """تمام مиграشن‌های جدید رو اجرا میکنه."""
    current = await get_current_version()
    log.info("Database version: %d", current)

    for migration in MIGRATIONS:
        if migration["version"] > current:
            log.info("Running migration %d: %s", migration["version"], migration["name"])
            try:
                async with aiosqlite.connect(_DB) as db:
                    for statement in migration["sql"].split(";"):
                        statement = statement.strip()
                        if statement:
                            await db.execute(statement)
                    await db.execute(
                        "INSERT INTO migrations (version, name, applied_at) VALUES (?, ?, ?)",
                        (migration["version"], migration["name"],
                         datetime.now(timezone.utc).isoformat()),
                    )
                    await db.commit()
                log.info("Migration %d applied successfully", migration["version"])
            except Exception as e:
                log.error("Migration %d failed: %s", migration["version"], e)
                raise
