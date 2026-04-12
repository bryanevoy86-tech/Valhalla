# 🔍 VALHALLA INFRASTRUCTURE - BOOTSTRAP BLOCKERS AUDIT

**Date**: April 12, 2026  
**Phase**: 1 (Bootstrap Blocker Identification)  
**Purpose**: Identify exact infrastructureissues blocking clean app startup

---

## EXECUTIVE SUMMARY

Identified **5 critical blockers** preventing Valhalla app from booting:

| # | Blocker | Root Cause | Severity | Blocks | File(s) |
|---|---------|-----------|----------|--------|---------|
| 1 | Alembic Multiple Migration Heads | Migration history has 3 independent branches | 🔴 CRITICAL | `alembic upgrade head` | alembic/versions/ |
| 2 | SQLite Syntax Error in empire_snapshots | `now()` function + DateTime(timezone=True) not SQLite-compatible | 🔴 CRITICAL | Migration execution | a10f5d7c3e01_pack_110_empire_snapshots.py |
| 3 | Duplicate Model Table Registration | **app/models package never imported upfront** - routers import models independently, causing re-registration | 🔴 CRITICAL | Router auto-load | app/main.py |
| 4 | Pydantic Type Annotation Error | Unknown model has conflicting field annotation | 🟠 HIGH | App initialization | app/models/ (unknown) |
| 5 | Multiple Telemetry/Freeze Tables | Same root cause as #3: models imported by multiple routers | 🔴 CRITICAL | Router load | routers/ (15+ files) |

**Network Effect:**
- Blocker #3 root cause explains symptoms in #3, #5, and affects #4
- Blocker #1 blocks deployment of all other fixes
- Blocker #2 blocks database initialization


---

## BLOCKER 1: ALEMBIC MULTIPLE MIGRATION HEADS

### Description
Alembic has multiple migration branches with no clear canonical head, preventing unified database migration.

### Current State
```
alembic branches:
├─ 0077 (branchpoint)
│  ├─ ci1_add_decision_recommendations
│  └─ 0078
├─ f2af0b1c2d4b (branchpoint)
│  ├─ f2b00b1c2d4c (head) ← HEAD 1
│  └─ 0106_pack_r_governance (head) ← HEAD 2  
└─ fdc9b660a48f (branchpoint)
   ├─ 102_trust_status_table
   └─ 0068
```

### Error When Attempting Migration
```bash
$ alembic upgrade head
ERROR: Multiple head revisions are present for given argument 'head'
ERROR: please specify a specific target revision, '<branchname>@head' 
        to narrow to a specific head, or 'heads' for all heads
```

### Root Cause
- Multiple independent migration paths from different branches
- No merge point bringing branches back together
- Unknown which head is "current production" state

### Severity
🔴 **CRITICAL** - Blocks all database operations

### Blocks
- `alembic upgrade head` (Phase 2)
- `alembic downgrade` (Phase 2)
- New migrations cannot be created without specifying parent (Phase 2)

### Files Involved
- `alembic/versions/` (all migration files)
- `alembic.ini` (Alembic configuration)

### Minimum Safe Fix
1. Determine which head represents current "truth"
2. Merge alternative head as child to canonical head
3. Verify single linear upgrade path

---

## BLOCKER 2: SQLITE SYNTAX ERROR IN EMPIRE_SNAPSHOTS MIGRATION

### Description
The `empire_snapshots` migration (a10f5d7c3e01) fails with SQLite syntax error when attempting to execute.

### Exact Error
```
sqlite3.OperationalError: near "(": syntax error
```

### Failing SQL
```sql
CREATE TABLE empire_snapshots (
    ...columns...
    "brRRR_count" INTEGER DEFAULT 0,  ← SQLite chokes on this syntax
    ...
)
```

### Root Cause
SQLite doesn't accept certain DDL patterns that PostgreSQL/MySQL would accept. The issue appears to be either:
- Quoted field names in certain contexts
- `now()` function (SQLite doesn't have it)
- `sa.DateTime(timezone=True)` with `server_default=sa.text("now()")`

### Specific Problem Line
```python
# File: alembic/versions/a10f5d7c3e01_pack_110_empire_snapshots.py, line 37
sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
```

SQLite doesn't have a `now()` function - it uses `CURRENT_TIMESTAMP` or similar.

### Severity  
🔴 **CRITICAL** - Prevents database schema creation

### Blocks
- `alembic upgrade heads` (when this revision is encountered)
- Database initialization
- Router loading (models depend on DB session)

### Files Involved
**SCOPE: 20+ migration files** affected - not just 1!

Batch grep found instances in (at minimum):
- `a10f5d7c3e01_pack_110_empire_snapshots.py` ✅ **FIXED**
- `f24e0f123456_pack_124_knowledge_sources.py` (2 instances)
- `f23d9e0f1234_pack_123_ai_training_jobs.py` (1 instance)
- `f22c8d9e0f12_pack_122_legacy_clone_profiles.py` (2 instances)
- `b21e6f8a4c12_pack_111_legacy_performance.py` (1 instance)
- `f21b7c8d9e01_pack_121_whole_life_policies.py` (2 instances)
- `f20a6b7c8d90_pack_120_bahamas_vault.py` (2 instances)
- `f19e5f6a7b89_pack_119_shield_profiles.py` (2 instances)
- `f18d4e5f6a78_pack_118_tax_risk_profiles.py` (2 instances)
- `f17c3d4e5f67_pack_117_legal_profiles.py` (2 instances)
- `c32f7a9b5d23_pack_112_brrrr_zones.py` (2 instances)
- `f16b2d3e4f56_pack_116_tenants_leases_rent_payments.py` (3 instances)
- **Plus potentially more** (20 matches in grep = multiple files)

### Minimum Safe Fix
Create batch replacement script to fix all migration files:
- **Pattern to fix:** `sa.DateTime(timezone=True), server_default=sa.text("now()")`
- **Replace with:** `sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")`
- **Columns affected:** created_at, updated_at, last_updated
- **Reason:** SQLite doesn't support PostgreSQL syntax for DateTime with timezone or now() function

---

## BLOCKER 3: DUPLICATE MODEL TABLE REGISTRATION (ROOT CAUSE ANALYSIS)

### Description
When routers auto-load, SQLAlchemy complains that tables are already defined. This affects multiple models: ScheduledJob, TelemetryEvent, FreezeEvent, etc.

### Exact Error Examples
```
sqlalchemy.exc.InvalidRequestError: Table 'scheduled_jobs' is already defined 
for this MetaDatabase instance
sqlalchemy.exc.InvalidRequestError: Table 'telemetry_events' is already defined 
for this MetaDatabase instance
sqlalchemy.exc.InvalidRequestError: Table 'freeze_events' is already defined 
for this MetaDatabase instance
```

### ROOT CAUSE (Critical Finding)
**app.models package is never imported upfront.** This causes cascading registration conflicts:

1. **What should happen (design intent):**
   - `app/main.py` imports `from app import models` FIRST
   - This triggers `models/__init__.py` which imports all models once
   - All models register with Base.metadata upfront
   - Router auto-loading finds models already registered

2. **What actually happens (current reality):**
   - `app/main.py` DOES NOT import `from app import models`
   - Routers are auto-loaded via `_autoload_router_modules()`
   - Each router imports models directly (not through models package):
     - `from app.models.freeze_events import FreezeEvent`
     - `from app.models.scheduled import ScheduledJob`
     - `from app.models.telemetry_event import TelemetryEvent`
   - Models are registered with metadata as each router is loaded
   - If same model imported by multiple routers → second registration attempt → ERROR

### Evidence
Grep search found direct model imports in routers:
- `closing_playbook.py`: `from app.models.freeze_events import FreezeEvent`
- `deal_workflow_status.py`: `from app.models.freeze_events import FreezeEvent`
- `flow_prepare_closing.py`: `from app.models.freeze_events import FreezeEvent`
- `triggers.py`: `from app.models.triggers import TriggerEvent`
- `contracts_pipeline.py`: `from app.models.contracts import ContractEvent`
- `notification_bridge.py`: `from app.models.event_log import EventLog`
- `regression.py`: `from app.models.kpi_event import KPIEvent`
- `notify.py`: `from app.models.sandbox_event import SandboxEvent`
- `execution.py`: `from app.models.execution_event import ExecutionEvent` ← (NEW execution layer)

Result: `app/models/__init__.py` is checked - it exists but is NEVER IMPORTED.

### Example Conflict Path
When app boots:
1. Load `closing_playbook` router
   - Import: `from app.models.freeze_events import FreezeEvent`
   - Action: `FreezeEvent.__init_subclass__()` → Register `freeze_events` table
   
2. Load `deal_workflow_status` router
   - Import: `from app.models.freeze_events import FreezeEvent`
   - Action: Try to register `freeze_events` table AGAIN
   - Result: ❌ ERROR "Table 'freeze_events' is already defined"

### Affected Models
- FreezeEvent (freeze_events table) - imported by 3+ routers
- ScheduledJob (scheduled_jobs table) - imported by scheduler routers
- TelemetryEvent (telemetry_events table) - imported by telemetry routers
- And potentially others

### Files Involved
- `services/api/app/main.py` (MISSING: `from app import models` import)
- `services/api/app/models/__init__.py` (EXISTS but never imported)
- All routers that import models directly (15+ routers)

### Severity
🔴 **CRITICAL** - Root cause of multiple blocker #5 errors

### Blocks
- Router auto-load during app initialization
- App startup cascade failure

### Minimum Safe Fix
Add single line to `app/main.py` BEFORE router auto-loading:
```python
# Import models package to register all models upfront (prevents duplicate registration)
from app import models  # noqa: F401
```

This ensures all models are registered with Base.metadata ONCE before any router imports.

---

## BLOCKER 4: PYDANTIC TYPE ANNOTATION ERROR

### Description
Some model contains an unresolvable pydantic field definition causing model class construction to fail.

### Exact Error
```
pydantic.errors.PydanticUserError: Error when building FieldInfo from annotated attribute. 
Make sure you don't have any field name clashing with a type annotation
```

### Error Context
```
File "D:\dev\services\api\app\main.py", line 219, in __new__
  set_model_fields(cls, bases, config_wrapper, types_namespace)
```

### Root Cause
A Pydantic model class likely has:
- A field name that conflicts with a type annotation
- A field without proper annotation
- An `__init__` parameter clashing with model field

### Affected Model
**Unknown** - Error is generic and doesn't identify the offending model

### Severity
🟠 **HIGH** - Prevents router/model loading during app init

### Blocks
- Unknown - depends on which model is affected
- Likely blocks one or more routers from loading

### Minimum Safe Fix
1. Run app and capture full error traceback
2. Identify exact model class
3. Fix field annotation or remove conflicting definition

---

## BLOCKER 5: DUPLICATE TELEMETRY_EVENTS & FREEZE_EVENTS TABLE REGISTRATION

### Description
Similar to ScheduledJob - table registration conflicts for `telemetry_events` and `freeze_events`.

### Exact Error
```
sqlalchemy.exc.InvalidRequestError: Table 'telemetry_events' is already defined 
for this MetaData instance
sqlalchemy.exc.InvalidRequestError: Table 'freeze_events' is already defined 
for this MetaData instance
```

### Root Cause
Same pattern as ScheduledJob:
- Models imported in multiple places
- Table registration attempted multiple times
- SQLAlchemy metadata conflict

### Files Involved
- `services/api/app/models/telemetry_event.py`
- `services/api/app/routers/telemetry_event.py`
- `services/api/app/models/freeze_events.py` (if it exists)
- `services/api/app/routers/underwriting_engine.py` (throws freeze_events error)

### Severity
🔴 **CRITICAL** - Prevents router auto-loading

### Blocks
- `telemetry_event` router loading
- `underwriting_engine` router loading
- App startup

### Minimum Safe Fix
Resolve duplicate model registrations (same approach as ScheduledJob)

---

## SUMMARY TABLE

| Blocker | Type | Severity | Fix Time | Dependencies |
|---------|------|----------|----------|--------------|
| Alembic Multiple Heads | Infra | 🔴 CRITICAL | 30min | Blocks all others |
| SQLite Syntax Error | Migration | 🔴 CRITICAL | 15min | Depends on #1 |
| ScheduledJob Duplicate | Model | 🔴 CRITICAL | 20min | Blocks #4 & app |
| Pydantic Annotation | Model | 🟠 HIGH | 20min | Blocks routers |
| Telemetry/Freeze Duplicates | Model | 🔴 CRITICAL | 20min | Blocks specific routers |

---

## SUMMARY TABLE BY PRIORITY

| Priority | Blocker | Type | Fix Time | Dependencies | Impact |
|----------|---------|------|----------|--------------|--------|
| 1️⃣ CRITICAL | Alembic Multiple Heads | Infra | 30min | None | Blocks EVERYTHING (DB schema) |
| 2️⃣ CRITICAL | SQLite Syntax Error | Migration | 15min | Blocks #1 | Blocks DB initialization after #1 |
| 3️⃣ CRITICAL | Model Registration (Root Cause) | Config | 5min | Blocks #4 | Fixes #3, #5, enables #4 diagnosis |
| 4️⃣ HIGH | Pydantic Annotation | Model | 20min | After #3 | Unknown impact (depends on model) |

**OBSOLETE (Merged into #3):**
- Blocker #5 (Telemetry/Freeze duplicates) - Same root cause as #3

---

## RECOMMENDED FIX ORDER

1. **First (NOW - 5 min)**: Fix Model Registration Root Cause
   - Add: `from app import models` to `app/main.py` before router auto-loading
   - This single line fix solves duplicates for FreezeEvent, TelemetryEvent, ScheduledJob, etc.
   - Unblocks app initialization so we can see Pydantic error

2. **Second (5-10 min)**: Diagnose Pydantic Error
   - Boot app with fix #1 applied
   - Capture full error traceback
   - Identify exact model with conflicting annotation

3. **Third (15 min)**: Fix SQLite Syntax Error  
   - Open: `alembic/versions/a10f5d7c3e01_pack_110_empire_snapshots.py`
   - Replace `sa.text("now()")` with SQLite-compatible alternative
   - Test: `alembic upgrade head` runs without errors

4. **Fourth (30 min)**: Fix Alembic Multiple Heads
   - Identify canonical migration head
   - Create merge migration to consolidate branches
   - Verify single linear upgrade path

---

## EXECUTION LAYER IMPACT

Once these 5 blockers are fixed:

✅ Alembic will run cleanly: `alembic upgrade head`  
✅ App will boot without router load failures  
✅ All existing routers will load  
✅ **Execution router will load automatically**  
✅ Execution layer endpoints will be testable

---

## NEXT PHASE

Once all blockers are identified in detail, proceed to:
- PHASE 2: Fix Alembic integrity
- PHASE 3: Fix model registration conflicts
- PHASE 4: Fix Pydantic blockers
- PHASE 5: Boot verification
