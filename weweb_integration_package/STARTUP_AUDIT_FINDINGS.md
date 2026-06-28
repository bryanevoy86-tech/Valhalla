# Backend Startup Audit - Evidence & Truth

**Date**: May 19, 2026  
**Status**: 🚨 REAL PRODUCTION BLOCKER CONFIRMED

## Summary
The backend **cannot start locally OR on Render** due to a broken import path mismatch.

---

## Evidence

### 1. Actual Directory Structure

| Path | Type | Status | Count |
|------|------|--------|-------|
| `d:\dev\app\heimdall\routes\` | Directory | ✅ EXISTS | 44 files |
| `d:\dev\services\api\app\heimdall\routes\` | Directory | ❌ MISSING | — |
| `d:\dev\services\api\app\heimdall\` | Directory | ✅ EXISTS (but empty of routes) | — |

**Verified route files in app/heimdall/routes/**:
- approval_execution.py
- bulk_property_enrichment.py
- buyer_demand.py
- buyer_import.py
- buyer_match.py
- buyer_outreach_queue.py
- buyer_sourcing.py
- ... (44 total)

### 2. Startup Commands Audit

**Local startup (start_backend.py)**:
```python
# Registers sys.modules['app'] = services.api.app
uvicorn.run("app.main:app", ...)
```

**Render deployment (render.yaml + entrypoint.sh)**:
```yaml
dockerCommand: python start.py
# entrypoint.sh does:
# cd /app/services/api && exec python start.py
```

**Problem**: `start.py` does NOT exist anywhere

**What exists**:
- ✅ `start_backend.py` (correct import setup)
- ❌ `start.py` (referenced but missing)

### 3. Import Failure Trace

**File**: `d:\dev\services\api\app\main.py` line 18

```python
from app.heimdall.routes.knowledge import router as heimdall_knowledge_router
```

**Error when run**:
```
ModuleNotFoundError: No module named 'app.heimdall.routes'
```

**Root cause**: 
- `main.py` imports from `app.heimdall.routes.*`
- With sys.modules aliasing, this resolves to `services.api.app.heimdall.routes.*`
- But actual files are at `app.heimdall.routes.*` (top-level, not nested in services/api)
- The import path is WRONG for where the files actually live

### 4. Current Endpoint Import Status

**In main.py**: 44+ imports like:
```python
from app.heimdall.routes.knowledge import router as heimdall_knowledge_router
from app.heimdall.routes.education import router as heimdall_education_router
# ... etc for all 44 route files
```

**All are BROKEN** - pointing to non-existent nested directory

### 5. Freeze Notice Context

**BACKEND_FREEZE_NOTICE.md** states:
- ✅ "Logs show stable startup" (May 6, 2026)
- ✅ "Smoke tests passing"
- ❌ But freeze was created BEFORE current code was broken

**Conclusion**: The freeze baseline was working, but current code has import regression.

---

## Classification

**Type**: **B) Wrong root / duplicate backend confusion + import path mismatch**

The repo has:
- `app/` (top-level) with all routers at `app/heimdall/routes/`
- `services/api/app/` (nested) with main.py trying to import from wrong path
- Mixed local/Render startup scripts with conflicting assumptions

---

## What's Actually Live?

**UNCERTAIN**: Cannot determine if Render is currently working without checking deployed logs.  
- If Render is working: it's running different code than this repo root
- If Render is broken: `start.py` missing means deployment fails

---

## Minimal Fix (No refactoring)

### Option 1: Create start.py wrapper (Recommended)
**File**: `d:\dev\start.py`  
**Purpose**: Render compatibility entry point  
**Size**: 3 lines  
**Risk**: None (pure wrapper)

```python
#!/usr/bin/env python
"""Render entrypoint - delegates to start_backend.py"""
import subprocess
import sys
result = subprocess.run([sys.executable, "start_backend.py"] + sys.argv[1:])
sys.exit(result.returncode)
```

### Option 2: Fix import paths (If needed)
If Option 1 doesn't work, change imports in `services/api/app/main.py`:
- FROM: `from app.heimdall.routes.knowledge import ...`
- TO: (depends on whether we move routes or fix path resolution)

---

## Next Steps

**DECISION NEEDED**:

1. **Is Render currently live and working?**  
   - If YES: Deployed backend uses different code; we need to know what command it actually runs
   - If NO: Fix is critical blocker before WeWeb can connect

2. **Should we fix or investigate?**
   - Quick fix: Create start.py wrapper → test local startup
   - Full audit: Check what Render actually deployed vs this repo

**RECOMMENDATION**: Create `start.py` wrapper (2 min fix) and test with:
```bash
cd d:\dev
python start.py
# Should start uvicorn on localhost:4000 without ModuleNotFoundError
```

If still fails: Import paths need fixing (separate analysis needed).

---

## Key Assumptions NOT to change

✅ Keep endpoint paths as-is  
✅ Keep auth mechanism  
✅ Keep CORS settings  
✅ Keep database models  
✅ Don't move route files  
✅ Don't delete old routes  
✅ Don't refactor module names  

