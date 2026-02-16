#!/usr/bin/env python3
"""
Send Telegram Digest via OpenClaw
Writes digest to a marker file that OpenClaw monitors and sends
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from usage_tracker import UsageTracker
from utils import setup_logging
from config import LOG_DIR, PROCESSED_DIR, TELEGRAM_TOP_N
from scoring import SCORING_CONFIG

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTBOX_DIR = DATA_DIR / 'telegram_outbox'
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logger = setup_logging(__name__, LOG_DIR / 'telegram.log')

def load_today_opportunities():
    """Load today's processed opportunities"""
    today = datetime.now().strftime('%Y%m%d')
    jsonl_file = PROCESSED_DIR / f'opportunities_{today}.jsonl'
    
    if not jsonl_file.exists():
        return []
    
    opportunities = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            opportunities.append(json.loads(line))
    
    return opportunities

def format_telegram_message(opportunities):
    """Format top opportunities for Telegram"""
    if not opportunities:
        return None  # Don't send empty digest
    
    # Sort by score
    sorted_opps = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)

    # Get top N from config
    top_n = sorted_opps[:TELEGRAM_TOP_N]
    
    # Build message
    date_str = datetime.now().strftime('%b %d, %Y')
    msg = f"🎯 **SaaS Opportunities — {date_str}**\n\n"

    # Get score threshold from config
    high_quality_threshold = SCORING_CONFIG.get('thresholds', {}).get('high_quality', 60)

    for i, opp in enumerate(top_n, 1):
        title = opp['title']
        score = opp['score']
        source = opp['source']
        url = opp['url']

        # Pain point emoji
        emoji = "⭐️" if score >= high_quality_threshold else "💡"
        
        msg += f"{i}. {emoji} **{title}** ({score} pts)\n"
        msg += f"   📍 {source}\n"
        
        # Engagement
        engagement = opp.get('engagement_data', {})
        if engagement.get('reactions'):
            msg += f"   👍 {engagement['reactions']} reactions\n"
        elif engagement.get('comments'):
            msg += f"   💬 {engagement['comments']} comments\n"
        
        msg += f"   🔗 {url}\n\n"
    
    # Summary
    total = len(opportunities)
    high_quality = len([o for o in opportunities if o.get('score', 0) >= high_quality_threshold])

    msg += f"📊 {total} collected | {high_quality} high quality ({high_quality_threshold}+)\n\n"
    
    # View full digest hint
    msg += "_Full digest: ~/saas-hunter/data/digests/_"
    
    return msg

def main():
    """Generate and queue Telegram digest for OpenClaw to send"""
    tracker = UsageTracker()
    
    with tracker.track_job('delivery', 'send_telegram_openclaw') as job:
        logger.info("=" * 60)
        logger.info("Queueing Telegram Digest for OpenClaw")
        logger.info("=" * 60)
        
        # Load opportunities
        opportunities = load_today_opportunities()
        logger.info(f"Loaded {len(opportunities)} opportunities")
        
        if not opportunities:
            logger.info("No opportunities to send")
            print("ℹ️  No opportunities found today - skipping Telegram digest")
            return
        
        # Format message
        message = format_telegram_message(opportunities)
        
        if not message:
            logger.info("Empty digest - not sending")
            return
        
        # Write to outbox with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        outbox_file = OUTBOX_DIR / f'digest_{timestamp}.txt'
        
        with open(outbox_file, 'w') as f:
            f.write(message)
        
        # Also write to "latest" symlink for easy access
        latest_link = OUTBOX_DIR / 'digest_latest.txt'
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(outbox_file.name)
        
        logger.info(f"✅ Digest queued: {outbox_file}")
        print(f"✅ Digest queued for OpenClaw: {outbox_file}")
        print(f"   OpenClaw will send to Telegram on next check")
        
        logger.info("=" * 60)
        
        job['items_processed'] = len(opportunities)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Digest queue failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
