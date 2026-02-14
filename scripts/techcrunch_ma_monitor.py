#!/usr/bin/env python3
"""
TechCrunch M&A Monitor - Track acquisition announcements
Phase 1: RSS feed scraping and basic extraction
"""
import feedparser
import json
import sys
from pathlib import Path
from datetime import datetime
from utils import setup_logging

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'ma_monitor.log')

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
MA_DIR = DATA_DIR / 'ma_acquisitions'
MA_DIR.mkdir(parents=True, exist_ok=True)

# RSS Feed
TECHCRUNCH_RSS = "https://techcrunch.com/feed/"

# M&A keywords to filter
MA_KEYWORDS = [
    'acqui', 'acquisition', 'acquired', 'acquires',
    'merger', 'merges', 'merge',
    'bought', 'buys', 'purchase',
    'snaps up', 'picks up',
    'takes over', 'takeover'
]

# Keywords to EXCLUDE (false positives)
EXCLUDE_KEYWORDS = [
    'exits from',  # Employee departures
    'steps down',
    'resigns',
    'quits'
]

def is_ma_article(title, description):
    """Check if article is about M&A"""
    text = (title + ' ' + description).lower()
    
    # Check for exclude keywords first
    if any(exclude in text for exclude in EXCLUDE_KEYWORDS):
        return False
    
    # Then check for M&A keywords
    return any(keyword in text for keyword in MA_KEYWORDS)

def extract_ma_signals(entry):
    """Extract structured M&A data from article"""
    return {
        'id': entry.get('id', ''),
        'title': entry.get('title', ''),
        'link': entry.get('link', ''),
        'published': entry.get('published', ''),
        'published_parsed': entry.get('published_parsed'),
        'description': entry.get('description', ''),
        'categories': [tag.get('term', '') for tag in entry.get('tags', [])],
        'author': entry.get('author', ''),
        'source': 'techcrunch',
        'collected_at': datetime.now().isoformat()
    }

def analyze_ma_article(article):
    """Analyze M&A article for opportunity signals"""
    title = article['title'].lower()
    desc = article['description'].lower()
    text = title + ' ' + desc
    
    signals = {
        'acquisition_type': None,
        'industry': None,
        'deal_size_mentioned': False,
        'strategic_rationale': None
    }
    
    # Detect acquisition type
    if 'acqui-hire' in text or 'talent' in text:
        signals['acquisition_type'] = 'acqui-hire'
    elif 'strategic' in text:
        signals['acquisition_type'] = 'strategic'
    elif 'competitive' in text or 'competitor' in text:
        signals['acquisition_type'] = 'competitive'
    
    # Detect if deal size mentioned
    if '$' in text or 'million' in text or 'billion' in text:
        signals['deal_size_mentioned'] = True
    
    # Detect industry from categories
    categories = article.get('categories', [])
    if categories:
        signals['industry'] = categories[0] if categories else 'unknown'
    
    # Look for rationale keywords
    rationale_keywords = ['expand', 'strengthen', 'fill', 'add', 'grow', 'enter']
    for keyword in rationale_keywords:
        if keyword in text:
            signals['strategic_rationale'] = keyword
            break
    
    return signals

def fetch_ma_articles(hours_back=24):
    """Fetch M&A articles from TechCrunch RSS"""
    logger.info(f"Fetching TechCrunch RSS feed: {TECHCRUNCH_RSS}")
    
    try:
        feed = feedparser.parse(TECHCRUNCH_RSS)
        
        if feed.bozo:
            logger.warning(f"Feed parsing issue: {feed.bozo_exception}")
        
        logger.info(f"Fetched {len(feed.entries)} total articles")
        
        # Filter for M&A articles
        ma_articles = []
        for entry in feed.entries:
            if is_ma_article(entry.get('title', ''), entry.get('description', '')):
                article = extract_ma_signals(entry)
                article['signals'] = analyze_ma_article(article)
                ma_articles.append(article)
        
        logger.info(f"Found {len(ma_articles)} M&A articles")
        return ma_articles
        
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {e}")
        return []

def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("TechCrunch M&A Monitor")
    logger.info("=" * 60)
    
    # Fetch articles
    articles = fetch_ma_articles()
    
    if not articles:
        logger.info("No M&A articles found")
        print("No M&A articles found in recent feed")
        return
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = MA_DIR / f'techcrunch_ma_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump({
            'source': 'techcrunch',
            'collected_at': timestamp,
            'count': len(articles),
            'articles': articles
        }, f, indent=2)
    
    logger.info(f"Saved {len(articles)} articles to {output_file}")
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"TechCrunch M&A Monitor - {len(articles)} articles found")
    print(f"{'='*70}\n")
    
    for i, article in enumerate(articles[:10], 1):  # Show top 10
        print(f"{i}. {article['title']}")
        print(f"   Published: {article['published']}")
        print(f"   Categories: {', '.join(article['categories'])}")
        
        signals = article['signals']
        if signals['acquisition_type']:
            print(f"   Type: {signals['acquisition_type']}")
        if signals['deal_size_mentioned']:
            print(f"   💰 Deal size mentioned")
        if signals['strategic_rationale']:
            print(f"   Rationale: {signals['strategic_rationale']}")
        
        print(f"   Link: {article['link']}\n")
    
    if len(articles) > 10:
        print(f"... and {len(articles) - 10} more")
    
    print(f"\nSaved to: {output_file}")
    logger.info("=" * 60)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
