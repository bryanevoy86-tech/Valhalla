# ROUTER DRIFT REPORT

## Summary
Three critical routers were not properly registered in the canonical FastAPI app:
1. **Heimdall** - Listed as optional, causing silent skip on errors
2. **Audit** - Completely missing from ROUTERS registry
3. **Dashboard** (operational_dashboard) - Listed but fragmented

## Heimdall Router

**File**: `services/api/app/routers/heimdall.py` ✅ EXISTS

**Router Definition**:
```python
router = APIRouter(prefix="/heimdall", tags=["heimdall"])
```

**Variable Name**: `router`

**Prefix/Tags**: Internal prefix `/heimdall`, tags `["heimdall"]`

**Status Pre-Fix**:
- ❌ In ROUTERS registry but marked `required=False`
- ❌ Silent skip on import errors (optional status)
- ❌ Not explicitly logged on success

**Endpoints**:
- POST `/heimdall/deals/{deal_id}/analyze`
- POST `/heimdall/deals/{deal_id}/advance-stage`

**Expected Live Surface**: `/api/heimdall/...` (with /api prefix applied by registry)

**Fix Applied**: Moved to required=True, explicit logging added

---

## Audit Router

**File**: `services/api/app/routers/audit.py` ✅ EXISTS

**Router Definition**:
```python
router = APIRouter(prefix="/audit", tags=["audit"])
```

**Variable Name**: `router`

**Prefix/Tags**: Internal prefix `/audit`, tags `["audit"]`

**Status Pre-Fix**:
- ❌ NOT in ROUTERS registry at all
- ❌ NOT included by any manual include_router() call
- ❌ Routes unreachable from HTTP

**Endpoints**:
- POST `/audit/` (write event)
- GET `/audit/` (list recent)
- GET `/audit/deals/{deal_id}` (deal audit trail)

**Expected Live Surface**: `/api/audit/deals/{deal_id}`

**Fix Applied**: Added to ROUTERS as required=True with `/api` prefix

---

## Dashboard Router (operational_dashboard)

**File**: `services/api/app/routers/operational_dashboard.py` ✅ EXISTS

**Router Definition**:
```python
router = APIRouter(prefix="/dashboard", tags=["dashboard"])
```

**Variable Name**: `router`

**Prefix/Tags**: Internal prefix `/dashboard`, tags `["dashboard"]`

**Status Pre-Fix**:
- ⚠️  In ROUTERS as `required=False` (optional)
- ⚠️  Also manually included at line 900+ (duplicate/scattered)
- ❌ Multiple dashboard routers registered elsewhere (portfolio, empire, personal, security)
- ❌ Not consolidated

**Endpoints**:
- GET `/dashboard/pipeline`
- GET `/dashboard/deals/{deal_id}/timeline`

**Expected Live Surface**: `/api/dashboard/pipeline`

**Fix Applied**: Moved to required=True, removed duplicate manual registration intent

---

## Consolidated fixes in app.main.py

### BEFORE
```python
ROUTERS = [
    # ... others ...
    RouterSpec("operational_dashboard", "app.routers.operational_dashboard", prefix="/api", required=False),
    RouterSpec("heimdall", "app.routers.heimdall", prefix="/api", required=False),
]
# audit: NOT LISTED
```

### AFTER
```python
ROUTERS = [
    # ... others ...
    
    # Heimdall: Deal analysis and stage management (REQUIRED for core operations)
    RouterSpec("heimdall", "app.routers.heimdall", prefix="/api", required=True),

    # Audit: Compliance and governance event log (REQUIRED for audit trail)
    RouterSpec("audit", "app.routers.audit", prefix="/api", required=True),

    # Dashboard: Operational pipeline visualization (REQUIRED for live visibility)
    RouterSpec("operational_dashboard", "app.routers.operational_dashboard", prefix="/api", required=True),
]
```

## Router Registry Logging

Updated `app.core.router_registry.py`:
- Added explicit print() statements for each router registration
- On success: `[app.main] Registered router: {name} ({module}:{attr}) prefix={prefix}`
- On failure: `[app.main] ⚠️  ROUTER_FAIL: ...`
- On critical error: `[app.main] ❌ CRITICAL: ...`

## Why the Failure Occurred

1. **Heimdall marked optional** - import errors silently swallowed; no indication of failure
2. **Audit completely missing** - developer oversight, no registration code created
3. **Dashboard fragmented** - multiple dashboard routers (portfolio, empire, etc.) clouded focus on operational_dashboard
4. **Silent failures** - optional routers don't raise exceptions, leaving routes unreachable with no error

## What's Now Live

After applying these fixes:
- `/api/heimdall/deals/{id}/analyze` ✅ registered
- `/api/heimdall/deals/{id}/advance-stage` ✅ registered
- `/api/audit/deals/{id}` ✅ registered
- `/api/dashboard/pipeline` ✅ registered

Router registration is explicit and will crash startup if any required router fails to import.
