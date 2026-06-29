# RENDER DEPLOYMENT CONFIGURATION

**Commit:** 62dfa67  
**Status:** ✅ Ready for Render deployment

## The Fix

Migrations are now **separated** from web service startup:
- **Pre-Deploy Phase:** Migrations run via `python scripts/render_migrate.py`
- **Web Service Phase:** Uvicorn starts immediately via `python start.py`

This prevents the "no open ports detected" timeout that was killing deployments.

---

## Render Configuration

### Option A: Using Pre-Deploy Command (RECOMMENDED)

If your Render plan supports **Pre-Deploy Command** (Web Service feature):

**Settings to configure:**

1. **Pre-Deploy Command:**
   ```
   python scripts/render_migrate.py
   ```

2. **Start Command:**
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Port:** `10000` (set this in Render dashboard if available)

4. **Build Command:** (no change needed, keep existing)

**Result:**
- Render runs migrations in pre-deploy phase (has unlimited time)
- Then starts web service (opens port within 5 seconds)
- Render detects port and considers deploy healthy
- API becomes available

**Steps:**
1. Go to Render Dashboard → Valhalla API service
2. Navigate to Settings
3. Find "Pre-Deploy Command" field
4. Enter: `python scripts/render_migrate.py`
5. Find "Start Command" field
6. Replace with: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Click Save
8. Manual Deploy → Clear build cache & deploy

---

### Option B: Using Dockerfile Command (ALTERNATIVE)

If Pre-Deploy Command is not available in your Render plan:

**In services/api/Dockerfile, update the CMD:**

```dockerfile
# OLD (from previous version):
CMD ["python", "start.py"]

# NEW:
# This assumes DATABASE_URL is set and migrations have run
# For Render, use Pre-Deploy Command to run migrations separately
CMD ["python", "start.py"]
```

**Then in Render:**
- Set Start Command: (leave blank or use default)
- Ensure Dockerfile CMD is: `python start.py`

**Note:** In this case, you must manually run migrations before deploying, or use a separate one-time command:

```bash
# SSH into Render container (if available)
python scripts/render_migrate.py

# OR create a Job in Render to run migrations
# Set Job Command: python scripts/render_migrate.py
```

---

### Option C: Mixed Approach

Use a wrapper script that checks if migrations have already run:

1. Create `scripts/render_start_web_only.py` (already provided as `start.py`)
2. Use Pre-Deploy: `python scripts/render_migrate.py` 
3. Use Start Command: `python start.py`

This is currently the recommended setup.

---

## Expected Render Logs (GOOD)

When deployment succeeds:

```
Pre-deploy command started: python scripts/render_migrate.py

================================================================================
RENDER PRE-DEPLOY MIGRATION RUNNER
================================================================================
Workspace root: /app
Alembic config: /app/alembic.ini
Alembic folder exists: True
DATABASE_URL: postgresql://***
Running from: /app

🔍 Checking current migration state...
  Current head count: 1

🚀 Running migrations: python -m alembic -c <config> upgrade head

...migration output...

================================================================================
✅ MIGRATIONS COMPLETED SUCCESSFULLY (elapsed: 120.5s)
================================================================================

Pre-deploy command completed successfully

Starting service...

================================================================================
VALHALLA API - WEB SERVICE STARTUP
================================================================================

Note: Database migrations must be run separately via pre-deploy command:
  python scripts/render_migrate.py

🚀 Starting Uvicorn:
   Host: 0.0.0.0
   Port: 10000
   App: main:app

================================================================================

INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)

Your service is live
```

---

## Expected Render Logs (FAILURE - WHAT TO AVOID)

❌ These errors mean something is wrong:

```
❌ No open ports detected - Pre-deploy phase never finishes (migrations stuck)
❌ Multiple head revisions - Alembic graph still has issues (shouldn't happen)
❌ Can't locate revision - Orphaned ID in production (stub migration may be needed)
❌ Migration timeout - Took > 1800s (check database performance)
```

---

## Testing Before Render

Before deploying to Render, confirm locally:

```bash
# 1. Verify graph
python scripts/audit_alembic_graph.py
# Expected: ✅ AUDIT PASSED

# 2. Verify table audits  
python scripts/audit_migration_tables.py
# Expected: ✅ AUDIT PASSED

# 3. Run migration command
python scripts/render_migrate.py
# Expected: ✅ MIGRATIONS COMPLETED SUCCESSFULLY

# 4. Verify single head
python -m alembic -c .\alembic.ini heads
# Expected: exactly one head (20260506_001)
```

---

## Database Configuration

**Confirm in Render dashboard:**

1. Environment Variables:
   - `DATABASE_URL`: should point to `valhalla_db_v2` on Railway PostgreSQL
   - Check it's set correctly (but masked in logs)

2. PostgreSQL Connection:
   - Host: Railway PostgreSQL endpoint
   - Database: `valhalla_db_v2`
   - User: configured in Railway

---

## After Deployment

Once Render shows "Your service is live":

1. Check health endpoint:
   ```
   curl https://valhalla-api-ha6a.onrender.com/health
   ```

2. Test key endpoints:
   ```
   curl https://valhalla-api-ha6a.onrender.com/governance/go-live/state
   curl https://valhalla-api-ha6a.onrender.com/api/jarvis/system-status
   curl https://valhalla-api-ha6a.onrender.com/reports/summary
   ```

3. Check Render logs for any errors

---

## Troubleshooting

**If "no open ports detected" still appears:**
- Pre-deploy command took too long (migrations hung)
- Check Render logs for migration errors
- Check database connectivity
- Review [MIGRATION_WAR_ROOM_REPORT.md](docs/MIGRATION_WAR_ROOM_REPORT.md)

**If "Can't locate revision" appears:**
- Production database has orphaned ID
- New stub migration is being deployed
- Should auto-fix with this deployment

**If "Multiple head revisions" appears:**
- Alembic graph merge migration not applied
- Verify commit 7281ba6 is deployed
- Clear Render cache and redeploy

---

## Architecture

```
GitHub main branch (7281ba6 + 62dfa67)
         ↓
Render webhook trigger
         ↓
Docker build
         ↓
Pre-Deploy Phase (via Pre-Deploy Command)
  - python scripts/render_migrate.py
  - Connects to valhalla_db_v2
  - Runs: python -m alembic -c /app/alembic.ini upgrade head
  - Waits for migrations to complete (1800s timeout)
         ↓
Web Service Phase (via Start Command or Dockerfile CMD)
  - python start.py
  - Starts Uvicorn on 0.0.0.0:10000
  - Opens port immediately (Render detects it)
         ↓
Service Healthy
  - API available at valhalla-api-ha6a.onrender.com
  - Requests processed normally
```

---

**Ready to deploy! Follow Option A configuration above.**
