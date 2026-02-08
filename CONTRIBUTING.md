# Contributing to SaaS Hunter

Thanks for your interest in improving SaaS Hunter!

## How to Contribute

### 1. Improve Collectors
- Add new subreddits to `scripts/config.py`
- Suggest better GitHub repos
- Refine keyword lists

### 2. Enhance Scoring
- Propose new scoring factors
- Share scoring weight adjustments
- Report false positives/negatives

### 3. Add Features
- New data sources (Twitter, Discord, etc.)
- Better deduplication algorithms
- Enhanced digest formats

### 4. Report Issues
- Collection failures
- Scoring bugs
- Documentation improvements

## Development Setup

```bash
git clone https://github.com/yourusername/saas-hunter.git
cd saas-hunter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your tokens
```

## Testing

```bash
cd scripts

# Test collectors
../venv/bin/python3 reddit_monitor.py
../venv/bin/python3 github_monitor.py
../venv/bin/python3 hackernews_monitor.py

# Test processing
../venv/bin/python3 process_opportunities.py

# Check usage
../venv/bin/python3 usage_stats.py
```

## Pull Request Guidelines

1. Test your changes locally
2. Update documentation if needed
3. Add your changes to CHANGELOG.md
4. Keep commits focused and descriptive

## Code Style

- Python: Follow PEP 8
- Comments: Explain why, not what
- Logging: Use the established logger
- Error handling: Graceful degradation

## Questions?

Open an issue or reach out!
