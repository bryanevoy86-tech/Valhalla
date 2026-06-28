# Render Deploy Verification Guide

**Objective**: After Render deployment, verify all endpoints work and the backend is production-ready.

---

## Prerequisites

Before running this verification:

1. **Render deployment complete** — Backend service is running on Render
2. **Environment variables set in Render**:
   - `DATABASE_URL` → Render PostgreSQL internal URL
   - `VALHALLA_OWNER_USERNAME` → admin or chosen username
   - `VALHALLA_OWNER_EMAIL` → actual admin email
   - `VALHALLA_OWNER_PASSWORD` → strong production password
   - `VALHALLA_JWT_SECRET` → long random secret key
   - `CORS_ALLOWED_ORIGINS` → wewe domains or "*"
3. **Render migration ran automatically** — Check Render logs for "Upgraded" messages from Alembic
4. **Render backend is healthy** — Check Render dashboard shows service is running

---

## Step 1: Get Render API URL

In Render Dashboard:
1. Go to your Valhalla backend service
2. Find the public URL (example: `https://valhalla-api-xyz123.onrender.com`)
3. Copy this URL

**Store as environment variable** (local machine):

```powershell
$RENDER_API = "https://valhalla-api-xyz123.onrender.com"
```

---

## Step 2: Test Basic Connectivity (No Auth)

### Test: /health endpoint

```powershell
Invoke-RestMethod "$RENDER_API/health" | ConvertTo-Json
```

**Expected response** (200 OK):
```json
{
  "ok": true,
  "service": "valhalla",
  "version": "1.0.0",
  "timestamp": "2026-06-27T..."
}
```

**If this fails**:
- Check Render service status
- Check Render logs for errors
- Verify DATABASE_URL is set correctly

### Test: /api/weweb/smoke endpoint

```powershell
Invoke-RestMethod "$RENDER_API/api/weweb/smoke" | ConvertTo-Json
```

**Expected response** (200 OK):
```json
{
  "ok": true,
  "status": "healthy"
}
```

**If this fails**:
- Check if weweb_auth router loaded (check logs)
- Verify VALHALLA_OWNER_USERNAME is set

---

## Step 3: Test Authentication

### Test: Login endpoint

```powershell
$body = @{
  email = "YOUR_RENDER_ADMIN_EMAIL"
  password = "YOUR_RENDER_ADMIN_PASSWORD"
} | ConvertTo-Json

$login = Invoke-RestMethod -Uri "$RENDER_API/api/weweb/login" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"

Write-Host "Status: 200 OK"
Write-Host "Token: $($login.access_token.Substring(0,30))..."
$RENDER_TOKEN = $login.access_token
```

**Expected response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**If login fails (400/401)**:
- Check VALHALLA_OWNER_EMAIL and VALHALLA_OWNER_PASSWORD in Render
- Verify VALHALLA_JWT_SECRET is set
- Check Render logs for auth errors

---

## Step 4: Test Authenticated Endpoints

### Test: /api/weweb/me

```powershell
$me = Invoke-RestMethod -Uri "$RENDER_API/api/weweb/me" `
  -Headers @{ Authorization = "Bearer $RENDER_TOKEN" }

Write-Host "Status: 200 OK"
Write-Host ($me | ConvertTo-Json -Depth 10)
```

**Expected response** (200 OK):
```json
{
  "ok": true,
  "user": {
    "email": "your-admin-email@example.com",
    "role": "owner"
  }
}
```

**If 401 (Unauthorized)**:
- Token not being sent correctly
- Token expired
- Wrong token

**If 500 (Server Error)**:
- Check Render logs for SQLAlchemy errors
- Verify DATABASE_URL connects to correct database

### Test: /governance/go-live/state

```powershell
$goLive = Invoke-RestMethod -Uri "$RENDER_API/governance/go-live/state" `
  -Headers @{ Authorization = "Bearer $RENDER_TOKEN" }

Write-Host "Status: 200 OK"
Write-Host ($goLive | ConvertTo-Json -Depth 10)
```

**Expected response** (200 OK):
```json
{
  "go_live_enabled": false,
  "kill_switch_engaged": false,
  "changed_by": null,
  "reason": null,
  "updated_at": "2026-06-27T..."
}
```

**If 500 (Server Error)**:
- Check if `go_live_state` table exists in Render database
- Run: `SELECT * FROM go_live_state LIMIT 1;` in Render Postgres console
- If table missing: Render migration failed, check Render logs
- If table exists but empty: Backend should auto-seed, check backend code

### Test: /api/jarvis/system-status

```powershell
$systemStatus = Invoke-RestMethod -Uri "$RENDER_API/api/jarvis/system-status" `
  -Headers @{ Authorization = "Bearer $RENDER_TOKEN" }

Write-Host "Status: 200 OK"
Write-Host ($systemStatus | ConvertTo-Json -Depth 10)
```

**Expected**: 200 OK with system status object

### Test: /reports/summary

```powershell
$reports = Invoke-RestMethod -Uri "$RENDER_API/reports/summary" `
  -Headers @{ Authorization = "Bearer $RENDER_TOKEN" }

Write-Host "Status: 200 OK"
Write-Host ($reports | ConvertTo-Json -Depth 10)
```

**Expected**: 200 OK with reports data

---

## Step 5: Test CORS (Optional)

From your browser (DevTools Console), try:

```javascript
fetch('https://YOUR-RENDER-API/api/weweb/smoke')
  .then(r => r.json())
  .then(d => console.log(d))
```

**If CORS error appears**:
- Check CORS_ALLOWED_ORIGINS in Render environment
- Current origin must be in the list
- Or set to "*" for testing

---

## Troubleshooting Matrix

| Issue | Endpoint | Status Code | Solution |
|---|---|---|---|
| Connection refused | Any | N/A | Render service not running, check dashboard |
| Endpoint not found | Any | 404 | Router not loaded, check Render logs |
| Missing env var | /api/weweb/smoke | 500 | VALHALLA_OWNER_USERNAME not set |
| Auth failed | /api/weweb/login | 401 | Email/password incorrect or VALHALLA_JWT_SECRET not set |
| Token invalid | /governance/go-live/state | 401 | Token expired, wrong format, or VALHALLA_JWT_SECRET changed |
| Table missing | /governance/go-live/state | 500 | Migrations didn't run, check Render build logs |
| Database error | Any authenticated | 500 | DATABASE_URL wrong, database down, or permission issue |
| CORS blocked | From browser | N/A | CORS_ALLOWED_ORIGINS missing your domain |

---

## Step 6: Documentation

If all tests pass, document:

1. **Render URL** (public-facing)
2. **Deployment date/time**
3. **Branch deployed** (fix/alembic-single-head)
4. **Last commit hash**
5. **All endpoints passing** ✅

Example:

```
✅ Render Deployment Verification — PASS

Render URL: https://valhalla-api-xyz123.onrender.com
Deployed: 2026-06-27 14:30 UTC
Branch: fix/alembic-single-head
Commit: 07e9175 (docs: add fresh database verification results)

Endpoints Verified:
✅ GET /health (200) — Connectivity OK
✅ GET /api/weweb/smoke (200) — No-auth endpoint OK
✅ POST /api/weweb/login (200) — Auth working, token issued
✅ GET /api/weweb/me (200) — Bearer token accepted
✅ GET /governance/go-live/state (200) — Database schema OK
✅ GET /api/jarvis/system-status (200) — System endpoints OK
✅ GET /reports/summary (200) — Reports endpoint OK

Status: READY FOR WEWEB VALIDATION
```

---

## Emergency Debugging

### Check Render Logs

```
Render Dashboard → Your Service → Logs
- Look for "ERROR" or "Traceback" messages
- Check migration output for "Upgraded" messages
- Note any missing environment variable warnings
```

### Check Database Connection

```sql
-- In Render Postgres console
SELECT version();
SELECT * FROM go_live_state LIMIT 1;
```

### Restart Render Service

Render Dashboard → Your Service → "Restart" button

(This will re-run startup scripts including Alembic migrations)

---

## Final Go/No-Go Decision

**GO to WeWeb Validation if**:
- ✅ /health returns 200
- ✅ /api/weweb/smoke returns 200
- ✅ /api/weweb/login returns 200 + valid token
- ✅ /api/weweb/me works with token
- ✅ /governance/go-live/state returns 200
- ✅ /api/jarvis/system-status returns 200
- ✅ /reports/summary returns 200
- ✅ No CORS errors in browser

**NO-GO if**:
- ❌ Any critical endpoint returns 500
- ❌ Authentication doesn't work
- ❌ Database isn't connected
- ❌ Migrations didn't run

---

Generated: Valhalla Render Deploy Verification
