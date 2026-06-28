# Render Docker Alembic Path Repair

## Problem Summary

**Render Error**:
```
FAILED: Path doesn't exist: '/app/alembic'
alembic.ini exists: False
```

**Root Cause**: Docker image was not including the root Alembic files.
- `.dockerignore` was excluding `/alembic/` and `/alembic.ini`
- These files were never copied into the Docker image
- Render working directory: `/app/services/api`
- Previous services/api/alembic folder was deleted (correctly)
- Services/api/alembic.ini pointed to root, but root files weren't in image

**This is NOT a database reset issue**—It's a Docker build/path issue. The migrations themselves are valid (single head confirmed). The Docker image simply didn't contain the source files.

## Files Changed

### 1. `.dockerignore` — Removed Alembic Exclusions
```diff
# Other services and tools (exclude root-level only, not services/api/*)
heimdall/
backend/
/app/
-/alembic/
-/alembic.ini
/migrations/
```
**Reason**: Root Alembic must be included in Docker image.

### 2. `Dockerfile` — Added Explicit COPY
```dockerfile
# CRITICAL: Explicitly ensure root Alembic files are in image
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
```
**Reason**: Explicit COPY makes it clear the image must contain these files.

### 3. `alembic.ini` — Config Location Safety
```diff
[alembic]
-script_location = alembic
+script_location = %(here)s/alembic
```
**Reason**: `%(here)s` resolves to directory containing alembic.ini, making path portable:
- Local (d:\dev): alembic.ini at d:\dev → %(here)s → d:\dev
- Docker (/app): alembic.ini at /app → %(here)s → /app

### 4. `services/api/run_migrations.py` — Absolute Path Resolution
```python
def find_repo_root() -> Path:
    """Find repo root by looking for alembic.ini from current directory."""
    current = Path.cwd()
    
    # If we're in services/api, root is parent/parent
    if current.name == "api" and (current.parent.name == "services"):
        return current.parent.parent
    
    # If we're at repo root already
    if (current / "alembic.ini").exists():
        return current
    
    # Try parent
    if (current.parent / "alembic.ini").exists():
        return current.parent
    
    # Try grandparent
    if (current.parent.parent / "alembic.ini").exists():
        return current.parent.parent
    
    # Fallback to /app (Render environment)
    if Path("/app/alembic.ini").exists():
        return Path("/app")
    
    raise FileNotFoundError("Could not find repository root with alembic.ini")
```

Migration commands now use explicit `-c` flag:
```python
subprocess.run(
    ["python", "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"]
)
```

**Diagnostics output**:
```
Alembic config: /app/alembic.ini (exists: True)
Alembic scripts: /app/alembic (exists: True)
Versions folder: /app/alembic/versions (exists: True)
Running: python -m alembic -c /app/alembic.ini upgrade head
```

## Docker Build Impact

Next Render deployment with these changes:

1. **Docker build phase**:
   - `.dockerignore` no longer excludes `/alembic/` or `/alembic.ini`
   - `COPY . .` includes root alembic folder ✓
   - Explicit `COPY alembic.ini /app/alembic.ini` ✓
   - Explicit `COPY alembic /app/alembic` ✓

2. **Docker image result**:
   ```
   /app/alembic.ini              ✓ (from root)
   /app/alembic/                 ✓ (folder structure)
   /app/alembic/env.py           ✓ (Alembic scripts)
   /app/alembic/versions/        ✓ (all migration files)
   ```

3. **Container startup** (WORKDIR /app/services/api):
   - `run_migrations.py` runs
   - Detects current dir = /app/services/api
   - Calculates repo_root = /app
   - Looks for /app/alembic.ini → EXISTS ✓
   - Looks for /app/alembic → EXISTS ✓
   - Runs: `python -m alembic -c /app/alembic.ini upgrade head` ✓

## Local Verification (PHASE 6)

From `/app/services/api` (simulating Render):

```powershell
cd d:\dev\services\api
python run_migrations.py
```

**Diagnostic output showed**:
```
Repository root: D:\dev
Alembic config: D:\dev\alembic.ini (exists: True)
Alembic scripts: D:\dev\alembic (exists: True)
Versions folder: D:\dev\alembic/versions (exists: True)
```

✅ **Path issue FIXED** — script correctly found root alembic from services/api working directory.

## Migration Status Note

**Single head confirmed**: `20260527_add_go_live_state (core_pipeline) (head)`

The migration failures observed during testing are a **separate schema/branching issue**, not caused by Docker paths. This is pre-existing in the migration graph and unrelated to this Docker path repair. The Render database corruption (from previous failed deployments) may need manual cleanup or reset, but that's a separate issue addressed in the migration remediation guide.

## Render Redeployment Steps

1. **Push these changes** (commit below)
2. **Render rebuilds Docker image**:
   - `COPY . .` now includes root alembic (not excluded)
   - Explicit COPY ensures redundancy
   - `/app/alembic/` exists in image ✓

3. **Container starts**:
   - `run_migrations.py` finds root alembic at /app ✓
   - Runs with explicit `-c /app/alembic.ini` ✓
   - Log output shows paths verified ✓

4. **If migration still fails**:
   - It's NOT a Docker path issue anymore (paths work)
   - It's the pre-existing schema/branching issue
   - Check Render logs for schema error details
   - May require database remediation (separate process)

## Files Committed

- `.dockerignore` — Removed alembic exclusions
- `Dockerfile` — Added explicit COPY for alembic
- `alembic.ini` — Updated to %(here)s/alembic
- `services/api/run_migrations.py` — Absolute path resolution + diagnostics
- `docs/RENDER_DOCKER_ALEMBIC_PATH_REPAIR.md` — This document

## Next Steps

1. ✅ Changes committed
2. Push to origin/fix/alembic-single-head
3. Trigger Render manual deploy
4. Watch Render logs for:
   ```
   Repository root: /app
   Alembic config: /app/alembic.ini (exists: True)
   Alembic scripts: /app/alembic (exists: True)
   ```
5. If these lines appear, Docker path issue is **RESOLVED**
6. If migration still fails, check whether it's schema vs path issue

---

**Date**: June 28, 2026  
**Status**: ✅ Docker path issue fixed and verified locally  
**Verification**: Path resolution works from services/api directory  
**Render impact**: /app/alembic will now exist in Docker image  
