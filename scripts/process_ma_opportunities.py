#!/usr/bin/env python3
"""
Process M&A Acquisitions into Opportunity Signals
Analyzes acquisitions to generate SaaS opportunity ideas
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from utils import setup_logging

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
logger = setup_logging(__name__, LOG_DIR / 'ma_processor.log')

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
MA_DIR = DATA_DIR / 'ma_acquisitions'
PROCESSED_DIR = DATA_DIR / 'processed'

def generate_opportunities_from_acquisition(acq_data):
    """
    Generate opportunity ideas from acquisition data
    
    Pattern: If X was acquired, there's opportunity for:
    - Simpler version of X
    - X for specific vertical
    - Alternative to X with different approach
    """
    opportunities = []
    
    # Extract key info
    if 'acquired_company' in acq_data:
        # Manual Crunchbase entry
        company = acq_data['acquired_company']
        category = acq_data.get('category', 'unknown')
        rationale = acq_data.get('rationale', '') or ''
        deal_size = acq_data.get('deal_size', '') or ''
    else:
        # TechCrunch article
        title = acq_data.get('title', '') or ''
        categories = acq_data.get('categories', []) or []
        category = categories[0] if categories else 'unknown'
        signals = acq_data.get('signals', {}) or {}
        rationale = signals.get('strategic_rationale', '') or ''
        deal_size = 'mentioned' if signals.get('deal_size_mentioned') else ''
        
        # Extract company name from title (rough heuristic)
        # "Google acquires X" or "X acquired by Y"
        if title and 'acquires' in title.lower():
            parts = title.split('acquires')
            company = parts[1].strip() if len(parts) > 1 else title
        elif title and 'acquired' in title.lower():
            parts = title.split('acquired')
            company = parts[0].strip() if parts else title
        else:
            company = title or 'Unknown Company'
    
    # Generate opportunity patterns
    base_opportunity = {
        'source_type': 'ma_acquisition',
        'source_company': company,
        'category': category,
        'rationale': rationale,
        'deal_size': deal_size,
        'collected_at': acq_data.get('collected_at', datetime.now().isoformat())
    }
    
    # Pattern 1: Vertical-specific version
    opportunities.append({
        **base_opportunity,
        'pattern': 'vertical_specific',
        'opportunity': f"{company} for [specific industry]",
        'description': f"Build a vertical-specific version targeting healthcare, legal, real estate, etc.",
        'score': 70
    })
    
    # Pattern 2: Simpler alternative
    opportunities.append({
        **base_opportunity,
        'pattern': 'simpler_alternative',
        'opportunity': f"Simpler alternative to {company}",
        'description': f"SMB-focused version with essential features only, easier to use",
        'score': 65
    })
    
    # Pattern 3: Privacy/self-hosted
    if category.lower() in ['ai', 'data', 'analytics', 'communication']:
        opportunities.append({
            **base_opportunity,
            'pattern': 'privacy_focused',
            'opportunity': f"Privacy-focused/self-hosted {company} alternative",
            'description': f"On-premise or privacy-first version for security-conscious customers",
            'score': 60
        })
    
    # Pattern 4: Integration gap
    if 'expand' in rationale.lower() or 'add' in rationale.lower():
        opportunities.append({
            **base_opportunity,
            'pattern': 'integration_opportunity',
            'opportunity': f"Tool that integrates {company} with [other platform]",
            'description': f"Bridge tool connecting acquired product with existing ecosystems",
            'score': 55
        })
    
    return opportunities

def process_ma_files():
    """Process all M&A files and generate opportunities"""
    logger.info("Processing M&A files...")
    
    all_opportunities = []
    files_processed = 0
    
    # Process all JSON files in MA directory
    for ma_file in sorted(MA_DIR.glob('*.json')):
        try:
            with open(ma_file, 'r') as f:
                data = json.load(f)
            
            # Handle different formats
            if 'articles' in data:
                # TechCrunch format
                for article in data['articles']:
                    opps = generate_opportunities_from_acquisition(article)
                    all_opportunities.extend(opps)
            elif 'acquisitions' in data:
                # Crunchbase manual format
                for acq in data['acquisitions']:
                    opps = generate_opportunities_from_acquisition(acq)
                    all_opportunities.extend(opps)
            
            files_processed += 1
            logger.info(f"Processed {ma_file.name}")
            
        except Exception as e:
            logger.error(f"Error processing {ma_file}: {e}")
    
    logger.info(f"Processed {files_processed} files, generated {len(all_opportunities)} opportunities")
    return all_opportunities

def save_opportunities(opportunities):
    """Save opportunities to processed directory"""
    if not opportunities:
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = PROCESSED_DIR / f'ma_opportunities_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump({
            'source': 'ma_processor',
            'generated_at': timestamp,
            'count': len(opportunities),
            'opportunities': opportunities
        }, f, indent=2)
    
    logger.info(f"Saved {len(opportunities)} opportunities to {output_file}")
    return output_file

def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("M&A Opportunity Processor")
    logger.info("=" * 60)
    
    # Process M&A files
    opportunities = process_ma_files()
    
    if not opportunities:
        logger.info("No opportunities generated")
        print("No M&A data found to process")
        return
    
    # Save opportunities
    output_file = save_opportunities(opportunities)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"M&A Opportunity Processor - {len(opportunities)} opportunities generated")
    print(f"{'='*70}\n")
    
    # Group by pattern
    patterns = {}
    for opp in opportunities:
        pattern = opp['pattern']
        patterns[pattern] = patterns.get(pattern, 0) + 1
    
    print("Opportunity Patterns:")
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {count}")
    
    print(f"\nTop 5 Opportunities:\n")
    top_opps = sorted(opportunities, key=lambda x: x['score'], reverse=True)[:5]
    for i, opp in enumerate(top_opps, 1):
        print(f"{i}. [{opp['score']}] {opp['opportunity']}")
        print(f"   Pattern: {opp['pattern']}")
        print(f"   Description: {opp['description']}")
        print(f"   Source: {opp['source_company']} ({opp['category']})\n")
    
    print(f"Saved to: {output_file}")
    logger.info("=" * 60)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Processor failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
