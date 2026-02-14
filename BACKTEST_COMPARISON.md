# Backtest Comparison - Scoring Config Analysis

**Date:** 2026-02-14  
**Data:** Last 7 days (261 unique opportunities after deduplication)

---

## Results Summary

| Config | Avg Score | Max Score | Top Tier (80+) | High Quality (60-79) | Worth Exploring (40-59) | Low Signal (<40) |
|--------|-----------|-----------|----------------|----------------------|------------------------|------------------|
| **Baseline (v1.0)** | 32.4 | 64 | 0 (0%) | 1 (0.4%) | 48 (18.4%) | 212 (81.2%) |
| **Pain Boost (v1.1)** | 36.9 | 76 | 0 (0%) | 14 (5.4%) | 79 (30.3%) | 168 (64.4%) |
| **Business Focus (v1.2)** | 44.4 | 91 | 4 (1.5%) | 41 (15.7%) | 101 (38.7%) | 115 (44.1%) |
| **Aggressive (v1.3)** | 52.4 | 100 | 17 (6.5%) | 60 (23.0%) | 129 (49.4%) | 55 (21.1%) |
| **Balanced (v1.4)** | 45.6 | 92 | 6 (2.3%) | 41 (15.7%) | 109 (41.8%) | 105 (40.2%) |

---

## Detailed Analysis

### 1. Baseline (v1.0) - Current Production

**Pros:**
- Conservative scoring
- Low false positive rate
- Clear signal when something scores 60+

**Cons:**
- Misses too many opportunities
- Only 1 opportunity >60 in 7 days
- 81% classified as "low signal" (likely has hidden gems)

**Top Opportunity:**
- [64] Hacker News Alternative Where People Are Positive About AI

**Verdict:** ❌ Too conservative, missing opportunities

---

### 2. Pain Boost (v1.1)

**Changes:**
- Increased pain signal scores: 10→15
- Added more pain keywords: "nightmare", "terrible", "sucks", "ridiculous"
- Added time waste category (10 pts)
- Boosted willingness to pay: 10→12

**Pros:**
- Better pain point detection
- 14 high-quality vs 1 baseline
- Still reasonable false positive rate

**Cons:**
- Avg score still low (36.9)
- No top-tier (80+) opportunities
- May still be missing business-focused opportunities

**Top Opportunity:**
- [76] Reviewtrics - AI Review Analysis for E-commerce

**Verdict:** ✅ Improvement but not enough

---

### 3. Business Focus (v1.2)

**Changes:**
- Boosted business subreddit weights (smallbusiness, startups, freelance)
- Massive boost to willingness_to_pay: 10→18
- Added ROI mentions category (10 pts)
- Increased business context scoring: 5→10
- More competitor names in detection

**Pros:**
- 4 top-tier opportunities (vs 0 in baseline)
- 41 high-quality (15.7% vs 0.4%)
- Avg score 44.4 (much better signal)
- Good balance of precision/recall

**Cons:**
- May favor $ mentions too much
- Could miss technical pain points

**Top Opportunities:**
- [91] How did you reduce admin time as a solo business owner? I'm drowning
- [84] Reviewtrics - AI Review Analysis for E-commerce
- [83] Found out my competitor dropped prices 3 weeks late

**Verdict:** ✅✅ Strong candidate - focuses on monetizable pain

---

### 4. Aggressive (v1.3)

**Changes:**
- Boosted everything: pain (18), willingness to pay (20), urgent need (15)
- Increased source weights across the board
- Added urgent need category
- More keywords in every category

**Pros:**
- 17 top-tier opportunities (6.5%)
- 60 high-quality (23%)
- Only 21% low signal (vs 81% baseline)
- Max score 100

**Cons:**
- ⚠️ Risk of score inflation
- May be too generous - are these all truly great?
- Could create false confidence

**Top Opportunities:**
- [100] How did you reduce admin time as a solo business owner?
- [93] $321k ARR as solo founder but burning out (appears twice - dedup issue?)
- [92] Anyone else tired of doing everything alone in business?

**Verdict:** ⚠️ Too aggressive - need to validate top 20 manually

---

### 5. Balanced (v1.4)

**Changes:**
- Middle ground between Business Focus and Aggressive
- Pain signals: 14 (not 18)
- Willingness to pay: 16 (not 20)
- Moderate source weight increases
- Added more keywords but not extreme

**Pros:**
- 6 top-tier (2.3%) - meaningful but not inflated
- 41 high-quality (15.7%)
- Avg 45.6 (good signal without inflation)
- 40% low signal (filtered half the noise)

**Cons:**
- None significant

**Top Opportunities:**
- [92] How did you reduce admin time as a solo business owner?
- [88] Reviewtrics - AI Review Analysis for E-commerce
- [86] Found out my competitor dropped prices 3 weeks late

**Verdict:** ✅✅✅ Best balance - recommended for production

---

## Key Insights

### 1. Pain + Money = Signal
Opportunities mentioning both frustration AND pricing/cost score highest across all configs.

Example: "Sick of paying $100+/mo for SaaS analytics"

### 2. Business Context Matters
Subreddits like r/smallbusiness, r/startups, r/freelance have higher conversion potential than general r/SaaS chatter.

### 3. Specificity Helps
Longer posts with numbers/metrics tend to be more actionable.

### 4. Keywords to Add

**Strong performers:**
- Pricing/cost indicators: "$100", "/month", "subscription", "expensive"
- Pain: "frustrated with", "sick of", "tired of", "nightmare"
- Time waste: "manual", "repetitive", "hours spent"
- Business: "clients", "customers", "agency", "revenue"
- Urgency: "need", "must have", "critical"

**Consider adding:**
- Brand names: "docusign", "salesforce", "hubspot", "zapier", "notion"
- SMB pain: "spreadsheet", "excel", "google sheets", "manual tracking"
- Scale indicators: "growing", "scaling", "team size"
- Integration needs: "integrate", "connect", "sync"

### 5. Source Quality Tiers

**Tier 1 (most valuable):**
- reddit:smallbusiness
- reddit:startups
- reddit:freelance
- GitHub reactions

**Tier 2:**
- reddit:sysadmin
- reddit:sales
- reddit:marketing
- Hacker News

**Tier 3:**
- reddit:SaaS (more noise, self-promotion)
- reddit:entrepreneur (mixed quality)

---

## Recommendation: Deploy "Balanced" Config

**Why Balanced (v1.4)?**

1. **Good signal without inflation**
   - 6 top-tier opps (2.3%) feels right
   - Max score 92 (not hitting ceiling)
   - 41 high-quality (enough to review daily)

2. **Filtered half the noise**
   - 40% low signal vs 81% baseline
   - Still conservative enough to trust

3. **Catches business pain + willingness to pay**
   - Top opps mention both frustration and money
   - Business context weighted appropriately

4. **Room to tune**
   - Not maxed out - can still boost specific signals
   - LLM layer will add another 40% weight on top

---

## Next Steps

### 1. Deploy Balanced Config
```bash
cp scoring_config_balanced.json scoring_config.json
```

### 2. Add More Keywords

**High priority additions:**
```json
"pain_point_signals": {
  "strong_pain": {
    "phrases": [...existing..., "struggling with", "pain point", "headache", "difficult to"]
  }
}
```

**Business context:**
```json
"market_signals": {
  "business_context": {
    "phrases": [...existing..., "freelancer", "consultant", "solopreneur", "small team"]
  }
}
```

**Integration pain:**
```json
"integration_needs": {
  "phrases": ["integrate with", "connect to", "sync with", "export to", "api for"],
  "score": 8
}
```

### 3. Monitor Live Performance

After deploying Balanced:
- Review next 3 daily digests
- Check if top 10 are actually good
- Tune weights if needed

### 4. Add LLM Enhancement

Current configs are rule-based only. Adding LLM will:
- Apply 40% additional weight to opps scoring ≥45
- Better context understanding
- Est. cost: $0.30-0.60/month

---

## Test Commands

```bash
cd ~/saas-hunter/scripts
source ../venv/bin/activate

# Rerun any config
python backtest.py --days 7 --config scoring_config_balanced.json --output test.json

# Compare results
cat ../data/backtests/baseline.txt
cat ../data/backtests/balanced.txt
```

---

## Appendix: Full Config Files

Saved in ~/saas-hunter/:
- `scoring_config.json` - Current production (baseline)
- `scoring_config_pain_boost.json` - v1.1
- `scoring_config_business.json` - v1.2
- `scoring_config_aggressive.json` - v1.3
- `scoring_config_balanced.json` - v1.4 ⭐ **RECOMMENDED**
