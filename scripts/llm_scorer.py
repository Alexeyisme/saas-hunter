#!/usr/bin/env python3
"""
LLM-enhanced opportunity scoring using OpenRouter
Phase 2 enhancement - only for high-scoring opportunities
"""
import os
import json
import requests
from pathlib import Path
from usage_tracker import UsageTracker

# Config
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MODEL = "anthropic/claude-3-haiku"  # Cheapest, fast, good enough
API_URL = "https://openrouter.ai/api/v1/chat/completions"

tracker = UsageTracker()

SCORING_PROMPT = """Analyze this SaaS opportunity and score it 0-100 based on:
1. Pain point clarity (0-30): Is the problem well-defined?
2. Market signal (0-30): Evidence of demand/willingness to pay?
3. Competition gap (0-20): Is this underserved?
4. Execution feasibility (0-20): Can a solo dev build this?

Return ONLY a JSON object:
{
  "score": <0-100>,
  "reasoning": "<brief 1-2 sentence explanation>",
  "pain_point": "<concise pain point description>",
  "opportunity": "<what to build>"
}

Opportunity:
Title: {title}
Source: {source}
Body: {body}
Engagement: {engagement}
"""

def llm_score(opportunity):
    """
    Score an opportunity using Claude Haiku
    Returns dict with score, reasoning, pain_point, opportunity
    Cost: ~$0.001 per call
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in environment")
    
    # Format prompt
    prompt = SCORING_PROMPT.format(
        title=opportunity.get('title', ''),
        source=opportunity.get('source', ''),
        body=opportunity.get('body', '')[:1000],  # Truncate to save tokens
        engagement=json.dumps(opportunity.get('engagement_data', {}))
    )
    
    # Call API
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 300
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    content = result['choices'][0]['message']['content']
    usage = result.get('usage', {})
    
    # Track usage
    tracker.log_tokens(
        'llm_scorer',
        input_tokens=usage.get('prompt_tokens', 0),
        output_tokens=usage.get('completion_tokens', 0),
        model=MODEL
    )
    
    # Parse response
    try:
        # Extract JSON from response (may have markdown wrapper)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return {
            "score": 50,
            "reasoning": "Failed to parse LLM response",
            "pain_point": opportunity.get('title', ''),
            "opportunity": "Unknown"
        }

def enhanced_score(base_score, opportunity):
    """
    Combine rule-based score with LLM score
    Only call LLM for promising opportunities (base_score > 45)
    """
    if base_score < 45:
        # Not worth the API cost
        return base_score, None
    
    try:
        llm_result = llm_score(opportunity)
        llm_score_value = llm_result.get('score', 50)
        
        # Weighted combination: 60% rule-based, 40% LLM
        final_score = (base_score * 0.6) + (llm_score_value * 0.4)
        
        return final_score, llm_result
    except Exception as e:
        print(f"LLM scoring failed: {e}")
        return base_score, None

if __name__ == "__main__":
    # Test with a sample opportunity
    test_opp = {
        "title": "Tired of expensive e-signature tools for small businesses",
        "source": "reddit:smallbusiness",
        "body": "I've been running a small real estate agency for 5 years. DocuSign costs us $300/month and we only use it for basic contracts. I'd happily pay $50/month for something simple that just works. Anyone else frustrated with this?",
        "engagement_data": {"score": 24, "comments": 12}
    }
    
    result = llm_score(test_opp)
    print(json.dumps(result, indent=2))
