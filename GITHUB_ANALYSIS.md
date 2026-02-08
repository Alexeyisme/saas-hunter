# GitHub Collector Analysis

## Problem Identified

**Current repos yield 0 opportunities** because:

1. **Wrong repo type** — Frameworks (React, Next.js, Kubernetes) get bug reports, not feature requests
2. **Inconsistent labels** — Different repos use different labels:
   - Next.js: "Improvement"
   - Supabase: "enhancement"
   - Many repos: No consistent feature request label
3. **Too generic** — TensorFlow users aren't your SaaS customers

## Solution: Target SaaS Tools & Developer Tools

### Recommended Repos (High Signal)

**Open Source SaaS Platforms:**
- `supabase/supabase` — Backend-as-a-service (enhancement label)
- `appwrite/appwrite` — Backend platform
- `directus/directus` — Headless CMS
- `n8n-io/n8n` — Workflow automation
- `nocodb/nocodb` — Airtable alternative
- `posthog/posthog` — Product analytics
- `meilisearch/meilisearch` — Search engine
- `hasura/graphql-engine` — GraphQL backend

**Developer Productivity:**
- `openai/openai-python` — OpenAI SDK (keep this one)
- `langchain-ai/langchain` — LLM framework
- `zed-industries/zed` — Code editor
- `excalidraw/excalidraw` — Diagramming tool

**Messaging/Communication:**
- `RocketChat/Rocket.Chat` — Chat platform
- `mattermost/mattermost` — Slack alternative
- `element-hq/element-web` — Matrix client

**AI/Automation:**
- `langgenius/dify` — LLM app platform
- `Stability-AI/StableStudio` — Image generation UI
- `invoke-ai/InvokeAI` — Stable Diffusion toolkit

**Niche SaaS:**
- `plausible/analytics` — Privacy-focused analytics
- `umami-software/umami` — Web analytics
- `ghostfolio/ghostfolio` — Wealth management
- `maybe-finance/maybe` — Personal finance

## Refined Strategy

### Option A: Drop Label Filtering
**Remove `label:"enhancement"` requirement** and rely on:
- Issue age (recent = more relevant)
- Engagement (comments, reactions)
- Keyword matching in title/body

### Option B: Multi-Label Search
Search for repos using ANY of:
- `enhancement`, `feature`, `feature-request`, `improvement`, `request`

### Option C: Hybrid
- Target smaller repos (10k-100k stars) with active communities
- Use engagement threshold (>3 comments OR >5 reactions)
- Skip label filtering entirely

## Recommended Implementation

Replace `GITHUB_REPOSITORIES` in `config.py`:

```python
GITHUB_REPOSITORIES = [
    # Open Source SaaS
    'supabase/supabase',
    'appwrite/appwrite',
    'nocodb/nocodb',
    'directus/directus',
    'n8n-io/n8n',
    'posthog/posthog',
    
    # Developer Tools
    'langchain-ai/langchain',
    'zed-industries/zed',
    'excalidraw/excalidraw',
    
    # Communication
    'RocketChat/Rocket.Chat',
    'mattermost/mattermost',
    
    # AI Tools
    'langgenius/dify',
    'invoke-ai/InvokeAI',
    
    # Analytics
    'plausible/analytics',
    'umami-software/umami'
]
```

**And simplify search query:**
```python
# Remove label filter, rely on engagement
search_query = f"is:open is:issue created:>{since_date} repo:{repo} comments:>2"
```

This should yield **5-20 opportunities per day** instead of 0.
