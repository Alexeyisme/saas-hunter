# Token Usage Tracking & Optimization Strategy

**Budget:** $15/month  
**Goal:** Maximize insight quality while staying within budget

---

## Current Token Usage: $0/month ✅

### Why Zero?

**Collection layer (0 tokens):**
- Reddit: RSS feeds (free, no LLM)
- GitHub: REST API (free, no LLM)
- HN: Algolia API (free, no LLM)

**Processing layer (0 tokens planned):**
- Scoring: Rule-based Python logic
- Deduplication: Fuzzy string matching (fuzzywuzzy)
- Enrichment: Keyword extraction (regex)
- Digest: Template-based Markdown generation

**All current processing = pure Python, no LLM calls**

---

## Where We COULD Use Tokens (Optional Enhancement)

### Option 1: LLM-Enhanced Scoring
**Current:** Rule-based (0 tokens)
```python
score = count_keywords() + check_engagement() + freshness()
```

**Enhanced:** LLM analysis (~500 tokens/opportunity)
```python
prompt = f"Rate this SaaS opportunity 0-100: {title}\n{body}"
score = claude_mini(prompt)  # $0.001 per opportunity
```

**Cost:** 15 opps/day × $0.001 = **$0.015/day = $0.45/month**

---

### Option 2: Intelligent Clustering
**Current:** Keyword grouping (0 tokens)
```python
domain = match_keywords(["email", "productivity", "saas"])
```

**Enhanced:** Semantic clustering (~200 tokens/opportunity)
```python
embeddings = openai_embed(opportunity_text)
clusters = group_by_similarity(embeddings)
```

**Cost:** 15 opps/day × $0.0001 = **$0.0015/day = $0.05/month**

---

### Option 3: Digest Summarization
**Current:** Template-based (0 tokens)
```markdown
## Top 3 Opportunities
1. {title} - {score}pts
```

**Enhanced:** LLM-generated summaries (~1000 tokens/digest)
```python
prompt = f"Summarize these opportunities: {all_opps}"
digest = claude_mini(prompt)  # $0.002 per digest
```

**Cost:** 1 digest/day × $0.002 = **$0.002/day = $0.06/month**

---

## Recommended Token Strategy

### Phase 1: Start with 0 Tokens (This Week)
✅ **Build everything with pure Python:**
- Rule-based scoring
- Fuzzy deduplication
- Template digests

**Reason:** Validate the pipeline before adding AI cost

---

### Phase 2: Add LLM Where It Matters (Week 2+)

**Priority 1: Enhanced Scoring (High ROI)**
- Use cheap model (Claude Haiku or GPT-4o-mini)
- Only for opportunities that pass basic threshold (score >50)
- ~5-8 opportunities/day
- **Cost: ~$0.20/month**

**Priority 2: Clustering (Medium ROI)**
- Embeddings for grouping similar problems
- Run weekly on all opportunities
- **Cost: ~$0.50/month**

**Priority 3: Summarization (Nice-to-Have)**
- Only for top 3 daily
- **Cost: ~$0.06/month**

**Total Enhanced:** ~$0.76/month (5% of budget)

---

## Token Tracking System

### Database Schema

**File: `data/usage_stats.db` (SQLite)**

```sql
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    job_type TEXT,  -- 'collection', 'processing', 'digest'
    job_name TEXT,  -- 'reddit_monitor', 'claude_scoring'
    
    -- Token metrics
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    
    -- Cost tracking
    model TEXT,     -- 'claude-haiku-3.5', 'gpt-4o-mini'
    cost_usd REAL,
    
    -- Job metrics
    items_processed INTEGER,
    duration_ms INTEGER,
    success BOOLEAN,
    
    -- Metadata
    notes TEXT
);

CREATE TABLE daily_summary (
    date TEXT PRIMARY KEY,
    total_tokens INTEGER,
    total_cost_usd REAL,
    opportunities_collected INTEGER,
    opportunities_processed INTEGER,
    digest_generated BOOLEAN
);
```

---

### Tracking Wrapper

**File: `scripts/usage_tracker.py`**

```python
import sqlite3
from datetime import datetime
from contextlib contextmanager

class UsageTracker:
    def __init__(self, db_path='data/usage_stats.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            job_type TEXT,
            job_name TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            model TEXT,
            cost_usd REAL,
            items_processed INTEGER,
            duration_ms INTEGER,
            success BOOLEAN,
            notes TEXT
        )''')
        conn.commit()
        conn.close()
    
    @contextmanager
    def track_job(self, job_type, job_name):
        """Context manager for automatic tracking"""
        start = datetime.now()
        job = {
            'job_type': job_type,
            'job_name': job_name,
            'timestamp': start.isoformat(),
            'items_processed': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'model': None,
            'cost_usd': 0.0
        }
        
        try:
            yield job
            job['success'] = True
        except Exception as e:
            job['success'] = False
            job['notes'] = str(e)
            raise
        finally:
            duration = (datetime.now() - start).total_seconds() * 1000
            job['duration_ms'] = int(duration)
            job['total_tokens'] = job['input_tokens'] + job['output_tokens']
            self._save_job(job)
    
    def _save_job(self, job):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''INSERT INTO token_usage 
            (timestamp, job_type, job_name, input_tokens, output_tokens, 
             total_tokens, model, cost_usd, items_processed, duration_ms, success, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (job['timestamp'], job['job_type'], job['job_name'],
             job['input_tokens'], job['output_tokens'], job['total_tokens'],
             job.get('model'), job['cost_usd'], job['items_processed'],
             job['duration_ms'], job['success'], job.get('notes'))
        )
        conn.commit()
        conn.close()
    
    def get_daily_usage(self, date=None):
        """Get usage for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        result = conn.execute('''
            SELECT 
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost,
                COUNT(*) as jobs
            FROM token_usage 
            WHERE DATE(timestamp) = ?
        ''', (date,)).fetchone()
        conn.close()
        
        return {
            'date': date,
            'total_tokens': result[0] or 0,
            'total_cost': result[1] or 0.0,
            'jobs_run': result[2] or 0
        }
    
    def get_monthly_usage(self, year_month=None):
        """Get usage for current month"""
        if year_month is None:
            year_month = datetime.now().strftime('%Y-%m')
        
        conn = sqlite3.connect(self.db_path)
        result = conn.execute('''
            SELECT 
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost,
                COUNT(*) as jobs
            FROM token_usage 
            WHERE strftime('%Y-%m', timestamp) = ?
        ''', (year_month,)).fetchone()
        conn.close()
        
        return {
            'month': year_month,
            'total_tokens': result[0] or 0,
            'total_cost': result[1] or 0.0,
            'budget_remaining': 15.0 - (result[1] or 0.0),
            'jobs_run': result[2] or 0
        }
```

---

### Usage in Scripts

**Example: Reddit Monitor (0 tokens)**
```python
from usage_tracker import UsageTracker

tracker = UsageTracker()

with tracker.track_job('collection', 'reddit_monitor') as job:
    results = fetch_subreddit_rss(...)
    job['items_processed'] = len(results)
    # No tokens used, cost = 0
```

**Example: LLM Scoring (future)**
```python
with tracker.track_job('processing', 'llm_scoring') as job:
    for opp in opportunities:
        response = claude.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Track tokens
        job['input_tokens'] += response.usage.input_tokens
        job['output_tokens'] += response.usage.output_tokens
        
        # Calculate cost (Claude Haiku: $0.25/1M in, $1.25/1M out)
        input_cost = (response.usage.input_tokens / 1_000_000) * 0.25
        output_cost = (response.usage.output_tokens / 1_000_000) * 1.25
        job['cost_usd'] += input_cost + output_cost
        job['model'] = 'claude-3-haiku-20240307'
    
    job['items_processed'] = len(opportunities)
```

---

## Optimization Strategies

### 1. Tiered Processing (Recommended)

**Tier 1: Free (all opportunities)**
- Rule-based scoring
- Keyword matching
- Basic deduplication

**Tier 2: Cheap LLM (score >50 only)**
- Enhanced scoring with Claude Haiku
- ~5-8 opportunities/day
- $0.001 each

**Tier 3: Premium LLM (score >80 only)**
- Deep analysis with GPT-4o
- ~2-3 opportunities/day
- $0.01 each

**Monthly cost:** $0.20 + $0.60 = **$0.80/month**

---

### 2. Batch Processing

**Instead of:** 1 API call per opportunity (15 calls/day)  
**Do:** 1 API call for 10 opportunities (1-2 calls/day)

```python
# Batch scoring
prompt = f"Score these 10 opportunities:\n{json.dumps(opps)}"
scores = claude(prompt)  # 1 call vs 10
```

**Savings:** 50-70% fewer API calls

---

### 3. Caching & Memoization

**Cache similar opportunities:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_domain_cluster(text_hash):
    return llm_classify(text)

# Reuse for similar texts
```

**Savings:** Avoid re-processing duplicates

---

### 4. Model Selection

**Cheapest to Most Expensive:**

| Model | Input | Output | Use Case |
|-------|-------|--------|----------|
| Claude Haiku | $0.25/1M | $1.25/1M | Scoring, classification |
| GPT-4o-mini | $0.15/1M | $0.60/1M | Fast summaries |
| GPT-4o | $2.50/1M | $10/1M | Deep analysis (rare) |

**Recommended:** Claude Haiku for 95% of tasks

---

### 5. Prompt Optimization

**Inefficient (500 tokens):**
```
Please analyze this SaaS opportunity and provide a detailed 
score from 0-100, considering factors like market size, 
pain point clarity, competition, and feasibility...
Title: {title}
Description: {body}
```

**Efficient (150 tokens):**
```
Score 0-100:
Title: {title}
Body: {body[:200]}
Return: {"score": X, "reason": "..."}
```

**Savings:** 70% fewer tokens

---

## Statistics Dashboard

### Command: `python scripts/usage_stats.py`

**Output:**
```
╔══════════════════════════════════════════════════════════╗
║         SaaS Hunter - Usage Statistics                   ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  📅 Today (2026-02-08)                                   ║
║     Opportunities: 24 collected, 12 processed            ║
║     Tokens: 0 used                                       ║
║     Cost: $0.00                                          ║
║     Jobs: 8 completed                                    ║
║                                                          ║
║  📊 This Month (Feb 2026)                                ║
║     Opportunities: 340 collected, 180 processed          ║
║     Tokens: 0 used                                       ║
║     Cost: $0.00 / $15.00 budget                          ║
║     Budget Remaining: $15.00 (100%)                      ║
║                                                          ║
║  ⏱️  Performance                                          ║
║     Avg Collection Time: 18s                             ║
║     Avg Processing Time: N/A                             ║
║     Success Rate: 100%                                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Breakdown by Job Type:
- reddit_monitor:     8 runs, 132 opportunities, 0 tokens
- hackernews_monitor: 6 runs,  18 opportunities, 0 tokens
- github_monitor:     1 run,    2 opportunities, 0 tokens
```

---

## Recommended Approach

### Start: Phase 1 (Week 1) - $0/month

✅ Build entire pipeline with **0 tokens:**
- Rule-based scoring
- Fuzzy deduplication
- Template digests
- Usage tracking (for future)

**Validate quality before adding AI cost**

---

### Enhance: Phase 2 (Week 2+) - ~$1/month

✅ Add LLM only where it adds value:
- Enhanced scoring for top candidates (>50 score)
- Clustering for trend analysis
- Cost: <$1/month (<7% of budget)

**Track everything, optimize based on data**

---

### Scale: Phase 3 (Month 2) - ~$5/month

✅ If quality justifies it:
- Deep analysis for top opportunities
- Competitive research via web search
- Market sizing estimates
- Still well under $15 budget

---

## Answer to Your Questions

### 1. Can we track all tokens?
**Yes!** SQLite database tracking:
- Every job run
- Tokens used (input/output)
- Cost per job
- Items processed
- Duration
- Success/failure

**Export options:**
- Daily/weekly/monthly reports
- CSV export for analysis
- Dashboard view

---

### 2. Token optimization recommendations?

**Short term (Phase 1):**
1. ✅ Use 0 tokens (pure Python) initially
2. ✅ Track all jobs even at 0 cost (baseline)
3. ✅ Validate quality before adding AI

**Medium term (Phase 2):**
4. ✅ Tiered processing (free → cheap LLM → premium)
5. ✅ Batch API calls when possible
6. ✅ Cache similar opportunities
7. ✅ Use cheapest model (Claude Haiku)

**Long term (Phase 3):**
8. ✅ Monitor ROI per token spent
9. ✅ Drop low-value LLM features
10. ✅ Optimize prompts based on usage data

---

## Budget Projection

| Phase | Timeline | Monthly Cost | % of Budget |
|-------|----------|--------------|-------------|
| **Phase 1** | Week 1 | $0.00 | 0% |
| **Phase 2** | Week 2-4 | $0.50-1.00 | 3-7% |
| **Phase 3** | Month 2+ | $3.00-5.00 | 20-33% |
| **Max** | Future | <$15.00 | 100% |

**Worst case:** $5/month = 67% budget headroom

---

## Implementation

**Next Steps:**

1. Build `scripts/usage_tracker.py` (tracking system)
2. Integrate tracker into all collectors (0 tokens baseline)
3. Build Phase 1 processing (0 tokens)
4. Add `scripts/usage_stats.py` (dashboard)
5. Run for 1 week, review quality
6. Decide: add LLM enhancement or stay at $0?

**Ready to build the tracker + Phase 1 processing?**
