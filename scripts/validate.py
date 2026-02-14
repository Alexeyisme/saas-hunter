#!/usr/bin/env python3
"""
Data validation utilities for SaaS Hunter
"""
from datetime import datetime

def validate_opportunity(opp):
    """
    Validate opportunity structure and data
    Raises ValueError if invalid
    """
    required_fields = ['title', 'source', 'published_utc']
    
    # Check required fields exist
    for field in required_fields:
        if field not in opp:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate title
    if not opp['title'] or not opp['title'].strip():
        raise ValueError("Empty title")
    
    if len(opp['title']) > 500:
        raise ValueError(f"Title too long: {len(opp['title'])} chars")
    
    # Validate source
    valid_sources = ['reddit:', 'hackernews', 'github:']
    if not any(opp['source'].startswith(s) for s in valid_sources):
        raise ValueError(f"Invalid source: {opp['source']}")
    
    # Validate date
    try:
        datetime.fromisoformat(opp['published_utc'].replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid date format: {opp.get('published_utc')}")
    
    # Validate engagement data (if present)
    if 'engagement_data' in opp and not isinstance(opp['engagement_data'], dict):
        raise ValueError("engagement_data must be a dict")
    
    return True

def validate_opportunities(opportunities):
    """Validate list of opportunities, return (valid, errors)"""
    valid = []
    errors = []
    
    for i, opp in enumerate(opportunities):
        try:
            validate_opportunity(opp)
            valid.append(opp)
        except ValueError as e:
            errors.append({
                'index': i,
                'error': str(e),
                'title': opp.get('title', 'N/A')[:50]
            })
    
    return valid, errors
