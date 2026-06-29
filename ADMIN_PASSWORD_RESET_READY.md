# VALHALLA ADMIN PASSWORD RESET — IMPLEMENTATION COMPLETE ✅

## Quick Summary

**Status:** Ready to deploy

**Files Created:**
1. ✅ `services/api/app/routers/auth_weweb.py` - Email-based login endpoint
2. ✅ `scripts/reset_owner_password.py` - Safe password reset script
3. ✅ `docs/ADMIN_PASSWORD_RESET_GUIDE.md` - Complete documentation

**Hash Method:** PBKDF2-SHA256 (210,000 iterations) - already in use, no new dependencies

---

## What Was Created

### 1. `/api/weweb/login` Endpoint

Located in: [services/api/app/routers/auth_weweb.py](services/api/app/routers/auth_weweb.py)

```bash
POST /api/weweb/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "SecurePassword123"
}

# Response (200 OK):
{
  "ok": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "Owner"
  }
}
```

**Also included:**
- `GET /api/weweb/me` - Get current user (requires Bearer token)
- `GET /api/weweb/smoke` - Public health check

### 2. Password Reset Script

Located in: [scripts/reset_owner_password.py](scripts/reset_owner_password.py)

**How to use:**
```bash
# Set environment variables
export VALHALLA_OWNER_EMAIL="admin@example.com"
export VALHALLA_OWNER_PASSWORD="SecurePassword123"
export RESET_OWNER_PASSWORD="true"
export DATABASE_URL="postgresql://user:pass@localhost/valhalla_db_v2"

# Run script
python scripts/reset_owner_password.py

# Output:
# ✅ Owner password reset complete for admin@example.com
```

**Script behavior:**
- ✅ Only runs if `RESET_OWNER_PASSWORD=true`
- ✅ Creates admin user if doesn't exist
- ✅ Updates password if user exists
- ✅ Hashes with PBKDF2-SHA256 (same as existing system)
- ✅ Never prints password or hash
- ✅ Returns exit code 0 on success, 1 on error

---

## Complete Information

| Item | Value |
|------|-------|
| **Hash Algorithm** | PBKDF2-SHA256 |
| **Hash Iterations** | 210,000 |
| **Salt Length** | 16 random bytes |
| **Hash Storage** | `account_settings.password_hash` |
| **JWT Token TTL** | 1 hour (configurable) |
| **JWT Secret Source** | `VALHALLA_JWT_SECRET` env var |

**Environment Variables Required:**
- `VALHALLA_OWNER_EMAIL` (string) - Admin email
- `VALHALLA_OWNER_PASSWORD` (string) - Plain text password (will be hashed)
- `RESET_OWNER_PASSWORD` (boolean) - Set to "true" to enable reset
- `DATABASE_URL` (string) - PostgreSQL connection
- `VALHALLA_JWT_SECRET` (string) - JWT signing secret (for production)

---

## Render Deployment Steps

### Step 1: Add Environment Variables

In Render dashboard for `srv-d3hatinfte5s73cqbbh0` → Environment:

```
VALHALLA_OWNER_EMAIL = your-admin-email@example.com
VALHALLA_OWNER_PASSWORD = your-secure-password
RESET_OWNER_PASSWORD = true
```

**⚠️ IMPORTANT:** `VALHALLA_OWNER_PASSWORD` must be **plain text**, not hashed.

### Step 2: Commit and Push Changes

```bash
cd d:\dev
git add services/api/app/routers/auth_weweb.py scripts/reset_owner_password.py docs/ADMIN_PASSWORD_RESET_GUIDE.md
git commit -m "feat: add admin password reset and WeWeb login endpoint"
git push origin main
```

### Step 3: Deploy

GitHub webhook will trigger automatic deploy on Render, OR manually trigger from Render dashboard.

### Step 4: Verify Success

Once deployed, test live endpoint:

```powershell
$base = "https://valhalla-api-ha6a.onrender.com"

# Test login
$response = Invoke-RestMethod "$base/api/weweb/login" -Method POST `
  -ContentType "application/json" `
  -Body '{
    "email": "your-admin-email@example.com",
    "password": "your-secure-password"
  }'

Write-Host "Login Success: $($response.ok)"
Write-Host "Token: $($response.access_token.Substring(0, 50))..."

# Test authenticated endpoint
$me = Invoke-RestMethod "$base/api/weweb/me" -Method GET `
  -Headers @{ "Authorization" = "Bearer $($response.access_token)" }

Write-Host "User: $($me.user.email)"
```

### Step 5: Disable Auto-Reset

After successful login, change:

```
RESET_OWNER_PASSWORD = false
```

Or remove the variable entirely. This prevents accidental resets on future deploys.

---

## Local Testing (Optional)

If you want to test locally before deploying to Render:

```powershell
# Terminal 1: Start backend (if not already running)
cd d:\dev
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn services.api.app.main:app --reload --port 8000
```

```powershell
# Terminal 2: Run reset script
cd d:\dev
$env:VALHALLA_OWNER_EMAIL="testadmin@localhost"
$env:VALHALLA_OWNER_PASSWORD="TestPassword123!"
$env:RESET_OWNER_PASSWORD="true"
$env:DATABASE_URL="your-local-db-url"

python scripts/reset_owner_password.py
```

```powershell
# Terminal 3: Test login
$response = Invoke-RestMethod "http://localhost:8000/api/weweb/login" -Method POST `
  -ContentType "application/json" `
  -Body '{
    "email": "testadmin@localhost",
    "password": "TestPassword123!"
  }'

Write-Host "Login Success: $($response.ok)"
```

---

## Security Features

✅ **No plaintext storage** - Passwords hashed with PBKDF2-SHA256 before database storage
✅ **No credentials in logs** - Passwords and hashes never printed
✅ **Optional reset flag** - Script only runs if explicitly enabled
✅ **JWT token expiration** - Tokens expire after 1 hour
✅ **Constant-time comparison** - Password verification uses HMAC comparison
✅ **Env var isolation** - Passwords read from env, never hardcoded

---

## Next Steps

1. ✅ Code implementation complete
2. ⏳ Add env vars to Render secrets
3. ⏳ Deploy to Render
4. ⏳ Test `/api/weweb/login` on live
5. ⏳ Disable `RESET_OWNER_PASSWORD` flag
6. 📋 Frontend integration with WeWeb

---

## Troubleshooting

**"VALHALLA_OWNER_EMAIL is required"**
→ Set env var before running script

**"Could not import pbkdf2_hash_password"**
→ Ensure app/security/auth.py exists (it does, no changes needed)

**Login returns 401**
→ Check email matches exactly (case-insensitive in code, but verify)
→ Verify password was successfully reset

**Token expired**
→ Normal - tokens expire after 1 hour. Re-login to get new token.

---

## Files Summary

| File | Purpose | Status |
|------|---------|--------|
| services/api/app/routers/auth_weweb.py | Login endpoints | ✅ Created |
| scripts/reset_owner_password.py | Password reset script | ✅ Created |
| docs/ADMIN_PASSWORD_RESET_GUIDE.md | Detailed guide | ✅ Created |

All files are syntactically valid and ready to deploy.
