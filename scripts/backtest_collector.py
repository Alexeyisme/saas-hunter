#!/usr/bin/env python3
"""
Backtest Historical Data Collection
Collects historical data from HackerNews and GitHub for a specified date range.
"""
import requests
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Import centralized configuration and utilities
from config import (
    RAW_DIR, HN_ASK_KEYWORDS, HN_PROMO_INDICATORS, HN_COMMENT_THRESHOLD,
    REQUEST_TIMEOUT, RETRY_DELAY, BODY_PREVIEW_LENGTH, LOG_DIR,
    HN_ALGOLIA_API_URL, API_PER_PAGE, GITHUB_TOKEN, GITHUB_REPOSITORIES,
    GITHUB_FEATURE_LABELS, GITHUB_REACTION_THRESHOLD, USER_AGENT
)
from utils import (
    setup_logging, DuplicateDetector, normalize_opportunity, clean_html
)
from usage_tracker import UsageTracker

# Setup logging
logger = setup_logging(__name__, LOG_DIR / 'backtest.log')

def fetch_hn_date_range(start_date: datetime, end_date: datetime, duplicate_detector: DuplicateDetector):
    """Fetch Ask HN stories for a specific date range."""
    results = []

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    logger.info(f"Fetching HN from {start_date.date()} to {end_date.date()}...")

    # Query parameters for date range
    query_params = {
        'tags': 'ask_hn',
        'numericFilters': f'created_at_i>{start_timestamp},created_at_i<{end_timestamp}',
        'hitsPerPage': API_PER_PAGE
    }

    try:
        response = requests.get(HN_ALGOLIA_API_URL, params=query_params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if 'hits' not in data:
            logger.warning("'hits' not found in Algolia response")
            return results

        for hit in data.get('hits', []):
            title = hit.get('title', '')
            story_text = hit.get('story_text', '')
            combined_text = (title + ' ' + story_text).lower()

            # Skip self-promotion
            if any(promo in combined_text for promo in HN_PROMO_INDICATORS):
                continue

            # Check for keywords
            matched_keywords = [kw for kw in HN_ASK_KEYWORDS if kw in combined_text]

            # Include if has keywords or high engagement
            if matched_keywords or hit.get('num_comments', 0) > HN_COMMENT_THRESHOLD:
                story_id = str(hit['objectID'])

                # Skip duplicates
                if duplicate_detector.is_duplicate('hackernews', story_id):
                    continue

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

        logger.info(f"  ✓ Found {len(results)} HN opportunities")
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching HN: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching HN: {e}")
        return []


def fetch_github_date_range(start_date: datetime, end_date: datetime, duplicate_detector: DuplicateDetector):
    """Fetch GitHub issues for a specific date range."""
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not set, skipping GitHub")
        return []

    results = []
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': USER_AGENT
    }

    # Format dates for GitHub API
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    logger.info(f"Fetching GitHub from {start_str} to {end_str}...")

    for repo in GITHUB_REPOSITORIES:
        try:
            # Build search query with date range using reactions as proxy for feature requests
            query = f'repo:{repo} is:issue created:{start_str}..{end_str} reactions:>{GITHUB_REACTION_THRESHOLD}'

            params = {
                'q': query,
                'sort': 'created',
                'order': 'desc',
                'per_page': API_PER_PAGE
            }

            logger.info(f"  Searching {repo}...")
            response = requests.get(
                'https://api.github.com/search/issues',
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Check rate limit
            remaining = response.headers.get('X-RateLimit-Remaining', '?')
            logger.info(f"    Rate limit remaining: {remaining}")

            for issue in data.get('items', []):
                issue_id = str(issue['number'])

                # Skip duplicates
                if duplicate_detector.is_duplicate(f'github:{repo}', issue_id):
                    continue

                results.append({
                    'source_id': issue_id,
                    'source': f'github:{repo}',
                    'title': issue['title'],
                    'body': (issue.get('body') or '')[:BODY_PREVIEW_LENGTH],
                    'url': issue['html_url'],
                    'author': issue['user']['login'],
                    'published_utc': issue['created_at'],
                    'engagement_data': {
                        'comments': issue.get('comments', 0),
                        'reactions': issue.get('reactions', {}).get('total_count', 0)
                    },
                    'collected_at': datetime.now().isoformat()
                })
                duplicate_detector.mark_seen(f'github:{repo}', issue_id)

            # Rate limiting - wait between repos
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {repo}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error with {repo}: {e}")
            continue

    logger.info(f"  ✓ Found {len(results)} GitHub opportunities")
    return results


def backtest(start_date: datetime, end_date: datetime, chunk_days: int = 7):
    """
    Run backtesting for a date range.
    Splits range into chunks to avoid API limits.
    """
    tracker = UsageTracker()

    with tracker.track_job('collection', 'backtest') as job:
        logger.info("=" * 60)
        logger.info("BACKTESTING - Historical Data Collection")
        logger.info("=" * 60)
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Chunk size: {chunk_days} days")
        logger.info("")

        duplicate_detector = DuplicateDetector()
        all_hn_results = []
        all_github_results = []

        # Split date range into chunks
        current_start = start_date
        chunk_count = 0

        while current_start < end_date:
            chunk_count += 1
            current_end = min(current_start + timedelta(days=chunk_days), end_date)

            logger.info(f"Chunk {chunk_count}: {current_start.date()} to {current_end.date()}")

            # Fetch HackerNews
            hn_results = fetch_hn_date_range(current_start, current_end, duplicate_detector)
            all_hn_results.extend(hn_results)

            # Fetch GitHub
            github_results = fetch_github_date_range(current_start, current_end, duplicate_detector)
            all_github_results.extend(github_results)

            logger.info("")

            # Move to next chunk
            current_start = current_end

            # Rate limiting between chunks
            if current_start < end_date:
                time.sleep(2)

        # Save seen IDs
        duplicate_detector.save()

        # Save HackerNews results
        if all_hn_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = RAW_DIR / f'hackernews_backtest_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.jsonl'

            normalized_opportunities = [normalize_opportunity(item) for item in all_hn_results]

            with open(output_file, 'w') as f:
                # Metadata
                metadata = {
                    '_metadata': True,
                    'scan_time': datetime.now().isoformat(),
                    'total_opportunities': len(normalized_opportunities),
                    'method': 'Backtest - HackerNews Algolia',
                    'date_range': f"{start_date.date()} to {end_date.date()}"
                }
                f.write(json.dumps(metadata) + '\n')

                # Opportunities
                for opp in normalized_opportunities:
                    f.write(json.dumps(opp) + '\n')

            logger.info(f"HackerNews saved to: {output_file}")

        # Save GitHub results
        if all_github_results:
            output_file = RAW_DIR / f'github_backtest_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.jsonl'

            normalized_opportunities = [normalize_opportunity(item) for item in all_github_results]

            with open(output_file, 'w') as f:
                # Metadata
                metadata = {
                    '_metadata': True,
                    'scan_time': datetime.now().isoformat(),
                    'total_opportunities': len(normalized_opportunities),
                    'method': 'Backtest - GitHub Search API',
                    'date_range': f"{start_date.date()} to {end_date.date()}"
                }
                f.write(json.dumps(metadata) + '\n')

                # Opportunities
                for opp in normalized_opportunities:
                    f.write(json.dumps(opp) + '\n')

            logger.info(f"GitHub saved to: {output_file}")

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("BACKTEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"HackerNews opportunities: {len(all_hn_results)}")
        logger.info(f"GitHub opportunities: {len(all_github_results)}")
        logger.info(f"Total opportunities: {len(all_hn_results) + len(all_github_results)}")
        logger.info(f"Total seen IDs tracked: {len(duplicate_detector.seen_ids)}")
        logger.info("=" * 60)

        job['items_processed'] = len(all_hn_results) + len(all_github_results)

        print(f"\n✅ Backtest complete!")
        print(f"   HackerNews: {len(all_hn_results)} opportunities")
        print(f"   GitHub: {len(all_github_results)} opportunities")
        print(f"   Total: {len(all_hn_results) + len(all_github_results)} opportunities")
        print(f"\n   Next: Run process_opportunities.py to score and analyze")


if __name__ == '__main__':
    try:
        # Default: last 2 weeks (Feb 1-15, 2026)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)

        # Allow command line override
        if len(sys.argv) > 1:
            start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        if len(sys.argv) > 2:
            end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')

        backtest(start_date, end_date, chunk_days=7)
        sys.exit(0)
    except Exception as e:
        logger.error(f"CRITICAL: Backtest failed: {e}", exc_info=True)
        print(f"ALERT: Backtest failed: {e}", file=sys.stderr)
        sys.exit(1)
