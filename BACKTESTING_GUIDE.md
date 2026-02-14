# SaaS Hunter - Backtesting Guide

**Purpose:** Rapidly test scoring configurations without waiting for new data

---

## Quick Start

```bash
cd ~/saas-hunter/scripts
source ../venv/bin/activate

# Run backtest with default config (last 7 days)
python backtest.py

# Test different time periods
python backtest.py --days 14

# Test with custom config
cp ../scoring_config.json ../scoring_config_v2.json
# Edit scoring_config_v2.json...
python backtest.py --config scoring_config_v2.json
```

---

## What It Does

1. **Loads historical raw data** from `~/saas-hunter/data/raw/`
2. **Applies current scoring config** from `scoring_config.json`
3. **Deduplicates** opportunities
4. **Generates analysis report** showing:
   - Score distribution
   - Top 10 opportunities
   - Source breakdown
   - Domain classification

5. **Saves results** to `~/saas-hunter/data/backtests/`

---

## Workflow: Tune Scoring Weights

### 1. Run Baseline

```bash
python backtest.py --days 7
```

Review the results:
- Are the top 10 actually interesting?
- What's the score distribution?
- Any obvious misses?

### 2. Adjust Config

Edit `scoring_config.json`:

```json
{
  "source_weights": {
    "reddit:startups": 15  // Increase if startups posts are high quality
  },
  "pain_point_signals": {
    "strong_pain": {
      "phrases": ["sick of", "frustrated", "hate", "tired of"],
      "score": 15  // Increase to boost pain point detection
    }
  }
}
```

### 3. Rerun Backtest

```bash
python backtest.py --days 7 --output backtest_v2.json
```

### 4. Compare Results

```bash
# View both reports
cat ~/saas-hunter/data/backtests/backtest_20260214_104500.txt
cat ~/saas-hunter/data/backtests/backtest_v2.txt

# Look for improvements:
# - Did avg score go up?
# - Are top 10 better?
# - Did high-quality count increase?
```

### 5. Iterate

Keep tweaking until you're satisfied, then deploy:

```bash
# Backtest looks good? Deploy to production
cp scoring_config.json scoring_config_backup.json
# scoring_config.json is already updated, just confirm it's what you want
```

---

## Example: Finding Optimal Weights

**Goal:** Maximize high-quality opportunities (60+) without inflating scores

### Iteration 1: Baseline
```bash
python backtest.py
```
**Result:** 48 opps, avg score 52, only 1 high-quality (60+)

### Iteration 2: Boost Pain Signals
Edit `scoring_config.json`:
```json
"strong_pain": {"score": 15}  // was 10
"willingness_to_pay": {"score": 12}  // was 10
```

```bash
python backtest.py --output backtest_pain_boost.json
```
**Result:** 48 opps, avg score 56, 8 high-quality

### Iteration 3: Increase Source Weights
```json
"reddit:startups": 15  // was 12
"reddit:sales": 12  // was 10
```

```bash
python backtest.py --output backtest_source_boost.json
```
**Result:** 48 opps, avg score 58, 12 high-quality

**Decision:** Deploy Iteration 3 config

---

## Config Parameters

### Source Weights (Max 20 points)
Higher = more credible source

```json
"source_weights": {
  "github": 20,           // Reactions = validated need
  "hackernews": 15,       // Tech-savvy audience
  "reddit:startups": 12,  // Founder-focused
  "reddit:saas": 8        // General SaaS talk
}
```

### Pain Point Signals (Max ~20-30 points)
Keywords indicating clear problems

```json
"pain_point_signals": {
  "strong_pain": {
    "phrases": ["sick of", "frustrated", "hate"],
    "score": 10
  },
  "willingness_to_pay": {
    "phrases": ["would pay", "expensive", "pricing"],
    "score": 10
  }
}
```

### Engagement Weights (Max 25 points)
Social proof signals

```json
"engagement_weights": {
  "github_reaction_multiplier": 2,  // 10 reactions = 20 pts
  "github_reaction_max": 15,
  "comments_max": 10
}
```

### Specificity (Max 15 points)
Detail level in the post

```json
"specificity_scoring": {
  "long_body_threshold": 300,
  "long_body_score": 10
}
```

---

## Backtesting Best Practices

### 1. Use Consistent Time Periods
Compare apples-to-apples:
```bash
# Always test against same 7-day window
python backtest.py --days 7
```

### 2. Version Your Configs
```bash
cp scoring_config.json scoring_config_v1.0.json
# Make changes...
cp scoring_config.json scoring_config_v1.1.json
```

### 3. Document Changes
Add notes to config:
```json
{
  "version": "1.1",
  "changelog": "Boosted pain signals +5pts, increased startups weight to 15"
}
```

### 4. Manual Validation
Don't just trust scores — actually read the top 10:
```bash
python backtest.py > results.txt
# Read results.txt - are top 10 genuinely interesting?
```

### 5. Watch for Inflation
If avg score goes from 50 → 70 but quality didn't improve, you're just inflating numbers.

---

## Common Tuning Scenarios

### "Top opportunities are all from one source"
**Fix:** Lower that source's weight or raise others

### "Missing obvious pain points"
**Fix:** Add more phrases to `pain_point_signals`

### "Scores too conservative (nothing >70)"
**Fix:** Increase max values in engagement/pain weights

### "Scores too inflated (everything >80)"
**Fix:** Decrease source weights and pain scores

### "Duplicates getting through"
**Fix:** Check `deduplicate_opportunities()` threshold (not in config yet)

---

## Output Files

```
~/saas-hunter/data/backtests/
├── backtest_20260214_104500.json    # Full results + opportunities
├── backtest_20260214_104500.txt     # Human-readable report
├── backtest_v2.json
└── backtest_v2.txt
```

**JSON contains:**
- All scored opportunities
- Config used
- Summary stats
- Full report text

**TXT contains:**
- Score distribution
- Top 10 list
- Source/domain breakdown

---

## Integration with Live System

Once you've found optimal weights:

1. **Update production config:**
   ```bash
   # scoring_config.json is already being used by process_opportunities.py
   # Just confirm your changes are there
   ```

2. **Next processing run uses new config automatically**

3. **Monitor results:**
   ```bash
   python usage_stats.py
   # Check if high-quality count improves
   ```

4. **Review next digest:**
   - Are opportunities better?
   - Compare to previous day's digest

---

## Advanced: A/B Testing Configs

```bash
# Test two configs side-by-side
python backtest.py --config scoring_config_A.json --output test_A.json
python backtest.py --config scoring_config_B.json --output test_B.json

# Compare results
diff data/backtests/test_A.txt data/backtests/test_B.txt
```

---

## Troubleshooting

**"No data found"**
- Check `~/saas-hunter/data/raw/` has JSON files
- Try `--days 14` for wider time range

**"Import error"**
- Make sure you're in venv: `source ../venv/bin/activate`
- Check `scoring.py` exists

**"Scores don't change"**
- Verify you edited the right `scoring_config.json`
- Reload config: restart Python or reimport

---

## Next Steps

1. **Run baseline backtest** to see current performance
2. **Identify weak spots** (missed opportunities, false positives)
3. **Tune config** based on findings
4. **Backtest again** to validate improvements
5. **Deploy to production** when satisfied
6. **Monitor live results** to confirm improvements

---

**Questions?** See `IMPLEMENTATION_PLAN.md` for broader context
