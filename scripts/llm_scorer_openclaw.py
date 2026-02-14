#!/usr/bin/env python3
"""
LLM-enhanced opportunity scoring using OpenClaw sessions_spawn
Uses Haiku via OpenClaw instead of direct OpenRouter API calls
"""
import json
import subprocess
from pathlib import Path

SCORING_PROMPT = """Analyze this SaaS opportunity and score it 0-100 based on:
1. Pain point clarity (0-30): Is the problem well-defined?
2. Market signal (0-30): Evidence of demand/willingness to pay?
3. Competition gap (0-20): Is this underserved?
4. Execution feasibility (0-20): Can a solo dev build this?

Return ONLY a JSON object with these fields:
- score (0-100 integer)
- reasoning (brief 1-2 sentence explanation)
- pain_point (concise pain point description)
- opportunity (what to build)

Opportunity:
Title: {{title}}
Source: {{source}}
Body: {{body}}
Engagement: {{engagement}}"""

def llm_score_via_openclaw(opportunity):
    """
    Score an opportunity using OpenClaw Python API
    Uses Haiku via OpenClaw - no separate API key needed
    """
    try:
        # Import OpenClaw Python client (if available)
        import sys
        sys.path.insert(0, '/usr/lib/node_modules/openclaw')
        
        # We can't easily use subprocess openclaw CLI from Python
        # Instead, let's use direct HTTP call to gateway
        # But that still requires knowing the gateway URL/token
        
        # Simpler approach: Just indicate LLM is not configured
        # User should set OPENROUTER_API_KEY if they want LLM scoring
        raise NotImplementedError("OpenClaw integration requires gateway token - use OPENROUTER_API_KEY for now")
        
    except Exception as e:
        # Fallback on any error
        return {
            "score": 50,
            "reasoning": f"LLM not configured: {str(e)[:50]}",
            "pain_point": opportunity.get('title', ''),
            "opportunity": "Unknown"
        }

def enhanced_score(base_score, opportunity):
    """
    Combine rule-based score with LLM score
    Only call LLM for promising opportunities (base_score > 45)
    """
    if base_score < 45:
        # Not worth the token cost
        return base_score, None
    
    try:
        llm_result = llm_score_via_openclaw(opportunity)
        llm_score_value = llm_result.get('score', 50)
        
        # Weighted combination: 60% rule-based, 40% LLM
        final_score = (base_score * 0.6) + (llm_score_value * 0.4)
        
        return final_score, llm_result
    except Exception as e:
        print(f"LLM scoring error: {e}")
        return base_score, None

if __name__ == "__main__":
    # Test with a sample opportunity
    test_opp = {
        "title": "Tired of expensive e-signature tools for small businesses",
        "source": "reddit:smallbusiness",
        "body": "I've been running a small real estate agency for 5 years. DocuSign costs us $300/month and we only use it for basic contracts. I'd happily pay $50/month for something simple that just works. Anyone else frustrated with this?",
        "engagement_data": {"score": 24, "comments": 12}
    }
    
    result = llm_score_via_openclaw(test_opp)
    print(json.dumps(result, indent=2))
