#!/usr/bin/env python3
"""
Generate Daily Digest - Create markdown summary of top opportunities
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from usage_tracker import UsageTracker
from utils import setup_logging

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'digest.log')

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
DIGEST_DIR = DATA_DIR / 'digests'
DIGEST_DIR.mkdir(parents=True, exist_ok=True)

def load_recent_opportunities(hours=24):
    """Load processed opportunities from last N hours"""
    cutoff = datetime.now() - timedelta(hours=hours)
    opportunities = []
    
    # Load from today's JSONL file
    today = datetime.now().strftime('%Y%m%d')
    jsonl_file = PROCESSED_DIR / f'opportunities_{today}.jsonl'
    
    if not jsonl_file.exists():
        return []
    
    with open(jsonl_file, 'r') as f:
        for line in f:
            opp = json.loads(line)
            # Check if processed recently
            processed_at = datetime.fromisoformat(opp['processed_at'])
            if processed_at > cutoff:
                opportunities.append(opp)
    
    # Also check yesterday's file if we're early in the day
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    yesterday_file = PROCESSED_DIR / f'opportunities_{yesterday}.jsonl'
    
    if yesterday_file.exists():
        with open(yesterday_file, 'r') as f:
            for line in f:
                opp = json.loads(line)
                processed_at = datetime.fromisoformat(opp['processed_at'])
                if processed_at > cutoff:
                    opportunities.append(opp)
    
    return opportunities

def format_opportunity(opp, rank):
    """Format single opportunity for digest"""
    title = opp['title']
    score = opp['score']
    source = opp['source']
    url = opp['url']
    domain = opp.get('domain', 'other')
    
    # Extract key pain points from body
    body = opp.get('body', '')[:200]
    
    # Engagement info
    engagement = opp.get('engagement_data', {})
    engagement_str = []
    if engagement.get('reactions'):
        engagement_str.append(f"{engagement['reactions']} reactions")
    if engagement.get('comments'):
        engagement_str.append(f"{engagement['comments']} comments")
    if engagement.get('score'):
        engagement_str.append(f"{engagement['score']} points")
    
    engagement_display = ", ".join(engagement_str) if engagement_str else "New"
    
    # Build markdown
    md = f"### {rank}. {title} (Score: {score})\n"
    md += f"**Source:** {source} | **Domain:** {domain}\n"
    md += f"**Engagement:** {engagement_display}\n"  
    md += f"**Link:** {url}\n\n"
    
    if body:
        md += f"**Preview:** {body}...\n\n"
    
    return md

def analyze_trends(opportunities):
    """Analyze trends across opportunities"""
    # Group by domain
    by_domain = defaultdict(list)
    for opp in opportunities:
        by_domain[opp.get('domain', 'other')].append(opp)
    
    # Common keywords
    keywords = defaultdict(int)
    pain_indicators = ['sick of', 'frustrated', 'tired of', 'hate', 'alternative']
    
    for opp in opportunities:
        text = (opp.get('title', '') + ' ' + opp.get('body', '')).lower()
        for keyword in pain_indicators:
            if keyword in text:
                keywords[keyword] += 1
    
    return {
        'domains': dict(by_domain),
        'keywords': dict(keywords)
    }

def generate_digest(opportunities):
    """Generate markdown digest"""
    if not opportunities:
        return None
    
    # Sort by score
    sorted_opps = sorted(opportunities, key=lambda x: x.get('score', 0), reverse=True)
    
    # Date
    date_str = datetime.now().strftime('%B %d, %Y')
    
    # Start digest
    md = f"# SaaS Opportunities — {date_str}\n\n"
    md += f"**Summary:** {len(opportunities)} opportunities collected and processed\n\n"
    md += "---\n\n"
    
    # Top tier (80+)
    top_tier = [o for o in sorted_opps if o.get('score', 0) >= 80]
    if top_tier:
        md += "## 🔥 Top Opportunities (Score 80+)\n\n"
        for i, opp in enumerate(top_tier[:5], 1):
            md += format_opportunity(opp, i)
        md += "---\n\n"
    
    # High potential (60-79)
    high_potential = [o for o in sorted_opps if 60 <= o.get('score', 0) < 80]
    if high_potential:
        md += "## ⭐ High Potential (Score 60-79)\n\n"
        for i, opp in enumerate(high_potential[:5], 1):
            md += format_opportunity(opp, i)
        md += "---\n\n"
    
    # Worth exploring (40-59)
    worth_exploring = [o for o in sorted_opps if 40 <= o.get('score', 0) < 60]
    if worth_exploring:
        md += "## 💡 Worth Exploring (Score 40-59)\n\n"
        # Just titles for this tier
        for opp in worth_exploring[:10]:
            title = opp['title']
            score = opp['score']
            source = opp['source']
            md += f"- **{title}** ({score} pts) — {source}\n"
        md += "\n---\n\n"
    
    # Trends
    trends = analyze_trends(opportunities)
    
    md += "## 📊 Trends\n\n"
    
    # Domain breakdown
    if trends['domains']:
        md += "**By Domain:**\n"
        for domain, opps in sorted(trends['domains'].items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            md += f"- {domain.capitalize()}: {len(opps)} opportunities\n"
        md += "\n"
    
    # Pain point keywords
    if trends['keywords']:
        md += "**Pain Point Indicators:**\n"
        for keyword, count in sorted(trends['keywords'].items(), key=lambda x: x[1], reverse=True):
            md += f"- '{keyword}': {count} mentions\n"
        md += "\n"
    
    # Footer
    md += "---\n\n"
    md += f"**Collected:** {len(opportunities)} total | "
    
    score_80_plus = len([o for o in opportunities if o.get('score', 0) >= 80])
    score_60_plus = len([o for o in opportunities if o.get('score', 0) >= 60])
    
    md += f"**High Quality:** {score_60_plus} (60+) | "
    md += f"**Top Tier:** {score_80_plus} (80+)\n\n"
    
    md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*\n"
    
    return md

def main():
    """Generate today's digest"""
    tracker = UsageTracker()
    
    with tracker.track_job('digest', 'generate_digest') as job:
        logger.info("=" * 60)
        logger.info("Generating Daily Digest")
        logger.info("=" * 60)
        
        # Load recent opportunities
        opportunities = load_recent_opportunities(hours=24)
        logger.info(f"Loaded {len(opportunities)} opportunities from last 24h")
        
        if not opportunities:
            logger.warning("No opportunities to digest")
            print("No opportunities found for digest")
            job['items_processed'] = 0
            return
        
        # Generate digest
        digest_md = generate_digest(opportunities)
        
        if not digest_md:
            logger.warning("Failed to generate digest")
            print("Failed to generate digest")
            job['items_processed'] = 0
            return
        
        # Save digest
        today = datetime.now().strftime('%Y%m%d')
        output = DIGEST_DIR / f'digest_{today}.md'
        
        with open(output, 'w') as f:
            f.write(digest_md)
        
        logger.info(f"Saved digest to {output}")
        logger.info(f"Digest contains {len(opportunities)} opportunities")
        
        # Log score distribution
        scores = [o.get('score', 0) for o in opportunities]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        
        logger.info(f"Score range: {avg_score:.1f} avg, {max_score} max")
        logger.info("=" * 60)
        
        job['items_processed'] = len(opportunities)
        
        # Print summary
        print(f"✅ Generated digest with {len(opportunities)} opportunities")
        print(f"   Saved to: {output}")
        print(f"   Score range: {avg_score:.1f} avg, {max_score} max")

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Digest generation failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
