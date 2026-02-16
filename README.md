# SaaS Hunter 🎯

**Automated SaaS opportunity discovery system** — monitors Reddit, Hacker News, and GitHub to surface validated pain points and unmet market needs.

Built to find profitable SaaS ideas by tracking real developer and entrepreneur complaints, with a focus on signal over noise.

---

## 🚀 What It Does

SaaS Hunter runs on cron, collecting opportunities from:

- **Reddit** — 36 subreddits across business, tech, creative (every 6h)
- **Hacker News** — Ask HN, pain point discussions (every 6h)
- **GitHub** — 23 high-signal repos, feature requests (weekly)

**Scoring: 0-100 points**
- Rule-based (60%): source, engagement, pain keywords, specificity
- LLM-enhanced (40%): Claude Haiku for promising leads (≥45 base score)
- Weekly reviews: automated data quality analysis + recommendations

**Daily digest** via Telegram with top opportunities ranked by score.

---

## 📊 Architecture

```
COLLECT → VALIDATE → SCORE → DEDUPE → DIGEST → DELIVER
(6h)      (LLM opt)  (weekly review)    (daily)  (Telegram)
```

**Files:** JSONL (streamable, append-friendly)  
**Quality:** Automated weekly reviews + continuous expansion  
**Cost:** <$0.01/month (massive headroom)

---

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Reddit API credentials (free)
- GitHub personal access token (free)

### Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Alexeyisme/saas-hunter.git
   cd saas-hunter
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure API credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

   **Note:** You can place `.env` in either:
   - Project root: `/saas-hunter/.env`
   - Scripts directory: `/saas-hunter/scripts/.env` (loaded as fallback/override)

   Required:
   - `GITHUB_TOKEN` — [Create token](https://github.com/settings/tokens)

   Optional:
   - `OPENROUTER_API_KEY` — For LLM-enhanced scoring (Claude Haiku via OpenRouter)
   - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — For Telegram delivery

   **Note:** Reddit and Hacker News use public RSS/API endpoints (no auth needed)

4. **Test collectors:**
   ```bash
   cd scripts
   python3 reddit_monitor.py
   python3 hackernews_monitor.py
   python3 github_monitor.py
   ```

5. **Set up cron jobs:**
   ```bash
   crontab -e
   ```

   Add:
   ```cron
   # Reddit - every 3 hours
   5 */3 * * * cd /path/to/saas-hunter/scripts && /path/to/venv/bin/python3 reddit_monitor.py >> /path/to/saas-hunter/logs/cron_reddit.log 2>&1

   # HackerNews - every 4 hours
   15 */4 * * * cd /path/to/saas-hunter/scripts && /path/to/venv/bin/python3 hackernews_monitor.py >> /path/to/saas-hunter/logs/cron_hn.log 2>&1

   # GitHub - daily at 6 AM
   0 6 * * * cd /path/to/saas-hunter/scripts && /path/to/venv/bin/python3 github_monitor.py >> /path/to/saas-hunter/logs/cron_github.log 2>&1

   # Process - every 6 hours
   25 */6 * * * cd /path/to/saas-hunter/scripts && /path/to/venv/bin/python3 process_opportunities.py >> /path/to/saas-hunter/logs/cron_process.log 2>&1

   # Digest - daily at 8 AM
   0 8 * * * cd /path/to/saas-hunter/scripts && /path/to/venv/bin/python3 generate_digest.py >> /path/to/saas-hunter/logs/cron_digest.log 2>&1
   ```

---

## 📁 Project Structure

```
saas-hunter/
├── scripts/
│   ├── *_monitor.py           # Collectors (Reddit, HN, GitHub)
│   ├── process_opportunities.py  # Validate, score, dedupe
│   ├── validate.py            # Data quality checks
│   ├── llm_scorer.py          # Claude Haiku enhancement
│   ├── weekly_review.py       # Automated quality analysis
│   ├── config.py              # 36 subreddits, 74 keywords, 23 repos
│   └── scoring.py             # Rule-based algorithm
├── data/
│   ├── raw/                   # JSONL collections
│   ├── processed/             # Scored JSONL
│   ├── reports/               # Weekly reviews
│   └── digests/               # Daily summaries
├── scoring_config.json        # Weights, LLM config
├── EXPANSION_PLAN.md          # Phase 1→2→3 roadmap
└── README.md
```

---

## 🎯 Scoring Algorithm

Each opportunity gets a score from **0-100 points**:

| **Factor**               | **Max Points** | **Description**                                  |
|--------------------------|----------------|--------------------------------------------------|
| **Source Credibility**   | 20             | GitHub > HN > Reddit                             |
| **Engagement**           | 25             | Upvotes, comments, reactions                     |
| **Pain Point Clarity**   | 20             | Keywords: "sick of", "frustrated", "hate"        |
| **Specificity**          | 15             | Detailed posts, metrics, numbers                 |
| **Freshness**            | 10             | <6h = 10 pts, <24h = 7 pts, <72h = 4 pts         |
| **Niche Fit**            | 10             | B2B, SaaS, API, dev tools                        |

**Example High-Score Opportunity (92 pts):**
```
Title: "Sick of paying $40/month for Supademo just to make ONE demo"
Source: Reddit r/SaaS
Engagement: 15 upvotes, 8 comments
Pain Signal: "sick of", pricing complaint, specific competitor
Niche: SaaS product demos
```

Configuration: `scoring_config.json`

---

## 📮 Daily Digest Format

```markdown
🎯 SaaS Opportunities — Feb 15, 2026

1. ⭐️ Alternative to Supademo (92 pts)
   📍 reddit:SaaS
   🔗 https://reddit.com/r/SaaS/...

2. ⭐️ Workflow Automation for Non-Developers (85 pts)
   📍 reddit:nocode
   🔗 https://reddit.com/r/nocode/...

3. 💡 Email Management AI (72 pts)
   📍 reddit:SaaS
   🔗 https://reddit.com/r/SaaS/...

📊 39 collected | 2 high quality (60+)
```

Delivered via Telegram to your phone every morning.

---

## 🔧 Configuration

### Tuning the Scoring

Edit `scoring_config.json`:

```json
{
  "pain_keywords": ["sick of", "frustrated", "hate", "tired of"],
  "pay_keywords": ["would pay", "expensive", "pricing"],
  "min_score_threshold": 40,
  "freshness_hours": {
    "high": 6,
    "medium": 24,
    "low": 72
  }
}
```

### Subreddit Filters

Edit `scripts/config.py`:

```python
SUBREDDITS = [
    'SaaS',
    'startups',
    'Entrepreneur',
    'smallbusiness',
    'sales'
]
```

### GitHub Topics

Edit `scripts/config.py`:

```python
GITHUB_TOPICS = [
    'saas',
    'productivity',
    'developer-tools',
    'automation'
]
```

---

## 📄 Data Format

All data files use **JSONL (JSON Lines)** format for consistency and streaming efficiency:

**Raw collection files** (`data/raw/*.jsonl`):

```jsonl
{"_metadata": true, "scan_time": "2026-02-15T18:57:11", "total_opportunities": 8, "method": "RSS"}
{"source_id": "abc123", "source": "reddit:SaaS", "title": "Looking for Zapier alternative", ...}
{"source_id": "def456", "source": "reddit:Entrepreneur", "title": "Frustrated with email tools", ...}
```

**Processed files** (`data/processed/*.jsonl`):

```jsonl
{"source_id": "abc123", "title": "...", "score": 85, "domain": "automation", ...}
{"source_id": "def456", "title": "...", "score": 72, "domain": "communication", ...}
```

**Benefits:**

- ✅ Stream-friendly (process line-by-line)
- ✅ Append-friendly (no need to rewrite entire file)
- ✅ Tool compatible (`jq`, `awk`, `grep`)
- ✅ Parallel processing ready

---

## 🤖 LLM Enhancement (Optional)

Enable AI-powered scoring refinement using Claude Haiku:

1. **Set API key** in `.env`:

   ```bash
   OPENROUTER_API_KEY=your_key_here
   ```

2. **How it works:**
   - Base scoring: Rule-based (always active)
   - LLM enhancement: Kicks in for promising opportunities (score ≥45)
   - Final score: 60% rule-based + 40% LLM adjustment
   - Model: Claude Haiku via OpenRouter (~$0.0003 per opportunity)

3. **Cost tracking:**

   ```bash
   # View usage stats
   sqlite3 data/usage_stats.db "SELECT * FROM token_usage"
   ```

**When to enable:** Improves accuracy for nuanced pain points at ~$3-5/month cost.

---

## 📊 Monitoring

Check collection health:

```bash
# View recent logs
tail -f logs/cron_reddit.log
tail -f logs/cron_process.log

# Check last digest
cat data/digests/digest_$(date +%Y%m%d).md

# Count today's opportunities
wc -l data/processed/opportunities_$(date +%Y%m%d).jsonl
```

---

## 💰 Cost

**Current: $0.0005/week (~$0.002/month)**

- Reddit/HN: RSS/public APIs (free)
- GitHub API: Free tier
- LLM scoring: Claude Haiku via OpenRouter (~5 opps/week enhanced)
- Storage: ~5 MB/day

**Budget:** $15/month target, <1% utilized. Can scale 100x+.

---

## 📈 Current Status (Feb 16, 2026)

**Week 1 baseline:**
- 323 opportunities collected
- 7 high-quality (60+), 0 top-tier (80+)
- Avg score: 36.6
- Phase 1 expansion: 13→36 subreddits, 18→74 keywords, 12→23 repos

**Automated:**
- Weekly reviews (Mondays 9 AM)
- Phase 2 expansion (Feb 23)
- Phase 3 decision (Mar 2)

**Philosophy:** Start broad, refine based on data. See `EXPANSION_PLAN.md`.

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- Built with [PRAW](https://praw.readthedocs.io/) for Reddit
- [feedparser](https://pypi.org/project/feedparser/) for Hacker News RSS
- [PyGithub](https://pygithub.readthedocs.io/) for GitHub API

---

## 📧 Contact

- **Author:** Alexey
- **GitHub:** [@Alexeyisme](https://github.com/Alexeyisme)
- **Project:** [saas-hunter](https://github.com/Alexeyisme/saas-hunter)

---

**Built to help developers find profitable SaaS ideas by listening to what people actually need.**

*Last updated: Feb 16, 2026*
