# SaaS Hunter - Deployment Guide

**Date:** 2026-02-08  
**Status:** Ready to Deploy  
**Cost:** $0/month

---

## ✅ Pre-Deployment Checklist

- [x] All scripts built and tested
- [x] Usage tracking integrated
- [x] Processing pipeline working
- [x] Digest generator functional
- [x] Telegram delivery prepared
- [ ] Cron jobs deployed
- [ ] First digest delivered

---

## Deployment Steps

### 1. Final Verification

```bash
cd ~/saas-hunter/scripts

# Test each component
../venv/bin/python3 reddit_monitor.py
../venv/bin/python3 hackernews_monitor.py
../venv/bin/python3 github_monitor.py
../venv/bin/python3 process_opportunities.py
../venv/bin/python3 generate_digest.py
../venv/bin/python3 send_telegram.py

# Check usage stats
../venv/bin/python3 usage_stats.py
```

All should run without errors.

---

### 2. Deploy Cron Jobs

```bash
crontab -e
```

**Add these lines:**

```cron
# SaaS Hunter - Data Collection
# Reddit: Every 3 hours
0 */3 * * * cd /root/saas-hunter/scripts && /root/saas-hunter/venv/bin/python3 reddit_monitor.py >> /root/saas-hunter/logs/cron.log 2>&1

# HackerNews: Every 4 hours
0 */4 * * * cd /root/saas-hunter/scripts && /root/saas-hunter/venv/bin/python3 hackernews_monitor.py >> /root/saas-hunter/logs/cron.log 2>&1

# GitHub: Daily at 6 AM UTC (1-week lookback)
0 6 * * * cd /root/saas-hunter/scripts && /root/saas-hunter/venv/bin/python3 github_monitor.py >> /root/saas-hunter/logs/cron.log 2>&1

# SaaS Hunter - Processing & Delivery
# Process: Every 6 hours (30 min after collection starts)
30 */6 * * * cd /root/saas-hunter/scripts && /root/saas-hunter/venv/bin/python3 process_opportunities.py >> /root/saas-hunter/logs/cron.log 2>&1

# Digest: Daily at 8 AM UTC
0 8 * * * cd /root/saas-hunter/scripts && /root/saas-hunter/venv/bin/python3 generate_digest.py >> /root/saas-hunter/logs/cron.log 2>&1

# Prepare Telegram: Daily at 8:01 AM UTC
1 8 * * * cd /root/saas-hunter/scripts && /root/saas-hunter/venv/bin/python3 send_telegram.py >> /root/saas-hunter/logs/cron.log 2>&1

# Send via OpenClaw: Daily at 8:02 AM UTC
2 8 * * * /root/saas-hunter/scripts/send_digest.sh >> /root/saas-hunter/logs/cron.log 2>&1

# Cleanup: Weekly (Mondays at 3 AM UTC)
0 3 * * 1 find /root/saas-hunter/data/raw -mtime +7 -name "*.json" -exec gzip {} \;
```

**Save and exit.**

---

### 3. Verify Cron Installation

```bash
# List cron jobs
crontab -l

# Should see 8 saas-hunter jobs
```

---

### 4. Monitor First Runs

```bash
# Watch cron log
tail -f ~/saas-hunter/logs/cron.log

# Or check individual logs
tail -f ~/saas-hunter/logs/processing.log
tail -f ~/saas-hunter/logs/digest.log
```

---

## Daily Digest Flow

### How It Works

**8:00 AM UTC:**
1. `generate_digest.py` runs
2. Loads last 24h processed opportunities
3. Generates markdown digest
4. Saves to `data/digests/digest_YYYYMMDD.md`

**8:01 AM UTC:**
2. `send_telegram.py` runs
3. Loads opportunities
4. Formats top 3
5. Saves to `data/telegram_queue/digest_YYYYMMDD.txt`

**8:02 AM UTC:**
3. `send_digest.sh` runs
4. Reads telegram_queue file
5. Sends via `openclaw message send`
6. Archives file as `.sent`

---

## Telegram Message Format

```
🎯 SaaS Opportunities — Feb 08, 2026

1. ⭐️ Sick of paying $40/month for Supademo (53 pts)
   📍 reddit:SaaS
   🔗 https://reddit.com/...

2. 💡 Email management AI (52 pts)
   📍 hackernews
   💬 3 comments
   🔗 https://news.ycombinator.com/...

3. 💡 Workflow automation tool (48 pts)
   📍 github:n8n-io/n8n
   👍 5 reactions
   🔗 https://github.com/...

📊 30 collected | 2 high quality (60+)

Full digest: ~/saas-hunter/data/digests/
```

---

## Troubleshooting

### Cron Not Running?

```bash
# Check if cron service is running
systemctl status cron

# Check cron log
tail -100 ~/saas-hunter/logs/cron.log

# Run manually to test
cd ~/saas-hunter/scripts && ../venv/bin/python3 reddit_monitor.py
```

### No Digest Generated?

```bash
# Check if processed opportunities exist
ls -lh ~/saas-hunter/data/processed/

# Check digest log
tail ~/saas-hunter/logs/digest.log

# Run manually
cd ~/saas-hunter/scripts && ../venv/bin/python3 generate_digest.py
```

### Telegram Not Sending?

```bash
# Check telegram queue
ls -lh ~/saas-hunter/data/telegram_queue/

# Test send manually
openclaw message send --channel telegram --target YOUR_TELEGRAM_ID --message "Test from SaaS Hunter"
```

---

## Monitoring

### Daily Checks

```bash
# View today's digest
cat ~/saas-hunter/data/digests/digest_$(date +%Y%m%d).md

# Check usage stats
cd ~/saas-hunter/scripts && ../venv/bin/python3 usage_stats.py

# View recent opportunities
cat ~/saas-hunter/data/processed/opportunities_$(date +%Y%m%d).jsonl | jq -s 'sort_by(-.score) | .[0:5]'
```

### Weekly Checks

```bash
# Last 7 days of digests
ls -lh ~/saas-hunter/data/digests/

# Usage breakdown
cd ~/saas-hunter/scripts && ../venv/bin/python3 usage_stats.py

# Check for errors
grep -i error ~/saas-hunter/logs/cron.log | tail -20
```

---

## Expected Daily Schedule

```
00:00 - Reddit collects
03:00 - Reddit collects, HN collects
06:00 - Reddit collects (Sunday: GitHub too)
06:30 - Process runs
09:00 - Reddit collects, HN collects
12:00 - Reddit collects
12:30 - Process runs
15:00 - Reddit collects, HN collects
18:00 - Reddit collects
18:30 - Process runs
21:00 - Reddit collects, HN collects

Next Day:
00:00 - Reddit collects
00:30 - Process runs
08:00 - Generate digest
08:01 - Prepare Telegram
08:02 - Send digest ← YOU GET MESSAGE
```

---

## Stopping/Pausing

### Pause All Jobs
```bash
# Comment out all saas-hunter cron jobs
crontab -e
# Add # before each line

# Or remove entirely
crontab -r
```

### Pause Specific Source
```bash
# Just comment out that source's cron line
crontab -e
```

---

## Disk Usage

**Expected growth:**
- Raw JSON: ~5MB/day (~150MB/month before cleanup)
- Processed JSONL: ~500KB/day (~15MB/month)
- Digests: ~50KB/day (~1.5MB/month)
- Logs: ~1MB/day (~30MB/month)

**Total:** ~200MB/month (negligible)

**Cleanup:** Cron compresses raw files >7 days old

---

## Success Indicators (First Week)

✅ Daily digest delivered by 8:05 AM  
✅ 10-15 opportunities/day processed  
✅ $0 token usage  
✅ No cron failures  
✅ Digest quality acceptable  

---

**Status:** Ready to Deploy  
**Next:** Run `crontab -e` to activate  
**Review:** Feb 15, 2026 @ 8 AM UTC (auto-scheduled)
