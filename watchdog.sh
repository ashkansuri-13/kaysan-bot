#!/bin/bash
# Kaysan AI Health Check Watchdog
# Checks services every 30 seconds and restarts if needed

BOT_SERVICE="kaysan-bot.service"
WEB_SERVICE="kaysan-web.service"
LOG_FILE="/root/kaysan-bot/watchdog.log"

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

check_service() {
    local service=$1
    local status=$(systemctl is-active "$service" 2>/dev/null)
    
    if [ "$status" != "active" ]; then
        log_msg "⚠️  $service is not running (status: $status). Restarting..."
        systemctl restart "$service"
        sleep 5
        local new_status=$(systemctl is-active "$service" 2>/dev/null)
        if [ "$new_status" = "active" ]; then
            log_msg "✅ $service restarted successfully"
        else
            log_msg "❌ Failed to restart $service"
        fi
        return 1
    fi
    return 0
}

check_port() {
    local port=$1
    local name=$2
    
    if ! ss -tlnp | grep -q ":${port} "; then
        log_msg "⚠️  Port $port ($name) is not listening"
        return 1
    fi
    return 0
}

check_internet() {
    if ! ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
        log_msg "⚠️  Internet connectivity lost"
        return 1
    fi
    if ! ping -c 1 -W 3 api.telegram.org >/dev/null 2>&1; then
        log_msg "⚠️  Telegram API unreachable"
        return 1
    fi
    return 0
}

check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 90 ]; then
        log_msg "⚠️  Disk usage critical: ${usage}%"
        return 1
    fi
    return 0
}

check_memory() {
    local free_mem=$(free -m | awk 'NR==2 {print $7}')
    if [ "$free_mem" -lt 100 ]; then
        log_msg "⚠️  Low memory: ${free_mem}MB available"
        return 1
    fi
    return 0
}

log_msg "Watchdog started"

while true; do
    check_service "$BOT_SERVICE"
    check_service "$WEB_SERVICE"
    
    check_port 8080 "Bot Health"
    check_port 3000 "Web Server"
    check_port 80 "Nginx"
    
    check_internet
    check_disk_space
    check_memory
    
    sleep 30
done
