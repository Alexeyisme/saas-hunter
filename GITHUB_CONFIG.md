# GitHub Collector - Final Configuration

**Last Updated:** 2026-02-08  
**Strategy:** Weekly collection with reaction-based filtering

---

## Configuration

### Time Window
- **Lookback:** 168 hours (1 week)
- **Rationale:** Reactions need time to accumulate; daily collection yielded 0 results

### Filtering
- **Threshold:** reactions:>2
- **Why reactions:** Bugs get comments, feature requests get 👍 reactions
- **Signal:** 2+ reactions indicates validated user interest

### Repository List (11 repos)

**High-Signal SaaS Platforms:**
- `supabase/supabase` — Backend-as-a-service
- `posthog/posthog` — Product analytics
- `n8n-io/n8n` — Workflow automation
- `plausible/analytics` — Privacy-focused analytics

**Developer Tools:**
- `langchain-ai/langchain` — LLM framework
- `excalidraw/excalidraw` — Diagramming tool
- `trpc/trpc` — Type-safe API

**Indie SaaS:**
- `formbricks/formbricks` — Survey tool
- `documenso/documenso` — E-signature
- `nocodb/nocodb` — No-code database
- `directus/directus` — Headless CMS

**Removed:**
- ❌ `Cal-com/cal.com` — Returns 422 API errors

---

## Performance

### Test Results (2026-02-08)

| Window | Threshold | Results |
|--------|-----------|---------|
| 24 hours | reactions:>3 | 0 |
| 168 hours | reactions:>3 | 2 |
| 168 hours | reactions:>2 | 2 |

**Outcome:** ~2 opportunities per week (sustainable yield)

### Sample Opportunities
1. Supabase: "Overlapping Sidebar over Project cards" (4 reactions)
2. PostHog: "Unable to pull remote config via useFeatureFlagWithPayload" (10 reactions)

---

## Execution

### Rate Limiting
- **Delay:** 3 seconds between repos (avoids 403 errors)
- **Total runtime:** ~45 seconds for 11 repos
- **API quota:** Uses ~11-15 requests per run (well within 30/min limit)

### Schedule
```cron
# Run every Sunday at 6 AM UTC
0 6 * * 0 cd ~/saas-hunter/scripts && ../venv/bin/python3 github_monitor.py
```

---

## Maintenance

### Monthly Review
Check these metrics per repo:
```json
{
  "repo": "supabase/supabase",
  "opportunities_found": 4,
  "avg_reactions": 6.5,
  "last_reviewed": "2026-03-08"
}
```

**Action:** Drop repos with <2 opportunities/month.

### Adding New Repos
**Criteria:**
1. B2B SaaS or developer tool
2. Active community (>10 open issues/week)
3. Clear labeling or high reaction rates
4. Target audience = builders

**Test before adding:**
```bash
curl -s -H "Authorization: token YOUR_TOKEN" \
  "https://api.github.com/search/issues?q=is:open+is:issue+reactions:>2+created:>2026-01-01+repo:OWNER/REPO&per_page=1" \
  | jq .total_count
```

If `total_count > 5` in last month → Good candidate

---

## Cost

**Current:**
- API calls: 11-15 per week
- Rate: Free tier (5,000/hour authenticated)
- Cost: $0

**Headroom:**
- Can add ~300 more repos before hitting limits
- Or increase frequency (currently optimal at weekly)

---

## Why This Works

1. **Reactions = Validation**  
   People 👍 features they want; bugs get comments

2. **Time = Signal**  
   Week gives reactions time to accumulate

3. **Quality > Quantity**  
   2 validated opportunities/week beats 0 daily

4. **Budget Friendly**  
   15 API calls/week vs 180 calls/week (daily)

---

## Comparison with Reddit/HN

| Source | Frequency | Window | Yield | Signal |
|--------|-----------|--------|-------|--------|
| Reddit | Every 3h | 6h | 15-25/day | Medium |
| HN | Every 4h | 6h | 3-8/day | High |
| GitHub | Weekly | 168h | 2-4/week | Very High |

**Strategy:** Let Reddit/HN provide volume, GitHub provides validated requests.

---

## Configuration Files

### `.env`
```bash
GITHUB_HOURS_BACK=168
GITHUB_REACTION_THRESHOLD=2
```

### `config.py`
```python
GITHUB_REPOSITORIES = [
    'supabase/supabase',
    'posthog/posthog',
    # ... (see above)
]
```

### `github_monitor.py`
```python
search_query = f"is:open is:issue created:>{since_date} repo:{repo} reactions:>2"
time.sleep(3)  # Delay between repos
```

---

**Status:** ✅ Production Ready  
**Next Review:** 2026-03-08
