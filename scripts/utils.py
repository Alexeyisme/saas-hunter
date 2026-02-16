#!/usr/bin/env python3
"""
SaaS Hunter - Utility Functions
Shared utilities for duplicate detection, logging, and data validation.
"""
import json
import logging
from pathlib import Path
from typing import Set, Dict, Any, List
from datetime import datetime
from config import SEEN_IDS_FILE

# Setup logging
def setup_logging(name: str, log_file: Path = None) -> logging.Logger:
    """Configure logging with both file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Duplicate Detection
class DuplicateDetector:
    """Track and filter duplicate opportunities across collection runs."""
    
    def __init__(self, seen_ids_file: Path = SEEN_IDS_FILE):
        self.seen_ids_file = seen_ids_file
        self.seen_ids: Set[str] = self._load_seen_ids()
    
    def _load_seen_ids(self) -> Set[str]:
        """Load previously seen IDs from file."""
        if self.seen_ids_file.exists():
            try:
                with open(self.seen_ids_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('seen_ids', []))
            except (json.JSONDecodeError, IOError):
                return set()
        return set()
    
    def is_duplicate(self, source: str, source_id: str) -> bool:
        """Check if an opportunity has been seen before."""
        unique_id = f"{source}:{source_id}"
        return unique_id in self.seen_ids
    
    def mark_seen(self, source: str, source_id: str) -> None:
        """Mark an opportunity as seen."""
        unique_id = f"{source}:{source_id}"
        self.seen_ids.add(unique_id)
    
    def save(self) -> None:
        """Persist seen IDs to file."""
        try:
            with open(self.seen_ids_file, 'w') as f:
                json.dump({
                    'seen_ids': list(self.seen_ids),
                    'last_updated': datetime.now().isoformat(),
                    'total_count': len(self.seen_ids)
                }, f, indent=2)
        except IOError as e:
            logging.error(f"Failed to save seen IDs: {e}")


# HTML Cleaning
def clean_html(html_content: str) -> str:
    """Remove HTML tags from content using BeautifulSoup."""
    if not html_content:
        return ""
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except ImportError:
        # Fallback to simple tag removal if BeautifulSoup not available
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_content)


# Data Validation
def validate_opportunity(opp: Dict[str, Any]) -> bool:
    """Validate that an opportunity has all required fields."""
    required_fields = ['source_id', 'source', 'title', 'url', 'published_utc']
    return all(field in opp and opp[field] for field in required_fields)


def normalize_opportunity(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize opportunity data to standard schema."""
    from config import BODY_PREVIEW_LENGTH
    return {
        'source_id': str(item.get('source_id', '')),
        'source': item.get('source', ''),
        'title': item.get('title', ''),
        'body': item.get('body', '')[:BODY_PREVIEW_LENGTH],
        'url': item.get('url', ''),
        'published_utc': item.get('published_utc', ''),
        'engagement_data': item.get('engagement_data', {}),
        'collected_at': item.get('collected_at', datetime.now().isoformat())
    }


# File Utilities
def load_recent_json_files(directory: Path, hours_back: int = 24) -> List[Dict[str, Any]]:
    """Load and combine opportunities from recent JSONL files."""
    from datetime import timedelta

    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    all_opportunities = []

    for file_path in sorted(directory.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True):
        if datetime.fromtimestamp(file_path.stat().st_mtime) >= cutoff_time:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            # Skip metadata line
                            if data.get('_metadata'):
                                continue
                            all_opportunities.append(data)
                        except json.JSONDecodeError:
                            continue
            except IOError as e:
                logging.warning(f"Failed to load {file_path}: {e}")

    return all_opportunities
