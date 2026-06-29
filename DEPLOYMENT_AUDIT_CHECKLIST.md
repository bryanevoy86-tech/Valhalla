# DEPLOYMENT AUDIT — FILES CONFIRMED ACTIVE

## File Location Audit ✅

### 1. Auth Router
- **Location:** `d:\dev\services\api\app\routers\auth_weweb.py`
- **Docker Path:** `/app/services/api/app/routers/auth_weweb.py`
- **Status:** ✅ Created, syntactically valid
- **Router Definition:** `router = APIRouter(prefix="/api/weweb", tags=["weweb-auth"])`
- **Endpoints:**
  - `POST /api/weweb/login` - Email-based login
  - `GET /api/weweb/me` - Current user (requires token)
  - `GET /api/weweb/smoke` - Deployment self-check
  - `POST /api/weweb/admin/reset-owner-password` - Backup reset endpoint

### 2. Reset Script
- **Location:** `d:\dev\scripts\reset_owner_password.py`
- **Docker Path:** `/app/scripts/reset_owner_password.py`
- **Status:** ✅ Created, syntactically valid
- **Called From:** `services/api/start.py` (if RESET_OWNER_PASSWORD=true)

### 3. Start Script (Enhanced)
- **Location:** `d:\dev\services/api/start.py`
- **Status:** ✅ Updated to call reset script before Uvicorn
- **Behavior:**
  - Checks `RESET_OWNER_PASSWORD` env var
  - If true, runs `/app/scripts/reset_owner_password.py`
  - Then starts Uvicorn on port 10000

### 4. Main App (Enhanced)
- **Location:** `d:\dev\services/api/app/main.py`
- **Status:** ✅ Added startup logging for auth_weweb
- **Log Output:** `✅ auth_weweb router loaded - /api/weweb/* endpoints available`

## Dockerfile Verification ✅

```dockerfile
WORKDIR /app
COPY . .                    # Copies everything including scripts/
WORKDIR /app/services/api   # Changes to services/api for execution
PYTHONPATH=/app/services/api
```

**Result:** Both files will be available in Docker:
- ✅ `/app/services/api/app/routers/auth_weweb.py` (will be auto-loaded)
- ✅ `/app/scripts/reset_owner_password.py` (will be called by start.py)

## Deployment Flow (Render)

### Step 1: Pre-Deploy (Optional - can skip now)
```bash
# Pre-deploy command (optional, if we add it)
python scripts/render_migrate.py
```

### Step 2: Web Service Startup
```bash
# This runs:
cd /app/services/api
python start.py
```

**start.py will:**
1. Check if `RESET_OWNER_PASSWORD=true`
2. If yes, run `/app/scripts/reset_owner_password.py`
3. Then start Uvicorn

### Step 3: Render detects port 10000 is open
- ✅ Service goes live
- ✅ Endpoints available

## Environment Variables for Render

```
RESET_OWNER_PASSWORD = true
VALHALLA_OWNER_EMAIL = your-admin-email@example.com
VALHALLA_OWNER_PASSWORD = your-secure-password
VALHALLA_SETUP_TOKEN = (optional, for backup endpoint security)
```

**Current status in Render:**
- ❌ Pre-Deploy Command: (empty - OK for now)
- ❌ RESET_OWNER_PASSWORD: (not set)
- ❌ VALHALLA_OWNER_EMAIL: (not set)
- ❌ VALHALLA_OWNER_PASSWORD: (not set)

## Testing Paths

### Local Test (Before Render)
```powershell
# Test import
cd d:\dev\services\api
python -c "import sys; sys.path.insert(0, '.'); from app.routers.auth_weweb import router; print('✅ OK')"

# Test start.py syntax
cd d:\dev\services\api
python -m py_compile start.py
```

### Live Test (After Render Deploy)
```powershell
# Test public endpoint (no auth)
$r = Invoke-RestMethod "https://valhalla-api-ha6a.onrender.com/api/weweb/smoke" -Method GET
$r

# Test login (with credentials)
$login = Invoke-RestMethod "https://valhalla-api-ha6a.onrender.com/api/weweb/login" -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"admin@example.com","password":"your-password"}'
$login.access_token

# Test authenticated endpoint
$me = Invoke-RestMethod "https://valhalla-api-ha6a.onrender.com/api/weweb/me" -Method GET `
  -Headers @{"Authorization"="Bearer $($login.access_token)"}
$me
```

## Render Deployment Checklist

- [ ] Set env vars in Render dashboard:
  - [ ] RESET_OWNER_PASSWORD = true
  - [ ] VALHALLA_OWNER_EMAIL = your-admin@example.com
  - [ ] VALHALLA_OWNER_PASSWORD = your-secure-password
- [ ] Commit all changes to main branch
- [ ] Push to GitHub (auto-triggers Render deploy)
- [ ] Wait for Render to deploy (~2 min)
- [ ] Check Render logs for: `✅ auth_weweb router loaded`
- [ ] Test `/api/weweb/smoke` endpoint
- [ ] Test `/api/weweb/login` with credentials
- [ ] If successful, set RESET_OWNER_PASSWORD = false
- [ ] Redeploy

## Backup Reset Endpoint (If Pre-Deploy Fails)

If the automatic reset from start.py doesn't work, use the backup endpoint:

```powershell
$base = "https://valhalla-api-ha6a.onrender.com"

# If VALHALLA_SETUP_TOKEN is set:
$response = Invoke-RestMethod "$base/api/weweb/admin/reset-owner-password" `
  -Method POST `
  -Headers @{
    "X-Setup-Token" = "your-setup-token"
  }

# If VALHALLA_SETUP_TOKEN is NOT set:
$response = Invoke-RestMethod "$base/api/weweb/admin/reset-owner-password" `
  -Method POST
  
$response
```

**Response (200 OK):**
```json
{
  "ok": true,
  "message": "Owner password reset complete for admin@example.com"
}
```

## File Summary

| File | Path | Status | Docker Path |
|------|------|--------|-------------|
| Auth Router | services/api/app/routers/auth_weweb.py | ✅ Created | /app/services/api/app/routers/auth_weweb.py |
| Reset Script | scripts/reset_owner_password.py | ✅ Created | /app/scripts/reset_owner_password.py |
| Start Script | services/api/start.py | ✅ Enhanced | /app/services/api/start.py |
| Main App | services/api/app/main.py | ✅ Enhanced | /app/services/api/app/main.py |

## Next Steps

1. ✅ Files created and verified
2. ⏳ Commit changes to main
3. ⏳ Set env vars in Render dashboard
4. ⏳ Deploy to Render
5. ⏳ Check logs for auth_weweb router loaded
6. ⏳ Test /api/weweb/smoke
7. ⏳ Test login endpoint
8. ⏳ Disable reset flag after success
