#!/usr/bin/env python3
"""
Backtesting - Reprocess historical data with different scoring configs
Test scoring strategies without waiting for new data
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse
from collections import defaultdict

# Import scoring logic
from scoring import score_opportunity
from process_opportunities import deduplicate_opportunities, enrich_opportunity

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
BACKTEST_DIR = DATA_DIR / 'backtests'
BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

def load_scoring_config(config_path):
    """Load scoring configuration from JSON"""
    with open(config_path, 'r') as f:
        return json.load(f)

def load_raw_data(days_back=7):
    """Load raw opportunities from last N days"""
    cutoff = datetime.now() - timedelta(days=days_back)
    all_opps = []
    files_processed = 0
    
    for file in sorted(RAW_DIR.glob('*.json')):
        # Parse date from filename (e.g., reddit_20260214_120030.json)
        try:
            date_str = file.stem.split('_')[1]  # Get YYYYMMDD
            file_date = datetime.strptime(date_str, '%Y%m%d')
            
            if file_date >= cutoff:
                with open(file, 'r') as f:
                    data = json.load(f)
                    opps = data.get('opportunities', [])
                    all_opps.extend(opps)
                    files_processed += 1
        except Exception as e:
            print(f"⚠ Skipping {file.name}: {e}")
    
    print(f"Loaded {len(all_opps)} opportunities from {files_processed} files (last {days_back} days)")
    return all_opps

def analyze_results(opportunities):
    """Generate analysis report"""
    if not opportunities:
        return "No opportunities to analyze"
    
    scores = [o['score'] for o in opportunities]
    
    # Score distribution
    score_buckets = defaultdict(int)
    for score in scores:
        if score >= 80:
            score_buckets['80+ (Top Tier)'] += 1
        elif score >= 60:
            score_buckets['60-79 (High Quality)'] += 1
        elif score >= 40:
            score_buckets['40-59 (Worth Exploring)'] += 1
        else:
            score_buckets['<40 (Low Signal)'] += 1
    
    # Source breakdown
    sources = defaultdict(int)
    for opp in opportunities:
        source = opp.get('source', 'unknown')
        sources[source] += 1
    
    # Domain breakdown
    domains = defaultdict(int)
    for opp in opportunities:
        domain = opp.get('domain', 'other')
        domains[domain] += 1
    
    # Build report
    report = []
    report.append("=" * 70)
    report.append("BACKTEST RESULTS")
    report.append("=" * 70)
    report.append("")
    
    report.append(f"Total Opportunities: {len(opportunities)}")
    report.append(f"Average Score: {sum(scores)/len(scores):.1f}")
    report.append(f"Max Score: {max(scores)}")
    report.append(f"Min Score: {min(scores)}")
    report.append("")
    
    report.append("Score Distribution:")
    for bucket, count in sorted(score_buckets.items(), reverse=True):
        pct = (count / len(opportunities)) * 100
        report.append(f"  {bucket}: {count} ({pct:.1f}%)")
    report.append("")
    
    report.append("Top 10 Opportunities:")
    top_10 = sorted(opportunities, key=lambda x: x['score'], reverse=True)[:10]
    for i, opp in enumerate(top_10, 1):
        report.append(f"{i}. [{opp['score']:.0f}] {opp.get('title', 'No title')[:70]}")
        report.append(f"   Source: {opp.get('source')} | Domain: {opp.get('domain')}")
    report.append("")
    
    report.append("By Source:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {source}: {count}")
    report.append("")
    
    report.append("By Domain:")
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {domain}: {count}")
    report.append("")
    
    report.append("=" * 70)
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Backtest scoring configurations')
    parser.add_argument('--days', type=int, default=7, help='Days of historical data to process (default: 7)')
    parser.add_argument('--config', type=str, default='scoring_config.json', help='Scoring config file (default: scoring_config.json)')
    parser.add_argument('--output', type=str, help='Output file name (default: backtest_TIMESTAMP.json)')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM scoring for backtest')
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(__file__).parent.parent / args.config
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    print(f"Loading config: {config_path}")
    config = load_scoring_config(config_path)
    print(f"Config version: {config.get('version', 'unknown')}")
    print("")
    
    # Load historical data
    print(f"Loading last {args.days} days of data...")
    raw_opps = load_raw_data(args.days)
    
    if not raw_opps:
        print("❌ No data found")
        sys.exit(1)
    
    print("")
    
    # Score with current config
    print("Scoring opportunities...")
    for opp in raw_opps:
        opp['score'] = score_opportunity(opp, config=config)
    
    # Deduplicate
    print("Deduplicating...")
    unique_opps = deduplicate_opportunities(raw_opps)
    print(f"After deduplication: {len(unique_opps)} unique ({len(raw_opps) - len(unique_opps)} duplicates removed)")
    print("")
    
    # Enrich
    for opp in unique_opps:
        enrich_opportunity(opp)
    
    # Generate report
    report = analyze_results(unique_opps)
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_name = args.output or f'backtest_{timestamp}.json'
    output_path = BACKTEST_DIR / output_name
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'config_file': args.config,
        'config_version': config.get('version'),
        'days_back': args.days,
        'raw_count': len(raw_opps),
        'unique_count': len(unique_opps),
        'opportunities': unique_opps,
        'report': report
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save report as text
    report_path = BACKTEST_DIR / output_name.replace('.json', '.txt')
    with open(report_path, 'w') as f:
        f.write(report)
    
    print("")
    print(f"✅ Results saved to: {output_path}")
    print(f"✅ Report saved to: {report_path}")
    print("")
    print("Next steps:")
    print("1. Review top opportunities - are they actually good?")
    print("2. Adjust scoring_config.json weights")
    print("3. Run backtest again to compare")

if __name__ == '__main__':
    main()
