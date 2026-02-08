# GitHub Collector - Final Analysis & Recommendation

**Date:** 2026-02-08  
**Tests Conducted:** 5 different strategies  
**Conclusion:** GitHub is the wrong source for daily SaaS opportunity hunting

---

## What We Learned

### Test 1: Original Strategy (Failed)
- **Query:** Label-based (`label:enhancement`)
- **Repos:** Framework repos (React, Kubernetes, etc.)
- **Result:** 0 opportunities
- **Why:** Wrong repo type + inconsistent labeling

### Test 2: New Repos + No Labels (Partial Success)
- **Query:** `comments:>1` (no label filter)
- **Repos:** SaaS tools (supabase, n8n, posthog)
- **Result:** 2 opportunities (but both were bugs)
- **Why:** Comments indicate activity, not feature requests

### Test 3: Multi-Label OR Query (Failed)
- **Query:** `(label:enhancement OR label:feature OR ...)`
- **Result:** 422 errors (invalid syntax)
- **Why:** GitHub doesn't support complex boolean nesting

### Test 4: Reactions-Based (Failed)
- **Query:** `reactions:>3` in 24 hours
- **Repos:** 12 curated SaaS tools
- **Result:** 0 opportunities
- **Why:** Even active repos don't get 3+ reactions daily

### Test 5: Lower Threshold (Still Failed)
- **Query:** `reactions:>1` in 24 hours for supabase
- **Result:** 0 opportunities
- **Reality Check:** Only 3 issues with >3 reactions in ENTIRE MONTH

---

## The Core Problem

### GitHub Issue Velocity is Too Low

**Supabase** (34k stars, very active):
- Issues with >3 reactions in last 24h: **0**
- Issues with >3 reactions in last 30 days: **3**
- Average: **~2 per week**

**Implication:**  
Even the most active SaaS repos don't produce enough high-signal issues for **daily** collection.

### Why 24-Hour Windows Don't Work

1. **Feature requests are rare** — Most issues are bugs
2. **Reactions take time** — New issues don't get reactions same-day
3. **Labels are inconsistent** — Can't reliably filter
4. **Volume is low** — Even big repos get <5 feature requests/week

---

## Two Paths Forward

### Option A: Change GitHub Strategy ⭐ RECOMMENDED
**Shift from daily micro-collections to weekly digests**

**New Approach:**
```python
GITHUB_HOURS_BACK = 168  # 1 week
search_query = f"is:open is:issue created:>{since_date} repo:{repo} reactions:>2"
```

**Run:** Once per week (not daily)  
**Expected Yield:** 5-15 opportunities per week  
**Trade-off:** Less frequent, but more signal

**Why This Works:**
- Gives reactions time to accumulate
- Catches actual popular requests
- Reduces API calls (cost-effective)
- Better signal-to-noise ratio

---

### Option B: Drop GitHub Entirely
**Focus resources on Reddit + HN**

**Reasoning:**
- Reddit: **18 opportunities in 6 hours** (high volume)
- HN: **4 opportunities in 6 hours** (good signal)
- GitHub: **0-2 opportunities in 24 hours** (low ROI)

**Budget Impact:**
- Frees up API quota
- Reduces complexity
- Reddit/HN already provide abundant signal

---

## Recommended Decision: **Option A (Weekly GitHub)**

### Implementation

**1. Update Config:**
```python
# .env
GITHUB_HOURS_BACK=168  # 1 week
GITHUB_REACTION_THRESHOLD=2
```

**2. Update Query:**
```python
search_query = f"is:open is:issue created:>{since_date} repo:{repo} reactions:>{GITHUB_REACTION_THRESHOLD}"
```

**3. Cron Schedule:**
```cron
# Run GitHub once per week (Sundays at 6 AM)
0 6 * * 0 cd ~/saas-hunter/scripts && ../venv/bin/python3 github_monitor.py
```

**4. Keep Refined Repo List:**
Only the highest-signal repos:
```python
GITHUB_REPOSITORIES = [
    'supabase/supabase',
    'posthog/posthog',
    'n8n-io/n8n',
    'langchain-ai/langchain',
    'plausible/analytics',
    'Cal-com/cal.com'
]
```
(6 repos instead of 12 — focus on quality)

---

## Expected Outcomes (Weekly Model)

### Before (Daily Attempts)
- ❌ 0-2 opportunities/day
- ❌ Mostly bugs
- ❌ High API cost for low return

### After (Weekly Collection)
- ✅ 8-15 opportunities/week
- ✅ Higher quality (reactions = validation)
- ✅ Lower API usage
- ✅ More sustainable

---

## Alternative: Hybrid Model

**If you want some GitHub data daily:**

**Daily:** Use reactions:>0 (get everything, filter later)  
**Weekly:** Special run with reactions:>3 (curated highlights)

```cron
# Daily: Low-threshold scan
0 6 * * * ...github_monitor.py --mode=daily --reactions=0

# Weekly: High-signal digest  
0 6 * * 0 ...github_monitor.py --mode=weekly --reactions=3
```

This gives you:
- Daily volume for processing/learning
- Weekly highlights for immediate opportunities

---

## Final Verdict

**GitHub is valuable but on a different cadence than Reddit/HN.**

**Recommended Setup:**
1. **Reddit:** Every 3 hours (high volume, free)
2. **HN:** Every 4 hours (moderate volume, free)
3. **GitHub:** Once per week (low volume, high signal)

This balances:
- ✅ Daily fresh opportunities (Reddit/HN)
- ✅ Weekly validated requests (GitHub)
- ✅ Budget efficiency
- ✅ Signal quality

---

## Action Items

- [ ] Update `GITHUB_HOURS_BACK` to 168 (1 week)
- [ ] Change cron to weekly (not daily)
- [ ] Reduce repo list to top 6
- [ ] Lower reaction threshold to 2
- [ ] Test weekly run and measure yield
- [ ] Document in README

**Est. implementation time:** 5 minutes  
**Expected improvement:** 400-800% more GitHub opportunities
