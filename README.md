# SaaS Hunter 🎯

**Automated SaaS opportunity discovery system** — monitors Reddit, Hacker News, and GitHub to surface validated pain points and unmet market needs.

Built to find profitable SaaS ideas by tracking real developer and entrepreneur complaints, with a focus on signal over noise.

---

## 🚀 What It Does

SaaS Hunter runs on cron, collecting opportunities from:

- **Reddit** — r/SaaS, r/startups, r/Entrepreneur, r/smallbusiness, r/sales (every 3h)
- **Hacker News** — Show HN, Ask HN, trending discussions (every 4h)
- **GitHub** — Trending repos, highly-reacted issues (daily)

Each opportunity is **scored 0-100** based on:
- Source credibility
- Engagement (upvotes, comments, reactions)
- Pain point clarity ("sick of", "frustrated")
- Specificity (detailed problems > vague complaints)
- Freshness (recent = higher score)
- Niche fit (B2B SaaS, developer tools)

**Daily digest** delivered via Telegram at 8 AM UTC with top opportunities ranked and categorized.

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ COLLECTION (Cron)                                           │
│  Reddit (3h) → HN (4h) → GitHub (daily)                    │
│  Output: data/raw/SOURCE_YYYYMMDD_HHMMSS.json              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ PROCESSING (Every 6h)                                       │
│  1. Load new raw files                                      │
│  2. Score each opportunity (0-100)                          │
│  3. Deduplicate across sources                              │
│  4. Enrich with metadata                                    │
│  Output: data/processed/opportunities_YYYYMMDD.jsonl        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ AGGREGATION (Daily 8 AM)                                    │
│  1. Load last 24h opportunities                             │
│  2. Rank by score                                           │
│  3. Group by domain                                         │
│  4. Generate digest                                         │
│  Output: data/digests/digest_YYYYMMDD.md                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ DELIVERY                                                     │
│  Telegram bot → top 3-5 opportunities                       │
│  (via OpenClaw heartbeat polling)                           │
└─────────────────────────────────────────────────────────────┘
```

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

   Required:
   - `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — [Get here](https://www.reddit.com/prefs/apps)
   - `GITHUB_TOKEN` — [Create token](https://github.com/settings/tokens)

   Optional (Hacker News is public, no auth needed):
   - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — for delivery

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
│   ├── reddit_monitor.py          # Reddit collector
│   ├── hackernews_monitor.py      # HN collector
│   ├── github_monitor.py          # GitHub collector
│   ├── process_opportunities.py   # Scoring + deduplication
│   ├── generate_digest.py         # Daily aggregation
│   ├── send_telegram_openclaw.py  # Telegram delivery
│   ├── config.py                  # Shared configuration
│   ├── scoring.py                 # Scoring algorithm
│   └── utils.py                   # Helper functions
├── data/
│   ├── raw/                       # Collected JSON files
│   ├── processed/                 # Scored opportunities (JSONL)
│   ├── digests/                   # Daily markdown summaries
│   ├── telegram_outbox/           # Pending Telegram messages
│   └── seen_ids.json              # Deduplication tracking
├── logs/                          # Cron execution logs
├── scoring_config.json            # Scoring weights/thresholds
├── .env                           # API credentials (git-ignored)
├── .env.example                   # Template for credentials
└── README.md                      # This file
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

**Current setup: $0/month**

- Reddit API: Free tier (60 requests/min)
- GitHub API: Free tier (5,000 requests/hour)
- Hacker News: Public RSS, no auth
- Storage: ~5 MB/day (~150 MB/month)
- Compute: Runs on your server/VPS

Designed to fit within a **$15/month** budget if you add paid features later (e.g., OpenAI for clustering).

---

## 📈 Example Output

**Real digest from Feb 15, 2026:**

- **39 opportunities** collected
- **2 high-quality** (60+ score)
- **10 worth exploring** (40-59 score)

Top find:
> "6 years in sales, moving to SF in 5 months. How would you approach this?" (65.8 pts)  
> Signal: Career transition pain point, location-specific networking needs

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

**Areas for improvement:**
- Better deduplication (ML-based clustering)
- Domain classification (auto-categorize by industry)
- Sentiment analysis (detect urgency/willingness to pay)
- Web dashboard for browsing opportunities

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

*Last updated: Feb 15, 2026*
