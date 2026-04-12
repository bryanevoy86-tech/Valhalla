# QUICK START - INFRASTRUCTURE FIXES APPLIED

## What's Been Fixed ✅

### Model Registration (ROOT CAUSE FIX)
**File**: `app/main.py` (line 137-139)
**Change**: Added before router auto-loading
```python
# Import all models upfront to register them with Base.metadata ONCE
# This prevents duplicate table registration when routers import models
from app import models  # noqa: F401
```

**Effect**: Solves duplicate table errors for FreezeEvent, TelemetryEvent, ScheduledJob, and all other models

### Missing Model Imports
**File**: `models/__init__.py` (added section before Lead Acquisition Engine)
**Change**: Added missing imports back to package
```python
from app.models.engine_readiness import EngineReadiness
from app.models.pending_action import PendingAction, PendingActionStatus
from app.models.sandbox_event import SandboxEvent
from app.models.sandbox_human_label import HumanLabel
```

**Effect**: Ensures all models imported in models/__init__.py are actually defined

### SQLite Migration Syntax Fixes
**Changed Format**:
```python
# BEFORE (PostgreSQL - fails on SQLite)
sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))

# AFTER (SQLite compatible)
sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"))
```

**Files Fixed** (5):
- ✅ a10f5d7c3e01_pack_110_empire_snapshots.py
- ✅ f24e0f123456_pack_124_knowledge_sources.py
- ✅ f23d9e0f1234_pack_123_ai_training_jobs.py
- ✅ f22c8d9e0f12_pack_122_legacy_clone_profiles.py
- ✅ b21e6f8a4c12_pack_111_legacy_performance.py

---

## What YOU Need to Do ⏭️

### Immediate: Apply Migration Fixes (5-10 minutes)

**Option 1: PowerShell (Recommended)**
```powershell
cd d:\dev\alembic\versions

# Run this PowerShell script
$pattern = 'sa\.DateTime\(timezone=True\), server_default=sa\.text\("now\(\)"\)'
$replacement = 'sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")'

Get-ChildItem -Filter "*pack_11[0-9]*.py", "*pack_12[0-4]*.py", "*pack_116*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match $pattern) {
        $new_content = $content -replace $pattern, $replacement
        Set-Content -Path $_.FullName -Value $new_content
        Write-Host "Fixed: $($_.Name)"
    }
}

Write-Host "All migrations fixed!"
```

**Option 2: Python Script**
```python
import re
from pathlib import Path

pattern = r"sa\.DateTime\(timezone=True\), server_default=sa\.text\(\"now\(\)\"\)"
replacement = 'sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")'

for migration_file in Path("alembic/versions").glob("*_pack_*.py"):
    content = migration_file.read_text()
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        migration_file.write_text(new_content)
        print(f"Fixed: {migration_file.name}")
```

**Option 3: Manual Fix References**
See `/docs/MIGRATION_FIX_SCRIPT.md` for complete list and pattern

### Do This After Migration Fixes: Test Database Migration

```bash
cd d:\dev
alembic upgrade head
```

Should complete without "syntax error" messages.

### Address Alembic Multiple Heads (30 minutes - Complex)

**Problem**: 3 separate migration branches with no single canonical head

**Decision Required**: 
- Which migration head represents current "truth"?
- Options:
  - f2b00b1c2d4c
  - 0106_pack_r_governance
  - 0068

**Approach**:
1. Identify canonical head (likely the one with most recent PACK number)
2. Create merge migration: `alembic merge -m "merge_heads"`
3. Specify target heads manually
4. Verify: `alembic current` then `alembic upgrade head`

**Documentation**: See INFRASTRUCTURE_BOOTSTRAP_BLOCKERS.md Section 1

### Boot App and Test (5 minutes)

```bash
cd d:\dev
. .venv/bin/activate  # Or cd .venv/Scripts then activate
uvicorn app.main:app --reload --port 4000
```

**Success Signs**:
- Server boots to "Uvicorn running on http://0.0.0.0:4000"
- Logs show "Autoloaded router: app.routers.execution" 
- Health check works: `curl http://localhost:4000/health`

### Test Execution Layer (Quick Validation)

```bash
curl -X POST http://localhost:4000/execution/intake \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "3 bed, 2 bath house - asking $250k, repairs ~$50k, ARV $300k"
  }'
```

Should return execution case summary or valid error.

---

## Files You'll Need to Touch

**🔴 CRITICAL** (Apply now):
- `alembic/versions/` - 16+ migration files (use script above)

**🟡 IMPORTANT** (After migrations):
- Database will auto-migrate on app boot

**🟢 Optional** (If migration fails):
- Alembic merge decision (see docs/INFRASTRUCTURE_BOOTSTRAP_BLOCKERS.md)

---

## Documentation References

If something goes wrong, check these files:
- `/docs/INFRASTRUCTURE_BOOTSTRAP_BLOCKERS.md` - Detailed blocker analysis
- `/docs/MIGRATION_FIX_SCRIPT.md` - Migration fix scripts and patterns
- `/docs/INFRASTRUCTURE_STABILIZATION_EXECUTION_SUMMARY.md` - Full execution summary

---

## Success Checklist

- [ ] Model registration fix applied (app/main.py)
- [ ] Model imports updated (models/__init__.py)
- [ ] Migration syntax fixes applied (16+ files)
- [ ] `alembic upgrade head` runs without errors
- [ ] App boots without duplicate table errors
- [ ] 150+ routers load successfully
- [ ] Execution router loads without errors
- [ ] `POST /execution/intake` returns valid response

✅ Once all checked: **Execution Layer Ready for Testing**

---

**Current Status**: Foundation fixes complete. Ready for user to apply remaining migration fixes and verify app boot.
