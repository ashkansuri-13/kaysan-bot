#!/bin/bash
BOT_DIR="/root/kaysan-bot"
SNAP_FILE="/tmp/kaysan_snapshot.txt"

# Create initial snapshot
find "$BOT_DIR" -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*" -printf "%p %T@\n" | sort > "$SNAP_FILE"

echo "🔍 Kaysan Bot Monitor Started at $(date)"
echo "Monitoring: $BOT_DIR"
echo "==========================================="
while true; do
    sleep 10
    NEW_SNAP=$(mktemp)
    find "$BOT_DIR" -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*" -printf "%p %T@\n" | sort > "$NEW_SNAP"
    
    # Check for changes
    CHANGED=$(diff "$SNAP_FILE" "$NEW_SNAP" 2>/dev/null)
    if [ -n "$CHANGED" ]; then
        TIMESTAMP=$(date "+%H:%M:%S %Z")
        echo ""
        echo "⚡ [$TIMESTAMP] Changes detected:"
        echo "$CHANGED" | grep "^[<>]" | while read line; do
            if echo "$line" | grep -q "^<"; then
                FILE=$(echo "$line" | awk "{print \$1}")
                echo "  📝 Modified: $(basename $FILE)"
            elif echo "$line" | grep -q "^>"; then
                FILE=$(echo "$line" | awk "{print \$1}")
                echo "  📄 Changed: $(basename $FILE)"
            fi
        done
        
        # Show git diff if available
        cd "$BOT_DIR" && git diff --stat 2>/dev/null | head -5
        
        cp "$NEW_SNAP" "$SNAP_FILE"
    fi
    rm -f "$NEW_SNAP"
done
