# M&A & Acquisition Sources - Research

**Purpose:** Track startup acquisitions to understand what investors value  
**Date:** 2026-02-14

---

## Why Track Acquisitions?

**Key Insights from M&A Data:**
1. **Validated Problems** - If a company was acquired, investors saw value in solving that problem
2. **Market Timing** - Shows which categories are hot right now
3. **Acquisition Multiples** - Revenue/valuation indicates market demand
4. **Feature Gaps** - Acquired products often had unique features competitors lacked
5. **Team/Tech** - Acqui-hires reveal talent/technology gaps

**Example:** DocuSign acquired for $6B → e-signature market validated  
**Opportunity:** Simpler e-signature for specific niches (real estate, SMBs)

---

## Primary Sources

### 1. Crunchbase (crunchbase.com)
**Coverage:** Global M&A, funding, IPOs  
**Features:**
- Acquisition database with deal values
- Filters by industry, stage, location
- Historical trends
- Investor activity

**API:** Yes (paid)  
**Pricing:** Free tier limited, Pro starts ~$30/month  
**Quality:** ⭐⭐⭐⭐⭐ Gold standard

**What to Track:**
- Recent SaaS acquisitions (<6 months)
- Deal size $10M-500M (sweet spot for validated ideas)
- Acquirer notes (often mention "filling gap in X")

**Example Acquisitions (from page):**
- Vectara (probable acquisition) - AI search
- Honeycomb (probable) - observability  
- Yoodli (very likely) - communication coaching

---

### 2. TechCrunch (techcrunch.com)
**Coverage:** Startup news, M&A, funding  
**Features:**
- Detailed M&A articles with rationale
- Comments reveal industry reactions
- "Why [Company] acquired [Startup]" analysis

**RSS Feed:** https://techcrunch.com/feed/  
**Quality:** ⭐⭐⭐⭐ Strong editorial

**What to Monitor:**
- M&A category: techcrunch.com/tag/mergers-acquisitions/
- Look for "acqui-hire" vs strategic acquisition
- Reader comments often reveal pain points

---

### 3. Axios Pro Rata (axios.com/newsletters/axios-pro-rata)
**Coverage:** Daily M&A newsletter  
**Features:**
- Deal announcements
- Deal rationale
- Financial terms when disclosed

**Format:** Newsletter  
**Quality:** ⭐⭐⭐⭐ Finance-focused

---

### 4. CB Insights (cbinsights.com)
**Coverage:** Market intelligence, trends  
**Features:**
- M&A heat maps by category
- Acquirer strategies
- Market maps showing consolidation

**API:** Yes (enterprise)  
**Pricing:** Enterprise only (~$50K/year)  
**Quality:** ⭐⭐⭐⭐⭐ Institutional grade

**Alternative:** Follow their blog/newsletter (free)

---

### 5. Product Hunt Acquired (producthunt.com)
**Coverage:** Tech product acquisitions  
**Features:**
- Community discusses why acquisition happened
- Often reveals feature/market gaps

**Quality:** ⭐⭐⭐ Community insights

---

### 6. Indie Hackers M&A Forum
**Coverage:** Small SaaS exits ($100K-10M)  
**Features:**
- Founder posts acquisition stories
- Reveals what made product attractive
- Buyer profiles (often private equity)

**Quality:** ⭐⭐⭐⭐ Ground-level insights

---

### 7. MicroAcquire / Acquire.com
**Coverage:** Marketplace for small SaaS sales  
**Features:**
- Active listings show what's selling
- Sold listings reveal multiples
- Categories trending

**Quality:** ⭐⭐⭐ Small deals (<$5M)

---

### 8. BizBuySell / Flippa
**Coverage:** Very small business sales  
**Features:**
- Micro-SaaS ($10K-500K)
- Shows what small buyers want
- Niche opportunities

**Quality:** ⭐⭐ Mostly tiny deals

---

### 9. SEC Filings (sec.gov)
**Coverage:** Public company acquisitions  
**Features:**
- Required disclosure of material deals
- Detailed rationale in 8-K filings
- Purchase price, earn-outs

**Search:** EDGAR database  
**Quality:** ⭐⭐⭐⭐⭐ Authoritative

---

### 10. Private Equity / VC Blogs
**Coverage:** Portfolio company exits  
**Examples:**
- a16z blog
- Sequoia blog
- Bessemer blog

**Quality:** ⭐⭐⭐ Strategic insights

---

## Data to Extract from Each Acquisition

### Deal Basics
- Company acquired
- Acquirer
- Deal size (if disclosed)
- Date
- Category/industry

### Strategic Rationale
- **Why did they buy?**
  - Fill product gap?
  - Acquire customers?
  - Talent/tech?
  - Geographic expansion?

### Market Signals
- **What problem did the acquired company solve?**
- Revenue/metrics at acquisition
- Customer base size
- Competitive positioning

### Opportunity Indicators
- **What was unique about the product?**
- Common customer complaints about alternatives
- Underserved segments
- Technology moat

---

## Implementation Plan

### Phase 1: Manual Monitoring (This Week)

**Daily checks:**
1. TechCrunch M&A tag
2. Crunchbase acquisitions feed (free)
3. Product Hunt discussions

**Weekly review:**
- Compile acquisitions
- Categorize by industry
- Extract pain points/opportunities

---

### Phase 2: Semi-Automated (Week 2)

**Build scrapers for:**
1. **TechCrunch RSS**
   - Filter for M&A articles
   - Extract deal details
   - Store in database

2. **Crunchbase API** (if budget allows)
   - Query recent acquisitions
   - Filter by SaaS category
   - Track trends

3. **Product Hunt**
   - Monitor acquisition discussions
   - Extract community insights

**Effort:** 4-6 hours  
**Output:** Weekly M&A digest

---

### Phase 3: Integration (Week 3+)

**Combine with existing pipeline:**
- Cross-reference acquired companies with Reddit pain points
- "Company X was acquired for Y → opportunity in Z niche"
- Track acquirer shopping patterns

**Example:**
- Salesforce acquires Slack → communication + CRM integration gap
- Opportunity: Simpler Slack-like tool for specific industries

---

## Scoring M&A Signals

**High-Value Acquisitions:**
- $50M-500M range (validated, not mega-corp)
- SaaS/software
- B2B focus
- Acquirer mentions "filling gap"
- Multiple bidders (competitive process)

**Acquisition Rationale = Opportunity:**
- "Adding feature X" → X is valuable
- "Serving segment Y" → Y is underserved
- "Better UX than incumbents" → UX opportunity
- "Vertical-specific solution" → niche plays work

---

## Example Analysis

### Recent SaaS Acquisition: Calendly (hypothetical $3B valuation)

**What they solved:**
- Scheduling hell (back-and-forth emails)
- Calendar sync complexity
- Time zone confusion

**Who they served:**
- Sales teams
- Customer success
- Freelancers/consultants

**What made them valuable:**
- Dead simple UX
- Instant setup
- Free tier = viral growth

**Opportunity:**
- **Calendly for X:** Healthcare (HIPAA), Legal (conflict checks), Restaurants (reservations)
- **Calendly alternative:** Privacy-focused, no branding, team scheduling

---

## Keywords to Add from M&A Data

### Acquisition Rationale Phrases
- "fill a gap in"
- "expand our capabilities in"
- "strengthen our position in"
- "acquire talent in"
- "faster time to market"

### Market Validation
- "validated product-market fit"
- "proven revenue model"
- "strong customer retention"
- "unique technology"

### Category Trends
Track which categories see most M&A:
- AI/ML tools
- Developer tools
- No-code/low-code
- Security/compliance
- Data/analytics

---

## Integration with SaaS Hunter

### New Processing Pipeline

**Input:** M&A announcements  
**Process:**
1. Extract acquired company problem/solution
2. Identify market gap they filled
3. Generate related opportunities
4. Cross-reference with Reddit/HN pain points

**Output:**
```
🎯 Acquisition Insight

Company: Calendly
Acquirer: (Hypothetical) Microsoft
Deal: $3B

Problem Solved: Meeting scheduling friction
Market: SMB, Sales, CS

Opportunity:
- Calendly for healthcare (HIPAA-compliant)
- Simpler alternative for solopreneurs
- Industry-specific scheduling (legal, education)

Related Pain Points:
- r/smallbusiness: "Calendly is too expensive for just me"
- r/freelance: "Need scheduling without branding"
```

---

## ROI Analysis

**Time Investment:**
- Phase 1 (manual): 30 min/day
- Phase 2 (semi-auto): 1 hour setup, 15 min/day
- Phase 3 (integrated): 2 hours setup, automated

**Expected Output:**
- 5-10 M&A signals/week
- 2-3 validated opportunities/week
- Higher quality than pure Reddit scraping

**Value:**
- **Investor validation** - acquisitions prove market demand
- **Timing signals** - hot categories = now is the time
- **Niche ideas** - "[Acquired Product] for [Vertical]"

---

## Next Steps

### Immediate (Today)
1. ✅ Research M&A sources
2. Set up TechCrunch M&A RSS feed
3. Create Crunchbase free account
4. Monitor for 2-3 days manually

### This Week
1. Build TechCrunch RSS scraper
2. Extract M&A data to structured format
3. Analyze 20-30 recent acquisitions
4. Identify patterns/opportunities

### Week 2
1. Add to daily digest (if valuable)
2. Cross-reference with Reddit opportunities
3. Track which categories are "hot"
4. Consider Crunchbase API (if budget allows)

---

## Success Metrics

**Good M&A source = answers:**
1. What problem did they solve? ✓
2. Why did acquirer buy? ✓
3. What was unique? ✓
4. Market size/revenue? ✓
5. Competitive gaps? ✓

If we can answer 3+ of these per acquisition, it's valuable signal.

---

**Status:** Research complete, ready to implement Phase 1  
**Recommendation:** Start with TechCrunch RSS + manual Crunchbase monitoring
