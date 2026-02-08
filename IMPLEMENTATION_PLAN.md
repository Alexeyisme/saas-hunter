# SaaS Hunter - Implementation Plan

**Start Date:** 2026-02-08  
**Phase 1 Duration:** 1 week  
**Review Date:** 2026-02-15

---

## Phase 1: Core Pipeline (Week 1)

### Goals
- ✅ Complete data collection → processing → digest pipeline
- ✅ Zero token usage (pure Python)
- ✅ Track all metrics for baseline
- ✅ Deliver daily Telegram digests

### Components to Build

**1. Token Tracking System**
- `scripts/usage_tracker.py` — SQLite-based tracking
- `scripts/usage_stats.py` — Dashboard CLI
- Integrate into all collectors

**2. Processing Pipeline**
- `scripts/process_opportunities.py` — Score, dedupe, enrich
- Rule-based scoring (0-100)
- Fuzzy title matching for deduplication
- Domain classification via keywords

**3. Digest Generation**
- `scripts/generate_digest.py` — Markdown daily summary
- Template-based (0 tokens)
- Top 5-10 opportunities
- Trend analysis

**4. Telegram Delivery**
- `scripts/send_telegram.py` — Send digest to Telegram
- Top 3 opportunities
- Daily at 8 AM UTC

**5. Cron Setup**
- Collection jobs (Reddit 3h, HN 4h, GitHub weekly)
- Processing every 6h
- Digest + delivery daily at 8 AM

---

## Cron Schedule

```cron
# Collection Layer
0 */3 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 reddit_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1
0 */4 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 hackernews_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1
0 6 * * 0 cd ~/saas-hunter/scripts && ../venv/bin/python3 github_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1

# Processing Layer
30 */6 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 process_opportunities.py >> ~/saas-hunter/logs/cron.log 2>&1

# Delivery Layer
0 8 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 generate_digest.py >> ~/saas-hunter/logs/cron.log 2>&1
1 8 * * * cd ~/saas-hunter/scripts && ../venv/bin/python3 send_telegram.py >> ~/saas-hunter/logs/cron.log 2>&1

# Weekly cleanup
0 3 * * 1 find ~/saas-hunter/data/raw -mtime +7 -name "*.json" -exec gzip {} \;
```

---

## Week 1 Timeline

### Day 1 (Feb 8) — Build Core
- [x] Design architecture
- [x] Review & optimize collectors
- [ ] Build usage_tracker.py
- [ ] Build process_opportunities.py
- [ ] Build generate_digest.py
- [ ] Test end-to-end with sample data

### Day 2 (Feb 9) — Integration
- [ ] Integrate tracker into collectors
- [ ] Build send_telegram.py
- [ ] Set up Telegram bot
- [ ] Test Telegram delivery

### Day 3 (Feb 10) — Deployment
- [ ] Set up all cron jobs
- [ ] First automated digest at 8 AM
- [ ] Monitor for errors

### Days 4-7 (Feb 11-14) — Monitor & Iterate
- [ ] Review daily digests
- [ ] Check usage stats
- [ ] Fix any bugs
- [ ] Tune scoring weights if needed

### Day 8 (Feb 15) — Week 1 Review
- [ ] Analyze 7 days of data
- [ ] Review opportunity quality
- [ ] Check false positive rate
- [ ] Decide: Phase 2 (add LLM) or stay at $0?

---

## Success Metrics (Week 1)

### Operational
- ✅ 100% uptime for cron jobs
- ✅ Daily digest delivered by 8 AM
- ✅ 0 errors in processing
- ✅ All data backed up

### Quality
- ✅ 10-15 opportunities/day collected
- ✅ 60%+ precision after deduplication
- ✅ Top 3 daily are actionable
- ✅ <5% duplicate across sources

### Cost
- ✅ $0 token usage
- ✅ All tracking functional
- ✅ Baseline metrics established

---

## Review Checklist (Feb 15)

### Data Quality
- [ ] How many opportunities collected? (target: 70-100)
- [ ] How many after deduplication? (target: 50-70)
- [ ] False positive rate? (target: <30%)
- [ ] Daily digest quality? (1-10 rating)

### System Performance
- [ ] Any cron failures?
- [ ] Processing speed acceptable? (target: <10s)
- [ ] Digest generation time? (target: <5s)
- [ ] Telegram delivery reliable?

### Scoring Accuracy
- [ ] Are scores meaningful? (manual validation)
- [ ] Top 3 daily actually interesting?
- [ ] Any scoring bugs/edge cases?
- [ ] Weights need tuning?

### Deduplication
- [ ] Fuzzy matching working?
- [ ] Any obvious duplicates getting through?
- [ ] False deduplication? (different opps marked same)

### Token Usage
- [ ] Confirm $0 usage
- [ ] Tracker working correctly?
- [ ] Ready to add LLM if needed?

---

## Decision Points (Feb 15)

### Option A: Stay at $0 (If quality is good)
- Continue with rule-based processing
- Focus on expanding sources
- Refine scoring weights
- Add more subreddits

### Option B: Add LLM Enhancement (If quality needs boost)
- Enhanced scoring for top candidates
- Semantic clustering
- Better deduplication
- Cost: ~$1/month

### Option C: Scale Back (If too noisy)
- Drop low-signal subreddits
- Increase thresholds
- Focus on GitHub + HN only

---

## Dependencies

### Python Packages (Install)
```bash
cd ~/saas-hunter
source venv/bin/activate
pip install fuzzywuzzy python-Levenshtein
```

### Telegram Setup
1. Create bot via @BotFather
2. Get bot token
3. Get your chat ID
4. Add to .env:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

---

## Rollback Plan

If anything breaks:
1. Disable cron jobs: `crontab -r`
2. Check logs: `tail -100 ~/saas-hunter/logs/cron.log`
3. Fix issues
4. Test manually: `python scripts/process_opportunities.py`
5. Re-enable cron: `crontab -e`

---

## File Structure After Phase 1

```
~/saas-hunter/
├── scripts/
│   ├── config.py                    # Centralized config
│   ├── utils.py                     # Shared utilities
│   ├── usage_tracker.py             # Token tracking [NEW]
│   ├── usage_stats.py               # Stats dashboard [NEW]
│   ├── reddit_monitor.py            # Reddit collector [UPDATED]
│   ├── github_monitor.py            # GitHub collector [UPDATED]
│   ├── hackernews_monitor.py        # HN collector [UPDATED]
│   ├── process_opportunities.py     # Processing pipeline [NEW]
│   ├── generate_digest.py           # Digest generator [NEW]
│   └── send_telegram.py             # Telegram delivery [NEW]
├── data/
│   ├── raw/                         # Collector outputs
│   ├── processed/                   # Scored opportunities (JSONL)
│   ├── digests/                     # Daily digests (Markdown)
│   ├── seen_ids.json                # Deduplication
│   └── usage_stats.db               # Token tracking [NEW]
├── logs/
│   ├── cron.log                     # Cron job logs
│   ├── reddit_monitor.log
│   ├── github_monitor.log
│   ├── hackernews_monitor.log
│   └── processing.log               # Processing logs [NEW]
├── .env                             # Config + secrets
├── ARCHITECTURE.md                  # System design
├── IMPLEMENTATION_PLAN.md           # This file
└── README.md                        # Project overview
```

---

## Phase 2 Preview (Week 2+)

**If we decide to add LLM:**

### Enhanced Scoring
```python
# Only for opportunities scoring >50 in rule-based
if base_score > 50:
    llm_score = claude_haiku_score(opportunity)
    final_score = (base_score * 0.6) + (llm_score * 0.4)
```

**Cost:** ~$0.50/month

### Semantic Clustering
```python
# Weekly batch job
embeddings = openai.embed(all_opportunities)
clusters = group_by_similarity(embeddings)
```

**Cost:** ~$0.20/month

**Total Phase 2:** ~$0.70/month (5% of budget)

---

## Notes

- All timestamps in UTC
- Telegram delivery at 8 AM UTC (adjust if needed)
- Process before digest (6:30 AM run ensures fresh data for 8 AM digest)
- Weekly GitHub runs on Sundays at 6 AM
- Logs rotate automatically (keep 30 days)

---

**Status:** Ready to implement  
**Next:** Build Phase 1 components
