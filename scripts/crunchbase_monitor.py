#!/usr/bin/env python3
"""
Crunchbase M&A Monitor - Manual tracking via web scraping
Since API requires paid subscription, we'll do manual collection for now
This script helps structure manual data entry
"""
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

def manual_entry_template():
    """Interactive template for manual M&A entry"""
    print("\n" + "="*70)
    print("Crunchbase M&A Manual Entry")
    print("="*70 + "\n")
    
    print("Enter acquisition details (or 'done' to finish):\n")
    
    acquisitions = []
    
    while True:
        print("\n--- New Acquisition ---")
        
        acquired = input("Acquired company: ").strip()
        if acquired.lower() == 'done':
            break
        
        acquirer = input("Acquirer: ").strip()
        deal_size = input("Deal size (e.g., $50M, undisclosed): ").strip()
        date = input("Date (YYYY-MM-DD): ").strip()
        category = input("Category/Industry: ").strip()
        rationale = input("Why acquired? (brief): ").strip()
        url = input("Crunchbase URL (optional): ").strip()
        
        acquisition = {
            'acquired_company': acquired,
            'acquirer': acquirer,
            'deal_size': deal_size,
            'date': date,
            'category': category,
            'rationale': rationale,
            'url': url,
            'source': 'crunchbase_manual',
            'collected_at': datetime.now().isoformat()
        }
        
        acquisitions.append(acquisition)
        print(f"✓ Added: {acquirer} acquires {acquired}")
        
        more = input("\nAdd another? (y/n): ").strip().lower()
        if more != 'y':
            break
    
    if not acquisitions:
        print("No acquisitions entered.")
        return
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = MA_DIR / f'crunchbase_manual_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump({
            'source': 'crunchbase_manual',
            'collected_at': timestamp,
            'count': len(acquisitions),
            'acquisitions': acquisitions
        }, f, indent=2)
    
    print(f"\n✅ Saved {len(acquisitions)} acquisitions to {output_file}")
    
    # Print summary
    print(f"\n{'='*70}")
    print("Summary")
    print("="*70)
    for acq in acquisitions:
        print(f"\n• {acq['acquirer']} → {acq['acquired_company']}")
        print(f"  ${acq['deal_size']} | {acq['category']}")
        print(f"  Rationale: {acq['rationale']}")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crunchbase M&A Manual Entry')
    parser.add_argument('--interactive', action='store_true', help='Interactive entry mode')
    args = parser.parse_args()
    
    if args.interactive:
        manual_entry_template()
    else:
        print("Crunchbase M&A Monitor")
        print("\nNote: Crunchbase API requires paid subscription.")
        print("Use --interactive for manual data entry.")
        print("\nOr visit: https://www.crunchbase.com/search/acquisitions")
        print("Filter for: SaaS, last 30 days, $10M-500M")

if __name__ == '__main__':
    main()
