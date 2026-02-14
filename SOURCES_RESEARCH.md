# SaaS Hunter - Source Expansion Research

**Goal:** Find more high-signal sources for SaaS opportunities  
**Date:** 2026-02-14

---

## Current Sources

### Reddit (Active)
- r/SaaS — General SaaS discussion
- r/smallbusiness — SMB pain points
- r/sysadmin — IT infrastructure needs
- r/Entrepreneur — Startup/business ideas

### Hacker News (Active)
- Show HN — Product launches
- Ask HN — Questions/pain points
- Comments — Discussion threads

### GitHub (Active)
- Issue reactions — Feature requests
- Discussions — Community needs

---

## Proposed New Sources

### Reddit - Additional Subreddits

**High Priority (add first):**
- r/startups (700K+ members) — Founder pain points, tool discussions
- r/freelance (200K+) — Solo business needs, client management
- r/sales (200K+) — CRM, automation, sales tools
- r/marketing (900K+) — MarTech needs, analytics
- r/webdev (1.8M+) — Developer tools, hosting, frameworks
- r/devops (300K+) — Infrastructure, monitoring, deployment
- r/ecommerce (130K+) — Store management, payments, fulfillment
- r/realestate (400K+) — Property management, contracts, client tracking
- r/accounting (100K+) — Invoicing, bookkeeping, tax tools
- r/legaladvice (2M+) — Document management, contracts (look for tech solutions)

**Medium Priority:**
- r/consulting (80K+) — Client management, proposals
- r/agencylife (10K+) — Agency-specific tools
- r/productmanagement (200K+) — PM tools, roadmaps
- r/customerservice (50K+) — Support tools, ticketing
- r/restaurateur (100K+) — Restaurant POS, scheduling
- r/fitness (professional) — Gym management, client tracking

**Low Priority (niche but high-value):**
- r/msp (Managed Service Providers) — IT business tools
- r/realtors — Real estate tech
- r/dentistry — Practice management
- r/medicine (various) — Healthcare IT

### Indie Hacker Communities

**IndieHackers.com**
- Forum posts about pain points
- Product pages with common requests
- API available: https://www.indiehackers.com/api

**Maker Log / WIP.chat**
- Daily updates from indie makers
- Often mention frustrations/needs

### Product Hunt

**Areas to monitor:**
- Comment threads on new products
- "We need X feature" feedback
- Competitor comparisons

**API:** https://api.producthunt.com/v2/docs

### Twitter/X

**Search queries:**
- "I need a tool for..."
- "Why is [existing tool] so expensive"
- "Frustrated with [category]"
- "Alternative to [product]"

**Lists to monitor:**
- SaaS founders
- Indie hackers
- Small business owners

### Discord Servers

**High-signal servers:**
- Indie Hackers Discord
- Y Combinator Startup School
- SaaS Growth Hackers
- Various tech/niche communities

**Challenge:** Harder to automate, may need manual monitoring

### Linear/GitHub Public Roadmaps

**What to track:**
- Highly upvoted feature requests
- Issues with "needs" labels
- Discussion threads about missing features

### Quora

**Topics to monitor:**
- Small Business
- SaaS
- Productivity
- Industry-specific (real estate, etc.)

**Queries:**
- "What tools do you use for..."
- "Alternatives to..."
- "How do you manage..."

---

## Implementation Priority

### Phase 1 (This Week)
Add 5 high-signal Reddit subreddits:
1. r/startups
2. r/freelance  
3. r/sales
4. r/marketing
5. r/webdev

**Effort:** Minimal — just add to reddit_monitor.py config  
**Expected volume:** +20-30 opportunities/day

### Phase 2 (Next Week)
Add IndieHackers:
- Build scraper for forum/products
- Similar to HN monitor
- API makes this straightforward

**Effort:** 2-3 hours  
**Expected volume:** +10-15 opportunities/day

### Phase 3 (Week 3+)
Add Product Hunt:
- Use API to monitor new launches
- Track comment threads
- Focus on competitor mentions

**Effort:** 3-4 hours  
**Expected volume:** +5-10 opportunities/day

### Phase 4 (Future)
Twitter/X monitoring:
- Search API (may have costs)
- Track specific keywords
- Monitor founder accounts

**Effort:** 4-6 hours  
**Challenge:** API costs, rate limits

---

## Source Quality Scoring

Adjust `scoring_config.json` weights based on source quality:

**Tier 1 (20 pts):** GitHub reactions, IndieHackers upvotes  
**Tier 2 (15 pts):** HN score, Product Hunt upvotes  
**Tier 3 (12 pts):** r/smallbusiness, r/sysadmin, r/startups, r/freelance  
**Tier 4 (8 pts):** Other Reddit subreddits  
**Tier 5 (5 pts):** Twitter, Quora (lower signal/noise)

---

## Data Volume Projections

**Current:** ~50 opportunities/day  
**After Phase 1:** ~70-80/day (+5 Reddit sources)  
**After Phase 2:** ~85-95/day (+IndieHackers)  
**After Phase 3:** ~95-105/day (+Product Hunt)

**Processing cost at scale:**
- 100 opps/day × 20% score ≥45 = 20 LLM calls/day
- 20 × $0.001 × 30 days = **$0.60/month**
- Still <5% of budget

---

## Next Steps

1. **Add 5 Reddit sources** (30 min)
2. **Run backtest** to verify scoring works
3. **Monitor for 2-3 days** to check quality
4. **Add IndieHackers** if Reddit sources look good
5. **Review scoring weights** based on new data

---

**Questions to Answer:**
- Are new Reddit sources too noisy?
- Do they find different opportunities or duplicates?
- Should we adjust source weights?
- What's the optimal number of sources before diminishing returns?
