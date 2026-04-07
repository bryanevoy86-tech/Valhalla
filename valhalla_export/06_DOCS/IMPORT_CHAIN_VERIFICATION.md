# Import Chain Verification & Detailed File References

## EXECUTION FLOW: From Entry to Database

### 1. ENTRY POINT CHAIN

```
Task: uvicorn app.main:app --reload --port 4000
       ↓
       Loads: d:\dev\app\main.py
       ↓
       sys.modules['app'] = import_module("services.api.app")
       ↓
       from services.api.app.main import app
       ↓
       LOADS: d:\dev\services\api\app\main.py  ⭐ REAL APP
```

---

## 2. MODULE ALIASING TRICK

The wrapper uses Python's `sys.modules` injection:

```python
# In d:\dev\app\main.py
from importlib import import_module

# Register services.api.app as 'app' module BEFORE importing main
_real_package = import_module("services.api.app")
sys.modules['app'] = _real_package

# Now imports of 'from app.xxx' will resolve to services.api.app.xxx
from services.api.app.main import app
```

**Result:**
- When code does `from app.core.db import ...` 
- Python's import system resolves it to `from services.api.app.core.db import ...`
- This allows the canonical system to use `app.*` imports throughout
- No code changes needed, just module aliasing

---

## 3. COMPLETE IMPORT HIERARCHY

### ACTIVE CANONICAL SYSTEM: services/api/app

```
d:\dev\services\api\app\
├── main.py (line 13)
│   ├── from app.core.db import verify_schema_initialized
│   ├── from app.core.settings import settings
│   ├── from app.middleware.safety import safety_guard
│   ├── from app.core.correlation_middleware import CorrelationIdMiddleware
│   ├── from app.core.read_only_middleware import ReadOnlyShieldMiddleware
│   ├── from app.core.error_handling import register_error_handlers
│   ├── from app.core.go_live_middleware import GoLiveMiddleware
│   ├── from app.core.execution_class_middleware import ExecutionClassMiddleware
│   ├── from app.core.router_registry import RouterSpec, include_router_safe
│   └── [Line 1778+] from app.core.prelaunch.alerts_engine.router import router
│
├── core/
│   ├── db.py (ORM engine & sessions)
│   ├── config.py (Settings)
│   ├── settings.py (Feature flags)
│   ├── correlation_middleware.py
│   ├── error_handling.py
│   ├── execution_class.py
│   ├── go_live_middleware.py
│   ├── read_only_middleware.py
│   ├── execution_class_middleware.py
│   ├── router_registry.py
│   ├── runtime_flags.py
│   ├── prelaunch/
│   │   ├── alerts_engine/router.py
│   │   └── daily_ops/router.py
│   └── [40+ infrastructure files]
│
├── routers/ (200+ files)
│   ├── admin.py
│   ├── admin_*.py (15+ admin routers)
│   ├── deals.py
│   ├── deal_analyzer.py
│   ├── leads.py
│   ├── buyers.py
│   ├── governance_*.py (8+ governance routers)
│   ├── finance routers (20+)
│   └── [170+ more routers]
│
├── models/ (180+ files)
│   ├── deal.py
│   ├── lead.py
│   ├── user.py
│   ├── buyer.py
│   ├── contracts.py
│   ├── governance_decision.py
│   └── [175+ more models]
│
├── services/ (140+ files)
│   ├── deal_finalization.py
│   ├── governance_service.py
│   ├── lead_service.py
│   ├── analytics_engine.py
│   └── [135+ more services]
│
├── schemas/
│   └── [Pydantic models for all routers]
│
└── [100+ domain-specific directories]
    ├── accounting/
    ├── banking/
    ├── compliance/
    ├── deals/
    ├── governance/
    ├── heimdall/
    ├── leads/
    └── [More domains...]
```

---

## 4. DATABASE CONNECTION FLOW

### Active Path: ORM-Based

```
Request → app.dependencies.py (Depends())
   ↓
FastAPI injects: Session = Depends(get_db_session)
   ↓
SessionLocal() from app.core.db
   ↓
Engine created from: app.core.db.engine
   ↓
Connection Pool (SQLAlchemy)
   ↓
PostgreSQL (via DATABASE_URL) OR SQLite (fallback)
   ↓
Models: app.models.*  (SQLAlchemy ORM)
```

**File References:**
- Engine config: `d:\dev\services\api\app\core\db.py`
- Session factory: `d:\dev\services\api\app\core\db.py` 
- Dependency injection: `d:\dev\services\api\app\core\dependencies.py`
- Models base: `d:\dev\services\api\app\models\base.py`

### Compatibility Shim Path:

```
Old code: from app.db import engine
   ↓
Resolves to: d:\dev\services\api\app\db.py
   ↓
Which has: from app.core.db import engine  # Compatibility shim
   ↓
Actual engine: d:\dev\services\api\app\core\db.py
```

**File Reference:** `d:\dev\services\api\app\db.py` (11 lines)

---

## 5. LEGACY SYSTEM - TEST FOR INACTIVITY

### What Would Happen If We Used `/dev/backend/main.py`:

```
uvicorn backend.main:app
   ↓
Loads: d:\dev\backend\main.py
   ↓
Tries: from backend.db import get_conn
   ↓
Fails to find: 
   - backend.models.*
   - backend.schemas.*
   - backend.services.governance_service
   - backend.core.correlation_middleware
   - (All 180+ canonical services/models)
   ↓
Result: APP CRASHES - Missing dependencies
```

**Proof of Legacy Status:**
- `d:\dev\backend\main.py` imports from `backend.*` namespace
- Never imports from `services.api.app`
- Returns: raw psycopg2 connections (no ORM)
- Contains: only Heimdall/admin routes (150+ lines of just those)
- Handler count: ~40 Heimdall-specific endpoints
- Total apps: ISOLATED, DOESN'T CONNECT TO REAL SYSTEM

---

## 6. WRAPPER ARCHITECTURE - WHY IT EXISTS

### The Problem It Solves:

Inside `services/api/app/`, all code does:
```python
from app.core.db import engine
from app.routers.deals import router
from app.models.deal import Deal
```

But Python imports are relative to the **current package name**. The code is in package `services.api.app`, so:
```
from app.core.db  
  ↓ 
Error: No module named 'app' 
(because we're in 'services.api.app', not 'app')
```

### The Solution: Module Aliasing

The wrapper (`d:\dev\app\main.py`) does:
```python
sys.modules['app'] = import_module("services.api.app")
```

Now when canonical system imports `from app.core.db`, Python:
1. Looks in `sys.modules['app']`
2. Finds: `services.api.app` object
3. Imports successfully ✅

### Why Not Move Code?

1. **Massive refactoring** - 300+ files use `app.` imports
2. **Runtime cost** - Regex-replacing 10,000+ import lines
3. **Current solution works** - Elegant hack
4. **Backward compatible** - Old packs still work

---

## 7. COMPLETE FILE LISTING BY CATEGORY

### ENTRY POINTS (2 active, 2 legacy)

| File | Type | Status | Lines | Purpose |
|------|------|--------|-------|---------|
| `d:\dev\app\main.py` | Wrapper | **ACTIVE** | ~30 | Entry proxy |
| `d:\dev\services\api\app\main.py` | Application | **ACTIVE** | ~1800 | Real backend |
| `d:\dev\backend\main.py` | Legacy | INACTIVE | ~1000 | Old admin |
| `d:\dev\backend\app\main.py` | Legacy | OBSOLETE | ~50 | Intermediate |

### DATABASE CONNECTIONS (3 versions)

| File | Type | Status | Purpose |
|------|------|--------|---------|
| `d:\dev\services\api\app\core\db.py` | SQLAlchemy | **ACTIVE** | ORM engine |
| `d:\dev\services\api\app\db.py` | Shim | **ACTIVE** | Backward compat |
| `d:\dev\backend\app\core\db.py` | SQLAlchemy | LEGACY | Old config |
| `d:\dev\backend\db.py` | psycopg2 | NEVER USED | Raw SQL only |

### MODELS (3 levels)

| Location | Count | Status | Coverage |
|----------|-------|--------|----------|
| `d:\dev\services\api\app\models\` | 180+ | **ACTIVE** | Complete |
| `d:\dev\backend\app\models\` | 18 | OBSOLETE | Limited |
| `d:\dev\app\models\` | 4 | Wrapper | Minimal |

### ROUTERS (3 levels)

| Location | Count | Status | Coverage |
|----------|-------|--------|----------|
| `d:\dev\services\api\app\routers\` | 200+ | **ACTIVE** | Complete API |
| `d:\dev\backend\app\routers\` | 16 | OBSOLETE | Admin only |
| `d:\dev\app\routers\` | 11 | Wrapper | Minimal |

### SERVICES (3 levels)

| Location | Count | Status | Coverage |
|----------|-------|--------|----------|
| `d:\dev\services\api\app\services\` | 140+ | **ACTIVE** | Full logic |
| `d:\dev\backend\app\services\` | 16 | OBSOLETE | Limited |
| `d:\dev\app\services\` | 4 | Wrapper | Minimal |

### INFRASTRUCTURE (2 versions)

| Location | Count | Status |
|----------|-------|--------|
| `d:\dev\services\api\app\core\` | 40+ | **ACTIVE** |
| `d:\dev\backend\app\core\` | 8 | LEGACY |

---

## 8. HOW TO VERIFY EACH CLAIM

### Claim: `/dev/app/` is just a wrapper

**Verification CMD:**
```bash
# Count actual code lines (excluding comments/blanks)
wc -l d:\dev\app\main.py          # ~30 lines
wc -l d:\dev\services\api\app\main.py   # ~1800 lines

# Check imports
grep "from services.api.app" d:\dev\app\main.py  # Should find 1
```

### Claim: `/dev/backend/` is never imported

**Verification CMD:**
```bash
# Search entire canonical system for 'from backend' or 'import backend'
grep -r "from backend" d:\dev\services\api\app\  # Should find 0
grep -r "import backend" d:\dev\services\api\app\  # Should find 0

# Search in active system
grep -r "from backend" d:\dev\app\   # Should find 0
```

### Claim: `/dev/services/api/app/` is the real system

**Verification CMD:**
```bash
# Count substantial components
ls -1 d:\dev\services\api\app\models\*.py | wc -l    # 180+
ls -1 d:\dev\services\api\app\routers\*.py | wc -l   # 200+
ls -1 d:\dev\services\api\app\services\*.py | wc -l  # 140+
ls -1d d:\dev\services\api\app\*/ | wc -l            # 100+ domains
```

### Claim: sys.modules aliasing is used

**Verification CMD:**
```bash
grep -n "sys.modules" d:\dev\app\main.py  # Line ~15
grep -n "import_module" d:\dev\app\main.py  # Line ~10
```

---

## 9. DEPENDENCY INJECTION PATTERN

### How Routers Access Database

**Pattern used throughout routers:**

```python
# From d:\dev\services\api\app\routers\deals.py (example - actual file)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db_session

router = APIRouter(prefix="/api/v1/deals", tags=["deals"])

@router.get("/")
def list_deals(db: Session = Depends(get_db_session)):
    # db is auto-injected FastAPI dependency
    # Type: SQLAlchemy ORM Session
    deals = db.query(Deal).all()
    return deals
```

**Dependency Chain:**
1. FastAPI sees `Depends(get_db_session)`
2. Calls: `app.core.dependencies.get_db_session()`
3. Gets: `SessionLocal()` from `app.core.db`
4. SessionLocal uses: `engine` from `app.core.db`
5. Engine configured in: `app.core.config`

**File References:**
- `d:\dev\services\api\app\core\dependencies.py` - Defines get_db_session()
- `d:\dev\services\api\app\core\db.py` - Creates SessionLocal
- All `/routers/*.py` - Use this pattern

---

## 10. REQUEST LIFECYCLE

```
HTTP Request: GET /api/v1/deals
     ↓
uvicorn → d:\dev\app\main.py
     ↓
sys.modules['app'] injection established
     ↓
from services.api.app.main import app
     ↓
d:\dev\services\api\app\main.py lifespan context
     ↓
Starts all middleware:
  - CorrelationIdMiddleware
  - ReadOnlyShieldMiddleware
  - ExecutionClassMiddleware
  - GoLiveMiddleware
     ↓
Routes request to matching router
  (d:\dev\services\api\app\routers\deals.py)
     ↓
Router gets DB session: Depends(get_db_session)
     ↓
from app.core.dependencies.get_db_session()
     ↓
SessionLocal() from app.core.db
     ↓
Uses: d:\dev\services\api\app\core\db.engine
     ↓
Executes ORM query against PostgreSQL
     ↓
Router returns response using models/schemas
  (d:\dev\services\api\app\models\deal.py)
  (d:\dev\services\api\app\schemas\deal.py)
     ↓
Response middleware processes response
     ↓
HTTP Response sent to client
```

---

## 11. KEY FILE LOCATIONS (QUICK REFERENCE)

### Must-Know Paths

```
ENTRY:       d:\dev\app\main.py
REAL APP:    d:\dev\services\api\app\main.py
ORM CONFIG:  d:\dev\services\api\app\core\db.py
SETTINGS:    d:\dev\services\api\app\core\config.py
MIDDLEWARE:  d:\dev\services\api\app\core\*middleware.py
MODELS:      d:\dev\services\api\app\models\*.py
ROUTERS:     d:\dev\services\api\app\routers\*.py
SERVICES:    d:\dev\services\api\app\services\*.py
SCHEMAS:     d:\dev\services\api\app\schemas\*.py
DEPENDENCIES: d:\dev\services\api\app\core\dependencies.py

LEGACY (IGNORE):
OLD MAIN:    d:\dev\backend\main.py (not used)
OLD APP:     d:\dev\backend\app\main.py (superseded)
OLD DB:      d:\dev\backend\db.py (raw SQL, unused)
```

---

## 12. CONSOLIDATION IMPACT ANALYSIS

### Safe to Delete (No Active References)

```
d:\dev\backend\
  - No imports from active system
  - Uses 'from backend.*' which doesn't exist in canonical
  - Would crash if someone tried to use it as entry point
  - Safe to archive/delete
  
d:\dev\backend\app\
  - Models not imported anywhere
  - Routers not registered in main app
  - Services not called by canonical system
  - Safe to delete/archive
```

### Required (Active)

```
d:\dev\app\
  - Entry point for uvicorn
  - Entry point for all imports
  - Cannot delete
  - Can minimize further if needed

d:\dev\services\api\app\
  - Contains all business logic
  - Cannot delete or move
  - ALL development targets this
```

### Optional (Testing/Archive)

```
d:\dev\valhalla\
  - Mirror of entire structure
  - If used for testing, keep it
  - If not used, archive to /archive/valhalla_mirror
  - Check git history to determine purpose
```

---

## 13. IMPORT VERIFICATION TESTS

### Test 1: Wrapper Correctness

```python
# This should work:
import sys
sys.path.insert(0, 'd:\\dev')
from app.main import app
print(type(app))  # Should be: <class 'fastapi.FastAPI'>

# Verify the aliasing:
import services.api.app
sys.modules['app'] = services.api.app
from app.core.db import engine
print(engine)  # Should print SQLAlchemy engine
```

### Test 2: No Legacy Imports in Active System

```bash
# Expected: 0 results
grep -r "^from backend" d:\dev\services\api\app\
grep -r "^import backend" d:\dev\services\api\app\
grep -r "from backend" d:\dev\app\
grep -r "import backend" d:\dev\app\
```

### Test 3: All Routers Loaded

```python
# From d:\dev\services\api\app\main.py around line 1778
from app.core.prelaunch.alerts_engine.router import router as alerts_router
from app.core.prelaunch.daily_ops.router import router as daily_ops_router
# ... 200+ router includes

# Each router is included via include_router_safe()
app.include_router(...)
```

---

## SUMMARY TABLE

| Aspect | Value | Evidence |
|--------|-------|----------|
| **Canonical Backend** | `d:\dev\services\api\app\` | 300+ files, all imports point here |
| **Entry Proxy** | `d:\dev\app\main.py` | ~30 lines, imports canonical |
| **Legacy System** | `d:\dev\backend\` | 0 imports from canonical |
| **Active Models** | 180+ files | In `services/api/app/models/` |
| **Active Routers** | 200+ files | In `services/api/app/routers/` |
| **Active Services** | 140+ files | In `services/api/app/services/` |
| **Module Aliasing** | `sys.modules['app'] = services.api.app` | Line 15 of `/dev/app/main.py` |
| **Database** | SQLAlchemy ORM | In `services/api/app/core/db.py` |
| **Legacy DB** | psycopg2 raw SQL | In `backend/db.py` (unused) |
| **Task Runner** | `uvicorn app.main:app` | Runs `/dev/app/main.py` |

