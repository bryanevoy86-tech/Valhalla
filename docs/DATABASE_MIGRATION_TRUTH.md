# DATABASE & MIGRATION TRUTH — Valhalla Backend

**Generated**: June 27, 2026  
**Scope**: Alembic configuration, migration status, and database schema  
**Status**: 🚨 **CRITICAL: Multiple migration heads detected — backend cannot start**

---

## EXECUTIVE SUMMARY

### Current State
- **Alembic Status**: ❌ BLOCKED — Multiple active heads
- **Database**: ❌ NOT INITIALIZED (migrations fail at startup)
- **Tables**: ❌ UNKNOWN (cannot inspect without running migrations)
- **Startup**: ❌ FAILED — `alembic upgrade head` returns error code 1

### Root Cause
Alembic configuration has two active migration heads that cannot be merged:
1. `20260422_add_brrrr_analysis` (Branch A)
2. `20260506_001` (Branch B)

Previous merge attempt (`7daef17`) did not fully resolve the conflict.

---

## ALEMBIC CONFIGURATION

### File Location
```
d:\dev\alembic.ini
```

### Key Settings

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg2://
```

### Important Notes

- `script_location`: Points to `d:\dev\alembic` directory
- `sqlalchemy.url`: Empty in INI (uses `DATABASE_URL` environment variable)
- **Dual Alembic Folders** ⚠️:
  - `d:\dev\alembic/` — Used by alembic.ini (PRIMARY)
  - `d:\dev\services\api\alembic/` — Duplicate (NOT USED)

### Environment Variable Handling

| Variable | Used For | Default |
|----------|----------|---------|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///valhalla_test.db` (set by start.py) |
| `VALHALLA_JWT_SECRET` | JWT signing | dev-secret-key (start.py) |
| `PORT` | Server port | 8000 |
| `HOST` | Server host | 0.0.0.0 |

---

## MIGRATION CONFLICT ANALYSIS

### Multiple Heads Issue

**Status**: 🚨 CRITICAL BLOCKER

#### Branch A: BRRRR Analysis
- **Origin**: `20260422_002` (base merge point)
- **Path**:
  ```
  20260422_002
    ↓
  20260422_003
    ↓
  20260422_add_buyer_matching
    ↓
  20260422_add_flip_analysis
    ↓
  20260422_add_brrrr_analysis ← HEAD A
  ```

#### Branch B: VA Intake
- **Origin**: `20260422_002` (base merge point)
- **Path**:
  ```
  20260422_002
    ↓
  20260506_001 (VA intake tables) ← HEAD B
  ```

### Merge Attempt

**Commit**: `7daef17` "fix: merge migration heads to resolve Alembic multiple heads error"

**Merge Revision**: `650836770c62` (2026-05-08 13:43:00)

**Merge Result**: Incomplete

**Current HEAD**: `20260508_add_property_intel` (2026-05-08 14:00:00)

**Problem**: Merge commit exists in code but database has not been upgraded to it

---

## MIGRATION HISTORY (Partial)

```
f8e5d12 ← Latest (20260508_add_property_intel)
  ↑
  ├─ down_revision: 650836770c62
  │
650836770c62 ← Merge commit (attempted to resolve conflict)
  ↑
  ├─ Merged from:
  │  ├─ 20260422_add_brrrr_analysis (Branch A)
  │  └─ 20260506_001 (Branch B)
  │
  │
20260422_add_brrrr_analysis ← HEAD A (unmerged)
  ↑
20260422_add_flip_analysis
  ↑
20260422_add_buyer_matching
  ↑
20260422_003
  ↑
20260422_002 ← Base (common ancestor)
  ↑
20260506_001 ← HEAD B (unmerged)
```

---

## DATABASE TABLE EXPECTATIONS

### Core Pipeline Tables (Required)

| Table | Purpose | Migration | Status |
|-------|---------|-----------|--------|
| `users` | User authentication | `20260422_*` | ❓ Unknown |
| `leads` | Lead database | `20260422_*` | ❓ Unknown |
| `deals` | Deal management | `20260422_*` | ❓ Unknown |
| `approvals` | Approval workflow | `20260422_*` | ❓ Unknown |
| `buyers` | Buyer information | `20260422_*` | ❓ Unknown |

### VA Intake Tables (New)

| Table | Purpose | Migration | Status |
|-------|---------|-----------|--------|
| `va_leads` | VA intake leads | `20260506_001` | ❓ Unknown |
| `va_approval_queue` | VA approval queue | `20260506_001` | ❓ Unknown |

### System Tables (Inferred)

| Table | Purpose | Migration | Status |
|-------|---------|-----------|--------|
| `audit_events` | Audit log | Various | ❓ Unknown |
| `system_metadata` | System state | Various | ❓ Unknown |
| `go_live_state` | Go-live flag | Likely recent | ❓ Unknown |

### BRRRR Analysis Tables (From Branch A)

| Table | Purpose | Migration | Status |
|-------|---------|-----------|--------|
| BRRRR-specific | Analysis data | `20260422_add_brrrr_analysis` | ❓ Unknown |
| Flip analysis | Deal flip analysis | `20260422_add_flip_analysis` | ❓ Unknown |
| Buyer matching | Buyer matching data | `20260422_add_buyer_matching` | ❓ Unknown |

---

## STARTUP FAILURE DETAILS

### Startup Command
```bash
python start.py
```

### Startup Sequence

1. **start.py runs**
   - Sets `DATABASE_URL = "sqlite:///valhalla_test.db"` (if not set)
   - Sets JWT secret
   - Configures Python path

2. **Before uvicorn starts, migrations are run:**
   ```python
   # In services/api/app/main.py lifespan or similar
   result = subprocess.run(["alembic", "upgrade", "head"])
   if result.returncode != 0:
       print("❌ STARTUP FAILED: Migrations failed with code 1")
       sys.exit(1)
   ```

3. **Alembic upgrade head fails:**
   ```
   ERROR: Multiple migration heads detected in alembic/versions/
   Cannot proceed with upgrade head — ambiguous targets
   ```

4. **Application exits**
   ```
   Exit code: 1
   Server never starts
   All endpoints unavailable
   ```

---

## VERIFICATION ATTEMPTS

### Attempt 1: Check Current Revision

**Command**: 
```bash
cd d:\dev
$env:DATABASE_URL = "sqlite:///valhalla_test.db"
alembic current
```

**Result**: 
```
ERROR: Current() not supported when multiple heads are present
Use alembic heads to view all heads
```

### Attempt 2: List Heads

**Command**:
```bash
alembic heads
```

**Expected Result** (if run): 
```
20260422_add_brrrr_analysis
20260506_001
```

### Attempt 3: View Migration History

**Command**:
```bash
alembic history --verbose | head -30
```

**Expected Result** (if run):
```
20260422_002 - Base merge point
20260422_003 - Branch A continues
20260422_add_buyer_matching - Branch A
20260422_add_flip_analysis - Branch A
20260422_add_brrrr_analysis - HEAD A
20260506_001 - HEAD B (parallel branch)
650836770c62 - Merge attempt (incomplete)
20260508_add_property_intel - After merge (unapplied)
```

---

## TABLES CREATED BY VA INTAKE MIGRATION

### va_leads Table

**Purpose**: Store VA-submitted lead information

**Columns** (inferred from router code):
- `id` (PK)
- `source` (string) — VA source identifier
- `contact_name` (string)
- `contact_phone` (string)
- `contact_email` (string)
- `property_address` (string)
- `property_value` (decimal)
- `distress_signals` (JSON) — Heimdall scoring data
- `heimdall_score` (int) — Lead qualification score
- `status` (enum) — new, qualified, approved, denied, converted
- `created_at` (timestamp)
- `qualified_at` (timestamp, nullable)
- `audit_trail` (JSON) — Historical events

### va_approval_queue Table

**Purpose**: Track leads pending approval

**Columns** (inferred from router code):
- `id` (PK)
- `va_lead_id` (FK → va_leads)
- `status` (enum) — pending, approved, denied
- `queued_at` (timestamp)
- `approved_by` (string, nullable) — Approver identifier
- `approved_at` (timestamp, nullable)
- `denial_reason` (string, nullable)
- `deal_id` (int, nullable) — After conversion

---

## MIGRATION RESOLUTION OPTIONS

### Option 1: Complete the Merge (RECOMMENDED)

1. Examine merge commit `650836770c62`
2. Verify it correctly combines both branches
3. Set database to merge commit: `alembic stamp 650836770c62`
4. Continue to HEAD: `alembic upgrade head`

### Option 2: Choose Single Branch

**Choose Branch A** (BRRRR Analysis):
```bash
alembic stamp 20260422_add_brrrr_analysis
# Then downgrade VA tables if needed
```

**Choose Branch B** (VA Intake):
```bash
alembic stamp 20260506_001
# Then downgrade BRRRR tables if needed
```

### Option 3: Create New Merge Migration

```bash
alembic merge -m "resolve brrrr_analysis and va_intake branches"
# Edit the resulting file to handle schema conflicts
alembic upgrade head
```

### Option 4: Reset and Rebuild (Nuclear)

```bash
# Backup existing db
cp valhalla_test.db valhalla_test.db.bak

# Delete test db
rm valhalla_test.db

# Downgrade to base
alembic downgrade base

# Upgrade fresh to head
alembic upgrade head

# Note: This will fail if migrations are still conflicted
```

---

## RECOMMENDED FIX SEQUENCE

### Step 1: Diagnose

```bash
cd d:\dev

# See the exact error
alembic heads
alembic history -v | more

# Examine merge commit
cat alembic/versions/650836770c62_*py
```

### Step 2: Resolve

**If merge is valid**:
```bash
# Mark DB as at merge point
alembic stamp 650836770c62

# Then upgrade
alembic upgrade head
```

**If merge needs rework**:
```bash
# Create new merge migration
alembic merge -m "integrate brrrr and va_intake"

# Edit file and run
alembic upgrade head
```

### Step 3: Verify

```bash
# Check current revision
alembic current
# Should show: 20260508_add_property_intel

# Verify tables exist
# For SQLite:
sqlite3 valhalla_test.db ".tables"
# Should show: leads, deals, users, va_leads, va_approval_queue, ...

# For PostgreSQL:
psql $DATABASE_URL -c "\dt"
```

### Step 4: Start Backend

```bash
$env:DATABASE_URL = "sqlite:///valhalla_test.db"
python start.py

# Should succeed with:
# INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## PREVENTIVE MEASURES

### For Future Development

1. **Use single alembic directory**: Delete `services/api/alembic/` to avoid confusion
2. **Merge branches early**: Don't let parallel migrations diverge far
3. **Test migrations locally**: Before committing
4. **Automated migration tests**: In CI/CD pipeline
5. **Clear commit messages**: Include migration rationale in commits

### Maintenance

- **Weekly review**: Check for stray migration files
- **Document merge decisions**: Add comments to merge migrations
- **Backup production**: Before any alembic operations
- **Test downgrade**: Ensure migrations are reversible

---

## TABLE SCHEMA (Expected, Not Yet Verified)

### Core Tables (from git history)

**users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**leads**
```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id),
    name VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);
```

**deals**
```sql
CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    value DECIMAL,
    stage VARCHAR DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### VA Intake Tables (from code)

**va_leads**
```sql
CREATE TABLE va_leads (
    id SERIAL PRIMARY KEY,
    source VARCHAR,
    contact_name VARCHAR,
    contact_phone VARCHAR,
    contact_email VARCHAR,
    property_address VARCHAR,
    property_value DECIMAL,
    distress_signals JSONB,
    heimdall_score INTEGER,
    status VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**va_approval_queue**
```sql
CREATE TABLE va_approval_queue (
    id SERIAL PRIMARY KEY,
    va_lead_id INTEGER REFERENCES va_leads(id),
    status VARCHAR,
    queued_at TIMESTAMP DEFAULT NOW(),
    approved_by VARCHAR,
    approved_at TIMESTAMP,
    deal_id INTEGER REFERENCES deals(id)
);
```

---

## CRITICAL PATH TO PRODUCTION

| Step | Blocker | Resolution Time |
|------|---------|-----------------|
| Fix migrations | 🚨 CRITICAL | 30-60 min |
| Start backend | Depends on migrations | 5 min |
| Initialize DB | Depends on migrations | 1 min |
| Test endpoints | Depends on DB | 15 min |
| Deploy to Render | Depends on local success | 5-10 min |

---

## CONCLUSION

**Valhalla backend is blocked by alembic migration conflict.**

Once the multiple-heads issue is resolved:
1. Database will initialize successfully
2. All tables (core + VA intake) will be created
3. Backend will start and serve all endpoints
4. WeWeb integration can proceed

**Next action**: Follow "Recommended Fix Sequence" above.
