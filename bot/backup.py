"""Backup Automation — بکاپ خودکار دیتابیس."""
import asyncio
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("kaysan.backup")


class BackupManager:
    """مدیریت بکاپ خودکار دیتابیس."""

    def __init__(self, db_path: str, backup_dir: str = "backups", max_backups: int = 7):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> str | None:
        """بکاپ جدید بساز."""
        if not self.db_path.exists():
            log.error("Database file not found: %s", self.db_path)
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"kaysan_{timestamp}.db"

        try:
            shutil.copy2(self.db_path, backup_path)
            log.info("Backup created: %s", backup_path)
            self._cleanup_old_backups()
            return str(backup_path)
        except Exception as e:
            log.error("Backup failed: %s", e)
            return None

    def _cleanup_old_backups(self):
        """بکاپ‌های قدیمی رو پاک میکنه."""
        backups = sorted(self.backup_dir.glob("kaysan_*.db"), key=lambda p: p.stat().st_mtime)
        while len(backups) > self.max_backups:
            old = backups.pop(0)
            try:
                old.unlink()
                log.info("Old backup deleted: %s", old)
            except Exception as e:
                log.warning("Failed to delete old backup: %s", e)

    def list_backups(self) -> list[dict]:
        """لیست بکاپ‌ها رو برمیگرداند."""
        backups = []
        for f in sorted(self.backup_dir.glob("kaysan_*.db"), key=lambda p: p.stat().st_mtime, reverse=True):
            backups.append({
                "path": str(f),
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
        return backups


async def backup_loop(db_path: str, backup_dir: str = "backups", interval: int = 21600):
    """چرخه بکاپ خودکار (هر ۶ ساعت)."""
    manager = BackupManager(db_path, backup_dir)
    while True:
        try:
            manager.create_backup()
        except Exception as e:
            log.error("Backup loop error: %s", e)
        await asyncio.sleep(interval)
