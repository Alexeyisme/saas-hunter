#!/usr/bin/env python3
"""
Data Validation Module
Validates opportunity data structure and content quality
"""
from typing import List, Dict, Tuple, Any
from datetime import datetime
import re


def validate_opportunity(opp: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single opportunity

    Args:
        opp: Opportunity dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required fields
    required_fields = ['source_id', 'source', 'title', 'url', 'published_utc']

    for field in required_fields:
        if field not in opp or not opp[field]:
            return False, f"Missing required field: {field}"

    # Validate source format
    source = opp['source']
    valid_sources = ['hackernews', 'reddit:', 'github:']
    if not any(source.startswith(src) for src in valid_sources):
        return False, f"Invalid source format: {source}"

    # Validate title
    title = opp.get('title', '')
    if len(title) < 10:
        return False, "Title too short (min 10 chars)"
    if len(title) > 500:
        return False, "Title too long (max 500 chars)"

    # Validate URL format
    url = opp.get('url', '')
    if not url.startswith(('http://', 'https://')):
        return False, f"Invalid URL format: {url}"

    # Validate published_utc timestamp
    try:
        # Try to parse the timestamp
        pub_utc = opp['published_utc']
        if isinstance(pub_utc, str):
            # Handle both ISO format and Z suffix
            pub_utc_clean = pub_utc.replace('Z', '+00:00')
            datetime.fromisoformat(pub_utc_clean)
    except (ValueError, TypeError) as e:
        return False, f"Invalid published_utc timestamp: {e}"

    # Validate engagement_data if present
    if 'engagement_data' in opp:
        engagement = opp['engagement_data']
        if not isinstance(engagement, dict):
            return False, "engagement_data must be a dictionary"

        # Check numeric fields
        for field in ['comments', 'reactions', 'score']:
            if field in engagement:
                if not isinstance(engagement[field], (int, float)):
                    return False, f"engagement_data.{field} must be numeric"
                if engagement[field] < 0:
                    return False, f"engagement_data.{field} cannot be negative"

    # Content quality checks
    body = opp.get('body', '')

    # Skip if body is just a URL or very short
    if body and len(body.strip()) < 5:
        return False, "Body too short or empty"

    # Check for spam patterns
    spam_patterns = [
        r'^(http|www\.)',  # Starts with URL
        r'(click here|subscribe|follow me)',  # Spam keywords
    ]

    combined_text = (title + ' ' + body).lower()
    for pattern in spam_patterns:
        if re.search(pattern, combined_text, re.IGNORECASE):
            return False, f"Potential spam detected: {pattern}"

    return True, ""


def validate_opportunities(opportunities: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Validate a list of opportunities

    Args:
        opportunities: List of opportunity dictionaries

    Returns:
        Tuple of (valid_opportunities, errors)
        - valid_opportunities: List of opportunities that passed validation
        - errors: List of error dictionaries with 'error' and 'title' keys
    """
    valid_opps = []
    errors = []

    for opp in opportunities:
        is_valid, error_msg = validate_opportunity(opp)

        if is_valid:
            valid_opps.append(opp)
        else:
            errors.append({
                'error': error_msg,
                'title': opp.get('title', 'Unknown title')[:100],
                'source': opp.get('source', 'Unknown source'),
                'url': opp.get('url', '')
            })

    return valid_opps, errors


def validate_batch_stats(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get validation statistics for a batch

    Args:
        opportunities: List of opportunity dictionaries

    Returns:
        Dictionary with validation statistics
    """
    valid_opps, errors = validate_opportunities(opportunities)

    # Count error types
    error_types = {}
    for err in errors:
        error_type = err['error'].split(':')[0]
        error_types[error_type] = error_types.get(error_type, 0) + 1

    return {
        'total': len(opportunities),
        'valid': len(valid_opps),
        'invalid': len(errors),
        'validation_rate': len(valid_opps) / len(opportunities) if opportunities else 0,
        'error_types': error_types
    }


if __name__ == '__main__':
    # Test validation
    test_opportunities = [
        # Valid opportunity
        {
            'source_id': '123',
            'source': 'reddit:SaaS',
            'title': 'Looking for alternative to expensive tool',
            'body': 'I need a better solution for my workflow automation',
            'url': 'https://reddit.com/r/SaaS/comments/123',
            'published_utc': '2026-02-15T10:00:00Z',
            'engagement_data': {'comments': 5, 'score': 10}
        },
        # Invalid - missing field
        {
            'source_id': '124',
            'source': 'reddit:SaaS',
            'title': 'Short',
            'url': 'https://reddit.com/r/SaaS/comments/124',
            # Missing published_utc
        },
        # Invalid - spam pattern
        {
            'source_id': '125',
            'source': 'reddit:SaaS',
            'title': 'Click here to subscribe to my newsletter',
            'body': 'Follow me for more tips',
            'url': 'https://reddit.com/r/SaaS/comments/125',
            'published_utc': '2026-02-15T10:00:00Z',
        }
    ]

    valid, errors = validate_opportunities(test_opportunities)

    print(f"Validated {len(test_opportunities)} opportunities:")
    print(f"  Valid: {len(valid)}")
    print(f"  Invalid: {len(errors)}")
    print("\nErrors:")
    for err in errors:
        print(f"  - {err['error']}: {err['title']}")

    print("\nBatch stats:")
    stats = validate_batch_stats(test_opportunities)
    print(f"  Validation rate: {stats['validation_rate']:.1%}")
    print(f"  Error types: {stats['error_types']}")
