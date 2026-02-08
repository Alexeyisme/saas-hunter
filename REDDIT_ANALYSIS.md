# Reddit Collector - Critical Review

**Date:** 2026-02-08  
**Sample Size:** 18 opportunities from 6-hour collection  
**Issue:** High false positive rate

---

## Problem: Keyword Matching Too Broad

### False Positives Identified

**1. Self-Promotion Disguised as Pain Points**

❌ **"Starting a small AI MVP agency — looking to talk with SaaS founders"**
- Keyword matched: "struggling with"
- Actual content: Promoting an agency service
- **Problem:** Mentions founders "struggling" in pitch, not expressing own pain

❌ **"Validated 19 SaaS ideas in 11 months. 17 failed !!"**
- Keyword matched: "willing to pay"
- Actual content: Success story / framework promotion
- **Problem:** Mentions "willing to pay" in sales pitch

❌ **"Drop your Service, I'll find you posts & leads for free"**
- Keyword matched: "pain point"
- Actual content: Lead gen offer
- **Problem:** Uses "pain point" in marketing copy

---

**2. Competitor Complaints (Good Signal)**

✅ **"Sick of paying $40/month for Supademo just to make ONE product demo?"**
- Keyword matched: "sick of"
- Actual content: Genuine frustration with pricing
- **Quality:** HIGH — This IS a real opportunity (alternative to Supademo)

✅ **"'I'm sick of 'Renting' my life: Subscription fatigue is ruining the consumer experience."**
- Keyword matched: "sick of"
- Actual content: Real pain point about subscription model
- **Quality:** HIGH — Market insight

---

**3. Meta/Advice Posts (Low Value)**

❌ **"I stopped brainstorming business ideas. I started mining Reddit instead."**
- Keyword matched: "pain point"
- Actual content: Methodology post (ironically about what we're doing!)
- **Problem:** Uses keyword in advice, not expressing need

❌ **"Finally moved my side project to production and made my first $29"**
- Keyword matched: "struggling with"
- Actual content: Celebration post
- **Problem:** Tangential mention

---

## Analysis by Keyword

### Current 24 Keywords - Effectiveness

| Keyword | True Positives | False Positives | Precision |
|---------|---------------|-----------------|-----------|
| **"sick of"** | 2 | 1 | 67% ⚠️ |
| **"pain point"** | 1 | 3 | 25% ❌ |
| **"struggling with"** | 0 | 2 | 0% ❌ |
| **"willing to pay"** | 0 | 2 | 0% ❌ |
| **"better than"** | 1 | 0 | 100% ✅ |
| **"tired of"** | 1 | 0 | 100% ✅ |

**Pattern:** Generic business terms ("pain point", "willing to pay") are overused in marketing content.

---

## Root Causes

### 1. Context-Blind Matching
Current approach: Simple substring search in title + body  
**Problem:** Can't distinguish between:
- "I'm sick of X" (genuine pain)  
- "Are you sick of X? Try my product!" (marketing)

### 2. r/SaaS is Marketing-Heavy
- Lots of product launches
- Lots of advice posts
- Fewer genuine "I need X" posts

### 3. No Engagement Filtering
RSS doesn't provide upvotes/comments  
**Problem:** Can't filter by community validation

---

## Recommendations

### Strategy A: Refine Keywords ⭐ RECOMMENDED

**Remove marketing buzzwords:**
```python
# Remove (used in pitches):
- 'pain point'
- 'willing to pay'
- 'struggling with'

# Keep (genuine frustration):
+ 'sick of'
+ 'tired of'
+ 'frustrated with'
+ 'hate using'
+ "can't find"
+ 'why is there no'
```

**Add first-person patterns:**
```python
+ "I wish there was"
+ "I need a"
+ "I'm looking for"
+ "does anyone know"
+ "help me find"
```

**Rationale:** First-person = genuine need, not pitch

---

### Strategy B: Add Negative Filters

**Skip posts containing:**
```python
SPAM_INDICATORS = [
    'check out my',
    'i built a',
    'launching',
    'just released',
    'feedback on my',
    'introducing',
    'our platform',
    'use code',
    'lifetime deal',
    'free trial'
]
```

**Why:** Catches self-promotion even if keywords match

---

### Strategy C: Subreddit Weighting

**Adjust by signal quality:**

**High Signal (keep current):**
- r/smallbusiness (real owners with real problems)
- r/sysadmin (technical pain points)

**Medium Signal (review):**
- r/SaaS (50% marketing, 50% genuine)
- r/Entrepreneur (advice-heavy)

**Low Signal (consider dropping):**
- r/marketing (lots of pitches)
- r/saasmarketing (pure marketing content)

---

### Strategy D: Add Sentiment Analysis (Advanced)

Use simple heuristics:
```python
def is_genuine_pain(text):
    # First-person indicators
    if starts_with_first_person(text):
        score += 2
    
    # Question format
    if is_question(text):
        score += 1
    
    # Pitch indicators (negative)
    if contains_promotion(text):
        score -= 3
    
    return score > 0
```

---

## Recommended Implementation

### Phase 1: Quick Wins (Immediate)

**1. Remove Low-Precision Keywords**
```python
# Remove from REDDIT_PAIN_KEYWORDS:
- 'pain point'
- 'willing to pay'  
- 'struggling with'
```

**2. Add First-Person Keywords**
```python
# Add to REDDIT_PAIN_KEYWORDS:
+ "i wish there was"
+ "i need a"
+ "i'm looking for"
+ "does anyone know"
+ "is there a tool"
```

**3. Add Spam Filter**
```python
PROMO_INDICATORS = [
    'check out', 'i built', 'launching', 'feedback on my',
    'lifetime deal', 'discount', 'coupon'
]

# In reddit_monitor.py:
if any(indicator in text for indicator in PROMO_INDICATORS):
    continue  # Skip this post
```

---

### Phase 2: Subreddit Tuning (Week 2)

**Test signal quality per subreddit:**
```python
# Track for 1 week:
{
  "r/SaaS": {"collected": 50, "relevant": 15, "precision": 30%},
  "r/smallbusiness": {"collected": 10, "relevant": 8, "precision": 80%}
}
```

**Drop subreddits with <40% precision**

---

### Phase 3: Advanced Filtering (Month 2)

- Add simple NLP (spaCy for entity/intent detection)
- Score posts by multiple signals
- A/B test keyword combinations

---

## Expected Improvements

### Before (Current)
- 18 opportunities collected
- ~6 genuine (33% precision)
- 12 false positives (marketing/advice)

### After Phase 1
- ~12 opportunities collected
- ~8 genuine (67% precision)
- 4 false positives

**Trade-off:** Fewer results, but higher quality

---

## Positive Findings

### What IS Working

✅ **"sick of X" posts are goldmines**
- "Sick of paying $40/month for Supademo" → Real opportunity
- "Sick of 'Renting' my life" → Market insight

✅ **"better than" comparisons**
- "Is this UX better than a spreadsheet?" → Product validation

✅ **r/smallbusiness has high signal**
- Real business owners, real problems
- Less marketing spam

---

## Action Items

### Immediate (Today)
- [ ] Remove 3 low-precision keywords
- [ ] Add 5 first-person keywords
- [ ] Add spam filter (10 promo indicators)
- [ ] Test on fresh 6-hour window

### This Week
- [ ] Track precision per subreddit
- [ ] Identify top 3 subreddits by signal
- [ ] Consider dropping r/marketing, r/saasmarketing

### This Month
- [ ] Build simple scoring system
- [ ] A/B test keyword combinations
- [ ] Document best practices

---

## Conclusion

**Current State:** 33% precision (too many false positives)  
**Target:** 60-70% precision (acceptable for daily collection)  
**Path:** Refine keywords + add spam filters + drop low-signal subreddits

**Recommendation:** Implement Phase 1 immediately (10 minutes of work, 2x improvement expected)

---

**Next:** Apply recommended keyword changes and test?
