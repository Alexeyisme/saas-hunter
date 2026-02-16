#!/usr/bin/env python3
"""
Phase 2 Expansion - Add remaining subreddits and Twitter/Product Hunt monitoring
"""
import sys
from pathlib import Path

PHASE2_SUBREDDITS = [
    # Business & Industry (remaining)
    'legaladvice', 'healthcare', 'retail', 'freelanceWriters', 'agencylife',
    'teachers', 'logistics', 'supplychain',
    
    # Developer & Tech (remaining)
    'datascience', 'sysadminhumor', 'webhosting', 'analytics',
    
    # Creative & Content (remaining)
    'content_marketing', 'Twitch', 'NewTubers',
    
    # Process & Operations
    'projectmanagement', 'agile', 'CustomerSuccess', 'smallbiz'
]

PHASE2_GITHUB_REPOS = [
    # More developer tools
    'facebook/react',
    'microsoft/vscode',
    
    # Content/Media
    'BookStackApp/BookStack',
    'outline/outline',
    'mattermost/mattermost',
    'discourse/discourse'
]

def main():
    print("=" * 60)
    print("Phase 2 Expansion")
    print("=" * 60)
    
    config_file = Path(__file__).parent / 'config.py'
    
    # Read current config
    with open(config_file, 'r') as f:
        config_content = f.read()
    
    # Find the REDDIT_SUBREDDITS list and add phase 2
    # This is a simplified implementation - manual edit recommended
    print(f"\n📋 Add these {len(PHASE2_SUBREDDITS)} subreddits:")
    for sub in PHASE2_SUBREDDITS:
        print(f"  - r/{sub}")
    
    print(f"\n📋 Add these {len(PHASE2_GITHUB_REPOS)} GitHub repos:")
    for repo in PHASE2_GITHUB_REPOS:
        print(f"  - {repo}")
    
    print("\n💡 Manual action required:")
    print("1. Edit /root/saas-hunter/scripts/config.py")
    print("2. Add Phase 2 subreddits to REDDIT_SUBREDDITS list")
    print("3. Add Phase 2 repos to GITHUB_REPOSITORIES list")
    print("4. Add comment: '# Phase 2 expansion'")
    
    print("\n🔬 New data sources to explore:")
    print("- Twitter/X monitoring (via nitter.net or API)")
    print("- Product Hunt comments scraping")
    print("- Consider budget for Twitter API access")
    
    print("\n✅ Phase 2 checklist complete")
    print("=" * 60)

if __name__ == '__main__':
    main()
