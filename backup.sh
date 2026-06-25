#!/bin/bash
# ============================================================
#  Kaysan AI — بکاپ کامل هر ۵ دقیقه
#  شامل: کد، دیتابیس، کانفیگ، پکیج‌ها، systemd، .env
# ============================================================

set -euo pipefail

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M)
BOT_TOKEN=$(grep BOT_TOKEN /root/kaysan-bot/.env | cut -d= -f2)
ADMIN_ID="6278069364"
KEEP_DAYS=3

mkdir -p "$BACKUP_DIR"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

send_telegram() {
    local file="$1"
    local caption="$2"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
        -F document=@"$file" \
        -F chat_id="$ADMIN_ID" \
        -F caption="$caption" > /dev/null 2>&1 || true
}

send_text() {
    local text="$1"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="$ADMIN_ID" \
        -d text="$text" \
        -d parse_mode="HTML" > /dev/null 2>&1 || true
}

# ─── بکاپ کامل سرور اصلی ───
log "📦 شروع بکاپ کامل..."

TMP="/tmp/backup_${DATE}"
mkdir -p "$TMP"

# 1. لیست پکیج‌های نصب شده
dpkg --get-selections > "$TMP/packages.list" 2>/dev/null || true
apt-mark showmanual > "$TMP/packages_manual.list" 2>/dev/null || true

# 2. کانفیگ سیستم
cp /etc/fstab "$TMP/fstab" 2>/dev/null || true
cp /etc/hostname "$TMP/hostname" 2>/dev/null || true
cp /etc/hosts "$TMP/hosts" 2>/dev/null || true
cp /etc/crontab "$TMP/crontab" 2>/dev/null || true
crontab -l > "$TMP/crontab_user" 2>/dev/null || true

# 3. systemd service ها
cp /etc/systemd/system/kaysan-bot.service "$TMP/" 2>/dev/null || true
cp /etc/systemd/system/saveo-bot.service "$TMP/" 2>/dev/null || true

# 4. فایل‌های کاربر
cp /root/.bashrc "$TMP/" 2>/dev/null || true
cp /root/.profile "$TMP/" 2>/dev/null || true

# 5. SSH keys
mkdir -p "$TMP/ssh"
cp /root/.ssh/authorized_keys "$TMP/ssh/" 2>/dev/null || true

# 6. Xray config
cp /usr/local/etc/xray/config.json "$TMP/xray_config.json" 2>/dev/null || true

# 7. دیتابیس ربات
cp /root/kaysan-bot/kaysan.db "$TMP/kaysan.db" 2>/dev/null || true

# 8. کد ربات کامل (بدون venv)
tar czf "$TMP/kaysan_code.tar.gz" \
    -C /root \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    kaysan-bot/.env \
    kaysan-bot/bot/ \
    kaysan-bot/run.py \
    kaysan-bot/requirements.txt \
    kaysan-bot/kaysan-bot.service \
    kaysan-bot/backup.sh \
    kaysan-bot/sync.sh \
    2>/dev/null || true

# 9. کد Saveo Bot (اگه هست)
if [ -d /root/saveo-bot ]; then
    tar czf "$TMP/saveo_code.tar.gz" \
        -C /root \
        --exclude='venv' \
        --exclude='__pycache__' \
        saveo-bot/.env \
        saveo-bot/bot/ \
        saveo-bot/run.py \
        saveo-bot/requirements.txt \
        saveo-bot/saveo-bot.service \
        2>/dev/null || true
fi

# 10. crontab سرور
cp /var/spool/cron/crontabs/root "$TMP/crontab_root" 2>/dev/null || true

# 11. لیست فایل‌های سیستم
find /root/kaysan-bot -type f -not -path "*/venv/*" -not -path "*/__pycache__/*" > "$TMP/file_list.txt" 2>/dev/null || true

# ─── فشرده‌سازی نهایی ───
log "📦 فشرده‌سازی..."
cd /tmp
tar czf "${BACKUP_DIR}/full_backup_${DATE}.tar.gz" "backup_${DATE}/" 2>/dev/null

# ─── ارسال به تلگرام ───
log "📤 ارسال به تلگرام..."
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/full_backup_${DATE}.tar.gz" | cut -f1)
PKG_COUNT=$(wc -l < "$TMP/packages.list" 2>/dev/null || echo "?")

send_text "📦 <b>بکاپ کامل سرور</b>
📅 ${DATE}
💾 حجم: ${BACKUP_SIZE}
📦 پکیج‌ها: ${PKG_COUNT}
🖥️ شامل: کد+دیتابیس+کانفیگ+پکیج‌ها+systemd"

if [ -f "${BACKUP_DIR}/full_backup_${DATE}.tar.gz" ]; then
    send_telegram "${BACKUP_DIR}/full_backup_${DATE}.tar.gz" "📦 بکاپ کامل ${DATE}"
fi

# ─── پاکسازی ───
log "🧹 پاکسازی..."
rm -rf "$TMP"
find "$BACKUP_DIR" -name "full_backup_*.tar.gz" -mtime +${KEEP_DAYS} -delete 2>/dev/null || true

log "✅ بکاپ تمام شد!"
