# SaaS Hunter - Complete Architecture

**Design Goal:** Transform raw opportunities into actionable, prioritized insights ready for decision-making.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ COLLECTION LAYER (Cron Jobs)                                   │
│  Reddit (3h) → raw/reddit_YYYYMMDD_HHMMSS.json                 │
│  HN (4h)     → raw/hackernews_YYYYMMDD_HHMMSS.json            │
│  GitHub (7d) → raw/github_YYYYMMDD_HHMMSS.json                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ PROCESSING LAYER (Triggered after collection)                  │
│  1. Load new raw files                                         │
│  2. Score each opportunity (0-100)                             │
│  3. Deduplicate across sources                                 │
│  4. Enrich with metadata                                       │
│  5. Save to processed/opportunities_YYYYMMDD.jsonl             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGGREGATION LAYER (Daily digest)                               │
│  1. Load last 24h processed opportunities                      │
│  2. Group by problem domain                                    │
│  3. Rank by score + freshness                                  │
│  4. Generate daily digest (top 5-10)                           │
│  5. Save to digests/digest_YYYYMMDD.md                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ DELIVERY LAYER                                                  │
│  • Telegram message (top 3 daily)                              │
│  • Web dashboard (optional)                                     │
│  • JSONL export for analysis                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Collection Layer (Current)

### Files Structure
```
~/saas-hunter/
├── data/
│   ├── raw/                    # Raw collector output
│   │   ├── reddit_20260208_120000.json
│   │   ├── github_20260208_060000.json
│   │   └── hackernews_20260208_140000.json
│   ├── processed/              # Scored + enriched
│   │   └── opportunities_20260208.jsonl
│   ├── digests/                # Daily summaries
│   │   └── digest_20260208.md
│   └── seen_ids.json           # Deduplication
```

### Cron Schedule
```cron
# Reddit: Every 3 hours (8 collections/day)
0 */3 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 reddit_monitor.py

# HN: Every 4 hours (6 collections/day)
0 */4 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 hackernews_monitor.py

# GitHub: Weekly (Sundays at 6 AM)
0 6 * * 0 cd ~/saas-hunter/scripts && ../venv/bin/python3 github_monitor.py

# Process: Every 6 hours (or after each GitHub run)
30 */6 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 process_opportunities.py

# Digest: Daily at 8 AM
0 8 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 generate_digest.py
```

---

## 2. Processing Layer (New)

### Script: `process_opportunities.py`

**Purpose:** Score, deduplicate, and enrich raw opportunities

**Input:** All raw JSON files since last run  
**Output:** `processed/opportunities_YYYYMMDD.jsonl` (one line per opportunity)

### Scoring Algorithm (0-100 points)

```python
def score_opportunity(opp):
    score = 0
    
    # 1. Source credibility (max 20 points)
    if opp['source'].startswith('github:'):
        score += 20  # Validated by reactions
    elif opp['source'] == 'hackernews':
        score += 15  # Tech-savvy audience
    elif opp['source'].startswith('reddit:'):
        score += 10  # Varies by subreddit
    
    # 2. Engagement (max 25 points)
    engagement = opp.get('engagement_data', {})
    
    # GitHub reactions
    reactions = engagement.get('reactions', 0)
    score += min(reactions * 2, 15)
    
    # Comments (any source)
    comments = engagement.get('comments', 0)
    score += min(comments, 10)
    
    # HN score
    hn_score = engagement.get('score', 0)
    score += min(hn_score, 10)
    
    # 3. Pain point clarity (max 20 points)
    text = (opp['title'] + ' ' + opp['body']).lower()
    
    # Strong pain indicators
    if any(p in text for p in ['sick of', 'frustrated', 'hate']):
        score += 10
    
    # Willingness to pay signals
    if any(p in text for p in ['would pay', 'expensive', 'pricing']):
        score += 10
    
    # 4. Specificity (max 15 points)
    # Longer, detailed posts = more specific problem
    if len(opp['body']) > 300:
        score += 10
    elif len(opp['body']) > 150:
        score += 5
    
    # Contains numbers/metrics
    if any(char.isdigit() for char in opp['body']):
        score += 5
    
    # 5. Freshness (max 10 points)
    from datetime import datetime, timedelta
    pub_date = datetime.fromisoformat(opp['published_utc'].replace('Z', '+00:00'))
    age_hours = (datetime.now() - pub_date).total_seconds() / 3600
    
    if age_hours < 6:
        score += 10
    elif age_hours < 24:
        score += 7
    elif age_hours < 72:
        score += 4
    
    # 6. Niche fit (max 10 points)
    # B2B, SaaS, developer tools
    if any(kw in text for kw in ['b2b', 'saas', 'api', 'dev tool']):
        score += 10
    
    return min(score, 100)
```

### Deduplication Strategy

**Problem:** Same opportunity appears across sources
- Reddit post → HN discussion → GitHub issue

**Solution:** Fuzzy matching + domain clustering

```python
def deduplicate_opportunities(opps):
    clusters = []
    
    for opp in opps:
        # Extract core concept
        core = extract_keywords(opp['title'])
        
        # Find matching cluster
        match = find_similar_cluster(core, clusters)
        
        if match:
            # Keep highest-scored version
            if opp['score'] > match['score']:
                clusters[idx] = opp
        else:
            clusters.append(opp)
    
    return clusters
```

### Enrichment

Add computed fields:
```python
{
    "opportunity_id": "2026-02-08-reddit-saas-001",
    "score": 78,
    "age_hours": 12,
    "domain": "project-management",  # clustering
    "competitors": ["Asana", "Linear"],  # extracted
    "processed_at": "2026-02-08T18:00:00Z"
}
```

---

## 3. Aggregation Layer (New)

### Script: `generate_digest.py`

**Purpose:** Create human-readable daily summary

**Input:** Last 24h of processed opportunities  
**Output:** `digests/digest_YYYYMMDD.md`

### Digest Format

```markdown
# SaaS Opportunities — Feb 8, 2026

**Summary:** 24 opportunities collected, 12 processed, 5 top-tier

---

## 🔥 Top Opportunities (Score 80+)

### 1. Alternative to Supademo for Product Demos (Score: 92)
**Source:** Reddit r/SaaS  
**Pain Point:** "Sick of paying $40/month for Supademo just to make ONE demo"  
**Signal:** 15 upvotes, multiple comments validating pain  
**Market:** One-time payment for demo creation  
**Competition:** Supademo ($40/mo), Arcade ($50/mo)  
**Link:** https://reddit.com/r/SaaS/...

**Why High Score:**
- Clear frustration with pricing model
- Specific competitor mentioned
- Willing to pay signal
- Active discussion

---

### 2. Workflow Automation for Non-Developers (Score: 85)
**Source:** Reddit r/nocode  
**Pain Point:** "Need something better than Zapier for complex workflows"  
**Signal:** 8 comments, users sharing workarounds  
**Market:** Visual workflow builder with conditionals  
**Competition:** Zapier, Make, n8n (too technical)  
**Link:** https://reddit.com/r/nocode/...

---

## 💡 Worth Exploring (Score 60-79)

- **Email Management AI** (Score: 72) — "Tired of 20+ daily emails"
- **Spreadsheet UX for B2B** (Score: 68) — Better than Excel for wholesale
- **Canadian Tax Calculator** (Score: 65) — HN developer asking for data source

---

## 📊 Trends (Last 7 Days)

- **Subscription fatigue:** 5 mentions (pricing pain point)
- **AI integration:** 8 mentions (automation opportunity)
- **Spreadsheet alternatives:** 4 mentions (B2B workflow)

---

**Collected:** 24 total | **Processed:** 12 after dedup | **Top Tier:** 5

Generated: 2026-02-08 08:00 UTC
```

---

## 4. Delivery Layer

### Option A: Telegram Bot (Recommended)

**Daily message at 8 AM:**
```
🎯 SaaS Opportunities — Feb 8

Top 3 Today:

1. ⭐️ Alternative to Supademo (92 pts)
   💰 "Sick of paying $40/month for ONE demo"
   📍 Reddit r/SaaS, 15 upvotes
   🔗 reddit.com/r/SaaS/...

2. ⭐️ Workflow Automation (85 pts)
   💰 "Better than Zapier for complex workflows"
   📍 Reddit r/nocode, 8 comments
   
3. 💡 Email Management AI (72 pts)
   📍 Reddit r/SaaS, "20+ emails daily"

📊 24 collected | 12 processed | 5 top-tier

View full digest: /digest
```

### Option B: Web Dashboard (Future)

Simple HTML page with:
- Today's opportunities (scored)
- Weekly trends
- Search/filter by domain
- Export to CSV

---

## 5. Data Flow Example

### Day in the Life (Feb 8, 2026)

**00:00** - Reddit collector runs → 4 opportunities  
**03:00** - Reddit collector runs → 3 opportunities  
**04:00** - HN collector runs → 1 opportunity  
**06:00** - Reddit collector runs → 5 opportunities  
**06:00** - GitHub collector runs (Sunday) → 2 opportunities  
**06:30** - Processor runs:
  - Loads 15 raw opportunities
  - Scores each (0-100)
  - Deduplicates → 12 unique
  - Saves to `processed/opportunities_20260208.jsonl`

**08:00** - Digest generator runs:
  - Loads processed file
  - Ranks by score
  - Groups by domain
  - Generates `digests/digest_20260208.md`

**08:01** - Telegram delivery:
  - Reads digest
  - Formats top 3
  - Sends message to you

**Throughout day:** Reddit/HN continue collecting...

---

## 6. Storage Strategy

### File Retention

```
raw/        — Keep 7 days, then archive
processed/  — Keep 30 days, then compress
digests/    — Keep forever (small files)
seen_ids    — Keep forever, grows slowly
```

### Cleanup Script

```bash
# Run weekly
find data/raw -mtime +7 -name "*.json" -exec gzip {} \;
find data/processed -mtime +30 -name "*.jsonl" -exec gzip {} \;
```

---

## 7. Quality Monitoring

### Metrics to Track

**Collection Health:**
```json
{
  "date": "2026-02-08",
  "collected": {
    "reddit": 24,
    "hackernews": 6,
    "github": 2,
    "total": 32
  },
  "processed": {
    "total": 32,
    "deduplicated": 18,
    "scored_80plus": 3
  },
  "avg_score": 58.5
}
```

**Weekly Review:**
- How many opportunities became actionable?
- Precision per source (manual review sample)
- Keyword effectiveness
- Score distribution

---

## 8. Processing Script Skeleton

```python
#!/usr/bin/env python3
"""
Process raw opportunities: score, deduplicate, enrich
"""
from pathlib import Path
import json
from datetime import datetime, timedelta

def main():
    # 1. Find new raw files since last run
    last_run = load_last_run_time()
    raw_files = find_new_files('data/raw', since=last_run)
    
    # 2. Load all opportunities
    all_opps = []
    for file in raw_files:
        opps = load_json(file)['opportunities']
        all_opps.extend(opps)
    
    # 3. Score each
    for opp in all_opps:
        opp['score'] = score_opportunity(opp)
    
    # 4. Deduplicate
    unique_opps = deduplicate(all_opps)
    
    # 5. Enrich
    for opp in unique_opps:
        opp['opportunity_id'] = generate_id(opp)
        opp['domain'] = classify_domain(opp)
        opp['processed_at'] = datetime.now().isoformat()
    
    # 6. Save as JSONL (one per line)
    today = datetime.now().strftime('%Y%m%d')
    output = f'data/processed/opportunities_{today}.jsonl'
    
    with open(output, 'a') as f:
        for opp in unique_opps:
            f.write(json.dumps(opp) + '\n')
    
    # 7. Update last run time
    save_last_run_time()
    
    print(f"Processed {len(all_opps)} → {len(unique_opps)} unique")
    print(f"Top score: {max(o['score'] for o in unique_opps)}")

if __name__ == '__main__':
    main()
```

---

## 9. Implementation Plan

### Phase 1: Core Processing (Week 1)
- [x] Collection layer (done)
- [ ] Build `process_opportunities.py` (scoring + dedup)
- [ ] Build `generate_digest.py` (markdown output)
- [ ] Test end-to-end with sample data
- [ ] Set up cron jobs

### Phase 2: Delivery (Week 2)
- [ ] Telegram bot integration
- [ ] Daily digest delivery
- [ ] Alert for high-score opportunities (>85)

### Phase 3: Refinement (Month 2)
- [ ] Improve scoring algorithm based on feedback
- [ ] Add domain clustering (ML-based)
- [ ] Track opportunity outcomes (which became products?)
- [ ] Web dashboard (optional)

---

## 10. Budget Impact

**Current:**
- Collection: $0 (all free APIs)
- Storage: ~5MB/day = ~150MB/month
- Processing: Local, $0

**Future (if scaling):**
- OpenAI for clustering/summarization: ~$2-5/month
- Database (optional): PostgreSQL on VPS, $5/month
- Total: <$15/month budget ✅

---

## Key Decisions

### ✅ Recommended Approach

1. **Storage:** File-based (JSONL) — Simple, cheap, portable
2. **Processing:** Python scripts — Easy to modify, debug
3. **Delivery:** Telegram — Instant, mobile-friendly
4. **Frequency:** Process every 6h, digest daily @ 8 AM
5. **Retention:** 7d raw, 30d processed, infinite digests

### ⚠️ Avoid For Now
- Real-time processing (overkill for daily insights)
- Database (adds complexity, not needed yet)
- ML clustering (simple keyword matching works)
- Web dashboard (Telegram sufficient initially)

---

## Questions to Answer

Before implementing:

1. **Delivery preference?**
   - Telegram daily digest?
   - Email?
   - Just files to review manually?

2. **Alert threshold?**
   - Should scores >85 trigger immediate notification?
   - Or just wait for daily digest?

3. **Storage location?**
   - Keep in ~/saas-hunter/data?
   - Or separate analytics folder?

4. **Processing frequency?**
   - Every 6 hours?
   - Only after GitHub runs?
   - Before daily digest only?

---

**Ready to implement?** Let me know your preferences and I'll build the processing + digest scripts.
