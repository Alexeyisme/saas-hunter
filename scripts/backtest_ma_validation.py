#!/usr/bin/env python3
"""
Backtest M&A Opportunities Against Reddit/HN Data
Validates M&A-generated opportunities by checking if Reddit/HN users mentioned similar pain points
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
MA_OPP_FILE = DATA_DIR / 'processed' / 'ma_opportunities_20260214_172108.json'

def load_ma_opportunities():
    """Load M&A-generated opportunities"""
    with open(MA_OPP_FILE, 'r') as f:
        data = json.load(f)
    return data['opportunities']

def load_reddit_hn_data():
    """Load all Reddit/HN opportunities"""
    all_opps = []
    for file in sorted(RAW_DIR.glob('*.json')):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                opps = data.get('opportunities', [])
                all_opps.extend(opps)
        except:
            pass
    return all_opps

def extract_keywords(text):
    """Extract key product/category keywords"""
    if not text:
        return set()
    text_lower = text.lower()
    keywords = set()
    
    # Product keywords
    products = [
        'figma', 'slack', 'mailchimp', 'typeform', 'loom', 'airtable',
        'calendly', 'notion', 'zapier', 'grammarly',
        'design', 'collaboration', 'communication', 'email', 'marketing',
        'forms', 'survey', 'video', 'scheduling', 'calendar',
        'productivity', 'automation', 'integration', 'writing'
    ]
    
    for product in products:
        if product in text_lower:
            keywords.add(product)
    
    return keywords

def find_reddit_mentions(ma_opp, reddit_data):
    """Find Reddit/HN posts that mention the same product/category"""
    source_company = ma_opp['source_company'].lower()
    category = ma_opp['category'].lower()
    
    matches = []
    
    for opp in reddit_data:
        title = opp.get('title', '').lower()
        body = opp.get('body', '').lower()
        text = title + ' ' + body
        
        # Check for product name mention
        if source_company in text or any(keyword in text for keyword in category.split('/')):
            matches.append({
                'title': opp.get('title'),
                'source': opp.get('source'),
                'engagement': opp.get('engagement_data', {}),
                'relevance': 'direct_mention' if source_company in text else 'category_match'
            })
    
    return matches

def analyze_validation():
    """Main analysis"""
    print("=" * 80)
    print("M&A OPPORTUNITY BACKTEST - Validating Against Reddit/HN Data")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading M&A opportunities...")
    ma_opps = load_ma_opportunities()
    print(f"Loaded {len(ma_opps)} M&A-generated opportunities")
    
    print("\nLoading Reddit/HN data...")
    reddit_data = load_reddit_hn_data()
    print(f"Loaded {len(reddit_data)} Reddit/HN opportunities")
    print()
    
    # Group M&A opps by source company
    by_company = defaultdict(list)
    for opp in ma_opps:
        company = opp['source_company']
        by_company[company].append(opp)
    
    # Analyze each company
    results = []
    
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    
    for company, opps in sorted(by_company.items(), key=lambda x: x[0]):
        print(f"\n{'─' * 80}")
        print(f"🎯 {company}")
        print(f"{'─' * 80}")
        
        # Find Reddit mentions
        matches = find_reddit_mentions(opps[0], reddit_data)
        
        if matches:
            print(f"✅ VALIDATED - Found {len(matches)} Reddit/HN mentions")
            
            # Show top 3 matches
            for i, match in enumerate(matches[:3], 1):
                print(f"\n  {i}. {match['title'][:70]}")
                print(f"     Source: {match['source']}")
                print(f"     Relevance: {match['relevance']}")
                eng = match['engagement']
                if eng.get('score'):
                    print(f"     Engagement: {eng.get('score')} score, {eng.get('comments', 0)} comments")
                elif eng.get('reactions'):
                    print(f"     Engagement: {eng.get('reactions')} reactions")
            
            if len(matches) > 3:
                print(f"\n  ... and {len(matches) - 3} more")
            
            results.append({
                'company': company,
                'category': opps[0]['category'],
                'validated': True,
                'mention_count': len(matches),
                'opportunity_patterns': len(opps)
            })
        else:
            print(f"❌ NOT VALIDATED - No Reddit/HN mentions found")
            print(f"   (May indicate niche product or data gap)")
            
            results.append({
                'company': company,
                'category': opps[0]['category'],
                'validated': False,
                'mention_count': 0,
                'opportunity_patterns': len(opps)
            })
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    validated = [r for r in results if r['validated']]
    not_validated = [r for r in results if not r['validated']]
    
    print(f"Total M&A Acquisitions Analyzed: {len(results)}")
    print(f"✅ Validated (Reddit/HN mentions): {len(validated)} ({len(validated)/len(results)*100:.0f}%)")
    print(f"❌ Not Validated: {len(not_validated)} ({len(not_validated)/len(results)*100:.0f}%)")
    print()
    
    if validated:
        print("Top Validated Opportunities:")
        for i, r in enumerate(sorted(validated, key=lambda x: x['mention_count'], reverse=True)[:5], 1):
            print(f"  {i}. {r['company']} - {r['mention_count']} mentions ({r['category']})")
    
    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    validation_rate = len(validated) / len(results) * 100
    
    if validation_rate >= 70:
        print("✅ STRONG VALIDATION")
        print(f"   {validation_rate:.0f}% of M&A acquisitions have Reddit/HN pain point mentions")
        print("   This confirms M&A signals align with community-expressed problems")
    elif validation_rate >= 40:
        print("⚠️  MODERATE VALIDATION")
        print(f"   {validation_rate:.0f}% of M&A acquisitions have Reddit/HN mentions")
        print("   M&A provides complementary signal but not perfect overlap")
    else:
        print("❌ WEAK VALIDATION")
        print(f"   Only {validation_rate:.0f}% validated")
        print("   May need broader Reddit coverage or different M&A categories")
    
    print()
    print("💡 Insight: M&A acquisitions represent investor-validated problems.")
    print("   Cross-referencing with Reddit/HN shows which problems have active")
    print("   user communities discussing them = double validation!")

if __name__ == '__main__':
    try:
        analyze_validation()
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
