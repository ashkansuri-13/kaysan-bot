#!/bin/bash
# ============================================================
#  Kaysan AI — هماهنگ‌سازی خودکار سرورها
#  هر ۱۰ دقیقه کد از سرور اصلی به ریموت sync میشه
# ============================================================

REMOTE="root@46.249.100.119"
LOCAL="/root/kaysan-bot"
REMOTE_DIR="/root/kaysan-bot"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

log "🔄 شروع هماهنگ‌سازی..."

# sync کد
rsync -avz --delete \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='backups/' \
    "$LOCAL/" "$REMOTE:$REMOTE_DIR/" > /dev/null 2>&1

# sync .env
scp "$LOCAL/.env" "$REMOTE:$REMOTE_DIR/.env" > /dev/null 2>&1

# فقط sync کن — ربات رو اجرا نکن (فقط سرور اصلی اجرا می‌کنه)
# ssh "$REMOTE" "systemctl restart kaysan-bot 2>/dev/null" > /dev/null 2>&1

log "✅ هماهنگ‌سازی تمام شد!"
