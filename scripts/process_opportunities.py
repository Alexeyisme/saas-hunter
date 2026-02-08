#!/usr/bin/env python3
"""
Process Opportunities - Score, deduplicate, and enrich
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from usage_tracker import UsageTracker
from utils import setup_logging

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'processing.log')

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Last run tracking
LAST_RUN_FILE = DATA_DIR / 'last_processing_run.txt'

def load_last_run_time():
    """Get timestamp of last processing run"""
    if LAST_RUN_FILE.exists():
        with open(LAST_RUN_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    return datetime.now() - timedelta(days=1)  # Process last 24h on first run

def save_last_run_time():
    """Save current timestamp"""
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

def find_new_files(since):
    """Find raw JSON files created since timestamp"""
    files = []
    for file in sorted(RAW_DIR.glob('*.json')):
        if datetime.fromtimestamp(file.stat().st_mtime) > since:
            files.append(file)
    return files

def score_opportunity(opp):
    """
    Score opportunity 0-100 based on multiple signals
    Pure Python - no LLM calls
    """
    score = 0
    text = (opp.get('title', '') + ' ' + opp.get('body', '')).lower()
    
    # 1. Source credibility (max 20 points)
    source = opp.get('source', '')
    if source.startswith('github:'):
        score += 20  # GitHub reactions = validated
    elif source == 'hackernews':
        score += 15  # Tech-savvy audience
    elif source.startswith('reddit:'):
        # Different subreddits have different signal
        if 'smallbusiness' in source or 'sysadmin' in source:
            score += 12  # High signal subreddits
        else:
            score += 8
    
    # 2. Engagement (max 25 points)
    engagement = opp.get('engagement_data', {})
    
    # GitHub reactions
    reactions = engagement.get('reactions', 0)
    score += min(reactions * 2, 15)
    
    # Comments (any source)
    comments = engagement.get('comments', 0)
    score += min(comments, 10)
    
    # HN score
    hn_score = engagement.get('score', 0)
    score += min(hn_score, 10)
    
    # 3. Pain point clarity (max 20 points)
    # Strong pain indicators
    pain_words = ['sick of', 'frustrated', 'hate', 'tired of']
    if any(p in text for p in pain_words):
        score += 10
    
    # Willingness to pay signals
    pay_words = ['would pay', 'expensive', 'pricing', 'cost', 'price']
    if any(p in text for p in pay_words):
        score += 10
    
    # 4. Specificity (max 15 points)
    body = opp.get('body', '')
    if len(body) > 300:
        score += 10
    elif len(body) > 150:
        score += 5
    
    # Contains numbers/metrics
    if any(char.isdigit() for char in body):
        score += 5
    
    # 5. Freshness (max 10 points)
    try:
        pub_date = datetime.fromisoformat(opp['published_utc'].replace('Z', '+00:00'))
        age_hours = (datetime.now(pub_date.tzinfo) - pub_date).total_seconds() / 3600
        
        if age_hours < 6:
            score += 10
        elif age_hours < 24:
            score += 7
        elif age_hours < 72:
            score += 4
    except:
        pass
    
    # 6. Niche fit (max 10 points)
    niche_words = ['b2b', 'saas', 'api', 'dev tool', 'developer', 'automation']
    if any(kw in text for kw in niche_words):
        score += 10
    
    return min(score, 100)

def deduplicate_opportunities(opps):
    """
    Deduplicate using fuzzy title matching
    Keep highest-scored version of duplicates
    """
    if not opps:
        return []
    
    unique = []
    seen_titles = []
    
    # Sort by score descending
    opps_sorted = sorted(opps, key=lambda x: x.get('score', 0), reverse=True)
    
    for opp in opps_sorted:
        title = opp.get('title', '').lower()
        
        # Check if similar to any seen title
        is_duplicate = False
        for seen in seen_titles:
            similarity = fuzz.ratio(title, seen)
            if similarity > 85:  # 85% similar = duplicate
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(opp)
            seen_titles.append(title)
    
    return unique

def classify_domain(opp):
    """Simple domain classification via keywords"""
    text = (opp.get('title', '') + ' ' + opp.get('body', '')).lower()
    
    # Domain keywords
    domains = {
        'productivity': ['productivity', 'task', 'todo', 'calendar', 'scheduling'],
        'communication': ['email', 'chat', 'messaging', 'slack', 'team'],
        'development': ['api', 'code', 'developer', 'devops', 'deployment'],
        'marketing': ['marketing', 'seo', 'analytics', 'campaign'],
        'finance': ['invoice', 'payment', 'billing', 'accounting', 'tax'],
        'automation': ['automation', 'workflow', 'zapier', 'integration'],
        'data': ['data', 'database', 'analytics', 'reporting'],
        'design': ['design', 'ui', 'ux', 'figma', 'prototype']
    }
    
    for domain, keywords in domains.items():
        if any(kw in text for kw in keywords):
            return domain
    
    return 'other'

def enrich_opportunity(opp):
    """Add computed fields"""
    # Generate unique ID
    timestamp = datetime.fromisoformat(opp['collected_at']).strftime('%Y%m%d%H%M%S')
    source_id = opp['source_id'].replace('/', '-')[:20]
    opp['opportunity_id'] = f"{timestamp}-{opp['source'].replace(':', '-')}-{source_id}"
    
    # Classify domain
    opp['domain'] = classify_domain(opp)
    
    # Add processing metadata
    opp['processed_at'] = datetime.now().isoformat()
    
    # Calculate age
    try:
        pub_date = datetime.fromisoformat(opp['published_utc'].replace('Z', '+00:00'))
        opp['age_hours'] = int((datetime.now(pub_date.tzinfo) - pub_date).total_seconds() / 3600)
    except:
        opp['age_hours'] = 0
    
    return opp

def main():
    """Main processing pipeline"""
    tracker = UsageTracker()
    
    with tracker.track_job('processing', 'process_opportunities') as job:
        logger.info("=" * 60)
        logger.info("Processing Opportunities")
        logger.info("=" * 60)
        
        # 1. Find new raw files
        last_run = load_last_run_time()
        logger.info(f"Processing files since: {last_run.isoformat()}")
        
        raw_files = find_new_files(last_run)
        logger.info(f"Found {len(raw_files)} new raw files")
        
        if not raw_files:
            logger.info("No new files to process")
            job['items_processed'] = 0
            return
        
        # 2. Load all opportunities
        all_opps = []
        for file in raw_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    opps = data.get('opportunities', [])
                    all_opps.extend(opps)
                    logger.info(f"Loaded {len(opps)} from {file.name}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        logger.info(f"Total opportunities loaded: {len(all_opps)}")
        
        # 3. Score each
        for opp in all_opps:
            opp['score'] = score_opportunity(opp)
        
        logger.info(f"Scored {len(all_opps)} opportunities")
        
        # 4. Deduplicate
        unique_opps = deduplicate_opportunities(all_opps)
        logger.info(f"After deduplication: {len(unique_opps)} unique ({len(all_opps) - len(unique_opps)} duplicates removed)")
        
        # 5. Enrich
        for opp in unique_opps:
            enrich_opportunity(opp)
        
        logger.info(f"Enriched {len(unique_opps)} opportunities")
        
        # 6. Save as JSONL (one per line)
        today = datetime.now().strftime('%Y%m%d')
        output = PROCESSED_DIR / f'opportunities_{today}.jsonl'
        
        with open(output, 'a') as f:
            for opp in unique_opps:
                f.write(json.dumps(opp) + '\n')
        
        logger.info(f"Saved to {output}")
        
        # 7. Update last run time
        save_last_run_time()
        
        # Log summary
        if unique_opps:
            top_score = max(o['score'] for o in unique_opps)
            avg_score = sum(o['score'] for o in unique_opps) / len(unique_opps)
            logger.info(f"Score range: {avg_score:.1f} avg, {top_score} max")
        
        logger.info("=" * 60)
        logger.info(f"Processing complete: {len(all_opps)} → {len(unique_opps)} unique")
        logger.info("=" * 60)
        
        job['items_processed'] = len(unique_opps)
        
        # Print summary
        print(f"Processed {len(all_opps)} opportunities → {len(unique_opps)} unique")
        print(f"Saved to: {output}")

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
