# SaaS Hunter - Data Collection Evaluation

**Test Date:** 2026-02-08 17:05-17:07 UTC  
**Test Duration:** ~2 minutes total  
**Lookback Window:** 6 hours

---

## ✅ Overall Status: **SUCCESSFUL**

All three collectors ran without errors and produced valid, normalized JSON outputs.

---

## 📊 Results Summary

| Source | Opportunities Found | Runtime | Status | API Cost |
|--------|-------------------|---------|--------|----------|
| **Reddit** | 18 | ~21s | ✅ Success | $0 (RSS) |
| **GitHub** | 0 | ~14s | ✅ Success | $0 (within free tier) |
| **Hacker News** | 4 | <1s | ✅ Success | $0 (free API) |
| **TOTAL** | **22** | **~36s** | ✅ | **$0** |

---

## 🔍 Detailed Analysis

### 1. Reddit Collector (`reddit_monitor.py`)

**Performance:**
- Scanned 12 subreddits in 21 seconds
- Found 18 opportunities (after keyword filtering)
- No API rate limit issues (RSS-based)

**Data Quality:**
✅ Proper keyword matching (e.g., "struggling with", "pain point")  
✅ Time filtering working (6-hour window)  
✅ Duplicate detection working  
✅ Clean HTML parsing  
✅ Normalized schema  

**Sample Opportunity:**
```json
{
  "source": "reddit:SaaS",
  "title": "Looking for marketing/account conversion advice",
  "keywords": ["pain point"],
  "url": "https://www.reddit.com/r/SaaS/comments/1qzd3na/...",
  "published_utc": "2026-02-08T16:18:37"
}
```

**Breakdown by Subreddit:**
- r/SaaS: 12 opportunities ⭐
- r/smallbusiness: 3 opportunities
- r/Entrepreneur: 1 opportunity
- r/webdev: 1 opportunity
- r/nocode: 1 opportunity
- Other 7 subreddits: 0 opportunities

**Issues:** None

---

### 2. GitHub Collector (`github_monitor.py`)

**Performance:**
- Scanned 13 repositories in 14 seconds
- Found 0 opportunities (expected — large repos, 6-hour window)
- Rate limit: 17 requests remaining (started with ~30)

**Data Quality:**
✅ GitHub API authentication working  
✅ Search query construction correct  
✅ Rate limit tracking functional  
⚠️ Rate limit warning threshold too aggressive (500 is way too high)

**Rate Limit Consumption:**
- Used ~13 requests for 13 repos
- API limit: 30 req/min (authenticated)
- Safe to run every 6 hours

**Issues to Fix:**
1. **Rate limit warning threshold** — Currently warns at <500, but limit is only 30/min for search API
   - Change threshold to 10 or remove warning entirely
2. **Low yield** — 6-hour window too narrow for these repos
   - Consider 24-hour window for GitHub
   - Or target smaller, more active repos

---

### 3. Hacker News Collector (`hackernews_monitor.py`)

**Performance:**
- Single API call, <1 second
- Found 4 Ask HN stories
- No rate limit issues

**Data Quality:**
✅ Algolia API working perfectly  
✅ Keyword filtering effective  
✅ Engagement threshold (>5 comments) working  
✅ Normalized schema  

**Sample Opportunities:**
1. "Would you use an ESLint-like tool for SEO..." (matched: "tool for")
2. "What do you expect from a Turkey-based hosting provider?" (>5 comments)

**Issues:** None

---

## 📁 File Structure Validation

✅ **Directory structure:**
```
~/saas-hunter/
├── data/
│   ├── raw/
│   │   ├── reddit_20260208_170657.json
│   │   ├── github_20260208_170711.json
│   │   └── hackernews_20260208_170717.json
│   └── seen_ids.json
└── logs/
    ├── reddit_monitor.log
    ├── github_monitor.log
    └── hackernews_monitor.log
```

✅ **Normalized output schema:**
All sources use consistent fields:
- `source_id`, `source`, `title`, `body`, `url`
- `published_utc`, `engagement_data`, `collected_at`

✅ **Deduplication working:**
- 22 unique IDs tracked in `seen_ids.json`
- Format: `{source}:{source_id}` (e.g., `reddit:SaaS:1qzd3na`)

---

## 🐛 Issues Found & Recommendations

### Critical (Fixed)
1. ✅ **Path resolution bug** — Config created `data/` under `scripts/` instead of project root
   - **Fix applied:** Changed `PROJECT_ROOT` logic to always use `SCRIPT_DIR.parent`

### Medium Priority
2. ⚠️ **GitHub rate limit warning threshold**
   - Current: Warns at <500 remaining
   - Actual limit: 30 requests/min (search API)
   - **Recommendation:** Lower to 10 or remove warning

3. ⚠️ **GitHub 6-hour window too narrow**
   - Big repos like `kubernetes/kubernetes` rarely have new issues in 6 hours
   - **Recommendation:** Either:
     - Increase to 24 hours for GitHub only
     - Target smaller, more active repos (niche SaaS tools)
     - Mix of both

### Low Priority (Quality Improvements)
4. 💡 **Keyword filtering may be too broad**
   - Example: "struggling with" matched a self-promotional post
   - **Recommendation:** Add scoring/ranking in processing phase

5. 💡 **No engagement data for Reddit**
   - RSS feeds don't include upvotes/comments
   - **Options:**
     - Accept limitation (free tier)
     - Add Reddit API for engagement (requires API key)
     - Process URL to scrape engagement (slow, fragile)

---

## 💰 Cost Analysis

**Current Setup (6-hour collections, 4x/day):**
- Reddit: $0 (RSS)
- GitHub: $0 (free tier, ~52 req/day << 5000/hour limit)
- Hacker News: $0 (free API)

**Projected Monthly Cost:** $0  
**Budget:** $15/month  
**Headroom:** $15/month for future expansion

**Safe to add:**
- More subreddits (unlimited, RSS-based)
- More GitHub repos (up to ~300 before hitting limits)
- More HN queries (generous free tier)

---

## 🚀 Next Steps

### Immediate (Before Cron Setup)
1. **Fix GitHub rate limit warning threshold**
   ```python
   RATE_LIMIT_WARNING_THRESHOLD = 10  # Down from 500
   ```

2. **Adjust GitHub lookback window** (in `.env`)
   ```bash
   GITHUB_HOURS_BACK=24  # Separate from COLLECTION_HOURS_BACK
   ```

### For Cron Implementation
3. **Stagger schedules:**
   - Reddit: Every 3 hours (0,3,6,9,12,15,18,21)
   - GitHub: Every 6 hours (0,6,12,18)
   - HN: Every 4 hours (0,4,8,12,16,20)

4. **Add wrapper script** for logging/error handling

5. **Consider environment-specific configs:**
   - GitHub repos could be customized per user interest
   - Subreddits could be expanded based on niche

### Nice-to-Have
6. **Processing/scoring pipeline** (next phase)
7. **Digest/summary generator**
8. **Telegram notification integration**

---

## ✅ Validation Checklist

- [x] All dependencies installed (venv)
- [x] Config file loads correctly
- [x] Environment variables working (.env)
- [x] Reddit collector runs without errors
- [x] GitHub collector authenticates successfully
- [x] HN collector fetches data
- [x] Duplicate detection persists across runs
- [x] Output files are valid JSON
- [x] Normalized schema consistent across sources
- [x] Logs created and readable
- [x] No API rate limit violations
- [x] Total cost: $0

---

## 🎯 Conclusion

**The data collection layer is production-ready** with minor improvements needed:

✅ **Strengths:**
- Clean architecture
- Zero cost
- Fast execution
- Good keyword filtering
- Solid error handling
- Proper deduplication

⚠️ **Minor Issues:**
- GitHub window too narrow (easy fix)
- Rate limit threshold needs adjustment

**Recommended Action:**  
Proceed with cron job setup after applying the two fixes above. The system is stable and efficient.
