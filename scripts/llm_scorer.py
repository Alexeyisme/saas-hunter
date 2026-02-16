#!/usr/bin/env python3
"""
LLM-Enhanced Scoring Module
Uses Claude Haiku via OpenRouter for enhanced opportunity scoring
"""
import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from scoring import SCORING_CONFIG

# Load environment variables
ENV_FILE = Path(__file__).parent.parent / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Also check scripts/.env
SCRIPTS_ENV = Path(__file__).parent / '.env'
if SCRIPTS_ENV.exists():
    load_dotenv(SCRIPTS_ENV)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Model configuration from scoring_config.json
LLM_CONFIG = SCORING_CONFIG.get('llm_config', {})
MODEL = LLM_CONFIG.get('model', 'anthropic/claude-3-haiku')
LLM_WEIGHT = LLM_CONFIG.get('weight', 0.4)
BASE_WEIGHT = LLM_CONFIG.get('base_weight', 0.6)


def call_openrouter(prompt: str, max_tokens: int = 500) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Call OpenRouter API with Claude Haiku

    Args:
        prompt: The prompt to send
        max_tokens: Maximum tokens in response

    Returns:
        Tuple of (response_text, usage_stats)
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/Alexeyisme/saas-hunter',
        'X-Title': 'SaaS Hunter'
    }

    payload = {
        'model': MODEL,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': max_tokens,
        'temperature': 0.3,  # Lower temperature for more consistent scoring
    }

    try:
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        # Extract response and usage
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {})

        return content, {
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0),
            'model': MODEL
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenRouter API error: {e}")
    except (KeyError, IndexError) as e:
        raise Exception(f"Invalid API response format: {e}")


def build_scoring_prompt(opp: Dict[str, Any], base_score: int) -> str:
    """
    Build prompt for LLM scoring

    Args:
        opp: Opportunity dictionary
        base_score: Base score from rule-based system

    Returns:
        Formatted prompt string
    """
    title = opp.get('title', '')
    body = opp.get('body', '')[:400]  # Limit body length
    source = opp.get('source', '')
    engagement = opp.get('engagement_data', {})

    prompt = f"""Analyze this SaaS opportunity and provide an enhanced score adjustment.

**Opportunity:**
Title: {title}
Source: {source}
Engagement: {engagement}

**Content Preview:**
{body}

**Base Score:** {base_score}/100 (from rule-based system)

**Your Task:**
1. Assess the QUALITY of this opportunity for a SaaS builder:
   - Is the pain point clear and specific?
   - Does it indicate willingness to pay?
   - Is there a viable business opportunity?
   - How urgent/frustrated does the poster seem?
   - How could this problem be solved with a saas?

2. Provide:
   - LLM_SCORE: 0-100 (your assessment)
   - REASONING: 1-2 sentences explaining your score
   - SIGNALS: List 2-3 key positive or negative signals you detected

**Output Format (JSON):**
{{
  "llm_score": <0-100>,
  "reasoning": "<brief explanation>",
  "signals": ["signal1", "signal2", "signal3"]
}}

Be critical - most opportunities are NOT worth pursuing. Only score highly if there's clear pain + willingness to pay + specificity."""

    return prompt


def parse_llm_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse LLM JSON response

    Args:
        response_text: Raw response from LLM

    Returns:
        Parsed dictionary or None if invalid
    """
    try:
        # Try to extract JSON from response (may have markdown code blocks)
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace('```json', '').replace('```', '').strip()

        data = json.loads(response_text)

        # Validate required fields
        if 'llm_score' not in data:
            return None

        # Ensure score is in valid range
        data['llm_score'] = max(0, min(100, int(data['llm_score'])))

        return data

    except (json.JSONDecodeError, ValueError, KeyError):
        return None


def calculate_final_score(base_score: int, llm_score: int) -> int:
    """
    Combine base score and LLM score with configured weights

    Args:
        base_score: Rule-based score (0-100)
        llm_score: LLM score (0-100)

    Returns:
        Final weighted score (0-100)
    """
    # Weighted average based on config
    final = (base_score * BASE_WEIGHT) + (llm_score * LLM_WEIGHT)
    return int(round(final))


def enhanced_score(base_score: int, opp: Dict[str, Any]) -> Tuple[int, Optional[Dict[str, Any]]]:
    """
    Get LLM-enhanced score for an opportunity

    Args:
        base_score: Base score from rule-based system
        opp: Opportunity dictionary

    Returns:
        Tuple of (final_score, llm_data)
        - final_score: Weighted combination of base + LLM scores
        - llm_data: Dict with LLM analysis, tokens, cost, or None if failed
    """
    try:
        # Build prompt
        prompt = build_scoring_prompt(opp, base_score)

        # Call LLM
        response_text, usage_stats = call_openrouter(prompt)

        # Parse response
        llm_analysis = parse_llm_response(response_text)

        if not llm_analysis:
            # Failed to parse, return base score
            return base_score, None

        # Calculate final score
        llm_score = llm_analysis['llm_score']
        final_score = calculate_final_score(base_score, llm_score)

        # Calculate cost (Claude Haiku pricing via OpenRouter)
        # Approximate: $0.25/M input, $1.25/M output tokens
        input_cost = (usage_stats['input_tokens'] / 1_000_000) * 0.25
        output_cost = (usage_stats['output_tokens'] / 1_000_000) * 1.25
        total_cost = input_cost + output_cost

        # Return final score and LLM data
        llm_data = {
            'llm_score': llm_score,
            'base_score': base_score,
            'final_score': final_score,
            'reasoning': llm_analysis.get('reasoning', ''),
            'signals': llm_analysis.get('signals', []),
            'tokens': usage_stats,
            'cost_usd': round(total_cost, 6),
            'model': MODEL
        }

        return final_score, llm_data

    except Exception as e:
        # On any error, return base score
        return base_score, None


if __name__ == '__main__':
    # Test LLM scorer
    print("Testing LLM Scorer...")
    print(f"Model: {MODEL}")
    print(f"Weights: Base={BASE_WEIGHT}, LLM={LLM_WEIGHT}")
    print()

    # Check API key
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY in ['your_openrouter_key_here', '']:
        print("❌ OPENROUTER_API_KEY not set or invalid")
        print("Set it in .env file to enable LLM scoring")
        exit(1)

    # Test opportunity
    test_opp = {
        'title': 'Sick of paying $300/month for DocuSign when I only need basic e-signatures',
        'body': 'Running a small real estate agency with 3 agents. We process about 20 contracts per month but DocuSign costs us $300/month. I would happily pay $50-75/month for something simple that just works for basic contracts. Anyone else in this boat?',
        'source': 'reddit:smallbusiness',
        'engagement_data': {'comments': 12, 'score': 24}
    }

    base_score = 68

    print(f"Testing with base score: {base_score}")
    print(f"Title: {test_opp['title'][:60]}...")
    print()

    try:
        final_score, llm_data = enhanced_score(base_score, test_opp)

        if llm_data:
            print("✅ LLM Enhancement successful!")
            print(f"   Base Score: {llm_data['base_score']}")
            print(f"   LLM Score: {llm_data['llm_score']}")
            print(f"   Final Score: {final_score}")
            print(f"   Reasoning: {llm_data['reasoning']}")
            print(f"   Signals: {', '.join(llm_data['signals'])}")
            print(f"   Tokens: {llm_data['tokens']['total_tokens']} (${llm_data['cost_usd']:.6f})")
        else:
            print("⚠️ LLM enhancement failed, using base score")

    except Exception as e:
        print(f"❌ Error: {e}")
