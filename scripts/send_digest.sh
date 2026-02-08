#!/bin/bash
# Send daily digest via OpenClaw message tool
# This script will be called by cron

DIGEST_FILE="$HOME/saas-hunter/data/telegram_queue/digest_$(date +%Y%m%d).txt"

if [ -f "$DIGEST_FILE" ]; then
    # Send via OpenClaw message tool to Telegram user ID 1153284
    openclaw message send --channel telegram --target 1153284 --message "$(cat "$DIGEST_FILE")"
    
    if [ $? -eq 0 ]; then
        echo "✅ Digest sent successfully"
        # Archive sent digest
        mv "$DIGEST_FILE" "$DIGEST_FILE.sent"
    else
        echo "⚠️  Failed to send digest"
    fi
else
    echo "⚠️  No digest file found: $DIGEST_FILE"
fi
