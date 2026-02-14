#!/usr/bin/env python3
"""
GitHub Issues SaaS Opportunity Monitor
Finds feature requests and high-engagement issues in popular repositories.
Uses GitHub API with authentication for better rate limits.
Outputs to a normalized JSON format.
"""
import requests
import json
import sys
import time
from datetime import datetime, timedelta

# Import centralized configuration and utilities
from config import (
    RAW_DIR, GITHUB_TOKEN, GITHUB_REPOSITORIES, GITHUB_FEATURE_LABELS,
    REQUEST_TIMEOUT, API_CALL_DELAY, RETRY_DELAY, API_PER_PAGE,
    BODY_PREVIEW_LENGTH, GITHUB_HOURS_BACK, USER_AGENT, LOG_DIR
)
from utils import (
    setup_logging, DuplicateDetector, normalize_opportunity,
    calculate_engagement_score
)
from usage_tracker import UsageTracker

# Setup logging
logger = setup_logging(__name__, LOG_DIR / 'github_monitor.log')

# Rate limiting
RATE_LIMIT_WARNING_THRESHOLD = 10

def fetch_github_search_issues(hours_back: int, duplicate_detector: DuplicateDetector):
    """Fetch issues/PRs from GitHub Search API matching query."""
    results = []
    
    since_date = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
    search_api_url = 'https://api.github.com/search/issues'
    
    headers = {
        'Accept': 'application/vnd.github.v3.text-match+json',
        'User-Agent': USER_AGENT
    }
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'

    for repo in GITHUB_REPOSITORIES:
        logger.info(f"Searching {repo}...")
        
        # Use reactions as a proxy for feature requests people care about
        # Bugs get comments, features get 👍 reactions
        # Reaction threshold of 2 filters out noise while catching popular requests
        search_query = f"is:open is:issue created:>{since_date} repo:{repo} reactions:>2"

        params = {
            'q': search_query,
            'sort': 'created', # Sort by creation date
            'order': 'desc',
            'per_page': API_PER_PAGE
        }
        
        page = 1
        while True:
            logger.info(f"  Fetching page {page} for {repo}...")
            try:
                response = requests.get(search_api_url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
                
                # Check rate limit
                remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                logger.info(f"    Rate limit remaining: {remaining}")
                if remaining < RATE_LIMIT_WARNING_THRESHOLD:
                    logger.warning(f"Approaching GitHub API rate limit. Remaining: {remaining}")

                response.raise_for_status()
                data = response.json()

                if 'items' not in data:
                    logger.error("'items' not found in GitHub API response.")
                    break

                issues = data['items']
                if not issues:
                    break # No more issues for this repo/query

                for issue in issues:
                    # Filter out pull requests, though search query should exclude them if 'is:issue' is used.
                    if issue.get('pull_request'): 
                        continue
                    
                    # Basic filtering for engagement - if it passes search criteria, it's likely relevant.
                    # We can add more filters here if needed (e.g., minimum reactions)
                    
                    # Normalize labels for consistency
                    issue_labels = [label['name'].lower() for label in issue.get('labels', [])]
                    
                    is_feature_request = any(fl in issue_labels for fl in GITHUB_FEATURE_LABELS)
                    
                    # Extract repo name from repository_url (search API doesn't include repository object)
                    if 'repository' in issue:
                        repo_name = issue['repository']['full_name']
                    else:
                        # Parse from repository_url: https://api.github.com/repos/owner/repo
                        repo_url = issue.get('repository_url', '')
                        repo_name = '/'.join(repo_url.split('/')[-2:]) if repo_url else repo
                    
                    issue_id = str(issue['number'])
                    
                    # Skip duplicates
                    if duplicate_detector.is_duplicate(f'github:{repo_name}', issue_id):
                        logger.debug(f"Skipping duplicate: {repo_name}#{issue_id}")
                        continue

                    results.append({
                        'source_id': issue_id,
                        'source': f'github:{repo_name}',
                        'title': issue['title'],
                        'body': (issue.get('body') or '')[:BODY_PREVIEW_LENGTH],
                        'url': issue['html_url'],
                        'author': issue['user']['login'],
                        'published_utc': issue['created_at'],
                        'engagement_data': {
                            'comments': issue.get('comments', 0),
                            'reactions': issue.get('reactions', {}).get('total_count', 0)
                        },
                        'labels': issue_labels,
                        'is_feature_request': is_feature_request,
                        'collected_at': datetime.now().isoformat()
                    })
                    duplicate_detector.mark_seen(f'github:{repo_name}', issue_id)
                
                # Pagination
                if len(issues) < API_PER_PAGE:
                    break
                
                page += 1
                params['page'] = page # Update page for next request
                time.sleep(API_CALL_DELAY)

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error fetching GitHub issues for {repo}: {e}. Retrying after {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                break
            except Exception as e:
                logger.error(f"Unexpected error processing GitHub issues for {repo}: {e}")
                break
        
        # Delay between repos to avoid rate limiting (30 req/min = 2 sec/req)
        # Adding 3 seconds to be safe
        time.sleep(3)
                
    return results

def main():
    """Main execution"""
    tracker = UsageTracker()
    
    with tracker.track_job('collection', 'github_monitor') as job:
        logger.info("=" * 60)
        logger.info("GitHub Issues SaaS Hunter")
        logger.info("=" * 60)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Looking back: {GITHUB_HOURS_BACK} hours")
        logger.info("")

        duplicate_detector = DuplicateDetector()
        all_results = []
    
    # Fetch issues using our combined search query
    logger.info("Scanning GitHub for feature requests...")
    issues = fetch_github_search_issues(hours_back=GITHUB_HOURS_BACK, duplicate_detector=duplicate_detector)
    all_results.extend(issues)
    logger.info(f" ✓ Found {len(issues)} new opportunities (duplicates filtered)")
    
    # Save seen IDs
    duplicate_detector.save()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RAW_DIR / f'github_{timestamp}.json'
    
    normalized_opportunities = [normalize_opportunity(item) for item in all_results]

    output_data = {
        'scan_time': datetime.now().isoformat(),
        'total_opportunities': len(normalized_opportunities),
        'sources_scanned': GITHUB_REPOSITORIES,
        'method': 'GitHub Search API',
        'hours_back': GITHUB_HOURS_BACK,
        'opportunities': normalized_opportunities
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
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
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN is not set. Please create a .env file with your token.")
        sys.exit(1)
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"CRITICAL: GitHub monitor failed: {e}", exc_info=True)
        print(f"ALERT: GitHub monitor failed: {e}", file=sys.stderr)
        sys.exit(1)
