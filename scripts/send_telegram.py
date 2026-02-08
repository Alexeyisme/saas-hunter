#!/usr/bin/env python3
"""
Send Telegram Digest - Prepare digest for manual sending
Writes digest to file for you to review/send
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from usage_tracker import UsageTracker
from utils import setup_logging

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'telegram.log')

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
TELEGRAM_DIR = DATA_DIR / 'telegram_queue'
TELEGRAM_DIR.mkdir(parents=True, exist_ok=True)

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
        return "🤷 No opportunities found today."
    
    # Sort by score
    sorted_opps = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)
    
    # Get top 3
    top_3 = sorted_opps[:3]
    
    # Build message
    date_str = datetime.now().strftime('%b %d, %Y')
    msg = f"🎯 **SaaS Opportunities — {date_str}**\n\n"
    
    for i, opp in enumerate(top_3, 1):
        title = opp['title']
        score = opp['score']
        source = opp['source']
        url = opp['url']
        
        # Pain point emoji
        emoji = "⭐️" if score >= 60 else "💡"
        
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
    high_quality = len([o for o in opportunities if o.get('score', 0) >= 60])
    
    msg += f"📊 {total} collected | {high_quality} high quality (60+)\n\n"
    
    # View full digest hint
    msg += "_Full digest: ~/saas-hunter/data/digests/_"
    
    return msg

def main():
    """Generate and save Telegram digest"""
    tracker = UsageTracker()
    
    with tracker.track_job('delivery', 'send_telegram') as job:
        logger.info("=" * 60)
        logger.info("Preparing Telegram Digest")
        logger.info("=" * 60)
        
        # Load opportunities
        opportunities = load_today_opportunities()
        logger.info(f"Loaded {len(opportunities)} opportunities")
        
        # Format message
        message = format_telegram_message(opportunities)
        
        # Save to file
        today = datetime.now().strftime('%Y%m%d')
        output_file = TELEGRAM_DIR / f'digest_{today}.txt'
        
        with open(output_file, 'w') as f:
            f.write(message)
        
        logger.info(f"Digest saved to {output_file}")
        logger.info("=" * 60)
        
        job['items_processed'] = len(opportunities)
        
        # Print message so it appears in output
        print("✅ Telegram digest prepared")
        print(f"   Saved to: {output_file}")
        print()
        print("=" * 60)
        print(message)
        print("=" * 60)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Digest preparation failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
