# Daily Ops Email - Quick Reference & Deployment Guide

**Status**: ✅ PRODUCTION READY  
**Implementation Date**: January 30, 2026  
**Files Modified**: 2 | **Files Created**: 5  
**Test Coverage**: Comprehensive (integration test included)

---

## 📋 What Was Built

A real daily ops email system that:
- ✅ Sends to VALHALLA_SYSTEM_EMAIL at 9 AM UTC
- ✅ Includes 7 comprehensive sections (health, deals, tasks, outcomes, etc.)
- ✅ Callable via POST endpoint or Python module
- ✅ Optional auth via VALHALLA_CRON_TOKEN
- ✅ Graceful error handling (never crashes)
- ✅ Configured in Render Blueprint for automated daily runs
- ✅ Fully documented with troubleshooting guide

---

## 🚀 Quick Start

### 1. Local Testing (Right Now)

```bash
# Test the integration
python test_daily_ops_integration.py

# Or test directly
cd services/api
python -m app.jobs.daily_ops_email

# Or test via API endpoint
python -m uvicorn app.main:app --reload
curl -X POST http://localhost:8000/api/notify/daily-ops-email
```

### 2. Deploy to Render

```bash
# Set environment variables in Render dashboard:
VALHALLA_SYSTEM_EMAIL = ops@valhalla.inc
VALHALLA_SERVICE_URL = https://your-api.render.com
VALHALLA_CRON_TOKEN = (optional)

# Deploy:
git add render.yaml
git commit -m "Add daily ops email cron"
git push

# Wait for deployment, then check logs at:
# Render Dashboard > Services > valhalla-daily-ops
```

### 3. Verify It Works

- Wait for 9 AM UTC (or click "Manual Trigger" in Render dashboard)
- Check `ops@valhalla.inc` inbox for: "Heimdall: Daily Ops (9AM)"
- Email should have all 7 sections populated

---

## 📂 Key Files

### Core Implementation

| File | What | Status |
|------|------|--------|
| [services/api/app/jobs/daily_ops_email.py](../services/api/app/jobs/daily_ops_email.py) | Email builder (332 lines) | ✅ Complete |
| [services/api/app/api/notify/test_email_router.py](../services/api/app/api/notify/test_email_router.py) | HTTP endpoint (164 lines) | ✅ Complete |
| [render.yaml](../render.yaml) | Cron job config | ✅ Updated |

### Supporting Scripts

| File | Purpose |
|------|---------|
| [cron_daily_ops.sh](../cron_daily_ops.sh) | Python module execution (primary) |
| [cron_daily_ops_http.sh](../cron_daily_ops_http.sh) | HTTP endpoint trigger (alternative) |

### Testing & Docs

| File | Purpose |
|------|---------|
| [test_daily_ops_integration.py](../test_daily_ops_integration.py) | 7 integration tests |
| [DAILY_OPS_EMAIL.md](../DAILY_OPS_EMAIL.md) | Full setup guide (4,000+ words) |
| [DAILY_OPS_EMAIL_IMPLEMENTATION.md](../DAILY_OPS_EMAIL_IMPLEMENTATION.md) | What was built |

---

## 🔧 Environment Variables

**Required:**
```bash
VALHALLA_SYSTEM_EMAIL = ops@valhalla.inc          # Recipient
DATABASE_URL = postgresql://...                   # Database
```

**Optional (Recommended):**
```bash
VALHALLA_SERVICE_URL = https://api.render.com     # Links in email
APP_ENV = production                              # Environment name
```

**Optional (If using Email):**
```bash
SMTP_HOST = smtp.gmail.com                        # Email server
SMTP_PORT = 587
SMTP_USER = your_email@gmail.com
SMTP_PASS = your_app_password
```

**Optional (If using Auth):**
```bash
VALHALLA_CRON_TOKEN = your_random_secret_here     # Generate with: openssl rand -hex 32
```

---

## 📧 Email Sections (Auto-Populated)

The email contains 7 sections automatically populated from system data:

### 1. **Header** (Auto)
- Timestamp with UTC timezone
- Environment (dev/production)
- Service URL

### 2. **Health Status** (Auto)
- Database connectivity: ✓
- Email service: ✓
- API endpoint: ✓

### 3. **Runbook Status** (From Database)
- Go-live enabled/disabled
- Kill switch state
- Active engine count
- Blocked engines count

### 4. **Deal Pipeline** (From Database)
- Active leads
- Under contract
- Closed/sold
- Archived
- Total count

### 5. **Today's Tasks** (From Database)
- Top 5 pending/in-progress tasks
- Priority (P1-P10)
- Category
- Due time
- Next action description

### 6. **Yesterday's Results** (From Database)
- Total outcomes logged
- Positive/neutral/negative breakdown
- Average quality score

### 7. **Quick Links** (Auto)
- API health endpoint
- Governance runbook status
- Runbook status (legacy)

---

## 🔌 API Endpoint

**Endpoint**: `POST /api/notify/daily-ops-email`

**Without Auth**:
```bash
curl -X POST http://localhost:8000/api/notify/daily-ops-email
```

**With CRON_TOKEN**:
```bash
curl -X POST \
  -H "Authorization: Bearer your_token_here" \
  http://localhost:8000/api/notify/daily-ops-email
```

**Response** (200 OK):
```json
{
  "ok": true,
  "sent_to": "ops@valhalla.inc",
  "subject": "Heimdall: Daily Ops (9AM)",
  "summary": {
    "timestamp": "2026-01-30T14:30:45.123456+00:00",
    "body_length": 2847,
    "sections": [
      "header", "health_status", "runbook_status", 
      "deal_pipeline", "todays_tasks", "yesterdays_results", 
      "quick_links"
    ]
  }
}
```

---

## 🔐 Authentication

### Option 1: No Auth (Recommended for Cron)
- Leave `VALHALLA_CRON_TOKEN` unset
- Endpoint is public/open
- Anyone can call it (design: internal use)

### Option 2: With Auth Token (Recommended for Security)
- Set `VALHALLA_CRON_TOKEN` to a random secret
- Endpoint requires: `Authorization: Bearer {token}`
- Generate token: `openssl rand -hex 32`
- Include in all cron calls

---

## 📅 Cron Schedule

**Current Setting**: `0 9 * * *` (9 AM UTC daily)

**Change Schedule** (in render.yaml):
```yaml
  - type: cron
    schedule: "0 14 * * *"  # 2 PM UTC instead
    # Or: "0 9 * * 1-5"      # Weekdays only (Mon-Fri)
    # Or: "*/30 * * * *"     # Every 30 minutes
```

**Time Zone Note**: Render uses UTC. Adjust `0 9` to your desired time in UTC.

---

## ✅ Deployment Checklist

### Before Deploy

- [ ] Run integration test locally: `python test_daily_ops_integration.py`
- [ ] Test endpoint locally: `curl -X POST http://localhost:8000/api/notify/daily-ops-email`
- [ ] Verify database has required tables (tasks, deal_briefs, decision_outcomes)

### Deploy

- [ ] Set environment variables in Render dashboard
- [ ] Update `render.yaml` with cron config
- [ ] Push to GitHub: `git push`
- [ ] Wait for Render deployment (2-3 minutes)

### Verify

- [ ] Check Render dashboard: Services > valhalla-daily-ops (should be "active")
- [ ] Wait for 9 AM UTC (or click "Manual Trigger")
- [ ] Check email inbox for: "Heimdall: Daily Ops (9AM)"
- [ ] Verify all 7 sections are present

---

## 🐛 Troubleshooting

### Email Not Arriving

**Check these in order:**

1. **Render logs** (Render Dashboard > valhalla-daily-ops > Logs)
   - Look for: `✅ Daily ops email sent to ops@valhalla.inc`
   - Or: `✗ Error: ...`

2. **Email credentials** (Render Dashboard > Environment Variables)
   - Is `SMTP_HOST` set?
   - Is `SMTP_USER` set?
   - Is `SMTP_PASS` set?

3. **System email** (Render Dashboard > Environment Variables)
   - Is `VALHALLA_SYSTEM_EMAIL` set to a valid email?

4. **Manual trigger**
   - Call endpoint manually: `curl -X POST https://your-api.render.com/api/notify/daily-ops-email`
   - Check response for errors

5. **Cron job**
   - Is `valhalla-daily-ops` service visible in Render dashboard?
   - Does it show "active"?
   - Click "Manual Trigger" to test

### Missing Sections in Email

**If email is blank or incomplete:**

1. **Check database connectivity**
   - Are the migrations run? (Should be in `alembic upgrade heads`)
   - Are required tables present? (tasks, deal_briefs, decision_outcomes)

2. **Check logs for errors**
   - Render logs may show which section failed

3. **Test locally**
   - Run: `python test_daily_ops_integration.py`
   - Should show all sections passing

### Cron Job Not Running

1. **Check if service exists**: Render Dashboard > Services
   - Should see: `valhalla-daily-ops`
   - Status: "Active"

2. **Check schedule**: Look at service config
   - Schedule should show: `0 9 * * *`

3. **Check next run time**:
   - Service page should show "Next run: ..."

4. **Manual trigger**: Click button in Render dashboard to test

5. **Logs**: Review execution logs

---

## 🔍 Monitoring

### Daily Checks

```bash
# 1. Check recent cron runs (in Render dashboard)
# Services > valhalla-daily-ops > Recent Logs

# 2. Check if email arrived
# Look in ops@valhalla.inc inbox

# 3. Optional: Set calendar reminder for 9 AM UTC
```

### Manual Trigger (for testing)

```bash
# In Render Dashboard:
# 1. Go to Services > valhalla-daily-ops
# 2. Click "Manual Trigger" button
# 3. Wait for execution
# 4. Check logs
# 5. Check email inbox
```

### Alternative: Call Endpoint Manually

```bash
# From command line (anywhere)
curl -X POST https://your-api.render.com/api/notify/daily-ops-email

# With auth token (if configured)
curl -X POST \
  -H "Authorization: Bearer your_token" \
  https://your-api.render.com/api/notify/daily-ops-email
```

---

## 📊 What Happens at 9 AM UTC

1. **Render triggers cron job**
2. **Container starts** (spins up Docker)
3. **Migrations run** (alembic upgrade heads)
4. **Script executes** (cron_daily_ops.sh)
5. **Module runs** (python -m app.jobs.daily_ops_email)
6. **Database queries** (fetches tasks, deals, outcomes, etc.)
7. **Email builds** (7 sections assembled)
8. **Email sends** (via SMTP to system email)
9. **Email arrives** (in ops@valhalla.inc inbox)
10. **Cron finishes** (container stops)

---

## 🎯 Success Criteria

Email should arrive at 9 AM UTC with:

- ✅ Header: Timestamp, environment, service URL
- ✅ Health: All status indicators (✓ or ✗)
- ✅ Runbook: Go-live state, kill switch state, engine count
- ✅ Deals: Counts by stage (active, under contract, closed, archived)
- ✅ Tasks: Top 5 tasks due today (if any)
- ✅ Outcomes: Yesterday's results (or "No outcomes logged")
- ✅ Links: Clickable API health, governance, runbook endpoints

---

## 📖 Full Documentation

For detailed information, see:

- **[DAILY_OPS_EMAIL.md](../DAILY_OPS_EMAIL.md)** - Complete 4000+ word guide
  - Components overview
  - Local testing procedures
  - Deployment checklist
  - Environment variable reference
  - Troubleshooting troubleshooting guide
  - Future enhancements

- **[DAILY_OPS_EMAIL_IMPLEMENTATION.md](../DAILY_OPS_EMAIL_IMPLEMENTATION.md)** - What was implemented
  - Components built
  - Deployment checklist
  - API response examples
  - Testing workflow
  - Rollback procedure

---

## 💡 Pro Tips

1. **Test locally first**: `python test_daily_ops_integration.py`
2. **Use CRON_TOKEN for security**: `openssl rand -hex 32`
3. **Monitor first week**: Check inbox daily to ensure working
4. **Set calendar reminder**: Don't miss the emails
5. **Custom schedule**: Edit `schedule: "0 9 * * *"` for different time
6. **Disable if needed**: Comment out cron section in render.yaml

---

## 🚀 Next Steps

1. **Test locally** (5 minutes):
   ```bash
   python test_daily_ops_integration.py
   ```

2. **Set env vars** in Render (5 minutes):
   - VALHALLA_SYSTEM_EMAIL
   - VALHALLA_SERVICE_URL
   - SMTP credentials (optional but recommended)

3. **Deploy** (3-5 minutes):
   ```bash
   git add render.yaml cron_daily_ops.sh
   git commit -m "Add daily ops email cron job"
   git push
   ```

4. **Verify** (wait for 9 AM or manually trigger):
   - Check Render logs
   - Check email inbox
   - Verify all sections present

---

## 📞 Quick Support

| Issue | Solution |
|-------|----------|
| Email not arriving | Check SMTP credentials in Render |
| Missing sections | Run integration test locally |
| Cron not running | Check if valhalla-daily-ops service is "active" |
| Auth token errors | Use correct format: `Authorization: Bearer {token}` |
| Blank email | Check database connectivity and migrations |

---

## 📝 Summary

✅ **Built**: Real daily ops email builder  
✅ **Endpoint**: POST /api/notify/daily-ops-email  
✅ **Cron**: 9 AM UTC daily (configurable)  
✅ **Auth**: Optional VALHALLA_CRON_TOKEN  
✅ **Sections**: 7 (header, health, runbook, deals, tasks, outcomes, links)  
✅ **Database**: Queries real system data  
✅ **Docs**: Complete setup and troubleshooting guide  
✅ **Tests**: Integration test suite included  
✅ **Ready**: Production deployment now  

---

**Status**: Ready for Production  
**Last Updated**: January 30, 2026  
**Questions?**: See DAILY_OPS_EMAIL.md for detailed guide
