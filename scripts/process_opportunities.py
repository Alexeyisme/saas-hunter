#!/usr/bin/env python3
"""
Process Opportunities - Score, deduplicate, and enrich
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from usage_tracker import UsageTracker
from utils import setup_logging

# Load environment variables first
ENV_FILE = Path(__file__).parent.parent / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
SCRIPTS_ENV = Path(__file__).parent / '.env'
if SCRIPTS_ENV.exists():
    load_dotenv(SCRIPTS_ENV)

# Setup logging first (needed for LLM check below)
LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'processing.log')

# Use config-driven scoring
try:
    from scoring import score_opportunity
    from validate import validate_opportunities
    SCORING_IMPORTED = True
except ImportError:
    SCORING_IMPORTED = False
    logger.error("Failed to import scoring.py - using fallback")
    validate_opportunities = None

# Check if LLM scoring is enabled (skip placeholder keys)
api_key = os.getenv('OPENROUTER_API_KEY', '')
LLM_ENABLED = api_key and api_key not in ['your_openrouter_key_here', '', 'your_api_key_here']

if LLM_ENABLED:
    try:
        from llm_scorer import enhanced_score
        logger.info("LLM scoring enabled with OpenRouter (Claude Haiku)")
    except ImportError:
        logger.warning("LLM scorer module not found, falling back to rule-based")
        LLM_ENABLED = False
else:
    logger.info("Rule-based scoring only (LLM disabled - set OPENROUTER_API_KEY to enable)")

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
    """Find raw JSONL files created since timestamp"""
    files = []
    for file in sorted(RAW_DIR.glob('*.jsonl')):
        if datetime.fromtimestamp(file.stat().st_mtime) > since:
            files.append(file)
    return files

def deduplicate_opportunities(opps):
    """
    Deduplicate using fuzzy title matching
    Keep highest-scored version of duplicates
    """
    from config import FUZZY_MATCH_THRESHOLD

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
            if similarity > FUZZY_MATCH_THRESHOLD:
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
        
        # 2. Load all opportunities from JSONL files
        all_opps = []
        for file in raw_files:
            try:
                opps = []
                with open(file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            data = json.loads(line.strip())
                            # Skip metadata line
                            if data.get('_metadata'):
                                continue
                            opps.append(data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse line {line_num} in {file.name}: {e}")
                all_opps.extend(opps)
                logger.info(f"Loaded {len(opps)} from {file.name}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        logger.info(f"Total opportunities loaded: {len(all_opps)}")
        
        # 2.5. Validate data
        if validate_opportunities:
            valid_opps, errors = validate_opportunities(all_opps)
            if errors:
                logger.warning(f"Validation errors: {len(errors)} invalid opportunities")
                for err in errors[:5]:  # Log first 5 errors
                    logger.warning(f"  {err['error']}: {err['title']}")
            all_opps = valid_opps
            logger.info(f"After validation: {len(all_opps)} valid opportunities")
        
        # 3. Score each
        llm_enhanced_count = 0
        total_llm_cost = 0.0
        total_tokens = 0

        for opp in all_opps:
            base_score = score_opportunity(opp)

            # Apply LLM enhancement if enabled and score is promising
            if LLM_ENABLED and base_score >= 45:
                try:
                    final_score, llm_data = enhanced_score(base_score, opp)
                    opp['score'] = final_score
                    if llm_data:
                        opp['llm_analysis'] = llm_data
                        llm_enhanced_count += 1
                        total_llm_cost += llm_data.get('cost_usd', 0)
                        total_tokens += llm_data.get('tokens', {}).get('total_tokens', 0)
                except Exception as e:
                    # LLM failed, use base score
                    logger.debug(f"LLM enhancement skipped for opportunity (using base score): {str(e)[:100]}")
                    opp['score'] = base_score
            else:
                opp['score'] = base_score

        logger.info(f"Scored {len(all_opps)} opportunities ({llm_enhanced_count} LLM-enhanced)")
        if llm_enhanced_count > 0:
            logger.info(f"LLM cost: ${total_llm_cost:.6f}, tokens: {total_tokens}")
            job['cost_usd'] = total_llm_cost
            job['input_tokens'] = total_tokens  # Approximate
            job['output_tokens'] = 0
        
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
        logger.error(f"CRITICAL: Processing failed: {e}", exc_info=True)
        print(f"ALERT: Processing failed: {e}", file=sys.stderr)
        sys.exit(1)
