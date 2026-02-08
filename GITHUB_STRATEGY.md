# GitHub Collection Strategy - Deep Dive

## Current Problem: Signal vs Noise

**We're collecting issues, but not the right kind.**

### What We're Getting Now
```
✗ "AI Assistant is incapable of doing literally anything" (bug)
✗ "Import History table text overlaps on small screens" (bug)
✗ "ChatOpenAI silently drops 'reasoning_content'" (bug)
```

### What We Want
```
✓ "CRUD API for Workflows & Templates" (feature request)
✓ "Asymmetric JWT Keys in Self Hosted Supabase" (enhancement)
✓ User pain points about missing features
```

---

## Root Cause Analysis

### Issue 1: Search Criteria Too Broad
Current query: `is:open is:issue created:>X comments:>1`

**Problems:**
- Catches bugs (most active issues are bugs)
- No feature request filtering
- Comments don't indicate feature requests

### Issue 2: Label Inconsistency
Different repos use different labels:
- `supabase/supabase` → `enhancement`
- `posthog/posthog` → `enhancement`
- `n8n-io/n8n` → `feature-request`
- `langchain-ai/langchain` → `enhancement`
- `mattermost/mattermost` → `feature`, `enhancement`

**But:** Not all repos label consistently.

### Issue 3: Wrong Metric for "Value"
Using `comments:>1` assumes engagement = feature request.

**Reality:**
- Bugs get lots of comments (people report same issue)
- Feature requests may get fewer comments but higher reactions (👍)

---

## Proposed Solutions

### Strategy A: Multi-Label Search ⭐ RECOMMENDED
Search for issues with ANY feature-related label:

```python
label_queries = [
    'label:enhancement',
    'label:"feature request"',
    'label:feature-request',
    'label:feature',
    'label:improvement'
]

# Combine with OR
search_query = f"is:open is:issue created:>{since_date} repo:{repo} ({' OR '.join(label_queries)})"
```

**Pros:**
- Filters out bugs
- Catches feature requests across different repos
- More precise signal

**Cons:**
- Misses unlabeled feature requests
- Different repos = different coverage

---

### Strategy B: Keyword-Based Filter (Hybrid)
Use label search + keyword fallback for unlabeled issues:

**Feature Request Keywords:**
```python
FEATURE_KEYWORDS = [
    'feature request', 'would be great', 'would love to', 
    'could you add', 'is it possible to', 'support for',
    'ability to', 'option to', 'would help if',
    'missing feature', 'lack of', 'no way to'
]
```

Search in title/body for these patterns.

**Pros:**
- Catches unlabeled requests
- Language-based signal

**Cons:**
- More complex
- May catch feature suggestions in bug reports

---

### Strategy C: Reaction-Based Filter
Instead of `comments:>1`, use reactions (👍):

```python
search_query = f"is:open is:issue created:>{since_date} repo:{repo} reactions:>3"
```

**Why this works:**
- People 👍 feature requests they want
- Bugs get comments, not reactions
- Higher signal-to-noise

**Cons:**
- Misses recent issues (not enough time for reactions)

---

## Recommended Implementation: **Hybrid A + C**

### Query Structure
```python
# Primary: Label-based (high precision)
label_filter = 'label:enhancement OR label:"feature request" OR label:feature-request OR label:feature OR label:improvement'

# Fallback: Reaction-based (catches unlabeled but popular)
search_query = f"is:open is:issue created:>{since_date} repo:{repo} ({label_filter}) OR reactions:>5"
```

### Why This Works
1. **Label filter** catches explicitly tagged feature requests
2. **Reaction threshold** catches popular unlabeled requests
3. Filters out low-engagement bugs

---

## Repo List Strategy

### Current List (16 repos)
✅ Keep:
- `supabase/supabase` — Active, well-labeled
- `posthog/posthog` — Product analytics (high SaaS signal)
- `n8n-io/n8n` — Workflow automation (users = builders)
- `langchain-ai/langchain` — AI tooling (hot space)
- `excalidraw/excalidraw` — Visual tool (design pain points)
- `plausible/analytics` — Privacy analytics (niche SaaS)

⚠️ Evaluate:
- `appwrite/appwrite` — Check label usage
- `nocodb/nocodb` — Check activity
- `directus/directus` — Check label consistency
- `meilisearch/meilisearch` — More infrastructure than SaaS

❌ Consider removing:
- `RocketChat/Rocket.Chat` — Mostly bugs in recent issues
- `mattermost/mattermost` — Enterprise, less indie SaaS signal
- `openai/openai-python` — SDK issues, not product pain points
- `umami-software/umami` — Small project, low activity

### Replacement Candidates (SaaS-first)
- `stripe/stripe-node` → Payment integration pain points
- `Cal-com/cal.com` → Scheduling tool
- `documenso/documenso` → E-signature tool
- `formbricks/formbricks` → Survey tool
- `matomo-org/matomo` → Analytics
- `inbox-zero/inbox-zero` → Email management
- `trpc/trpc` → API tooling (developer pain)
- `refine-dev/refine` — Admin panel builder

### Selection Criteria
1. **B2B SaaS or dev tools** (not consumer apps)
2. **Active community** (>50 stars/month, recent commits)
3. **Clear labeling** (has enhancement/feature labels)
4. **Target audience = builders** (people who might start SaaS)

---

## Testing Protocol

### Before Adding a Repo
Run this check:
```bash
curl -s -H "Authorization: token YOUR_TOKEN" \
  "https://api.github.com/search/issues?q=is:open+is:issue+label:enhancement+repo:OWNER/REPO&per_page=1" \
  | jq .total_count
```

**Decision:**
- `>10` recent enhancements → Add
- `<5` → Skip or manual review
- `0` → Check if they use different label

### Monthly Review
Track these metrics per repo:
```json
{
  "repo": "supabase/supabase",
  "opportunities_found": 12,
  "quality_score": 8.5,  // Manual review
  "last_updated": "2026-02-08"
}
```

Drop repos with <3 opportunities/month.

---

## Updated Config

### Refined Repo List (12 repos)
```python
GITHUB_REPOSITORIES = [
    # Tier 1: High Signal SaaS Platforms
    'supabase/supabase',
    'posthog/posthog',
    'n8n-io/n8n',
    'plausible/analytics',
    
    # Tier 2: Developer Tools
    'langchain-ai/langchain',
    'excalidraw/excalidraw',
    'trpc/trpc',
    
    # Tier 3: Indie SaaS
    'Cal-com/cal.com',
    'formbricks/formbricks',
    'documenso/documenso',
    
    # Tier 4: Evaluate (keep 1-2 months)
    'nocodb/nocodb',
    'directus/directus'
]
```

### Search Query
```python
# Multi-label OR reaction-based
label_filter = '(label:enhancement OR label:"feature request" OR label:feature-request OR label:feature OR label:improvement)'
reaction_filter = 'reactions:>5'

search_query = f"is:open is:issue created:>{since_date} repo:{repo} ({label_filter} OR {reaction_filter})"
```

---

## Expected Improvements

### Before (Current)
- 0-2 opportunities/day
- Mix of bugs and features
- Low relevance

### After (Optimized)
- 5-15 opportunities/day
- 80%+ feature requests
- Higher SaaS relevance

---

## Action Items

1. ✅ Add 3-second delay between repos (done)
2. ⏳ Update search query with label+reaction filter
3. ⏳ Refine repo list to 12 high-signal sources
4. ⏳ Test for 1 week, track quality
5. ⏳ Set up monthly review process

---

**Next:** Implement the hybrid search query and test with refined repo list.
