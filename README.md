# SaaS Hunter

**Automated SaaS opportunity discovery from Reddit, GitHub, and Hacker News.**

🎯 **Mission:** Surface actionable pain points and unmet needs by monitoring public discussions across three high-signal sources.

---

## 📊 Quick Stats

- **Sources:** 12 subreddits, 13 GitHub repos, Ask HN
- **Cost:** $0/month (within free tiers)
- **Collection Window:** 6-24 hours (source-dependent)
- **Last Tested:** 2026-02-08 — ✅ All collectors operational

---

## 🏗️ Architecture

```
saas-hunter/
├── scripts/
│   ├── config.py              # Centralized configuration
│   ├── utils.py               # Shared utilities (dedup, logging, normalization)
│   ├── reddit_monitor.py      # Reddit RSS collector (free)
│   ├── github_monitor.py      # GitHub API collector (authenticated)
│   └── hackernews_monitor.py  # HN Algolia API collector (free)
├── data/
│   ├── raw/                   # Timestamped JSON outputs
│   ├── processed/             # Analyzed/scored opportunities (TBD)
│   └── seen_ids.json          # Persistent duplicate tracking
├── logs/                      # Per-source execution logs
├── venv/                      # Python virtual environment
└── .env                       # API keys and config overrides
```

---

## 🚀 Setup

### 1. Install Dependencies

```bash
cd ~/saas-hunter
python3 -m venv venv
source venv/bin/activate
pip install feedparser requests beautifulsoup4 python-dotenv
```

### 2. Configure Environment

Edit `.env` and add your GitHub token:

```bash
GITHUB_TOKEN=ghp_your_token_here
```

Get a token at: https://github.com/settings/tokens (needs `public_repo` scope)

### 3. Test Collectors

```bash
cd scripts

# Reddit (RSS-based, no auth)
../venv/bin/python3 reddit_monitor.py

# GitHub (requires token)
../venv/bin/python3 github_monitor.py

# Hacker News (free API)
../venv/bin/python3 hackernews_monitor.py
```

---

## ⚙️ Configuration

Edit `.env` to customize:

```bash
# Collection Windows
COLLECTION_HOURS_BACK=6      # Reddit & HN lookback
GITHUB_HOURS_BACK=24         # GitHub lookback (wider window)

# Scoring & Filtering
MIN_OPPORTUNITY_SCORE=50     # Minimum score to include
DIGEST_TOP_N=5               # Top N for daily digest
```

Edit `scripts/config.py` for:
- **Subreddits:** `REDDIT_SUBREDDITS` list
- **GitHub repos:** `GITHUB_REPOSITORIES` list
- **Keywords:** `REDDIT_PAIN_KEYWORDS`, `HN_ASK_KEYWORDS`

---

## 📅 Cron Schedule (Recommended)

**Optimized for signal quality and API efficiency:**

```cron
# Reddit - every 3 hours (free, high volume)
0 */3 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 reddit_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1

# Hacker News - every 4 hours (free, moderate volume)
0 */4 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 hackernews_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1

# GitHub - daily at 6 AM (1-week lookback, dedup handles overlaps)
0 6 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 github_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1
```

**Why weekly GitHub?** Testing showed 24-hour windows yield 0 results. Weekly collection with reactions:>2 produces 2-4 quality opportunities.

---

## 📁 Output Format

All collectors produce normalized JSON:

```json
{
  "scan_time": "2026-02-08T17:06:57.008655",
  "total_opportunities": 18,
  "sources_scanned": ["SaaS", "Entrepreneur", "..."],
  "method": "RSS (no API)",
  "hours_back": 6,
  "opportunities": [
    {
      "source_id": "1qzd3na",
      "source": "reddit:SaaS",
      "title": "Looking for marketing/account conversion advice",
      "body": "Been working in my industry for 20 years...",
      "url": "https://www.reddit.com/r/SaaS/comments/...",
      "published_utc": "2026-02-08T16:18:37",
      "engagement_data": {
        "keywords": ["pain point"]
      },
      "collected_at": "2026-02-08T17:06:36.959610"
    }
  ]
}
```

---

## 🔍 Data Sources

### Reddit (RSS)
- **Subreddits:** r/SaaS, r/Entrepreneur, r/startups, r/smallbusiness, r/productivity, r/webdev, r/sysadmin, r/marketing, r/ecommerce, r/nocode, r/lowcode, r/saasmarketing
- **Filter:** 24 pain-point keywords ("looking for a tool", "frustrated with", "willing to pay", etc.)
- **Cost:** Free

### GitHub (Search API)
- **Repos:** supabase, posthog, n8n, plausible, langchain, excalidraw, trpc, formbricks, documenso, nocodb, directus
- **Filter:** Issues with reactions:>2, created in last 7 days (reactions = validation)
- **Collection:** Weekly (reactions need time to accumulate)
- **Cost:** Free (5,000 req/hour authenticated)

### Hacker News (Algolia)
- **Filter:** "Ask HN" posts matching 20 keywords OR >5 comments
- **Lookback:** 6 hours
- **Cost:** Free

---

## 📊 Typical Results

| Source | Frequency | Window | Opportunities | Time |
|--------|-----------|--------|--------------|------|
| Reddit | Every 3h | 6h | 15-25/day | ~20s |
| HN | Every 4h | 6h | 3-8/day | <1s |
| GitHub | Weekly | 7d | 2-4/week | ~45s |
| **Total** | | | **~30/day** | |

---

## 🔧 Utilities

### Duplicate Detection
- Persistent across runs via `data/seen_ids.json`
- Format: `{source}:{source_id}` (e.g., `reddit:SaaS:1qzd3na`)

### Logging
- Per-source logs in `logs/`
- Console + file output
- Includes rate limit tracking, error handling

### Normalization
- All sources → consistent schema
- HTML cleaning for Reddit
- Truncation to 500 chars

---

## 🛠️ Next Steps

1. **Processing pipeline:** Score/rank opportunities
2. **Digest generator:** Daily top-N summaries
3. **Notification:** Telegram integration for high-value finds
4. **Analysis:** Clustering by problem domain
5. **Validation:** Track which opportunities become real products

---

## 📖 Documentation

- **EVALUATION.md** — Full test results and analysis
- **scripts/config.py** — All configurable settings
- **.env.example** — Template for environment variables

---

## 💰 Cost Breakdown

| Service | API | Rate Limit | Monthly Cost |
|---------|-----|------------|--------------|
| Reddit RSS | None | Unlimited | **$0** |
| GitHub API | Token | 5,000/hr | **$0** |
| HN Algolia | None | Generous | **$0** |
| **TOTAL** | | | **$0** |

**Budget:** $15/month  
**Headroom:** 100% available for expansion

---

## 🐛 Known Issues

1. ~~GitHub 6-hour window too narrow~~ ✅ **Fixed:** Now weekly (168 hours)
2. ~~Rate limit warning at 500~~ ✅ **Fixed:** Threshold lowered to 10
3. ~~GitHub daily collection yields 0 results~~ ✅ **Fixed:** Changed to weekly with reactions:>2
4. Reddit engagement data missing (RSS limitation) — Low priority

---

## 🤝 Contributing

To customize for your niche:
1. Edit subreddits in `config.py`
2. Add niche GitHub repos
3. Expand keyword lists
4. Adjust time windows in `.env`

---

**Built with OpenClaw 🦞**
