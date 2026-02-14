# SaaS Hunter

**Automated SaaS opportunity discovery from Reddit, GitHub, and Hacker News.**

🎯 **Mission:** Surface actionable pain points and unmet needs by monitoring public discussions across three high-signal sources.

---

## 📊 Quick Stats

- **Sources:** 14 subreddits, 11 GitHub repos, Ask HN
- **Cost:** $0/month (within free tiers)
- **Collection:** Autonomous via OpenClaw cron
- **Status:** ✅ Production (monitoring active since 2026-02-14)

---

## 🏗️ Architecture

```
saas-hunter/
├── scripts/
│   ├── config.py                    # Centralized configuration
│   ├── utils.py                     # Shared utilities
│   ├── reddit_monitor.py            # Reddit RSS collector
│   ├── github_monitor.py            # GitHub API collector
│   ├── hackernews_monitor.py        # HN Algolia collector
│   ├── process_opportunities.py     # Scoring + dedup pipeline
│   ├── generate_digest.py           # Daily digest generator
│   └── send_telegram_openclaw.py    # Telegram delivery queue
├── data/
│   ├── raw/                         # Timestamped collector outputs
│   ├── processed/                   # Scored opportunities (JSONL)
│   ├── digests/                     # Daily markdown summaries
│   ├── telegram_outbox/             # Queued digests for delivery
│   └── seen_ids.json                # Deduplication tracking
├── logs/                            # Execution logs
├── scoring_config.json              # Scoring weights (v1.4-balanced)
├── venv/                            # Python environment
└── .env                             # API keys and settings
```

---

## 🚀 Setup

### 1. Install Dependencies

```bash
cd ~/saas-hunter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Requirements:
- feedparser
- requests
- beautifulsoup4
- python-dotenv

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# GitHub token (required)
GITHUB_TOKEN=ghp_your_token_here

# OpenRouter API for LLM scoring (optional)
OPENROUTER_API_KEY=sk-or-v1-your_key_here

# Collection windows
GITHUB_HOURS_BACK=168  # 1 week
COLLECTION_HOURS_BACK=6  # Reddit/HN
```

Get GitHub token: https://github.com/settings/tokens (needs `public_repo` scope)

### 3. Test Collectors

```bash
cd scripts

# Reddit (RSS, no auth required)
../venv/bin/python3 reddit_monitor.py

# GitHub (requires token)
../venv/bin/python3 github_monitor.py

# HackerNews (free API)
../venv/bin/python3 hackernews_monitor.py

# Processing pipeline
../venv/bin/python3 process_opportunities.py

# Digest generation
../venv/bin/python3 generate_digest.py
```

---

## 🤖 Autonomous Operation (OpenClaw)

The system runs autonomously via OpenClaw cron jobs:

### Cron Schedule

```
Reddit Monitor:       Every 3 hours
HackerNews Monitor:   Every 4 hours
GitHub Monitor:       Daily at 06:00 UTC
Process Pipeline:     Every 6 hours
Daily Digest:         Daily at 08:00 UTC
```

### Delivery Flow

1. Collectors gather opportunities → `data/raw/`
2. Processor scores & deduplicates → `data/processed/`
3. Digest generator creates markdown → `data/digests/`
4. Telegram queue created → `data/telegram_outbox/`
5. OpenClaw heartbeat delivers via Telegram

**No manual intervention required** — system is fully autonomous.

---

## 📊 Data Pipeline

### 1. Collection Layer

**Reddit (14 subreddits):**
- SaaS, Entrepreneur, startups, smallbusiness, productivity
- webdev, sysadmin, marketing, ecommerce, freelance
- sales, nocode, lowcode, saasmarketing
- **Filter:** 24 pain-point keywords
- **Volume:** 5-15 opps per run

**GitHub (11 repositories):**
- supabase, posthog, n8n, plausible, langchain
- excalidraw, trpc, formbricks, documenso, nocodb, directus
- **Filter:** Issues with reactions ≥2, last 7 days
- **Volume:** 0-5 opps per week

**HackerNews:**
- **Filter:** "Ask HN" posts with keywords or 5+ comments
- **Volume:** 0-3 opps per run

### 2. Processing Layer

**Features:**
- Data validation (schema checks)
- Scoring engine (config-driven, 0-100 points)
- Fuzzy deduplication (75% similarity threshold)
- LLM enhancement (Claude Haiku, opps ≥45 score)
- Domain classification

**Scoring Components:**
- Source credibility (0-20 pts)
- Engagement signals (0-25 pts)
- Pain point clarity (0-20 pts)
- Specificity (0-15 pts)
- Freshness (0-10 pts)
- Niche fit (0-10 pts)

### 3. Delivery Layer

**Daily Digest Format:**
- Top 3 opportunities (formatted for Telegram)
- Score-based ranking
- Source links
- Summary stats

**Delivery Method:**
- Queued in `telegram_outbox/`
- Picked up by OpenClaw heartbeat
- Sent via message tool to Telegram

---

## 📁 Output Formats

### Raw Collection (JSON)
```json
{
  "scan_time": "2026-02-14T21:54:54Z",
  "total_opportunities": 5,
  "sources_scanned": ["SaaS", "Entrepreneur"],
  "opportunities": [
    {
      "source_id": "1r3tube",
      "source": "reddit:SaaS",
      "title": "Recommendations for distribution...",
      "body": "Hey guys. I'm exhausted...",
      "url": "https://reddit.com/r/SaaS/...",
      "published_utc": "2026-02-14T12:00:00",
      "engagement_data": {"keywords": ["tired of"]}
    }
  ]
}
```

### Processed Opportunities (JSONL)
```json
{
  "opportunity_id": "20260214205314-reddit-SaaS-...",
  "source": "reddit:SaaS",
  "title": "...",
  "body": "...",
  "score": 60,
  "domain": "marketing",
  "llm_enhanced": false,
  "processed_at": "2026-02-14T20:53:14Z"
}
```

### Daily Digest (Markdown)
```markdown
# SaaS Opportunities — February 14, 2026

## ⭐ High Potential (Score 60-79)

### 1. Title (Score: 60)
**Source:** reddit:SaaS | **Domain:** marketing
**Link:** https://...

## 💡 Worth Exploring (Score 40-59)
...
```

---

## 🔧 Configuration

### Scoring Config (`scoring_config.json`)

**Current:** v1.4-balanced

Key settings:
- Source weights: GitHub=20, Reddit=8-14, HN=15
- Pain signals: 14 points for strong frustration
- Willingness to pay: 16 points
- LLM threshold: 45 (triggers Claude Haiku enhancement)

### Scoring Profiles Available

- `scoring_config.json` — Balanced (current)
- `scoring_config_aggressive.json` — Higher scores
- `scoring_config_business.json` — B2B focused
- `scoring_config_pain_boost.json` — Pain point emphasis

Switch by updating `scripts/config.py` → `SCORING_CONFIG_PATH`

---

## 📈 Performance (Feb 14, 2026)

### Collection Volume
- Reddit: 40-60 opps/day
- HN: 0-18 opps/day
- GitHub: 0-5 opps/week
- **Total: ~50-70 opps/day**

### Quality Distribution
- High (60+): 1-2% of opportunities
- Medium (40-59): 15-20%
- Low (<40): 78-85%

### System Health
- Collection success rate: >95%
- Validation pass rate: 100%
- Deduplication: ~5% duplicates removed
- LLM triggers: 0 (threshold=45, avg score=35)

---

## 💰 Cost Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| Collection | Reddit RSS, HN API, GitHub API | **$0** |
| Processing | Local Python | **$0** |
| LLM Scoring | OpenRouter (Claude Haiku) | **$0*** |
| Storage | Local files (~15MB) | **$0** |
| **TOTAL** | | **$0/month** |

*LLM not yet triggered (no opportunities reach threshold)

**Budget:** $15/month  
**Used:** $0  
**Available:** 100%

---

## 🔍 Monitoring

Active monitoring since 2026-02-14 22:01 UTC.

**Tracked Metrics:**
- Job success rates
- Collection volume
- Score distribution
- LLM enhancement triggers
- Processing errors

**Review Cycle:** 24 hours

---

## 📖 Documentation

### Core Docs
- **README.md** — This file (setup + overview)
- **ARCHITECTURE.md** — Detailed system design
- **SYSTEM_STATUS.md** — Current operational status

### Analysis Docs
- **PRODUCTION_TEST_RESULTS.md** — System testing results
- **BACKTEST_COMPARISON.md** — Scoring config comparison
- **KEYWORD_INSIGHTS.md** — Source analysis

### Implementation Docs
- **PHASE1_COMPLETE.md** — Collection layer implementation
- **PHASE2_LLM.md** — LLM scoring integration
- **DEPLOY.md** — Deployment guide

---

## 🐛 Known Issues & Limitations

### Current
- **Low scoring:** 79% of opps score <40 (config tuning needed)
- **LLM never triggered:** Threshold=45, but avg score=35
- **Log rotation needed:** Logs growing (minor)

### Resolved
- ✅ GitHub 6h window too narrow → Weekly
- ✅ Rate limit warnings → Threshold adjusted
- ✅ Daily GitHub collection → Changed to weekly
- ✅ Cron automation → All jobs enabled

---

## 🚧 Roadmap

### Short-term (Week 1-2)
- [ ] Tune scoring config (test aggressive profile)
- [ ] Lower LLM threshold to 40
- [ ] Add log rotation
- [ ] Weekly summary reports

### Medium-term (Month 1-2)
- [ ] Semantic deduplication (embeddings)
- [ ] Trend detection across time
- [ ] Product Hunt integration
- [ ] Competitor tracking

### Long-term (Month 3+)
- [ ] ML-based scoring
- [ ] Outcome tracking (which opps became products?)
- [ ] Multi-user support
- [ ] Web dashboard

---

## 🤝 Contributing

To customize for your niche:

1. **Add sources:** Edit `scripts/config.py`
   - `REDDIT_SUBREDDITS` — Add relevant subreddits
   - `GITHUB_REPOSITORIES` — Add relevant repos
   - `REDDIT_PAIN_KEYWORDS` — Add niche keywords

2. **Tune scoring:** Edit `scoring_config.json`
   - Adjust source weights
   - Add pain point phrases
   - Modify thresholds

3. **Adjust collection:** Edit `.env`
   - `COLLECTION_HOURS_BACK` — Reddit/HN lookback
   - `GITHUB_HOURS_BACK` — GitHub lookback

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Credits

**Built with:**
- OpenClaw (autonomous agent framework)
- Python (collection + processing)
- Claude (LLM scoring)

**Data Sources:**
- Reddit (RSS feeds)
- GitHub (Search API)
- Hacker News (Algolia API)

---

**Status:** 🟢 Production | **Monitoring:** Active | **Cost:** $0/month

Built with OpenClaw 🦞
