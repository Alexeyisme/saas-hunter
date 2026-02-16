# Quick Start

## Installation
```bash
git clone https://github.com/Alexeyisme/saas-hunter.git
cd saas-hunter
python3 -m venv venv
source venv/bin/activate
pip install feedparser praw openai
```

## Configuration
Create `.env`:
```bash
GITHUB_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here  # Optional, for LLM scoring
```

## Run Collectors
```bash
cd saas-hunter && source venv/bin/activate
python scripts/reddit_monitor.py      # Scans 36 subreddits
python scripts/hackernews_monitor.py  # Scans Ask HN
python scripts/github_monitor.py      # Scans 23 repos
```

## Process & Generate
```bash
python scripts/process_opportunities.py  # Score + dedupe
python scripts/generate_digest.py       # Daily summary
```

## Weekly Review
```bash
python scripts/weekly_review.py
cat data/reports/weekly_review_*.md
```

## Key Files
- **Config:** `scripts/config.py` (sources, keywords)
- **Scoring:** `scoring_config.json` (weights, thresholds)
- **Expansion:** `EXPANSION_PLAN.md` (phase 1→2→3)
- **Data:** `data/processed/*.jsonl` (scored opportunities)

## Expansion Status
- **Phase 1** (Feb 16): 36 subreddits, 74 keywords, 23 repos ✅
- **Phase 2** (Feb 23): +16 subreddits, Twitter/PH research 🕐
- **Phase 3** (Mar 2): Data-driven platform decision 🕐

**Budget:** $0.002/month (0.01% of $15 target)
