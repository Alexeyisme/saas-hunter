#!/usr/bin/env python3
"""
SaaS Hunter - Centralized Configuration
All paths, constants, and settings in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Determine project root - scripts are in ~/saas-hunter/scripts/
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = Path(os.getenv('SAAS_HUNTER_HOME', SCRIPT_DIR.parent))

# Create directory structure
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
LOG_DIR = PROJECT_ROOT / 'logs'

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
ENV_FILE = PROJECT_ROOT / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# API Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Collection Settings
COLLECTION_HOURS_BACK = int(os.getenv('COLLECTION_HOURS_BACK', '6'))
GITHUB_HOURS_BACK = int(os.getenv('GITHUB_HOURS_BACK', COLLECTION_HOURS_BACK))

# Reddit Settings
REDDIT_SUBREDDITS = [
    # Current sources
    'SaaS', 'Entrepreneur', 'smallbusiness', 'sysadmin',
    # Phase 1 expansion - high signal sources
    'startups', 'freelance', 'sales', 'marketing', 'webdev',
    # Existing
    'productivity', 'ecommerce', 'nocode', 'lowcode', 'saasmarketing'
]

REDDIT_PAIN_KEYWORDS = [
    # First-person expressions (high precision)
    'i wish there was', 'i need a', "i'm looking for", 'i hate', "i can't find",
    
    # Question patterns (genuine need)
    'does anyone know', 'is there a tool', 'anyone know a', 'does anyone have',
    'help me find', 'recommend a tool',
    
    # Frustration indicators (validated)
    'sick of', 'tired of', 'frustrated with', 'hate using',
    
    # Comparison/alternative seeking
    'alternative to', 'better than', 'why is there no',
    
    # Need expressions
    'looking for a tool', 'looking for a saas', 'need a solution',
    'need something that', 'solution for'
]

# Spam/self-promotion indicators - skip posts containing these
REDDIT_PROMO_INDICATORS = [
    'check out my', 'i built', 'i created', 'i made a', 'built a',
    'launching my', 'just released', 'just launched',
    'feedback on my', 'looking for feedback', 'product feedback',
    'introducing', 'try my', 'use code', 'discount code',
    'lifetime deal', 'early access', 'beta testers', 'beta users'
]

# GitHub Settings - Curated list of high-signal SaaS & dev tools
# Weekly collection (reactions need time to accumulate)
GITHUB_REPOSITORIES = [
    # Tier 1: High Signal SaaS Platforms
    'supabase/supabase',        # Backend-as-a-service
    'posthog/posthog',          # Product analytics
    'n8n-io/n8n',               # Workflow automation
    'plausible/analytics',      # Privacy-focused analytics
    
    # Tier 2: Developer Tools
    'langchain-ai/langchain',   # LLM framework
    'excalidraw/excalidraw',    # Diagramming tool
    'trpc/trpc',                # Type-safe API
    
    # Tier 3: Indie SaaS Tools
    'formbricks/formbricks',    # Survey tool
    'documenso/documenso',      # E-signature
    'nocodb/nocodb',            # No-code database
    'directus/directus'         # Headless CMS
]
# Note: Cal-com/cal.com removed (422 API errors)

GITHUB_FEATURE_LABELS = [
    'enhancement', 'feature', 'feature-request', 'feature request', 'suggestion'
]

# Hacker News Settings
HN_ASK_KEYWORDS = [
    # Seeker-focused (genuine need)
    'how do you currently', 'what do you use for', 'best way to',
    'struggling to find', 'frustrated that', 'recommend', 'alternative to',
    'better than', 'looking for', 'need something', 'frustrated with',
    'wish there was', 'does anyone use', 'solution for',
    'why is there no', 'how do you handle',
    
    # Removed builder-focused terms that appear in self-promotion:
    # 'build a', 'product for', 'startup idea', 'business model'
]

# Self-promotion indicators for HN - skip posts containing these
HN_PROMO_INDICATORS = [
    "i'm building", "i built", "i created", "i'm working on", "i made",
    "would you use", "my question is", "feedback on", "thoughts on my",
    "check out", "try out", "just launched", "just released",
    "show hn:", "open source", "available at"
]

# Engagement threshold for high-signal posts
HN_COMMENT_THRESHOLD = 15  # Increased from 5

# API Rate Limiting
REQUEST_TIMEOUT = 15  # seconds
API_CALL_DELAY = 1  # seconds between requests
RETRY_DELAY = 5  # seconds between retries
API_PER_PAGE = 100  # max results per page

# Scoring Configuration
MIN_OPPORTUNITY_SCORE = int(os.getenv('MIN_OPPORTUNITY_SCORE', '50'))

SCORING_WEIGHTS = {
    'pain_clarity': 30,
    'urgency': 20,
    'willingness_to_pay': 20,
    'market_engagement': 15,
    'competition_gap': 10,
    'technical_feasibility': 5
}

# User Agent
USER_AGENT = "OpenClaw SaaS Hunter Bot (feedparser; Contact: github.com/yourusername)"

# Duplicate Detection
SEEN_IDS_FILE = DATA_DIR / 'seen_ids.json'

# Content Limits
BODY_PREVIEW_LENGTH = 500  # characters

# Digest Settings
DIGEST_TOP_N = int(os.getenv('DIGEST_TOP_N', '5'))
DIGEST_DAYS_BACK = int(os.getenv('DIGEST_DAYS_BACK', '1'))

# Budget Settings
MONTHLY_BUDGET_USD = float(os.getenv('MONTHLY_BUDGET_USD', '15.0'))
