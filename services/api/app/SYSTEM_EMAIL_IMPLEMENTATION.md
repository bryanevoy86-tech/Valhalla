# System Email Identity Implementation Guide

**Status**: ✅ COMPLETE

This document describes the implementation of centralized system email identity configuration for Valhalla Legacy Inc.

---

## Overview

The system now has a single, centralized source of truth for system email identity. This ensures:

- **Consistency**: All outbound emails come from `ValhallaLegacyInc@gmail.com`
- **Maintainability**: Changing the email requires NO code changes
- **Security**: Guardrails prevent unauthorized email usage
- **Auditability**: System email is exposed in governance APIs

---

## Environment Variables

### Required
Set these in your `.env` (local) and Render → Environment Variables:

```
VALHALLA_SYSTEM_EMAIL=ValhallaLegacyInc@gmail.com
VALHALLA_FROM_NAME=Valhalla Legacy Inc
```

### Existing SMTP Configuration
Ensure these are also set (already configured):

```
SMTP_HOST=your.smtp.host
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASS=your-smtp-password
```

---

## Architecture

### 1. Core Identity Module

**File**: `app/core/identity.py`

Single source of truth for system email and display name:

```python
from app.core.identity import system_identity, get_system_email

# Get full identity
identity = system_identity()
print(identity["email"])      # ValhallaLegacyInc@gmail.com
print(identity["from_name"])  # Valhalla Legacy Inc

# Get just the email
email = get_system_email()    # ValhallaLegacyInc@gmail.com
```

**Guarantees**:
- Raises `RuntimeError` if `VALHALLA_SYSTEM_EMAIL` is not set
- Defaults `VALHALLA_FROM_NAME` to "Valhalla Legacy Inc"
- Cached at module load time for performance

---

### 2. Email Service

**File**: `app/services/email_service.py`

Integrates system identity with SMTP for sending emails:

```python
from app.services.email_service import send_email, send_summary

# Send a basic email
send_email(
    to_email="recipient@example.com",
    subject="Alert",
    body="System alert text",
)

# Send a summary to the system inbox
send_summary(
    subject="Daily Ops Summary",
    body="Today's summary...",
)
```

**Features**:
- Automatically uses system email as sender
- Properly formats From header: `Valhalla Legacy Inc <email@example.com>`
- Optional HTML email body support
- Graceful error handling (returns False on failure)

---

### 3. Daily Summary Service

**File**: `app/services/daily_summary.py`

Helper functions for building and sending daily summaries:

```python
from app.services.daily_summary import (
    get_default_summary_recipient,
    send_daily_summary,
    format_summary_report,
)

# Get where summaries should go
recipient = get_default_summary_recipient()  # Returns system email

# Send a summary
send_daily_summary(
    subject="Valhalla Daily Ops Summary",
    body="Today's ops report...",
)

# Format a nice text report
report = format_summary_report(
    title="Daily Operations Report",
    sections={
        "Deals Closed": "5 new deals",
        "Revenue": "$250,000",
        "Active Leads": "12",
    },
    footer="End of report"
)
```

**Usage Pattern**:
```python
sections = {
    "System Health": "✓ All systems operational",
    "Alerts": "2 pending alerts",
    "Actions": "Review daily dashboard",
}

report = format_summary_report(
    title="Valhalla Daily Summary",
    sections=sections,
)

send_daily_summary(
    subject="Daily Ops Summary",
    body=report,
)
```

---

### 4. Governance API Exposure

**Endpoint**: `GET /api/runbook/status`

The runbook status endpoint now includes system identity for verification:

```json
{
  "ok": true,
  "blockers": [],
  "warnings": {},
  "go_live": {
    "enabled": true,
    "kill_switch_engaged": false,
    "changed_by": null,
    "reason": null,
    "updated_at": null
  },
  "system_email": "ValhallaLegacyInc@gmail.com",
  "from_name": "Valhalla Legacy Inc",
  "engines": []
}
```

**Use Cases**:
- Verify correct environment via API
- Debug WeWeb integration
- Confirm identity before deploying
- Audit trail of system configuration

---

### 5. Email Guard (Optional)

**File**: `app/guards/email_guard.py`

Guardrail to prevent unauthorized email usage:

```python
from app.guards.email_guard import assert_system_email, validate_sender_email

# Validate before using an email
assert_system_email("ValhallaLegacyInc@gmail.com")  # OK
assert_system_email("personal@example.com")  # Raises UnauthorizedEmailError

# Or check without raising
if validate_sender_email(email):
    send_email(to_email=email, ...)
```

**Protection Against**:
- Personal emails being sent
- Rogue VA accounts
- Accidental misrouting
- Unauthorized identities

**Integration Pattern**:
```python
# In any VA action that touches email:
from app.guards.email_guard import assert_system_email

def send_notification(user_email: str, message: str):
    assert_system_email(user_email)  # Guardrail
    send_email(to_email=user_email, subject="...", body=message)
```

---

## Implementation Checklist

- [x] Create `app/core/identity.py` - Single source of truth
- [x] Create `app/services/email_service.py` - SMTP integration
- [x] Create `app/services/daily_summary.py` - Summary helpers
- [x] Update `app/routers/runbook_status.py` - Expose identity in API
- [x] Create `app/guards/email_guard.py` - Email guardrails
- [ ] Set `VALHALLA_SYSTEM_EMAIL` in `.env` (local)
- [ ] Set `VALHALLA_SYSTEM_EMAIL` in Render → Environment Variables
- [ ] Set `VALHALLA_FROM_NAME` in `.env` (local) - optional, defaults to "Valhalla Legacy Inc"
- [ ] Set `VALHALLA_FROM_NAME` in Render → Environment Variables - optional
- [ ] Test: Run `/api/runbook/status` and verify system_email appears
- [ ] Test: Send a test email to verify SMTP works

---

## Verification Steps

### 1. Set Environment Variables

**Local Development** (`.env`):
```
VALHALLA_SYSTEM_EMAIL=ValhallaLegacyInc@gmail.com
VALHALLA_FROM_NAME=Valhalla Legacy Inc
```

**Render Dashboard**:
1. Go to your Render service
2. Settings → Environment
3. Add:
   - `VALHALLA_SYSTEM_EMAIL=ValhallaLegacyInc@gmail.com`
   - `VALHALLA_FROM_NAME=Valhalla Legacy Inc`
4. Deploy

### 2. Test via API

After deployment, verify the identity is wired:

```bash
# Local
curl http://localhost:8000/api/runbook/status

# Render
curl https://valhalla-api-ha6a.onrender.com/api/runbook/status
```

Expected response:
```json
{
  "system_email": "ValhallaLegacyInc@gmail.com",
  "from_name": "Valhalla Legacy Inc",
  ...
}
```

### 3. Test Email Service

Create a quick test script:

```python
from app.services.email_service import send_summary

result = send_summary(
    subject="Test Email",
    body="This is a test from the system.",
    to_email="your-test@example.com"
)
print(f"Email sent: {result}")
```

### 4. Import Health Check

```python
# Verify imports work
from app.core.identity import system_identity
from app.services.email_service import send_email
from app.services.daily_summary import get_default_summary_recipient
from app.guards.email_guard import assert_system_email

print("✓ All imports successful")
```

---

## Common Tasks

### Send a Daily Summary

```python
from app.services.daily_summary import send_daily_summary, format_summary_report

sections = {
    "Deals": "3 closed, 5 pending",
    "Revenue": "$125,000 new",
    "Team": "All healthy",
}

report = format_summary_report(
    title="Daily Operations",
    sections=sections,
)

send_daily_summary(
    subject="Valhalla Daily Ops",
    body=report,
)
```

### Use Email in a Router

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.email_service import send_email
from app.guards.email_guard import assert_system_email

router = APIRouter()

@router.post("/api/notify/test")
def send_test_email(db: Session = Depends(get_db)):
    recipient = "ops@example.com"
    
    # Optional: validate it's the system email
    # assert_system_email(recipient)
    
    success = send_email(
        to_email=recipient,
        subject="Test Notification",
        body="This is from the system.",
    )
    
    return {"sent": success, "to": recipient}
```

### Integrate with Alerts

```python
from app.services.email_service import send_email
from app.core.identity import system_identity

def alert_system_health_issue(issue: str):
    identity = system_identity()
    
    send_email(
        to_email=identity["email"],
        subject=f"⚠️ Health Alert: {issue}",
        body=f"Issue detected: {issue}\n\nPlease investigate.",
    )
```

---

## File Summary

| File | Purpose | Type |
|------|---------|------|
| `app/core/identity.py` | Single source of truth for system email | Core Config |
| `app/services/email_service.py` | SMTP integration with system identity | Service |
| `app/services/daily_summary.py` | Summary email helpers | Service |
| `app/routers/runbook_status.py` | **Updated** - Now exposes identity | Router |
| `app/guards/email_guard.py` | Email authorization guardrails | Guard |

---

## Migration Guide

If you have existing email code:

### Before
```python
SMTP_FROM = "noreply@valhalla.local"  # Hardcoded

def send_email(to, subject, body):
    # Build email with hardcoded from
    msg = MIMEText(body)
    msg["From"] = SMTP_FROM
    msg["Subject"] = subject
    # ... send via SMTP
```

### After
```python
from app.services.email_service import send_email

# Use the service - no hardcoding needed
send_email(
    to_email=to,
    subject=subject,
    body=body,
)
```

**Benefits**:
- No hardcoded emails in code
- Change email in env, not in 10 files
- Consistent From headers
- Proper formatting

---

## Troubleshooting

### Error: `RuntimeError: VALHALLA_SYSTEM_EMAIL is not set`

**Solution**: Set the environment variable
```bash
# Local
echo "VALHALLA_SYSTEM_EMAIL=ValhallaLegacyInc@gmail.com" >> .env

# Render: Add to Environment Variables in dashboard
```

### Emails not sending

**Check**:
1. SMTP credentials are correct
2. SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS are set
3. VALHALLA_SYSTEM_EMAIL is set
4. Check logs for `send_email()` returning False

### System email shows as null in `/api/runbook/status`

**Cause**: VALHALLA_SYSTEM_EMAIL environment variable not set

**Fix**: Set it and redeploy

---

## Next Steps

1. **Deploy Code**: Push this implementation to your repo
2. **Set Env Vars**: Configure VALHALLA_SYSTEM_EMAIL in local and Render
3. **Test API**: Hit `/api/runbook/status` to verify
4. **Integration**: Update existing email code to use new services
5. **Monitoring**: Watch logs for email failures

---

## Notes

- The system email is the "single source of truth" - one inbox, one audit trail
- Changing from_name doesn't require code changes
- All emails automatically include proper formatting
- The guard can be added to any email-sending code path
- Identity module is imported at startup for early error detection

---

**Version**: 1.0  
**Last Updated**: 2026-01-29  
**Status**: Ready for deployment
