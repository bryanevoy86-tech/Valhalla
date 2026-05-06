# Bootstrap Admin User for WeWeb Integration

> One-time automatic admin user creation on backend startup

## Overview

The Valhalla backend now automatically creates a bootstrap admin user during startup if configured via environment variables. This allows immediate login to WeWeb without manual database manipulation.

**Key Features:**
- ✅ **Idempotent** - Safe to run multiple times (checks before creating)
- ✅ **Secure** - Uses PBKDF2-SHA256 password hashing
- ✅ **Non-breaking** - Existing auth and users unaffected
- ✅ **Dev-safe** - No hardcoded credentials
- ✅ **Production-aware** - No passwords in logs

---

## Quick Start

### 1. Configure `.env` (Already Done)

```bash
# In d:\dev\.env
BOOTSTRAP_ADMIN_EMAIL=bryanevoy86@gmail.com
BOOTSTRAP_ADMIN_PASSWORD=DrDoom!1
```

**Note:** Both env vars must be set to enable bootstrap. Leave commented to skip.

### 2. Start Backend

```bash
cd d:\dev
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 4000
```

**First startup** creates the bootstrap user automatically.  
**Subsequent startups** skip creation (user already exists).

### 3. Login to WeWeb

Use these credentials in WeWeb:

```
Email:    bryanevoy86@gmail.com
Password: DrDoom!1
```

---

## How It Works

### Startup Flow

```
Backend Starts
    ↓
lifespan() context manager activates
    ↓
5-second delay (let health stabilize)
    ↓
run_post_boot_init() async task
    ↓
run_post_boot_init_sync() main function
    ↓
[1] Seed community data (if needed)
    ↓
[2] bootstrap_admin_user(db) ← YOU ARE HERE
    ↓
Check BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD
    ├─ Both set? → Look up user by email
    │   ├─ Exists? → Skip (idempotent)
    │   └─ Not exist? → Create with hashed password
    ├─ Either missing? → Skip cleanly
    └─ Error? → Log warning, continue (don't fail startup)
    ↓
Bootstrap complete
    ↓
App ready at http://localhost:4000
```

### Code Architecture

**Three files modified:**

1. **`services/api/app/services/bootstrap_admin.py`** (NEW)
   - Read env vars safely
   - Create user with PBKDF2 hashing
   - Handle duplicates gracefully
   - Log appropriately

2. **`services/api/app/services/post_boot_init.py`** (MODIFIED)
   - Import bootstrap_admin_user
   - Call after community seed
   - Log results

3. **`.env`** (MODIFIED)
   - Add BOOTSTRAP_ADMIN_EMAIL
   - Add BOOTSTRAP_ADMIN_PASSWORD

### Database Schema

Bootstrap creates entries in two tables:

**`user_profiles` table:**
```
user_id (PK)     → 1 (auto-increment)
first_name       → "Bootstrap"
last_name        → "Admin"
email            → bryanevoy86@gmail.com
created_at       → 2026-04-17 04:05:41
```

**`account_settings` table:**
```
account_id (PK)  → 1 (auto-increment)
user_id (FK)     → 1
password_hash    → pbkdf2_sha256$210000$...
email_verified   → False
phone_verified   → False
two_factor_enabled → False
```

### Password Hashing

Uses PBKDF2-SHA256 (from `app.security.auth`):

```python
# Input
password = "DrDoom!1"

# Hash process
pbkdf2_hash_password(password)
  ├─ Generate 16-byte salt (random)
  ├─ PBKDF2-SHA256: 210,000 iterations
  ├─ 32-byte derived key
  └─ Return: pbkdf2_sha256$210000$[salt]$[hash]

# Stored in database
password_hash = "pbkdf2_sha256$210000$..."
```

**Verification (on login):**
```python
pbkdf2_verify(user_password, stored_hash)
  ├─ Parse hash format
  ├─ Extract salt and iterations
  ├─ Hash input password with same salt
  └─ Compare securely (constant-time)
```

---

## Environment Variables

### Required (for bootstrap)

| Variable | Value | Example |
|----------|-------|---------|
| `BOOTSTRAP_ADMIN_EMAIL` | Email address | `bryanevoy86@gmail.com` |
| `BOOTSTRAP_ADMIN_PASSWORD` | Plain text password | `DrDoom!1` |

### Supporting (required for auth system)

| Variable | Value | Example |
|----------|-------|---------|
| `VALHALLA_OWNER_USERNAME` | Owner username | `admin` |
| `VALHALLA_OWNER_PASSWORD` | Owner password | `admin-change-me` |
| `VALHALLA_JWT_SECRET` | JWT signing key | (auto-generated in dev) |

### Current `.env` Settings

```bash
# Database
DATABASE_URL=sqlite:///./valhalla_local.db
ENV=dev

# Bootstrap Admin (for WeWeb login)
BOOTSTRAP_ADMIN_EMAIL=bryanevoy86@gmail.com
BOOTSTRAP_ADMIN_PASSWORD=DrDoom!1

# Owner user (for /ops/token endpoint)
VALHALLA_OWNER_USERNAME=admin
VALHALLA_OWNER_PASSWORD=admin-change-me

# JWT
VALHALLA_JWT_SECRET=dev-secret-key-change-in-production

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:4000,http://localhost:3000,https://valhalla.weweb-preview.io,...
```

---

## Security Considerations

### What's NOT Done

❌ **No hardcoded credentials** in source code  
❌ **No passwords in logs** (only status messages)  
❌ **No public endpoints** to create users  
❌ **No exposure** of password hashes  

### What IS Done

✅ **PBKDF2-SHA256** hashing (210,000 iterations)  
✅ **Constant-time comparison** to prevent timing attacks  
✅ **Unique salt** per password (16 bytes)  
✅ **Idempotent creation** (prevents duplicates)  
✅ **Defensive checks** on startup  

### Production Recommendations

1. **Change credentials immediately:**
   ```bash
   BOOTSTRAP_ADMIN_EMAIL=your-real-email@yourcompany.com
   BOOTSTRAP_ADMIN_PASSWORD=strong-unique-password-here
   ```

2. **Use env var injection** (not .env file):
   ```bash
   export BOOTSTRAP_ADMIN_EMAIL="..."
   export BOOTSTRAP_ADMIN_PASSWORD="..."
   uvicorn app.main:app
   ```

3. **Disable bootstrap after first startup:**
   ```bash
   # In .env, comment out:
   # BOOTSTRAP_ADMIN_EMAIL=...
   # BOOTSTRAP_ADMIN_PASSWORD=...
   ```

4. **Database backup** before first startup

5. **Verify with logs:**
   ```
   ✓ Bootstrap admin created: bryanevoy86@gmail.com (user_id=1)
   ```

---

## Testing

### Pre-Flight Test

Run diagnostic before starting backend:

```bash
python test_bootstrap_admin.py
```

**Output:**
```
================================================================================
BOOTSTRAP ADMIN TEST
================================================================================

[1/3] Creating database tables...
✓ Tables created/verified

[2/3] Running bootstrap admin creation...
✓ Bootstrap result: created
  Email: bryanevoy86@gmail.com
  Detail: Bootstrap admin user bryanevoy86@gmail.com created successfully

[3/3] Verifying user creation...
✓ User found: Bootstrap Admin (bryanevoy86@gmail.com)
  User ID: 1
  Has password hash: True
  Created: 2026-04-17 04:05:41

================================================================================
✓ BOOTSTRAP TEST PASSED - User is ready for login
================================================================================
```

### Startup Verification

Watch logs for bootstrap confirmation:

```bash
$ python -m uvicorn app.main:app --reload --port 4000

...
INFO:     Uvicorn running on http://127.0.0.1:4000
...
INFO:     Valhalla startup complete. Loaded 230 router modules.
INFO:     ✓ Bootstrap admin created: bryanevoy86@gmail.com (user_id=1)
INFO:     ✓ Post-boot initialization completed successfully.
```

### Login Test

Via curl:

```bash
curl -X POST http://localhost:4000/ops/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bryanevoy86%40gmail.com&password=DrDoom%211"
```

**Success response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error response (wrong password):**
```json
{"detail": "Invalid credentials"}
```

### Via WeWeb

1. Open WeWeb editor: https://editor.weweb.io
2. Create REST API connector
3. Configure login endpoint:
   - **URL:** `http://localhost:4000/ops/token`
   - **Method:** POST
   - **Body:** `{username, password}`
4. Test with bootstrap credentials

---

## Troubleshooting

### User Not Created

**Check logs:**
```bash
grep "Bootstrap admin" *.log | tail
```

**Verify env vars:**
```bash
# PowerShell
$env:BOOTSTRAP_ADMIN_EMAIL
$env:BOOTSTRAP_ADMIN_PASSWORD

# Or in .env file
cat .env | grep BOOTSTRAP
```

**Solution:** Both env vars must be set and non-empty.

### Login Fails

**1. Check user exists:**
```python
from app.core.db import SessionLocal
from app.users.models import UserProfile

db = SessionLocal()
user = db.query(UserProfile).filter(
    UserProfile.email == "bryanevoy86@gmail.com"
).first()
print(f"Found: {user}")
db.close()
```

**2. Check password hash:**
```python
from app.users.models import AccountSettings

settings = db.query(AccountSettings).filter(
    AccountSettings.user_id == user.user_id
).first()
print(f"Has hash: {bool(settings.password_hash)}")
```

**3. Test hash verification:**
```python
from app.security.auth import pbkdf2_verify

password = "DrDoom!1"
result = pbkdf2_verify(password, settings.password_hash)
print(f"Valid password: {result}")
```

### Bootstrap Runs Multiple Times

**This is OK** - The code checks if user exists first:

```python
if _user_exists(db, email):
    return {
        "ok": True,
        "status": "already_exists",
        "email": email,
        "detail": f"User {email} already exists",
    }
```

**Idempotent by design** - Safe to restart backend multiple times.

### Database Locked

**Solution:** Close other connections:
```bash
# Kill uvicorn processes
taskkill /F /IM python.exe

# Or specific port
netstat -ano | findstr :4000
taskkill /PID <PID> /F
```

---

## Production Deployment

### Render

Set environment variables in Render dashboard:

```
BOOTSTRAP_ADMIN_EMAIL=your-email@company.com
BOOTSTRAP_ADMIN_PASSWORD=<strong-password>
VALHALLA_OWNER_USERNAME=admin
VALHALLA_OWNER_PASSWORD=<strong-password>
VALHALLA_JWT_SECRET=<generated-key>
DATABASE_URL=postgresql://...
```

### Docker

In `Dockerfile`:

```dockerfile
ENV BOOTSTRAP_ADMIN_EMAIL=${BOOTSTRAP_ADMIN_EMAIL}
ENV BOOTSTRAP_ADMIN_PASSWORD=${BOOTSTRAP_ADMIN_PASSWORD}
```

Run with vars:

```bash
docker run -e BOOTSTRAP_ADMIN_EMAIL=... -e BOOTSTRAP_ADMIN_PASSWORD=... valhalla:latest
```

### Kubernetes

In `values.yaml`:

```yaml
env:
  - name: BOOTSTRAP_ADMIN_EMAIL
    valueFrom:
      secretKeyRef:
        name: valhalla-secrets
        key: bootstrap_email
  - name: BOOTSTRAP_ADMIN_PASSWORD
    valueFrom:
      secretKeyRef:
        name: valhalla-secrets
        key: bootstrap_password
```

---

## Implementation Details

### Files Modified

#### 1. **`services/api/app/services/bootstrap_admin.py`** (NEW - 140 lines)

Core bootstrap logic:

```python
def bootstrap_admin_user(db: Session) -> Dict[str, Any]:
    """
    Bootstrap admin user creation on startup.
    
    Returns:
    - "ok": bool (operation success)
    - "status": str ("created" | "already_exists" | "skipped" | "error")
    - "email": str (email if relevant)
    - "detail": str (human-readable message)
    """
```

**Key functions:**
- `_read_bootstrap_env()` - Read env vars safely
- `_user_exists()` - Check if user already exists
- `_create_bootstrap_user()` - Create user with PBKDF2 hash
- `bootstrap_admin_user()` - Main entry point

#### 2. **`services/api/app/services/post_boot_init.py`** (MODIFIED)

Integrated bootstrap call:

```python
# Import
from app.services.bootstrap_admin import bootstrap_admin_user

# Usage in run_post_boot_init_sync()
bootstrap_result = bootstrap_admin_user(db)
if bootstrap_result["status"] == "created":
    log.info(f"✓ Bootstrap admin created: {bootstrap_result['email']}")
elif bootstrap_result["status"] == "already_exists":
    log.info(f"✓ Bootstrap admin already exists: {bootstrap_result['email']}")
```

#### 3. **`.env`** (MODIFIED)

Added two new variables:

```bash
# Bootstrap Admin User (one-time creation on startup)
BOOTSTRAP_ADMIN_EMAIL=bryanevoy86@gmail.com
BOOTSTRAP_ADMIN_PASSWORD=DrDoom!1

# Auth/Ops User (for /ops/token endpoint if needed)
VALHALLA_OWNER_USERNAME=admin
VALHALLA_OWNER_PASSWORD=admin-change-me
```

### Data Flow

```
.env (env vars)
    ↓
bootstrap_admin_user()
    ├─ _read_bootstrap_env()
    │   └─ Return {email, password}
    ├─ _user_exists(db, email)
    │   └─ Query UserProfile by email
    └─ _create_bootstrap_user(db, email, password)
        ├─ Create UserProfile row
        ├─ pbkdf2_hash_password(password)
        │   └─ PBKDF2-SHA256 hash
        ├─ Create AccountSettings with hash
        └─ Commit to database
    ↓
Return status → Log result
    ↓
Ready for login
```

### User Model Integration

**UserProfile** (d:\dev\services\api\app\users\models.py):
```python
class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    user_id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**AccountSettings** (same file):
```python
class AccountSettings(Base):
    __tablename__ = 'account_settings'
    
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'))
    password_hash = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False)
```

---

## Next Steps

1. ✅ **Backend started** → Bootstrap user created
2. ✅ **Test login** → Verify credentials work
3. ⏭️ **Connect WeWeb** → Add REST API connector
4. ⏭️ **Build UI** → Create WeWeb pages
5. ⏭️ **Test workflows** → Deal management, etc.

---

## FAQ

**Q: Can I change the bootstrap email after creation?**  
A: Yes, update directly:
```sql
UPDATE user_profiles SET email = 'new@email.com' WHERE user_id = 1;
```

**Q: What if I forget the bootstrap password?**  
A: Reset in database:
```python
from app.security.auth import pbkdf2_hash_password
from app.core.db import SessionLocal
from app.users.models import AccountSettings

new_password = "NewPassword123"
hash_value = pbkdf2_hash_password(new_password)

db = SessionLocal()
db.query(AccountSettings).filter(
    AccountSettings.user_id == 1
).update({"password_hash": hash_value})
db.commit()
```

**Q: Will bootstrap interfere with existing users?**  
A: No. It only checks/creates one user by email. Other users unaffected.

**Q: Can I create multiple bootstrap users?**  
A: Only one per startup (by design). For multiple, use admin endpoints or database directly.

**Q: Is this production-safe?**  
A: Yes, with caveats:
- ✅ Uses strong hashing
- ✅ Idempotent (safe to retry)
- ✅ Graceful error handling
- ⚠️ Set strong passwords
- ⚠️ Disable after first startup (optional)

**Q: How do I disable bootstrap?**  
A: Comment/remove env vars:
```bash
# BOOTSTRAP_ADMIN_EMAIL=...
# BOOTSTRAP_ADMIN_PASSWORD=...
```

---

## Support

**Logs location:** Check standard FastAPI/Uvicorn logs:
```bash
grep -i "bootstrap" *.log
```

**Debug mode:** Set `DEBUG=true` in `.env`

**Issues?** Check:
1. Both env vars are set
2. Database tables exist (migrations applied)
3. No duplicate users by email
4. Password not None/empty

---

**Status:** ✅ **Ready for WeWeb Integration**
