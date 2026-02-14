# Phase 2: LLM Enhancement

**Status:** Implemented  
**Date:** 2026-02-14  
**Activated by:** Alexey

---

## Implementation

### 1. LLM Scorer Module (`llm_scorer.py`)

**Model:** `anthropic/claude-3-haiku` via OpenRouter
- Cheapest Claude model (~$0.25 per 1M input tokens)
- Fast inference
- Good reasoning for this task

**Trigger:** Only for opportunities with base score ≥ 45
- Prevents wasting API calls on low-quality opportunities
- Focuses LLM compute on promising candidates

**Cost per call:** ~$0.001 (1000 tokens avg)

**Output:**
```json
{
  "score": 0-100,
  "reasoning": "Brief explanation",
  "pain_point": "Extracted pain point",
  "opportunity": "Suggested solution"
}
```

### 2. Hybrid Scoring

**Formula:** `final_score = (base_score × 0.6) + (llm_score × 0.4)`

**Rationale:**
- Rule-based scoring catches obvious signals (engagement, keywords)
- LLM adds nuance (context, problem clarity, market viability)
- 60/40 weight ensures rule-based stays primary (cheaper, faster)

### 3. Integration

Modified `process_opportunities.py`:
- Import `llm_scorer.enhanced_score()` if `OPENROUTER_API_KEY` is set
- Apply LLM scoring to opportunities scoring ≥ 45
- Store LLM analysis in `llm_analysis` field
- Track LLM-enhanced count in logs

### 4. Configuration

Add to `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

Get key at: https://openrouter.ai/keys

---

## Expected Costs

### Daily Volume Estimate
- ~50 opportunities/day collected
- ~10-15 score ≥ 45 (worth LLM review)
- 10 LLM calls × $0.001 = **$0.01/day**

### Monthly Projection
- $0.01/day × 30 days = **$0.30/month**
- Well under $15 budget (2% usage)

### Worst Case
- If all 50 opportunities score ≥ 45:
  - 50 × $0.001 × 30 = $1.50/month
  - Still only 10% of budget

---

## Testing

```bash
# Test LLM scorer standalone
cd ~/saas-hunter/scripts
source ../venv/bin/activate
export OPENROUTER_API_KEY=sk-or-v1-...
python llm_scorer.py

# Test full pipeline with LLM
python process_opportunities.py
```

Expected output:
```
✓ LLM scoring enabled
Scored 48 opportunities (12 LLM-enhanced)
```

---

## Monitoring

### Track Usage
```bash
cd ~/saas-hunter/scripts
python usage_stats.py
```

Look for:
- **Tokens Used:** Should see non-zero input/output tokens
- **Cost:** Track daily spend
- **LLM-enhanced count:** How many opportunities got LLM scoring

### Check Quality
- Compare scores before/after LLM enhancement
- Read `llm_analysis` field in processed JSONL files
- Verify reasoning makes sense

---

## Rollback

If costs spiral or quality drops:

1. Remove API key from `.env`
2. Restart cron jobs (will auto-detect and disable LLM)
3. Reverts to pure rule-based scoring

No code changes needed.

---

## Next Steps

### Week 2 (Feb 15-21)
1. Monitor LLM costs daily
2. Review quality of LLM-enhanced opportunities
3. Compare digests before/after LLM
4. Tune threshold (currently 45) if needed

### Possible Improvements
- **Semantic deduplication:** Use embeddings to find similar opportunities
- **Batch processing:** Send 5-10 opportunities in one LLM call (cheaper)
- **Opportunity clustering:** Group related pain points
- **Trend detection:** LLM identifies emerging patterns

### Cost Optimization
If costs creep up:
- Raise threshold to 50 (fewer LLM calls)
- Switch to `gpt-4o-mini` (even cheaper than Haiku)
- Batch opportunities in single prompt
- Weekly LLM runs instead of every 6h

---

## Success Criteria

After 1 week with LLM:
- [ ] At least 1 high-quality (70+) opportunity/day
- [ ] Improved pain point clarity in digests
- [ ] Cost stays under $1/month
- [ ] LLM reasoning adds value (not redundant)

Review on: **2026-02-21**

---

**Status:** ✅ Ready to deploy  
**Action:** Add OpenRouter API key to `.env` and monitor
