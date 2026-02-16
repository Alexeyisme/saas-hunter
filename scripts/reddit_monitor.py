#!/usr/bin/env python3
"""
Reddit RSS SaaS Opportunity Monitor
Uses free RSS feeds - NO API KEY NEEDED!
Handles basic rate limiting and user agent.
Outputs to a normalized JSON format.
"""
import feedparser
import json
import sys
import time
from datetime import datetime, timedelta
import requests

# Import centralized configuration and utilities
from config import (
    RAW_DIR, REDDIT_SUBREDDITS, REDDIT_PAIN_KEYWORDS, REDDIT_PROMO_INDICATORS,
    REQUEST_TIMEOUT, USER_AGENT, RETRY_DELAY, BODY_PREVIEW_LENGTH,
    COLLECTION_HOURS_BACK, LOG_DIR
)
from utils import (
    setup_logging, DuplicateDetector, clean_html,
    normalize_opportunity, validate_opportunity
)
from usage_tracker import UsageTracker

# Setup logging
logger = setup_logging(__name__, LOG_DIR / 'reddit_monitor.log')

def fetch_subreddit_rss(subreddit: str, hours_back: int, duplicate_detector: DuplicateDetector):
    """Fetch posts from a subreddit's RSS feed."""
    from config import API_PER_PAGE
    results = []
    rss_url = f'https://www.reddit.com/r/{subreddit}/new/.rss?limit={API_PER_PAGE}'
    
    try:
        logger.info(f"Fetching: {rss_url}")
        
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(rss_url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if not feed.entries:
            logger.warning(f"No entries found for r/{subreddit}")
            return results

        # Time filter
        time_filter = datetime.now() - timedelta(hours=hours_back)

        for entry in feed.entries:
            try:
                # Parse timestamp
                if 'published_parsed' in entry and entry.published_parsed:
                    pub_date_naive = datetime(*entry.published_parsed[:6])
                    # Assume pub_date is UTC if no timezone is specified by feedparser
                    pub_date_utc = pub_date_naive # feedparser often gives naive, assume UTC for simplicity
                else:
                    continue # Skip if no publish date

                # Skip old posts
                if pub_date_utc < time_filter:
                    continue

                # Get text content
                title = entry.title
                content_raw = entry.get('summary', '')
                content_clean = clean_html(content_raw)
                
                text = (title + " " + content_clean).lower()

                # Skip self-promotion / spam
                if any(promo in text for promo in REDDIT_PROMO_INDICATORS):
                    continue

                # Check for pain point keywords
                matched_keywords = [kw for kw in REDDIT_PAIN_KEYWORDS if kw in text]

                # Include if has keywords
                if matched_keywords:
                    # Extract post ID from link
                    post_id_str = entry.link.split('/')[-2] if '/' in entry.link else entry.id
                    
                    # Skip duplicates
                    if duplicate_detector.is_duplicate(f'reddit:{subreddit}', post_id_str):
                        logger.debug(f"Skipping duplicate: {post_id_str}")
                        continue

                    opportunity = {
                        'source_id': post_id_str,
                        'source': f'reddit:{subreddit}',
                        'title': title,
                        'body': content_clean[:BODY_PREVIEW_LENGTH],
                        'url': entry.link,
                        'author': entry.author if hasattr(entry, 'author') else 'unknown',
                        'published_utc': pub_date_utc.isoformat(),
                        'engagement_data': {'keywords': matched_keywords},
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    results.append(opportunity)
                    duplicate_detector.mark_seen(f'reddit:{subreddit}', post_id_str)
                    
            except Exception as e:
                logger.error(f"Error processing entry in r/{subreddit}: {e}")
                continue
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching r/{subreddit}: {e}. Retrying after {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching r/{subreddit}: {e}")
        return []

def main():
    """Main execution"""
    tracker = UsageTracker()
    
    with tracker.track_job('collection', 'reddit_monitor') as job:
        logger.info("=" * 60)
        logger.info("Reddit RSS SaaS Hunter")
        logger.info("=" * 60)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Method: RSS feeds (no API needed)")
        logger.info(f"Looking back: {COLLECTION_HOURS_BACK} hours")
        logger.info("")

        duplicate_detector = DuplicateDetector()
        all_results = []

        for sub in REDDIT_SUBREDDITS:
            logger.info(f"Scanning r/{sub}...")
            results = fetch_subreddit_rss(sub, hours_back=COLLECTION_HOURS_BACK, duplicate_detector=duplicate_detector)
            all_results.extend(results)
            logger.info(f" ✓ Found {len(results)} new opportunities (duplicates filtered)")

        # Save seen IDs
        duplicate_detector.save()

        # Save results as JSONL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = RAW_DIR / f'reddit_{timestamp}.jsonl'

        # Normalize opportunities
        normalized_opportunities = [normalize_opportunity(item) for item in all_results]

        # Write as JSONL: metadata first, then one opportunity per line
        with open(output_file, 'w') as f:
            # First line: metadata
            metadata = {
                '_metadata': True,
                'scan_time': datetime.now().isoformat(),
                'total_opportunities': len(normalized_opportunities),
                'sources_scanned': REDDIT_SUBREDDITS,
                'method': 'RSS (no API)',
                'hours_back': COLLECTION_HOURS_BACK
            }
            f.write(json.dumps(metadata) + '\n')

            # Subsequent lines: individual opportunities
            for opp in normalized_opportunities:
                f.write(json.dumps(opp) + '\n')

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Summary:")
        logger.info(f" Total new opportunities: {len(all_results)}")
        logger.info(f" Total seen IDs tracked: {len(duplicate_detector.seen_ids)}")
        logger.info(f" Saved to: {output_file}")
        logger.info("=" * 60)

        job['items_processed'] = len(all_results)

    return str(output_file)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"CRITICAL ERROR in reddit_monitor: {e}")
        logger.error(f"Traceback:", exc_info=True)
        print(f"ERROR: {e}", file=sys.stderr)
        
        # Alert via stderr (cron will capture)
        print(f"ALERT: Reddit monitor failed: {e}", file=sys.stderr)
        sys.exit(1)
