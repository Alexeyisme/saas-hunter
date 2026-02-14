#!/usr/bin/env python3
"""
LLM-enhanced opportunity scoring
SIMPLE VERSION: Just returns base score + 10 as a demonstration
Real LLM requires OpenRouter API key or OpenClaw integration
"""

def enhanced_score(base_score, opportunity):
    """
    Simple enhancement without LLM
    Just a demonstration that shows where LLM would plug in
    
    To enable real LLM:
    1. Get OpenRouter API key: https://openrouter.ai/keys
    2. Add to .env: OPENROUTER_API_KEY=sk-or-v1-...
    3. Use llm_scorer.py instead of this file
    """
    # For now, just return base score (no enhancement)
    return base_score, {
        "score": base_score,
        "reasoning": "LLM scoring disabled (no API key configured)",
        "pain_point": opportunity.get('title', ''),
        "opportunity": "Configure OpenRouter API key to enable LLM analysis"
    }

if __name__ == "__main__":
    # Test
    test_opp = {
        "title": "Test opportunity",
        "source": "reddit:SaaS",
        "body": "Test body"
    }
    
    score, data = enhanced_score(50, test_opp)
    print(f"Base score: 50")
    print(f"Enhanced score: {score}")
    print(f"LLM data: {data}")
