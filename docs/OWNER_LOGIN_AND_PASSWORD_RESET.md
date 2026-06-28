# Owner Login and Password Reset Guide

## Overview

Valhalla uses a single-operator authentication system with environment-based credentials. The owner (operator) logs in via WeWeb using JWT tokens. This guide explains how login works and how to reset passwords safely without storing secrets in code.

---

## 1. How Login Works

### Request Flow

```
1. User enters username + password in WeWeb UI
   ↓
2. WeWeb calls POST /ops/token (form data: username, password)
   ↓
3. Backend validates credentials against env vars
   ↓
4. Backend returns access_token (HS256 JWT)
   ↓
5. WeWeb stores token in AUTH_TOKEN variable
   ↓
6. All protected API calls include:
   - Authorization: Bearer {AUTH_TOKEN}
   - Session-Token: {AUTH_TOKEN}
```

### Endpoint Details

**POST /ops/token**
- File: `services/api/app/security/auth.py` (function: `issue_token()`)
- Request: `application/x-www-form-urlencoded` with `username` + `password`
- Response (success): 
  ```json
  {
    "access_token": "<jwt_token>",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```
- Response (failure): 401 Unauthorized
- Token lifespan: 1 hour (default, configurable)

### Backend Validation

The backend validates credentials by:
1. Comparing submitted username against `VALHALLA_OWNER_USERNAME` env var
2. Comparing submitted password against `VALHALLA_OWNER_PASSWORD_HASH` env var:
   - **Production:** Uses PBKDF2-SHA256 verification (210,000 iterations, timing-safe)
   - **Dev/Sandbox:** Falls back to plaintext if `VALHALLA_OWNER_PASSWORD` set (not recommended)
3. If valid: generates HS256 JWT signed with `VALHALLA_JWT_SECRET`
4. If invalid: returns 401

---

## 2. Render Production Setup

### Required Environment Variables

Configure these on Render dashboard (Settings → Environment Variables):

| Variable | Required | Description |
|----------|----------|-------------|
| `VALHALLA_AUTH_ENABLED` | Yes | Set to `true` to enable authentication |
| `VALHALLA_OWNER_USERNAME` | Yes | Single operator username (e.g., "admin") |
| `VALHALLA_OWNER_PASSWORD_HASH` | Yes (prod only) | PBKDF2-SHA256 hashed password, format: `pbkdf2_sha256$210000$<salt>$<hash>` |
| `VALHALLA_JWT_SECRET` | Yes (prod only) | Secret key for HS256 JWT signing (strong random string, min 32 chars) |
| `VALHALLA_TOKEN_TTL_SECONDS` | No | Token lifespan in seconds (default: 3600) |

### ⚠️ Security Rules

- **NEVER** use `VALHALLA_OWNER_PASSWORD` (plaintext) in production
- **ALWAYS** use `VALHALLA_OWNER_PASSWORD_HASH` (hashed) in production
- **NEVER** commit these env vars to git
- **NEVER** print these values in logs
- Rotate `VALHALLA_JWT_SECRET` if exposed
- Rotate `VALHALLA_OWNER_PASSWORD_HASH` quarterly minimum

---

## 3. How to Reset Password Safely

### Generate New Password Hash

Run this command **locally** in a secure environment (laptop, not shared terminals):

```bash
cd services/api
python -c "from app.security.auth import pbkdf2_hash_password; import getpass; print(pbkdf2_hash_password(getpass.getpass('New owner password: ')))"
```

This will:
1. Prompt you for the new password (input hidden)
2. Hash it using PBKDF2-SHA256 (210,000 iterations)
3. Print the hash (format: `pbkdf2_sha256$210000$<base64_salt>$<base64_hash>`)

Example output:
```
pbkdf2_sha256$210000$abcd1234efgh5678$xyzt9876uiop5432qwer1234asdf5678
```

### Update Render

1. Copy the generated hash
2. Log into Render dashboard
3. Go to Settings → Environment Variables
4. Update `VALHALLA_OWNER_PASSWORD_HASH` with the new hash
5. Render will auto-restart the service
6. Wait 30-60 seconds for restart
7. Test login with the new password

### Test Login

After password reset, test with:

```bash
curl -X POST "https://valhalla-api-ha6a.onrender.com/ops/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_USERNAME" \
  -d "password=YOUR_NEW_PASSWORD"
```

Expected response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 4. Local Development Setup

### Option A: Using PBKDF2 Hash (Recommended)

```bash
# Generate hash once (see section 3)
# Then set in shell:

export VALHALLA_AUTH_ENABLED=true
export VALHALLA_OWNER_USERNAME="your_username_here"
export VALHALLA_OWNER_PASSWORD_HASH="pbkdf2_sha256$210000$<your_hash_here>"
export VALHALLA_JWT_SECRET="local_dev_secret_change_me_for_each_dev"
export VALHALLA_TOKEN_TTL_SECONDS=3600

# Start backend
cd services/api
uvicorn app.main:app --reload --port 4000
```

### Option B: Using Plaintext Password (Dev Only)

**Only use this for isolated local development, never for shared environments:**

```bash
export VALHALLA_AUTH_ENABLED=true
export VALHALLA_OWNER_USERNAME="your_username_here"
export VALHALLA_OWNER_PASSWORD="your_dev_password_here"
export VALHALLA_JWT_SECRET="local_dev_secret_change_me_for_each_dev"

cd services/api
uvicorn app.main:app --reload --port 4000
```

**Do NOT commit these values to `.env` files or code.**

### Option C: Using .env File (Careful!)

If using a `.env` file, ensure:

1. `.env` is **NOT** committed to git
2. `.env` is in `.gitignore`:
   ```
   # In .gitignore
   .env
   .env.local
   .env.*.local
   ```
3. Never share `.env` file with team or in chat
4. Use this only for local development

Example `.env`:
```
VALHALLA_AUTH_ENABLED=true
VALHALLA_OWNER_USERNAME=dev_user
VALHALLA_OWNER_PASSWORD_HASH=pbkdf2_sha256$210000$...
VALHALLA_JWT_SECRET=dev_secret_12345
```

Then load:
```bash
cd services/api
export $(cat .env | xargs)
uvicorn app.main:app --reload --port 4000
```

---

## 5. Test Login Safely

### Test Endpoint Availability

```bash
# Check if auth is enabled
curl -s "http://127.0.0.1:4000/ops/me" -H "Authorization: Bearer invalid" | jq .

# Expected: 401 Unauthorized (auth is working) or 503 (auth disabled)
```

### Get Token

```bash
# Replace YOUR_USERNAME and YOUR_PASSWORD with actual values
curl -X POST "http://127.0.0.1:4000/ops/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_USERNAME" \
  -d "password=YOUR_PASSWORD"
```

Expected success response (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Expected failure response (401 Unauthorized):
```json
{
  "detail": "Invalid credentials"
}
```

### Verify Token Works

```bash
# Save token from previous response
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Use token to access protected endpoint
curl -s "http://127.0.0.1:4000/ops/me" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Expected response:
```json
{
  "ok": true,
  "user": "YOUR_USERNAME"
}
```

---

## 6. Security Warnings

### 🔴 CRITICAL - Never Do This

- ❌ Commit `VALHALLA_OWNER_PASSWORD` or `VALHALLA_OWNER_PASSWORD_HASH` to git
- ❌ Print passwords or hashes in logs or debugging
- ❌ Paste credentials into AI chats, emails, or Slack
- ❌ Use plaintext `VALHALLA_OWNER_PASSWORD` in production
- ❌ Use weak or default passwords in production
- ❌ Share Render environment variables with team members
- ❌ Leave password reset scripts in code

### 🟡 HIGH - Be Careful

- ⚠️ Use HTTPS only (https://valhalla-api-ha6a.onrender.com, not http://)
- ⚠️ Store `VALHALLA_JWT_SECRET` securely (min 32 random chars)
- ⚠️ Rotate `VALHALLA_JWT_SECRET` if exposed
- ⚠️ Keep Render dashboard access restricted
- ⚠️ Use unique dev passwords (do not reuse production password locally)
- ⚠️ Clear terminal history after entering passwords

### 🟢 GOOD - Follow These

- ✅ Use password hashes in production (PBKDF2-SHA256)
- ✅ Generate hashes locally, not on shared systems
- ✅ Store `.env` files with `chmod 600` permissions (Linux/Mac)
- ✅ Use environment variables for all secrets
- ✅ Rotate passwords quarterly
- ✅ Use unique username per environment (e.g., "render-admin", "local-dev")
- ✅ Keep WeWeb's `AUTH_TOKEN` in localStorage (browser, not code)

---

## 7. Password Reset Emergency Procedures

### If Admin Account is Locked Out

1. **Access Render Dashboard:**
   - Go to https://dashboard.render.com
   - Select the Valhalla service
   - Click "Manual Deploy"
   - This kills and restarts the service
   - All tokens become invalid

2. **Force Generate New Password Hash:**
   ```bash
   cd services/api
   python -c "from app.security.auth import pbkdf2_hash_password; import sys; print(pbkdf2_hash_password(sys.argv[1]))" "new_temp_password"
   ```

3. **Update Render Env Var:**
   - Set `VALHALLA_OWNER_PASSWORD_HASH` to new hash
   - Wait for auto-restart

4. **Log In:**
   - Use original `VALHALLA_OWNER_USERNAME`
   - Use the temp password
   - Change password again after verification

### If VALHALLA_JWT_SECRET is Exposed

1. **Generate New Secret:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

2. **Update Render Env Var:**
   - Set `VALHALLA_JWT_SECRET` to new value
   - All existing tokens become invalid (users will be logged out)

3. **Verify Service Restart:**
   - Check Render logs to confirm restart succeeded

---

## 8. WeWeb Integration

### WeWeb Variables to Set

After successful login, WeWeb should store:

```
AUTH_TOKEN = <access_token from response>
```

### WeWeb API Request Headers

All protected requests should include:

```javascript
// Option 1: Authorization header (preferred)
headers: {
  "Authorization": `Bearer ${AUTH_TOKEN}`,
  "Content-Type": "application/json"
}

// Option 2: Session-Token header (alternative)
headers: {
  "Session-Token": AUTH_TOKEN,
  "Content-Type": "application/json"
}
```

### WeWeb Login Workflow

1. User clicks "Login"
2. WeWeb prompts for username + password
3. WeWeb calls POST `/ops/token` with credentials
4. Extract `access_token` from response
5. Store in `AUTH_TOKEN` variable
6. Redirect to dashboard
7. Include `AUTH_TOKEN` in all subsequent API calls

---

## 9. Future Improvements TODO

- [ ] **Change Password Endpoint** - Allow operator to change password without Render access
- [ ] **Admin Reset Command** - CLI tool to safely reset password without dashboard access
- [ ] **Login Audit Log** - Track failed login attempts and successful logins
- [ ] **Token Refresh** - Implement refresh token to extend sessions without re-login
- [ ] **Token Expiry Warning** - Warn user in WeWeb before token expires
- [ ] **Password Expiry Policy** - Force password change quarterly
- [ ] **Multi-User Support** - Add role-based access control when needed
- [ ] **Passwordless Auth** - Consider TOTP or WebAuthn for future

---

## Summary

| Task | Command | Notes |
|------|---------|-------|
| Generate password hash | `python -c "from app.security.auth import pbkdf2_hash_password; import getpass; print(pbkdf2_hash_password(getpass.getpass()))"` | Run locally, keep hash private |
| Set local env vars | `export VALHALLA_OWNER_USERNAME=...` | Never commit to git |
| Start backend | `cd services/api && uvicorn app.main:app --reload --port 4000` | After setting env vars |
| Test login | `curl -X POST http://127.0.0.1:4000/ops/token ...` | Use curl template with placeholders |
| Reset on Render | Update `VALHALLA_OWNER_PASSWORD_HASH` in Render dashboard | Service auto-restarts |
| Emergency restart | Click "Manual Deploy" on Render dashboard | Invalidates all tokens |

---

**Last updated:** May 19, 2026  
**Audience:** Developers, deployment administrators  
**Confidentiality:** Unclassified (do not include actual credentials)
