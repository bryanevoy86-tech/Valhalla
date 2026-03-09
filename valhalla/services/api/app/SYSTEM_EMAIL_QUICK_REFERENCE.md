# Quick Reference: System Email Identity

## TL;DR

**All system emails come from**: `ValhallaLegacyInc@gmail.com`  
**Configured via**: `VALHALLA_SYSTEM_EMAIL` environment variable

---

## Setup (Do This Once)

### Environment Variables
```
VALHALLA_SYSTEM_EMAIL=ValhallaLegacyInc@gmail.com
VALHALLA_FROM_NAME=Valhalla Legacy Inc
```

Add to:
- Local: `.env`
- Render: Environment Variables dashboard

---

## Usage

### Get System Email
```python
from app.core.identity import get_system_email
email = get_system_email()  # ValhallaLegacyInc@gmail.com
```

### Get Full Identity
```python
from app.core.identity import system_identity
id = system_identity()
# {"email": "ValhallaLegacyInc@gmail.com", "from_name": "Valhalla Legacy Inc"}
```

### Send Email
```python
from app.services.email_service import send_email
send_email(
    to_email="recipient@example.com",
    subject="Subject",
    body="Body text"
)
```

### Send Summary
```python
from app.services.daily_summary import send_daily_summary
send_daily_summary(
    subject="Daily Summary",
    body="Today's report..."
)
```

### Validate Email (Guard)
```python
from app.guards.email_guard import assert_system_email
assert_system_email(email)  # Raises error if not system email
```

---

## Files

| File | What |
|------|------|
| `app/core/identity.py` | System email config |
| `app/services/email_service.py` | Send emails |
| `app/services/daily_summary.py` | Summary helpers |
| `app/guards/email_guard.py` | Validate emails |

---

## Verify

```bash
curl https://valhalla-api.onrender.com/api/runbook/status
# Look for: "system_email": "ValhallaLegacyInc@gmail.com"
```

---

## NO HARDCODING

❌ **Don't do this**:
```python
FROM_EMAIL = "system@example.com"  # Hardcoded!
```

✅ **Do this**:
```python
from app.core.identity import get_system_email
email = get_system_email()  # From environment
```

---

Done! Everything is centralized. Change email later = change env variable only.
