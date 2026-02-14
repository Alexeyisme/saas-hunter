#!/usr/bin/env python3
"""
Send alert to Telegram for critical errors
"""
import os
import sys
import requests

def send_alert(message):
    """Send alert message to Telegram"""
    # Use OpenClaw message tool instead of bot token
    # This script will be called from Python, not shell
    print(f"ALERT: {message}", file=sys.stderr)
    
    # For now, just log - OpenClaw integration would require subprocess
    # TODO: Integrate with OpenClaw message tool
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        send_alert(' '.join(sys.argv[1:]))
