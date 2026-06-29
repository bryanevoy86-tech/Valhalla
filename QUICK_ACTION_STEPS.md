# RENDER DEPLOYMENT — QUICK ACTION STEPS

## ✅ What VS Code Just Did

- ✅ Created `/api/weweb/login`, `/api/weweb/me`, `/api/weweb/smoke` endpoints
- ✅ Created backup `/api/weweb/admin/reset-owner-password` endpoint  
- ✅ Created `scripts/reset_owner_password.py` for safe password hashing
- ✅ Enhanced `start.py` to run reset script before web startup
- ✅ Added startup logging to see `auth_weweb router loaded`
- ✅ Committed and pushed all files to main branch
- ✅ GitHub webhook already triggered Render to start new deploy

**Commit:** 3f7f82c  
**Status:** Files in Git, waiting for Render env vars

---

## ⏳ What You Need To Do (3 Steps)

### Step 1: Set Environment Variables in Render (2 minutes)

1. Open: https://dashboard.render.com/web/srv-d3hatinfte5s73cqbbh0
2. Click **Environment**
3. Add 3 new variables:

```
RESET_OWNER_PASSWORD
Value: true

VALHALLA_OWNER_EMAIL
Value: your-admin@example.com  (use your real email)

VALHALLA_OWNER_PASSWORD
Value: your-secure-password    (use your real password - plain text)
```

Click **Save**.

**⚠️ IMPORTANT:** `VALHALLA_OWNER_PASSWORD` is plain text, not hashed. The backend will hash it.

---

### Step 2: Trigger Deploy (30 seconds)

Option A: **Automatic** (recommended)
- The new code is already in main branch
- Render webhook should auto-detect and deploy
- Check **Deployment Logs** in Render dashboard

Option B: **Manual**
1. Click **Manual Deploy** button on Render
2. Click **Deploy latest commit**

**Wait 2-3 minutes for deployment to complete.**

---

### Step 3: Verify Success (2 minutes)

#### Check Logs for Success Markers

In Render Dashboard → Logs, look for:
```
✅ auth_weweb router loaded - /api/weweb/* endpoints available
✅ Owner password reset complete for your-admin@example.com
```

#### Test Public Endpoint

```powershell
$base = "https://valhalla-api-ha6a.onrender.com"
$smoke = Invoke-RestMethod "$base/api/weweb/smoke" -Method GET
$smoke | ConvertTo-Json
```

Expected output:
```json
{
  "ok": true,
  "status": "operational",
  "router": "auth_weweb",
  "login_path": "/api/weweb/login",
  "me_path": "/api/weweb/me",
  "reset_path": "/api/weweb/admin/reset-owner-password"
}
```

**Status:** 200 OK ✅

#### Test Login

```powershell
$base = "https://valhalla-api-ha6a.onrender.com"
$login = Invoke-RestMethod "$base/api/weweb/login" -Method POST `
  -ContentType "application/json" `
  -Body '{
    "email": "your-admin@example.com",
    "password": "your-secure-password"
  }'

$login | ConvertTo-Json
```

Expected output:
```json
{
  "ok": true,
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "your-admin@example.com",
    "first_name": "Admin",
    "last_name": "Owner"
  }
}
```

**Status:** 200 OK ✅

#### Test Authenticated Endpoint

```powershell
$token = $login.access_token
$me = Invoke-RestMethod "$base/api/weweb/me" -Method GET `
  -Headers @{ "Authorization" = "Bearer $token" }

$me | ConvertTo-Json
```

Expected output:
```json
{
  "ok": true,
  "user": {
    "id": 1,
    "email": "your-admin@example.com",
    "first_name": "Admin",
    "last_name": "Owner"
  }
}
```

**Status:** 200 OK ✅

---

## ✅ After All Tests Pass

Disable the reset flag to prevent accidental password resets on future deploys:

1. Open Render dashboard
2. Click **Environment**
3. Change `RESET_OWNER_PASSWORD` from `true` to `false`
4. Click **Save**
5. Optional: **Manual Deploy** to redeploy with flag disabled

---

## 🆘 Troubleshooting

### Smoke endpoint returns 404
- **Check:** Wait 2-3 min for deploy to complete
- **Check:** Render logs show new code deployed
- **Check:** No errors in deployment

### Login returns 401
- **Check:** Email is exact match (case-insensitive in code, but double-check)
- **Check:** Password is exactly what you set
- **Check:** User was created (check Render logs for reset success)

### Auth endpoint not found after deploy
- **Check:** Render logs show `✅ auth_weweb router loaded`
- **Check:** Backend health endpoint returns 200: `https://valhalla-api-ha6a.onrender.com/health`
- **Check:** Git shows latest commit deployed

### Reset script didn't run
- **Check:** `RESET_OWNER_PASSWORD` env var is `true` (not `True`, not `"true"`)
- **Check:** Render logs for: `OPTIONAL: Running owner password reset...`
- **Manual Option:** Use backup endpoint:
  ```powershell
  Invoke-RestMethod "https://valhalla-api-ha6a.onrender.com/api/weweb/admin/reset-owner-password" -Method POST
  ```

---

## Files Reference

| File | Purpose | Location |
|------|---------|----------|
| auth_weweb.py | Login endpoints | services/api/app/routers/ |
| reset_owner_password.py | Password reset script | scripts/ |
| start.py | Enhanced startup | services/api/ |
| main.py | Enhanced logging | services/api/app/ |
| Docs | Full documentation | docs/ and root |

---

## Timeline

- ✅ **Now:** Code is in main branch
- ⏳ **Next:** You set env vars in Render (2 min)
- ⏳ **+3 min:** Deploy completes
- ⏳ **+2 min:** You test endpoints
- ✅ **Total:** ~7 minutes to live login

---

## Exact Environment Variables to Set

```
Name: RESET_OWNER_PASSWORD
Value: true

Name: VALHALLA_OWNER_EMAIL
Value: [your admin email]

Name: VALHALLA_OWNER_PASSWORD
Value: [your admin password - PLAIN TEXT]
```

That's it! Everything else is automatic.
