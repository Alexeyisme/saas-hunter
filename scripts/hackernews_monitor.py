#!/usr/bin/env python3
"""
Hacker News SaaS Opportunity Monitor
Finds "Ask HN" threads about tools, solutions, and pain points.
Uses Algolia HN Search API for efficiency.
Outputs to a normalized JSON format.
"""
import requests
import json
import sys
from datetime import datetime, timedelta
import time

# Import centralized configuration and utilities
from config import (
    RAW_DIR, HN_ASK_KEYWORDS, HN_PROMO_INDICATORS, HN_COMMENT_THRESHOLD,
    REQUEST_TIMEOUT, RETRY_DELAY, BODY_PREVIEW_LENGTH, COLLECTION_HOURS_BACK, LOG_DIR,
    HN_ALGOLIA_API_URL, API_PER_PAGE
)
from utils import (
    setup_logging, DuplicateDetector, normalize_opportunity
)
from usage_tracker import UsageTracker

# Setup logging
logger = setup_logging(__name__, LOG_DIR / 'hackernews_monitor.log')

def fetch_hn_ask_hn_stories(hours_back: int, duplicate_detector: DuplicateDetector):
    """Fetch Ask HN stories from Algolia API."""
    results = []
    
    # Algolia HN Search parameters
    # We're looking for stories tagged as 'ask_hn'
    # Combine keywords into a query, and filter by date
    
    # Time filter calculation
    cutoff_timestamp = int((datetime.now() - timedelta(hours=hours_back)).timestamp())

    # Set up query parameters
    query_params = {
        'tags': 'ask_hn',  # Only get "Ask HN" posts
        'numericFilters': f'created_at_i>{cutoff_timestamp}',  # Time filter
        'hitsPerPage': API_PER_PAGE  # Get more results per page
    }
    
    # Don't use keyword filtering in the query - it's too restrictive
    # We'll filter by keywords locally after getting results

    logger.info(f"Fetching Ask HN stories...")
    
    try:
        response = requests.get(HN_ALGOLIA_API_URL, params=query_params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        
        if 'hits' not in data:
            logger.warning("'hits' not found in Algolia response.")
            return results

        # Filter and process hits
        for hit in data.get('hits', []):
            # Filter by time (though numericFilters in API should handle this)
            if hit.get('created_at_i', 0) < cutoff_timestamp:
                continue

            # tags='ask_hn' already ensures we only get Ask HN posts
            # No need for additional type filtering

            title = hit.get('title', '')
            story_text = hit.get('story_text', '')
            combined_text = (title + ' ' + story_text).lower()

            # Skip self-promotion posts
            if any(promo in combined_text for promo in HN_PROMO_INDICATORS):
                continue

            # Check for keywords
            matched_keywords = [kw for kw in HN_ASK_KEYWORDS if kw in combined_text]

            # Include if it has keywords or has significant engagement (high threshold)
            if matched_keywords or hit.get('num_comments', 0) > HN_COMMENT_THRESHOLD:
                story_id = str(hit['objectID'])
                
                # Skip duplicates
                if duplicate_detector.is_duplicate('hackernews', story_id):
                    logger.debug(f"Skipping duplicate: {story_id}")
                    continue
                
                # Extracting date from timestamp
                item_time_dt = datetime.fromtimestamp(hit.get('created_at_i', 0))
                
                results.append({
                    'source_id': story_id,
                    'source': 'hackernews',
                    'title': title,
                    'body': (story_text or '')[:BODY_PREVIEW_LENGTH],
                    'url': f"https://news.ycombinator.com/item?id={story_id}",
                    'author': hit.get('author', 'unknown'),
                    'published_utc': item_time_dt.isoformat(),
                    'engagement_data': {
                        'score': hit.get('points', 0),
                        'comments': hit.get('num_comments', 0)
                    },
                    'matched_keywords': matched_keywords,
                    'collected_at': datetime.now().isoformat()
                })
                duplicate_detector.mark_seen('hackernews', story_id)
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching HN Algolia: {e}. Retrying after {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching HN Algolia: {e}")
        return []

def main():
    """Main execution"""
    tracker = UsageTracker()
    
    with tracker.track_job('collection', 'hackernews_monitor') as job:
        logger.info("=" * 60)
        logger.info("Hacker News SaaS Hunter")
        logger.info("=" * 60)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Looking back: {COLLECTION_HOURS_BACK} hours")
        logger.info("")

        duplicate_detector = DuplicateDetector()

        logger.info("Scanning Ask HN stories via Algolia...")
        results = fetch_hn_ask_hn_stories(hours_back=COLLECTION_HOURS_BACK, duplicate_detector=duplicate_detector)
        logger.info(f" ✓ Found {len(results)} new opportunities (duplicates filtered)")

        # Save seen IDs
        duplicate_detector.save()

        # Save results as JSONL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = RAW_DIR / f'hackernews_{timestamp}.jsonl'

        normalized_opportunities = [normalize_opportunity(item) for item in results]

        # Write as JSONL: metadata first, then one opportunity per line
        with open(output_file, 'w') as f:
            # First line: metadata
            metadata = {
                '_metadata': True,
                'scan_time': datetime.now().isoformat(),
                'total_opportunities': len(normalized_opportunities),
                'method': 'Hacker News Algolia Search',
                'hours_back': COLLECTION_HOURS_BACK
            }
            f.write(json.dumps(metadata) + '\n')

            # Subsequent lines: individual opportunities
            for opp in normalized_opportunities:
                f.write(json.dumps(opp) + '\n')

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Summary:")
        logger.info(f" Total new opportunities: {len(results)}")
        logger.info(f" Total seen IDs tracked: {len(duplicate_detector.seen_ids)}")
        logger.info(f" Saved to: {output_file}")
        logger.info("=" * 60)

        job['items_processed'] = len(results)

    return str(output_file)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"CRITICAL: HackerNews monitor failed: {e}", exc_info=True)
        print(f"ALERT: HackerNews monitor failed: {e}", file=sys.stderr)
        sys.exit(1)
