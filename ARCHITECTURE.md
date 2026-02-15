# SaaS Hunter - System Architecture

**Version:** 1.0  
**Last Updated:** 2026-02-15

---

## Overview

SaaS Hunter is a 4-layer pipeline system that transforms raw social media data into actionable SaaS opportunities.

**Design Goals:**
- **Signal over noise** — only surface high-quality, validated pain points
- **Cost-efficient** — free APIs, minimal compute
- **Transparent scoring** — every score is explainable
- **Modular** — each layer can run independently

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: COLLECTION (Cron-triggered)                           │
│                                                                 │
│  Reddit Monitor (every 3h)                                     │
│    └─→ raw/reddit_YYYYMMDD_HHMMSS.json                        │
│                                                                 │
│  HackerNews Monitor (every 4h)                                 │
│    └─→ raw/hackernews_YYYYMMDD_HHMMSS.json                    │
│                                                                 │
│  GitHub Monitor (daily 6 AM)                                   │
│    └─→ raw/github_YYYYMMDD_HHMMSS.json                        │
│                                                                 │
│  Deduplication: seen_ids.json                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: PROCESSING (Every 6h)                                 │
│                                                                 │
│  process_opportunities.py                                       │
│    1. Load new raw files since last run                        │
│    2. Score each opportunity (0-100)                            │
│       - Source credibility (20 pts)                             │
│       - Engagement metrics (25 pts)                             │
│       - Pain point clarity (20 pts)                             │
│       - Specificity (15 pts)                                    │
│       - Freshness (10 pts)                                      │
│       - Niche fit (10 pts)                                      │
│    3. Deduplicate across sources (fuzzy matching)              │
│    4. Enrich with metadata (domain, competitors)               │
│    5. Filter (min score 40)                                     │
│                                                                 │
│  Output: processed/opportunities_YYYYMMDD.jsonl                │
│          (one opportunity per line)                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: AGGREGATION (Daily 8 AM UTC)                          │
│                                                                 │
│  generate_digest.py                                             │
│    1. Load last 24h of processed opportunities                 │
│    2. Rank by score (descending)                                │
│    3. Group by problem domain                                   │
│    4. Format as markdown                                        │
│       - Top tier (60+): Full analysis                           │
│       - Worth exploring (40-59): Brief summary                  │
│       - Trends: Keyword patterns, domain distribution           │
│                                                                 │
│  Output: digests/digest_YYYYMMDD.md                            │
│          telegram_outbox/digest_latest.txt (symlink)            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: DELIVERY                                               │
│                                                                 │
│  send_telegram_openclaw.py (triggered after digest)            │
│    - Reads telegram_outbox/digest_latest.txt                   │
│    - Sends via OpenClaw message tool                           │
│    - Renames to .sent to prevent re-sending                    │
│                                                                 │
│  Alternative: OpenClaw heartbeat polling (every ~30 min)       │
│    - Checks for new digest_latest.txt                          │
│    - Auto-sends when detected                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Collection

### Purpose
Continuously gather raw opportunities from multiple sources.

### Components

#### Reddit Monitor
- **Script:** `reddit_monitor.py`
- **Frequency:** Every 3 hours (8x/day)
- **Subreddits:** r/SaaS, r/startups, r/Entrepreneur, r/smallbusiness, r/sales
- **Filter:** Posts from last 24h, min 3 upvotes
- **API:** PRAW (Reddit API wrapper)
- **Output:** `data/raw/reddit_YYYYMMDD_HHMMSS.json`

**Example Output:**
```json
{
  "source": "reddit",
  "subreddit": "SaaS",
  "collected_at": "2026-02-15T06:05:23Z",
  "count": 12,
  "opportunities": [
    {
      "id": "1r4xh7c",
      "title": "6 years in sales, moving to SF...",
      "url": "https://reddit.com/r/sales/...",
      "author": "username",
      "upvotes": 15,
      "num_comments": 8,
      "body": "Full post text...",
      "created_utc": "2026-02-15T04:23:10Z"
    }
  ]
}
```

#### HackerNews Monitor
- **Script:** `hackernews_monitor.py`
- **Frequency:** Every 4 hours (6x/day)
- **Sources:** Show HN, Ask HN, trending stories
- **Filter:** Min 5 points, posted in last 48h
- **API:** HN RSS feed + Algolia API
- **Output:** `data/raw/hackernews_YYYYMMDD_HHMMSS.json`

#### GitHub Monitor
- **Script:** `github_monitor.py`
- **Frequency:** Daily at 6 AM UTC
- **Targets:** 
  - Trending repos (topics: saas, productivity, developer-tools)
  - Issues with 5+ reactions
- **API:** PyGithub (GitHub API v3)
- **Output:** `data/raw/github_YYYYMMDD_HHMMSS.json`

### Deduplication
- **File:** `data/seen_ids.json`
- **Strategy:** Track unique IDs (reddit post ID, HN item ID, GitHub issue number)
- **Purpose:** Avoid re-collecting same item across runs

---

## Layer 2: Processing

### Purpose
Score, deduplicate, and enrich raw opportunities.

### Script
`process_opportunities.py`

### Execution
Every 6 hours (at :25 past the hour, staggered after collections)

### Pipeline

#### 1. Load New Files
```python
last_run = load_last_run_time()  # from state file
raw_files = find_files_since(last_run, 'data/raw/')
all_opportunities = []
for file in raw_files:
    opps = json.load(file)['opportunities']
    all_opportunities.extend(opps)
```

#### 2. Score Each Opportunity
```python
for opp in all_opportunities:
    score = 0
    
    # Source credibility (20 pts)
    if source == 'github':
        score += 20
    elif source == 'hackernews':
        score += 15
    elif source.startswith('reddit:'):
        score += 10
    
    # Engagement (25 pts max)
    score += min(reactions * 2, 15)      # GitHub reactions
    score += min(comments, 10)            # Any source
    score += min(hn_score, 10)            # HN points
    
    # Pain point clarity (20 pts)
    text = (title + body).lower()
    if 'sick of' in text or 'frustrated' in text:
        score += 10
    if 'would pay' in text or 'expensive' in text:
        score += 10
    
    # Specificity (15 pts)
    if len(body) > 300:
        score += 10
    if has_numbers(body):
        score += 5
    
    # Freshness (10 pts)
    age_hours = hours_since(published_utc)
    if age_hours < 6:
        score += 10
    elif age_hours < 24:
        score += 7
    elif age_hours < 72:
        score += 4
    
    # Niche fit (10 pts)
    if any(kw in text for kw in ['b2b', 'saas', 'api']):
        score += 10
    
    opp['score'] = min(score, 100)
```

#### 3. Deduplicate
```python
def deduplicate(opportunities):
    """Remove duplicates across sources"""
    unique = []
    seen_titles = set()
    
    for opp in sorted(opportunities, key=lambda x: -x['score']):
        title_core = extract_keywords(opp['title'])
        
        if not fuzzy_match(title_core, seen_titles, threshold=0.85):
            unique.append(opp)
            seen_titles.add(title_core)
    
    return unique
```

#### 4. Enrich
```python
for opp in opportunities:
    opp['opportunity_id'] = generate_id(opp)
    opp['domain'] = classify_domain(opp)  # e.g., "design", "productivity"
    opp['competitors'] = extract_competitors(opp['body'])
    opp['processed_at'] = datetime.now().isoformat()
```

#### 5. Filter & Save
```python
MIN_SCORE = 40
filtered = [o for o in opportunities if o['score'] >= MIN_SCORE]

with open(f'data/processed/opportunities_{today}.jsonl', 'a') as f:
    for opp in filtered:
        f.write(json.dumps(opp) + '\n')
```

### Output Format (JSONL)
```json
{"opportunity_id":"2026-02-15-reddit-saas-001","source":"reddit:SaaS","title":"Alternative to Supademo","score":92,"domain":"design","competitors":["Supademo","Arcade"],"processed_at":"2026-02-15T06:25:00Z"}
{"opportunity_id":"2026-02-15-reddit-nocode-002","source":"reddit:nocode","title":"Better workflow automation","score":85,"domain":"productivity","competitors":["Zapier","Make"],"processed_at":"2026-02-15T06:25:00Z"}
```

---

## Layer 3: Aggregation

### Purpose
Create human-readable daily summary.

### Script
`generate_digest.py`

### Execution
Daily at 8:00 AM UTC

### Process

#### 1. Load Last 24h
```python
today = datetime.now().date()
yesterday = today - timedelta(days=1)

opportunities = []
for date in [yesterday, today]:
    file = f'data/processed/opportunities_{date.strftime("%Y%m%d")}.jsonl'
    if exists(file):
        with open(file) as f:
            opportunities.extend([json.loads(line) for line in f])
```

#### 2. Rank & Group
```python
# Sort by score
opportunities.sort(key=lambda x: -x['score'])

# Group by domain
by_domain = defaultdict(list)
for opp in opportunities:
    by_domain[opp['domain']].append(opp)

# Tier by score
top_tier = [o for o in opportunities if o['score'] >= 60]
worth_exploring = [o for o in opportunities if 40 <= o['score'] < 60]
```

#### 3. Generate Markdown
```python
digest = f"# SaaS Opportunities — {today.strftime('%B %d, %Y')}\n\n"
digest += f"**Summary:** {len(opportunities)} opportunities collected\n\n"
digest += "---\n\n"

# Top tier
digest += "## ⭐ High Potential (Score 60-79)\n\n"
for opp in top_tier[:10]:
    digest += f"### {i}. {opp['title']} (Score: {opp['score']})\n"
    digest += f"**Source:** {opp['source']}\n"
    digest += f"**Link:** {opp['url']}\n\n"

# Worth exploring
digest += "## 💡 Worth Exploring (Score 40-59)\n\n"
for opp in worth_exploring:
    digest += f"- **{opp['title']}** ({opp['score']} pts) — {opp['source']}\n"

# Trends
digest += "\n## 📊 Trends\n\n"
digest += f"**By Domain:**\n"
for domain, opps in by_domain.items():
    digest += f"- {domain}: {len(opps)} opportunities\n"
```

#### 4. Save & Symlink
```python
digest_file = f'data/digests/digest_{today.strftime("%Y%m%d")}.md'
with open(digest_file, 'w') as f:
    f.write(digest)

# Create symlink for Telegram delivery
outbox = 'data/telegram_outbox/digest_latest.txt'
if exists(outbox):
    os.remove(outbox)
os.symlink(digest_file, outbox)
```

### Output Example
See [Example Digest](data/digests/digest_20260215.md)

---

## Layer 4: Delivery

### Purpose
Push daily digest to user's phone.

### Method 1: Direct Send (Post-Digest)
```bash
# In crontab, chained with digest generation
0 8 * * * ... generate_digest.py && send_telegram_openclaw.py
```

`send_telegram_openclaw.py`:
```python
def send_digest():
    latest = 'data/telegram_outbox/digest_latest.txt'
    
    if not exists(latest):
        print("No digest to send")
        return
    
    with open(latest) as f:
        text = f.read()
    
    # Send via OpenClaw message tool
    subprocess.run([
        'openclaw', 'message', 'send',
        '--channel', 'telegram',
        '--to', '1153284',
        '--message', text
    ])
    
    # Mark as sent
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.rename(latest, f'data/telegram_outbox/digest_{timestamp}.sent')
```

### Method 2: OpenClaw Heartbeat (Polling)
OpenClaw agent checks `telegram_outbox/` every ~30 min:
```python
# In HEARTBEAT.md
if exists('telegram_outbox/digest_latest.txt'):
    message.send(channel='telegram', target='1153284', text=read_file(...))
    rename_to_sent()
```

### Telegram Format
```
🎯 SaaS Opportunities — Feb 15, 2026

1. ⭐️ Alternative to Supademo (92 pts)
   📍 reddit:SaaS
   🔗 https://reddit.com/r/SaaS/...

2. ⭐️ Workflow Automation (85 pts)
   📍 reddit:nocode
   🔗 ...

📊 39 collected | 2 high quality (60+)

Full digest: ~/saas-hunter/data/digests/
```

---

## Data Flow Example

**Timeline: Feb 15, 2026**

| Time  | Event | Output |
|-------|-------|--------|
| 00:05 | Reddit run #1 | `reddit_20260215_000523.json` (4 opps) |
| 03:05 | Reddit run #2 | `reddit_20260215_030523.json` (3 opps) |
| 04:15 | HN run | `hackernews_20260215_041502.json` (2 opps) |
| 06:00 | GitHub run | `github_20260215_060037.json` (5 opps) |
| 06:25 | **Processor** | Loads 14 opps → scores → dedupes → saves `opportunities_20260215.jsonl` (12 unique) |
| 08:00 | **Digest generator** | Reads 12 opps → ranks → generates `digest_20260215.md` |
| 08:00 | **Telegram send** | Reads digest → sends top 3 → renames to `.sent` |
| 09:05 | Reddit run #3 | `reddit_20260215_090523.json` (6 opps) |
| ... | ... | ... |
| 18:25 | **Processor** | Loads opps from 06:00-18:00 → scores → appends to JSONL |

---

## File Retention Policy

| Directory | Retention | Reason |
|-----------|-----------|--------|
| `data/raw/` | 7 days | Archive after 1 week (compress with gzip) |
| `data/processed/` | 30 days | Compress after 1 month |
| `data/digests/` | Forever | Small text files, useful for historical analysis |
| `data/seen_ids.json` | Forever | Needed for deduplication |
| `logs/` | 30 days | Rotate monthly |

**Cleanup script (run weekly):**
```bash
find data/raw -name "*.json" -mtime +7 -exec gzip {} \;
find data/processed -name "*.jsonl" -mtime +30 -exec gzip {} \;
find logs -name "*.log" -mtime +30 -delete
```

---

## Configuration Files

### `scoring_config.json`
```json
{
  "source_weights": {
    "github": 20,
    "hackernews": 15,
    "reddit": 10
  },
  "engagement_weights": {
    "reactions_multiplier": 2,
    "comments_max": 10,
    "score_max": 10
  },
  "pain_keywords": [
    "sick of",
    "frustrated",
    "hate",
    "tired of"
  ],
  "pay_keywords": [
    "would pay",
    "expensive",
    "pricing"
  ],
  "min_score_threshold": 40,
  "freshness_hours": {
    "high": 6,
    "medium": 24,
    "low": 72
  }
}
```

### `scripts/config.py`
```python
SUBREDDITS = ['SaaS', 'startups', 'Entrepreneur', 'smallbusiness', 'sales']
GITHUB_TOPICS = ['saas', 'productivity', 'developer-tools', 'automation']
MIN_REDDIT_UPVOTES = 3
MIN_HN_SCORE = 5
MIN_GITHUB_REACTIONS = 5
```

---

## Performance Metrics

### Collection Health (Daily)
```json
{
  "date": "2026-02-15",
  "collected": {
    "reddit": 32,
    "hackernews": 12,
    "github": 5,
    "total": 49
  },
  "processed": {
    "total": 49,
    "deduplicated": 39,
    "scored_60plus": 2
  },
  "avg_score": 52.3
}
```

### API Usage
- Reddit: ~60 requests/day (well within 60/min limit)
- GitHub: ~20 requests/day (well within 5,000/hour limit)
- HN: RSS feed, no rate limit

### Storage Growth
- Raw JSON: ~1-2 MB/day
- Processed JSONL: ~500 KB/day
- Digests: ~5 KB/day
- **Total: ~3 MB/day (~90 MB/month)**

---

## Error Handling

### Collection Failures
- **Network errors:** Retry with exponential backoff (3 attempts)
- **API rate limits:** Log warning, skip run, resume next cycle
- **Invalid responses:** Log error, continue with partial data

### Processing Failures
- **Missing raw files:** Skip, log warning
- **Corrupt JSON:** Skip file, log error, continue with others
- **Scoring errors:** Default to score=0, flag for review

### Delivery Failures
- **Telegram API down:** Keep digest in outbox, retry on next heartbeat
- **Message too long:** Truncate to top 3 opportunities

---

## Monitoring & Alerts

### Daily Health Check
```bash
# Check last digest was generated
test -f data/digests/digest_$(date +%Y%m%d).md || echo "⚠️ No digest today"

# Check opportunity count
wc -l data/processed/opportunities_$(date +%Y%m%d).jsonl

# Check cron logs for errors
tail -100 logs/cron_*.log | grep -i error
```

### Alert Thresholds
- No opportunities collected for >12h → Alert
- No digest generated by 9 AM → Alert
- Avg score drops below 30 → Review filters

---

## Future Enhancements

### Phase 2: ML-Based Improvements
- **Clustering:** Group similar opportunities (ML embeddings)
- **Sentiment analysis:** Detect urgency/willingness to pay
- **Competitor extraction:** NER model to find mentioned products

### Phase 3: Analytics Dashboard
- Web UI for browsing opportunities
- Trend charts (domains over time)
- Search/filter by keyword, domain, score

### Phase 4: Feedback Loop
- Track which opportunities you act on
- Retrain scoring model based on your picks
- Personalized score weights

---

## Technical Decisions

### Why File-Based Storage?
- **Simple:** No database to manage
- **Portable:** Easy to backup, migrate
- **Debuggable:** Human-readable JSON/JSONL
- **Cheap:** Zero cost vs database hosting

### Why JSONL for Processed?
- **Append-friendly:** Add new opportunities throughout the day
- **Grep-able:** `grep '"score":9' opportunities.jsonl`
- **Line-by-line processing:** Stream large files without loading all into memory

### Why Cron vs Real-Time?
- **Cost:** No need for 24/7 server process
- **Focus:** Daily digest > live feed
- **Simplicity:** Standard Unix tooling, no message queue needed

---

## Dependencies

See `requirements.txt`:
```
praw>=7.0.0              # Reddit API
feedparser>=6.0.0        # HN RSS
PyGithub>=1.55           # GitHub API
requests>=2.28.0         # HTTP client
beautifulsoup4>=4.11.0   # HTML parsing
python-dotenv>=0.20.0    # .env loading
```

---

**Questions?** Open an issue on [GitHub](https://github.com/Alexeyisme/saas-hunter).
