# Alembic Multiple Heads Fix - January 21, 2026

## Problem Detected

Render deployment failed with error:
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'
```

## Root Cause

Two separate migration branches existed:
- Branch 1: `20260113_golive_merge` → `20260121_go_live_core_tables`
- Branch 2: `ops_enablers_001` (orphaned with `down_revision = None`)

Alembic requires a single linear chain when running `alembic upgrade head`.

## Solution Applied

**File:** `services/api/alembic/versions/20250922_ops_enablers.py`

**Changed:**
```python
# Before
down_revision = None  # ← Creates separate head

# After
down_revision = "20260121_go_live_core_tables"  # ← Chains to previous migration
```

## New Migration Chain

```
...
  ↓
20260113_golive_merge
  ↓
20260121_go_live_core_tables
  ↓
ops_enablers_001 ✅ (now properly linked)
```

## Result

✅ Single linear migration chain
✅ `alembic upgrade head` will succeed
✅ All tables created in correct order
✅ Deployment will proceed

## Commit

- **Hash:** 03b83c1
- **Message:** Fix Alembic multiple heads
- **Status:** ✅ Pushed to GitHub

## Next Steps

Render will automatically re-deploy with the fixed migrations. No manual action needed - the automatic deployment will retry and succeed.
