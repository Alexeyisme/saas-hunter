#!/usr/bin/env python3
"""
Config-driven scoring module
Separated from process_opportunities.py for easier backtesting
"""
import json
from pathlib import Path
from datetime import datetime

# Load scoring config
CONFIG_PATH = Path(__file__).parent.parent / 'scoring_config.json'

def load_config():
    """Load scoring configuration"""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

# Global config (reloaded on import)
SCORING_CONFIG = load_config()

def score_opportunity(opp, config=None):
    """
    Score opportunity 0-100 based on config-driven signals
    
    Args:
        opp: Opportunity dict
        config: Optional scoring config (uses global if not provided)
    
    Returns:
        int: Score 0-100
    """
    if config is None:
        config = SCORING_CONFIG
    
    score = 0
    text = (opp.get('title', '') + ' ' + opp.get('body', '')).lower()
    
    # 1. Source credibility
    source = opp.get('source', '')
    source_weights = config['source_weights']
    
    if source.startswith('github:'):
        score += source_weights['github']
    elif source == 'hackernews':
        score += source_weights['hackernews']
    elif source.startswith('reddit:'):
        # Extract subreddit name
        subreddit = source.replace('reddit:', '')
        key = f'reddit:{subreddit}'
        score += source_weights.get(key, source_weights['reddit:default'])
    
    # 2. Engagement signals
    engagement = opp.get('engagement_data', {})
    eng_weights = config['engagement_weights']
    
    # GitHub reactions
    reactions = engagement.get('reactions', 0)
    score += min(
        reactions * eng_weights['github_reaction_multiplier'],
        eng_weights['github_reaction_max']
    )
    
    # Comments (any source)
    comments = engagement.get('comments', 0)
    score += min(comments, eng_weights['comments_max'])
    
    # HN score
    hn_score = engagement.get('score', 0)
    score += min(hn_score, eng_weights['hackernews_score_max'])
    
    # 3. Pain point signals
    pain_config = config['pain_point_signals']
    
    for signal_type, signal_data in pain_config.items():
        if any(phrase in text for phrase in signal_data['phrases']):
            score += signal_data['score']
    
    # 4. Specificity
    body = opp.get('body', '')
    spec_config = config['specificity_scoring']
    
    if len(body) > spec_config['long_body_threshold']:
        score += spec_config['long_body_score']
    elif len(body) > spec_config['medium_body_threshold']:
        score += spec_config['medium_body_score']
    
    # Contains numbers/metrics
    if any(char.isdigit() for char in body):
        score += spec_config['contains_numbers_score']
    
    # 5. Competition signals
    comp_config = config['competition_signals']
    
    for signal_type, signal_data in comp_config.items():
        if any(phrase in text for phrase in signal_data['phrases']):
            score += signal_data['score']
    
    # 6. Market signals
    market_config = config['market_signals']
    
    for signal_type, signal_data in market_config.items():
        if any(phrase in text for phrase in signal_data['phrases']):
            score += signal_data['score']
    
    return min(score, 100)

def reload_config():
    """Reload config from disk"""
    global SCORING_CONFIG
    SCORING_CONFIG = load_config()
    return SCORING_CONFIG

if __name__ == '__main__':
    # Test scoring
    test_opp = {
        "title": "Tired of expensive e-signature tools for small businesses",
        "source": "reddit:smallbusiness",
        "body": "I've been running a small real estate agency for 5 years. DocuSign costs us $300/month and we only use it for basic contracts. I'd happily pay $50/month for something simple that just works. We process about 20 contracts per month. Anyone else frustrated with this?",
        "engagement_data": {"score": 24, "comments": 12}
    }
    
    score = score_opportunity(test_opp)
    print(f"Test opportunity score: {score}")
    print(f"\nConfig version: {SCORING_CONFIG['version']}")
