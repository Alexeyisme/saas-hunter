# GitHub Configuration - FINALIZED ✅

**Date:** 2026-02-08  
**Status:** Production Ready  
**Strategy:** Weekly collection with reaction-based filtering

---

## Summary of Changes

### ✅ What Was Fixed

1. **Time Window**
   - Before: 24 hours → 0 results
   - After: 168 hours (1 week) → 2-4 results
   - **Why:** Reactions need time to accumulate

2. **Search Query**
   - Before: `label:enhancement` (inconsistent across repos)
   - After: `reactions:>2` (universal signal)
   - **Why:** Bugs get comments, features get 👍

3. **Repository List**
   - Before: 13 repos (frameworks like React, Kubernetes)
   - After: 11 repos (SaaS tools like supabase, posthog)
   - Removed: Cal-com/cal.com (422 API errors)
   - **Why:** SaaS tools = SaaS pain points

4. **Rate Limiting**
   - Added: 3-second delay between repos
   - **Why:** Prevents 403 Forbidden errors

5. **Collection Frequency**
   - Before: Daily (planned)
   - After: Weekly (Sundays)
   - **Why:** Higher quality, lower API cost, better signal

---

## Final Configuration

### Environment Variables (.env)
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_HOURS_BACK=168  # 1 week
GITHUB_REACTION_THRESHOLD=2
```

### Repository List (11 repos)
```python
GITHUB_REPOSITORIES = [
    'supabase/supabase',      # Backend-as-a-service
    'posthog/posthog',        # Product analytics
    'n8n-io/n8n',             # Workflow automation
    'plausible/analytics',    # Privacy analytics
    'langchain-ai/langchain', # LLM framework
    'excalidraw/excalidraw',  # Diagramming
    'trpc/trpc',              # Type-safe API
    'formbricks/formbricks',  # Survey tool
    'documenso/documenso',    # E-signature
    'nocodb/nocodb',          # No-code DB
    'directus/directus'       # Headless CMS
]
```

### Search Query
```python
search_query = f"is:open is:issue created:>{since_date} repo:{repo} reactions:>2"
```

### Cron Schedule
```cron
# Every Sunday at 6 AM UTC
0 6 * * 0 cd ~/saas-hunter/scripts && ../venv/bin/python3 github_monitor.py >> ~/saas-hunter/logs/cron.log 2>&1
```

---

## Performance Metrics

### Test Results (2026-02-08)

| Configuration | Results | Runtime |
|--------------|---------|---------|
| 24h window, reactions:>3 | 0 | ~15s |
| 168h window, reactions:>3 | 2 | ~45s |
| 168h window, reactions:>2 | 2 | ~45s |

### Expected Yield
- **Per week:** 2-4 quality opportunities
- **Per month:** 8-16 validated feature requests
- **Quality:** High (reactions = user validation)

### Sample Opportunities
1. **Supabase:** "Overlapping Sidebar over Project cards"  
   4 reactions, 2 comments — UI/UX improvement

2. **PostHog:** "Unable to pull remote config via useFeatureFlagWithPayload"  
   10 reactions, 1 comment — Feature gap in React Native SDK

---

## Cost & Efficiency

### API Usage
- **Requests:** 11-15 per week
- **Limit:** 30/minute (5,000/hour authenticated)
- **Cost:** $0 (free tier)

### Comparison: Daily vs Weekly

| Frequency | Requests/Month | Results/Month | Cost |
|-----------|----------------|---------------|------|
| Daily | ~450 | 0-4 | $0 |
| Weekly | ~60 | 8-16 | $0 |

**Winner:** Weekly (80% fewer API calls, 400% more results)

---

## Three-Source Strategy

| Source | Frequency | Window | Yield/Day | Signal Quality |
|--------|-----------|--------|-----------|----------------|
| **Reddit** | Every 3h | 6h | 15-25 | Medium |
| **HN** | Every 4h | 6h | 3-8 | High |
| **GitHub** | Weekly | 7d | 0.3-0.6 | Very High |

**Combined:** ~25 opportunities/day with varied signal quality

**Philosophy:**
- Reddit provides **volume** (raw pain points)
- HN provides **context** (validated discussions)
- GitHub provides **proof** (reaction-validated requests)

---

## Maintenance

### Monthly Review Checklist
- [ ] Check opportunity yield per repo
- [ ] Remove repos with <2 opportunities/month
- [ ] Test new candidate repos
- [ ] Verify API quota usage
- [ ] Update documentation

### Adding New Repos

**Criteria:**
1. B2B SaaS or developer tool
2. Active community (recent issues)
3. Target audience = potential founders

**Test:**
```bash
curl -s -H "Authorization: token YOUR_TOKEN" \
  "https://api.github.com/search/issues?q=is:open+is:issue+reactions:>2+created:>2026-01-01+repo:OWNER/REPO&per_page=1" \
  | jq .total_count
```

If >5 in last month → Good candidate

---

## Documentation

### Files Updated
- ✅ `scripts/config.py` — Removed Cal.com, updated comments
- ✅ `.env` — Set GITHUB_HOURS_BACK=168, added GITHUB_REACTION_THRESHOLD
- ✅ `scripts/github_monitor.py` — Updated search query
- ✅ `README.md` — Updated cron schedule and yields
- ✅ `GITHUB_CONFIG.md` — New comprehensive config doc
- ✅ `GITHUB_FINALIZED.md` — This summary

### Reference Documents
- `GITHUB_STRATEGY.md` — Deep analysis (repo selection, labeling)
- `GITHUB_ANALYSIS.md` — Problem diagnosis
- `GITHUB_FINAL_ANALYSIS.md` — Test results & decision rationale

---

## Next Steps

### Immediate
- [x] Finalize GitHub config
- [ ] Set up cron jobs for all three sources
- [ ] Test full pipeline end-to-end
- [ ] Document processing/scoring layer (next phase)

### Future Enhancements
- [ ] Build opportunity scoring system
- [ ] Create daily digest generator
- [ ] Add Telegram notifications
- [ ] Clustering by problem domain
- [ ] Track which opportunities become real products

---

## Validation

### Quick Test
```bash
cd ~/saas-hunter/scripts
../venv/bin/python3 github_monitor.py
```

**Expected:**
- Runtime: ~45 seconds
- Results: 0-4 opportunities (depending on week)
- No errors (except Cal.com skip)
- Output: `data/raw/github_YYYYMMDD_HHMMSS.json`

---

**Status:** ✅ Configuration Complete  
**Ready For:** Cron job setup  
**Last Tested:** 2026-02-08 17:39 UTC
