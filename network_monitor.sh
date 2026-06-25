#!/bin/bash
# Network connectivity monitor and auto-recovery
# Ensures internet stays connected even during brief outages

LOG_FILE="/root/kaysan-bot/network_monitor.log"
PING_HOSTS=("8.8.8.8" "1.1.1.1" "api.telegram.org")
RETRY_INTERVAL=5
MAX_RETRIES=3

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

check_connectivity() {
    for host in "${PING_HOSTS[@]}"; do
        if ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
            return 0
        fi
    done
    return 1
}

recover_network() {
    log_msg "🔄 Attempting network recovery..."
    
    # Try restarting NetworkManager
    if systemctl is-active --quiet NetworkManager; then
        systemctl restart NetworkManager
        sleep 3
    fi
    
    # Try restarting networking
    if systemctl is-active --quiet networking; then
        systemctl restart networking
        sleep 3
    fi
    
    # Try renewing DHCP lease
    for iface in $(ip -o link show | awk -F': ' '{print $2}' | grep -v lo); do
        dhclient -r "$iface" 2>/dev/null
        dhclient "$iface" 2>/dev/null
    done
    
    # Flush and rebuild routing table
    ip route flush cache 2>/dev/null
    
    # Try DNS flush
    systemd-resolve --flush-caches 2>/dev/null
    
    sleep 5
}

log_msg "Network monitor started"

while true; do
    if ! check_connectivity; then
        log_msg "⚠️  Network connectivity lost. Attempting recovery..."
        
        for i in $(seq 1 $MAX_RETRIES); do
            log_msg "🔄 Recovery attempt $i/$MAX_RETRIES"
            recover_network
            
            if check_connectivity; then
                log_msg "✅ Network recovered after $i attempt(s)"
                break
            fi
        done
        
        if ! check_connectivity; then
            log_msg "❌ Network recovery failed after $MAX_RETRIES attempts"
        fi
    fi
    
    sleep $RETRY_INTERVAL
done
