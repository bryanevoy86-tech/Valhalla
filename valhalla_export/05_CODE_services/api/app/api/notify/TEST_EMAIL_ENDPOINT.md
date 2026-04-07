# Test Email Endpoint - Quick Reference

## Endpoint

**POST** `/api/notify/test-email`

## Purpose

Send a test email from the system account to verify:
1. System identity is configured (`VALHALLA_SYSTEM_EMAIL`)
2. Email service can send messages
3. Notification channel is online

## How to Use

### Via cURL (Local)
```bash
curl -X POST http://localhost:8000/api/notify/test-email
```

### Via cURL (Production/Render)
```bash
curl -X POST https://valhalla-api.onrender.com/api/notify/test-email
```

### Via Python
```python
import requests

response = requests.post("http://localhost:8000/api/notify/test-email")
print(response.json())
```

### Via FastAPI Docs
1. Go to `http://localhost:8000/docs` (local) or your Render URL + `/docs`
2. Find `/api/notify/test-email` in the list
3. Click "Try it out"
4. Click "Execute"

## Response

### Success (200)
```json
{
  "ok": true,
  "sent_to": "ValhallaLegacyInc@gmail.com",
  "subject": "Heimdall: Notification channel online ✅"
}
```

### What Happens

When you hit this endpoint:

1. ✅ System identity is loaded from `VALHALLA_SYSTEM_EMAIL`
2. ✅ An email is sent from `ValhallaLegacyInc@gmail.com` to itself
3. ✅ Subject: `Heimdall: Notification channel online ✅`
4. ✅ Body: `If you received this, Valhalla can send operational emails from Render.`
5. ✅ Response confirms the email was queued

## Requirements

### Environment Variables (Set in .env or Render)
```
VALHALLA_SYSTEM_EMAIL=ValhallaLegacyInc@gmail.com
VALHALLA_FROM_NAME=Valhalla Legacy Inc
```

### SMTP Configuration (Already exists in settings)
```
SMTP_HOST=your.smtp.host
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASS=your-smtp-password
```

## Testing Checklist

- [ ] Endpoint returns 200 OK with proper response JSON
- [ ] System email appears in response
- [ ] Check email inbox for the test email
- [ ] Verify From header: `Valhalla Legacy Inc <ValhallaLegacyInc@gmail.com>`
- [ ] Subject line shows: `Heimdall: Notification channel online ✅`

## Files

- **Endpoint**: `app/api/notify/test_email_router.py`
- **Registered in**: `app/main.py` (line ~165)
- **Uses services**: 
  - `app.core.identity` - Get system email
  - `app.services.email_service` - Send email

## Integration Examples

### From a Router Handler
```python
from fastapi import APIRouter
from app.api.notify.test_email_router import test_email

router = APIRouter()

@router.post("/my-endpoint")
def my_handler():
    # Trigger test email
    result = test_email()
    return result
```

### From a Service
```python
from app.services.email_service import send_email
from app.core.identity import system_identity

identity = system_identity()
send_email(
    to_email=identity["email"],
    subject="Test",
    body="Testing..."
)
```

## Troubleshooting

### 404 Not Found
- Router not registered in `main.py`
- Check that import exists in main.py around line 165

### 500 Error
- `VALHALLA_SYSTEM_EMAIL` not set
- SMTP credentials incorrect
- Check logs for details

### Email not received
- SMTP_HOST, SMTP_USER, SMTP_PASS not configured
- Email might be in spam
- Check SMTP service is accessible

## Next Steps

1. **Test locally**: `curl -X POST http://localhost:8000/api/notify/test-email`
2. **Check Swagger**: Visit `/docs` endpoint and try it out
3. **Deploy to Render**: Push code, test on production URL
4. **Verify email**: Check inbox for test email
5. **Integrate**: Use `send_email()` service in your workflows

---

**Status**: ✅ Ready to use  
**File**: `app/api/notify/test_email_router.py`
