# LIVE APP ENTRYPOINT PROOF

## Command to Start App
```bash
uvicorn app.main:app --reload --port 4000
```
(With venv activation: `. .venv/bin/activate && uvicorn app.main:app --reload --port 4000`)

## FastAPI App Object
- **File**: `services/api/app/main.py`
- **Module**: `app.main`
- **Variable**: `app = FastAPI(...)`
- **Created**: Line 93

## Router Registration Pattern
- **Type**: Static include_router() calls + RouterSpec registry
- **Registry**: Lines 165-199 (ROUTERS list with RouterSpec entries)
- **Registry Handler**: `include_router_safe()` from `app.core.router_registry`
- **Post-Registry Manual**: Additional include_router() calls scattered throughout file

## Critical Missing Routers (404 ROOT CAUSE)

### Audit Router
- **Status**: ❌ NOT IN ROUTERS REGISTRY
- **File**: `services/api/app/routers/audit.py` (EXISTS)
- **Router Variable**: `router` with prefix `/audit`
- **Expected Live Path**: `/api/audit/...` 
- **Actual Registration**: NONE - router never included

### Heimdall Router
- **Status**: ⚠️ IN ROUTERS BUT PREFIX WRONG
- **File**: `services/api/app/routers/heimdall.py` (EXISTS)
- **Router Variable**: `router` with prefix `/heimdall`
- **ROUTERS Entry** (line 199): 
  ```python
  RouterSpec("heimdall", "app.routers.heimdall", prefix="/api", required=False)
  ```
- **Issue**: `required=False` means silently skipped on import error; no /api prefix applied by registry
- **Expected Live Path**: `/api/heimdall/deals/{id}/analyze`
- **Actual Prefix**: Checking...

### Dashboard Router
- **Status**: ⚠️ FRAGMENTED - Multiple dashboards, operational_dashboard not early
- **File**: `services/api/app/routers/operational_dashboard.py` (EXISTS)
- **Router Variable**: `router` with prefix `/dashboard`
- **ROUTERS Entry** (line 198):
  ```python
  RouterSpec("operational_dashboard", "app.routers.operational_dashboard", prefix="/api", required=False)
  ```
- **Issue**: Listed but prefix should be properly applied
- **Expected Live Path**: `/api/dashboard/pipeline`

## Why Routes Return 404

1. **Audit** - Never registered at all (missing from ROUTERS + no manual include_router call)
2. **Heimdall** - Registered with optional=False, so import failures silently swallowed
3. **Dashboard** - Multiple incomplete registrations, fragmented across file

## Fix Required
1. Add audit to ROUTERS with required=True
2. Verify heimdall registration and logging
3. Consolidate dashboard registration early in the chain
4. Add explicit startup logging for all three
