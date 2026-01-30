# Daily Ops Email - Complete Setup Guide

**Status**: Ready for Production
**Endpoints**: 2 (test-email, daily-ops-email)
**Cron Schedule**: 9:00 AM UTC daily
**Auth**: Optional VALHALLA_CRON_TOKEN

---

## Overview

The Daily Ops Email system sends a comprehensive operational summary every day at 9 AM (UTC) to the system inbox. It includes:

- **Header**: Timestamp, environment, service URL
- **Health Status**: Database, email service, API endpoint
- **Runbook Status**: Go-live state, kill switch, active engines
- **Deal Pipeline**: Counts by stage (active, under contract, sold, archived)
- **Today's Tasks**: Top 5 tasks due today with priorities
- **Yesterday's Results**: Outcome metrics (positive/neutral/negative)
- **Quick Links**: API health, governance status, runbook endpoints

---

## Components

### 1. Email Builder Module
**File**: `services/api/app/jobs/daily_ops_email.py`

**Key Functions**:
- `build_daily_ops_body(db)` - Main builder, combines all sections
- `build_header_section()` - Header with timestamp/env/URL
- `build_health_section(db)` - Health status checks
- `build_runbook_section(db)` - Governance/blocker status
- `build_deals_section(db)` - Deal pipeline counts
- `build_tasks_section(db)` - Top 5 tasks due today
- `build_outcomes_section(db)` - Yesterday's results
- `build_links_section()` - Important links
- `run()` - Main entry point, sends email

**Execution Methods**:
```bash
# Direct Python execution
python -m app.jobs.daily_ops_email

# Via HTTP endpoint (preferred)
POST /api/notify/daily-ops-email

# Via cron job
# (Configured in render.yaml)
```

---

### 2. HTTP Endpoint
**File**: `services/api/app/api/notify/test_email_router.py`

**Endpoint**: `POST /api/notify/daily-ops-email`

**Response**:
```json
{
  "ok": true,
  "sent_to": "system@valhalla.inc",
  "subject": "Heimdall: Daily Ops (9AM)",
  "summary": {
    "timestamp": "2026-01-30T14:30:45.123456+00:00",
    "body_length": 2847,
    "sections": [
      "header",
      "health_status",
      "runbook_status",
      "deal_pipeline",
      "todays_tasks",
      "yesterdays_results",
      "quick_links"
    ]
  }
}
```

**Authentication**:
- If `VALHALLA_CRON_TOKEN` is set in environment, endpoint requires:
  ```
  Authorization: Bearer {token}
  ```
- Otherwise, endpoint is public (no auth required)

---

## Cron Job Configuration

### Render Deployment

In `render.yaml`, a cron job is configured:

```yaml
  - type: cron
    name: valhalla-daily-ops
    runtime: docker
    schedule: "0 9 * * *"  # 9 AM UTC daily
    dockerCommand: /bin/sh -c "cd /app && alembic upgrade heads 2>/dev/null; /bin/sh /app/cron_daily_ops.sh"
    envVars:
      - key: CRON_MODE
        value: daily_ops
```

**Schedule**: Cron expression `0 9 * * *` = 9:00 AM UTC every day

**Execution Flow**:
1. Migrations run (if any pending)
2. `cron_daily_ops.sh` script executes
3. Checks if `CRON_MODE=daily_ops`
4. Runs `python -m app.jobs.daily_ops_email`
5. Sends email to system inbox

---

## Local Testing

### 1. Integration Test
```bash
cd /path/to/valhalla
python test_daily_ops_integration.py
```

Checks:
- Module imports
- Database connection
- Email builder sections
- Endpoint registration
- CRON_TOKEN verification
- System email configuration

### 2. Direct Module Execution
```bash
cd services/api
python -m app.jobs.daily_ops_email
```

Requires:
- Database running
- VALHALLA_SYSTEM_EMAIL set
- SMTP credentials configured (optional)

### 3. HTTP Endpoint Test
```bash
# Start API
cd services/api
python -m uvicorn app.main:app --reload

# In another terminal
curl -X POST http://localhost:8000/api/notify/daily-ops-email

# With CRON_TOKEN auth
curl -X POST \
  -H "Authorization: Bearer your_token_here" \
  http://localhost:8000/api/notify/daily-ops-email
```

### 4. Alternative HTTP Trigger (via shell script)
```bash
# Set environment
export VALHALLA_SERVICE_URL="http://localhost:8000"
export CRON_TOKEN=""  # Empty if not using token

# Run the HTTP trigger script
./cron_daily_ops_http.sh
```

---

## Environment Variables

### Required
- `VALHALLA_SYSTEM_EMAIL` - System email address (e.g., ops@valhalla.inc)

### Optional
- `DAILY_OPS_RECIPIENT_EMAIL` - Override recipient (defaults to system email)
- `VALHALLA_SERVICE_URL` - Base URL for links in email (e.g., https://api.render.com)
- `VALHALLA_CRON_TOKEN` - Token for API authentication (if set, endpoint requires auth)
- `APP_ENV` - Environment name (dev/production)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` - Email credentials

### Render Dashboard Settings
In Render dashboard, ensure these are set:

```
VALHALLA_SYSTEM_EMAIL = ops@valhalla.inc
VALHALLA_SERVICE_URL = https://your-render-api-url.com
VALHALLA_CRON_TOKEN = (optional, generate a secret token if you want auth)
SMTP_HOST = (your email provider)
SMTP_USER = (email account)
SMTP_PASS = (password or app token)
SMTP_PORT = 587 or 465
```

---

## Deployment Checklist

### Before First Deploy to Render

- [ ] Email credentials are configured (SMTP settings)
- [ ] System email is set (VALHALLA_SYSTEM_EMAIL)
- [ ] Service URL is correct (VALHALLA_SERVICE_URL)
- [ ] Cron token is generated and set (VALHALLA_CRON_TOKEN) if needed
- [ ] Render blueprint includes the cron job
- [ ] Database migrations include required tables:
  - `tasks` (for task section)
  - `deal_briefs` (for deals section)
  - `decision_outcomes` (for outcomes section)
  - `go_live_states` (for runbook section)
  - `engine_states` (for engine health)

### After Deploy

1. **Wait for 9 AM UTC** (or manually trigger sooner)
2. **Check system email inbox** - should have email titled "Heimdall: Daily Ops (9AM)"
3. **Verify email content** - check sections are populated correctly
4. **Check Render logs** - look for:
   ```
   ==> Valhalla Daily Ops Cron Job
   ==> Running daily ops email builder...
   ✅ Daily ops email sent to ops@valhalla.inc
   ```

### Troubleshooting

**Email not arriving**:
- Check SMTP credentials in Render dashboard
- Verify VALHALLA_SYSTEM_EMAIL is valid
- Check Render logs for errors
- Test with `/api/notify/test-email` endpoint first

**Missing sections in email**:
- Verify database is running and accessible
- Run integration test: `python test_daily_ops_integration.py`
- Check database has required tables

**Cron job not running**:
- Verify cron service is created in Render
- Check schedule is correct: `0 9 * * *` (9 AM UTC)
- Review Render cron job logs in dashboard

**Auth token issues**:
- If VALHALLA_CRON_TOKEN is set, make sure HTTP trigger includes header
- Test with: `curl -H "Authorization: Bearer {token}" ...`
- Remove VALHALLA_CRON_TOKEN from env if not using auth

---

## Alternative Deployment (HTTP Trigger)

Instead of running the Python module directly, you can trigger via HTTP endpoint:

```yaml
  - type: cron
    name: valhalla-daily-ops-http
    runtime: docker
    plan: starter
    region: oregon
    dockerCommand: /bin/sh -c "/bin/sh /app/cron_daily_ops_http.sh"
    schedule: "0 9 * * *"
    envVars:
      - key: VALHALLA_SERVICE_URL
        value: https://your-render-api-url.com
      - key: CRON_TOKEN
        value: your_secret_token_here
```

**Advantages**:
- Avoids direct DB access from cron
- Can be triggered from anywhere
- Easier to test/debug
- Better separation of concerns

**Script**: `cron_daily_ops_http.sh`

---

## Monitoring & Maintenance

### Check Cron Job Status
```bash
# In Render dashboard
- Services > valhalla-daily-ops
- View logs for daily runs
- Check "Last run" timestamp
```

### Manual Trigger (for testing)
```bash
# Option 1: Call endpoint directly
curl -X POST https://your-api.render.com/api/notify/daily-ops-email

# Option 2: SSH into Render and run
python -m app.jobs.daily_ops_email

# Option 3: GitHub Actions (future enhancement)
# Create workflow to trigger at specific times
```

### Disable Cron Job (if needed)
In Render dashboard:
1. Go to Services > valhalla-daily-ops
2. Click "Suspend"
3. Or delete the service entirely

---

## Future Enhancements

- [ ] HTML email template with styling
- [ ] Deal pipeline visualization (charts via HTML)
- [ ] Task details with assignee info
- [ ] Runbook blockers with links to fix instructions
- [ ] Slack/Teams integration as alternative to email
- [ ] Configurable schedule per timezone
- [ ] Email template customization (Jinja2)
- [ ] Historical tracking (archive emails)
- [ ] Alert escalation (if critical issues)

---

## Quick Reference

| Component | Location | Type |
|-----------|----------|------|
| Builder | `services/api/app/jobs/daily_ops_email.py` | Python Module |
| Endpoint | `services/api/app/api/notify/test_email_router.py` | FastAPI Router |
| Cron Config | `render.yaml` | YAML |
| Cron Script | `cron_daily_ops.sh` | Shell Script |
| HTTP Trigger | `cron_daily_ops_http.sh` | Shell Script |
| Test Suite | `test_daily_ops_integration.py` | Python Test |
| Docs | `DAILY_OPS_EMAIL.md` | This File |

---

## Support

For issues or questions:
1. Check logs in Render dashboard
2. Run integration test locally
3. Test endpoint with curl
4. Review environment variables
5. Check database connectivity

---

**Last Updated**: January 30, 2026
**Author**: Heimdall Operations
**Status**: Production Ready
