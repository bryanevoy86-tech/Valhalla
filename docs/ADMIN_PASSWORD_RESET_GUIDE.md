# VALHALLA ADMIN PASSWORD RESET — IMPLEMENTATION COMPLETE

## Status Summary

✅ **New `/api/weweb/login` endpoint** - Email-based login with JWT token
✅ **New `scripts/reset_owner_password.py`** - Safe password reset script
✅ **PBKDF2-SHA256 hashing** - Industry-standard password hashing already in use
✅ **Optional safety flag** - `RESET_OWNER_PASSWORD=true` to enable reset on demand
✅ **Zero credentials in logs** - Passwords and hashes never printed

---

## Files Changed

### 1. New: `services/api/app/routers/auth_weweb.py`

**Endpoints:**
- `POST /api/weweb/login` - Login with email + password
- `GET /api/weweb/me` - Get current user (requires JWT token)
- `GET /api/weweb/smoke` - Public health check

**Request/Response:**
```bash
# Login
POST /api/weweb/login
{
  "email": "admin@example.com",
  "password": "SecurePassword123"
}

Response (200 OK):
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

### 2. New: `scripts/reset_owner_password.py`

**Purpose:** Reset admin password safely by reading plaintext from env vars and hashing before database storage.

**Environment Variables Required:**
- `VALHALLA_OWNER_EMAIL` - Admin email (will be created if not exists)
- `VALHALLA_OWNER_PASSWORD` - Plain password (never stored, only hashed)
- `RESET_OWNER_PASSWORD` - Set to "true" to enable reset
- `DATABASE_URL` - PostgreSQL connection string

**Behavior:**
- ✅ Only runs if `RESET_OWNER_PASSWORD=true`
- ✅ Hashes password with PBKDF2-SHA256 (same as existing auth system)
- ✅ Creates user if not exists, updates if exists
- ✅ Stores hash in `account_settings.password_hash`
- ✅ Never prints password or hash (only email and success)
- ✅ Exits with code 1 on error, 0 on success

---

## Hash Method

**Algorithm:** PBKDF2-SHA256
**Iterations:** 210,000
**Salt:** 16 random bytes (base64 urlsafe encoded)
**Format:** `pbkdf2_sha256$210000$<salt>$<hash>`

*Already implemented in `app.security.auth.pbkdf2_hash_password()`*

---

## Local Test (Phase 5)

### Prerequisites

1. **Backend running locally:**
   ```bash
   cd d:\dev
   python -m pip install -r requirements.txt  # if not already installed
   uvicorn services/api/app/main:app --reload --port 8000
   ```

2. **Database populated:**
   - Ensure `DATABASE_URL` points to valid PostgreSQL
   - Migrations must be run: `alembic upgrade head`

### Test Steps

```powershell
# Terminal 1: Start backend (if not already running)
cd d:\dev
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn services/api/app/main:app --reload --port 8000
```

```powershell
# Terminal 2: Run reset script
cd d:\dev
$env:VALHALLA_OWNER_EMAIL="testadmin@localhost"
$env:VALHALLA_OWNER_PASSWORD="TestPassword123!"
$env:RESET_OWNER_PASSWORD="true"
$env:DATABASE_URL="postgresql://user:pass@localhost/valhalla_db_v2"

python scripts/reset_owner_password.py
```

**Expected output:**
```
2026-06-29 12:34:56 - INFO - Starting admin password reset...
2026-06-29 12:34:56 - INFO - Creating new admin user for testadmin@localhost
2026-06-29 12:34:56 - INFO - Hashing password...
2026-06-29 12:34:56 - INFO - Creating new account settings
✅ Owner password reset complete for testadmin@localhost
```

### Test Login

```powershell
# Test with correct password
$base = "http://localhost:8000"
$response = Invoke-RestMethod "$base/api/weweb/login" -Method POST -ContentType "application/json" -Body '{
  "email": "testadmin@localhost",
  "password": "TestPassword123!"
}'
Write-Host "Login Success: $($response.access_token.Substring(0, 50))..."
$token = $response.access_token

# Test /me endpoint with token
$meResponse = Invoke-RestMethod "$base/api/weweb/me" -Method GET -Headers @{ 
  "Authorization" = "Bearer $token" 
}
Write-Host "Me Endpoint: $($meResponse.user.email)"

# Test with wrong password (should fail with 401)
try {
  Invoke-RestMethod "$base/api/weweb/login" -Method POST -ContentType "application/json" -Body '{
    "email": "testadmin@localhost",
    "password": "WrongPassword"
  }'
} catch {
  Write-Host "Wrong password correctly rejected: $($_.Exception.Response.StatusCode)"
}
```

---

## Render Deployment (Phase 6)

### Step 1: Add Environment Variables to Render

In Render dashboard for `valhalla-api` service:

```
VALHALLA_OWNER_EMAIL = your-admin@example.com
VALHALLA_OWNER_PASSWORD = your-secure-password-here
RESET_OWNER_PASSWORD = true
```

**⚠️ Important:** `VALHALLA_OWNER_PASSWORD` should be **plain text**, not hashed.

### Step 2: Create Pre-Deploy Command (Optional but Recommended)

Instead of relying on auto-reset, you can add explicit pre-deploy command:

```bash
python scripts/reset_owner_password.py
```

This runs before the web service starts.

### Step 3: Deploy

Push to main branch or manually trigger deploy:

```bash
git add services/api/app/routers/auth_weweb.py scripts/reset_owner_password.py
git commit -m "Add admin password reset and WeWeb login endpoint"
git push origin main
```

### Step 4: After Successful Login

Once you've successfully logged in and tested `/api/weweb/login`:

```
RESET_OWNER_PASSWORD = false
```

Or remove the variable entirely. This prevents accidental password resets on future deploys.

---

## Testing on Live Render

```powershell
$base = "https://valhalla-api-ha6a.onrender.com"

# Test public smoke endpoint (no auth)
$smoke = Invoke-RestMethod "$base/api/weweb/smoke" -Method GET
Write-Host "Smoke: $($smoke.status)"

# Test login with your admin credentials
$login = Invoke-RestMethod "$base/api/weweb/login" -Method POST `
  -ContentType "application/json" `
  -Body '{
    "email": "your-admin@example.com",
    "password": "your-secure-password"
  }'

Write-Host "Login Status: $($login.ok)"
Write-Host "Token: $($login.access_token.Substring(0, 50))..."

# Test authenticated endpoint
$me = Invoke-RestMethod "$base/api/weweb/me" -Method GET `
  -Headers @{ "Authorization" = "Bearer $($login.access_token)" }
  
Write-Host "User Email: $($me.user.email)"
```

---

## Environment Variables Summary

| Variable | Type | Required | Notes |
|----------|------|----------|-------|
| `VALHALLA_OWNER_EMAIL` | String | Yes (for reset) | Admin email address |
| `VALHALLA_OWNER_PASSWORD` | String | Yes (for reset) | **Plain text** (will be hashed) |
| `RESET_OWNER_PASSWORD` | Boolean | No | Set to "true" to enable reset |
| `DATABASE_URL` | String | Yes | PostgreSQL connection |
| `VALHALLA_JWT_SECRET` | String | Yes (prod) | Secret for JWT tokens |

---

## Database Schema

### `user_profiles` table
- `user_id` (PK)
- `email` (UNIQUE, case-insensitive)
- `first_name`
- `last_name`
- Created automatically via models

### `account_settings` table
- `account_id` (PK)
- `user_id` (FK → user_profiles.user_id, UNIQUE)
- `password_hash` (PBKDF2-SHA256 format)
- `last_password_change` (timestamp)
- Created automatically via models

---

## Security Notes

1. **Password hashing:** PBKDF2-SHA256 with 210,000 iterations (industry standard)
2. **Secrets management:** Passwords never appear in logs, config files, or responses
3. **Token expiration:** JWT tokens default to 1 hour TTL (configurable via `VALHALLA_TOKEN_TTL_SECONDS`)
4. **Optional reset:** Script only runs if explicitly enabled via env var
5. **Database-backed:** Passwords stored as hashes, not env vars (unlike VALHALLA_OWNER_PASSWORD_HASH)

---

## Troubleshooting

### "VALHALLA_OWNER_EMAIL is required but not set"
**Fix:** Set `VALHALLA_OWNER_EMAIL` env var before running script

### "Could not import pbkdf2_hash_password"
**Fix:** Ensure `app.security.auth` exists and `PYTHONPATH` includes app root

### Login returns 401 "Invalid email or password"
**Fix:** 
- Verify email exactly matches what's in database
- Check password was successfully set via reset script
- Confirm `account_settings.password_hash` is not null

### Token expired (401 on /api/weweb/me)
**Fix:** Re-login to get fresh token. TTL defaults to 1 hour.

---

## Next Steps

1. ✅ Test locally with sample credentials
2. ✅ Add env vars to Render secrets
3. ✅ Deploy changes
4. ✅ Test `/api/weweb/login` on live Render
5. ✅ Disable reset flag after successful login
6. 📋 Integrate with WeWeb frontend

---

## Complete Checklist

- [x] Create `/api/weweb/login` endpoint
- [x] Create reset script
- [x] Support RESET_OWNER_PASSWORD safety flag
- [x] Use PBKDF2-SHA256 hashing
- [x] Never print passwords/hashes
- [x] Create documentation
- [ ] Test locally (awaiting your run)
- [ ] Deploy to Render
- [ ] Test on live Render
- [ ] Frontend integration
