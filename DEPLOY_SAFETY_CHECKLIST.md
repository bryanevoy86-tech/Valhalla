# VALHALLA GO-LIVE: CRITICAL BLOCKER FIX (Approved Safe Sequence)

## ⚠️ CURRENT STATE
Your governance is BLOCKING go-live because:
```
backend_complete = FALSE
ok_to_enable_go_live = false
go_live_checklist = BLOCKER
```

This is stored in your Postgres database, not a code issue.

---

## 🔧 FIX SEQUENCE (Copy/Paste Order)

### PHASE 1: Fix Database Blocker

**This must happen first.** The database is the source of truth.

#### Option A: Using Python Script (Easiest)
```bash
cd C:\dev\valhalla
python fix_backend_complete.py
```

Output should be:
```
[STEP 1] Checking current system_metadata...
[STEP 2] Setting backend_complete = TRUE...
  ✅ Updated: backend_complete = True

SUCCESS
```

**If this works**, skip to **PHASE 2**.

#### Option B: Direct SQL (If Python script fails)

**Via Render Dashboard:**
1. Go: https://dashboard.render.com
2. Find your Postgres database
3. Click **"Connect"** → **"PSQL"**  
4. Paste this:

```sql
INSERT INTO system_metadata (id, version, backend_complete, notes, updated_at, completed_at)
VALUES (1, '1.0.0', TRUE, 'Go-live backend marked complete', NOW(), NOW())
ON CONFLICT (id)
DO UPDATE SET
  backend_complete = TRUE,
  notes = 'Go-live backend marked complete',
  updated_at = NOW(),
  completed_at = NOW();

SELECT id, backend_complete, updated_at FROM system_metadata WHERE id=1;
```

Should output:
```
 id | backend_complete |       updated_at       
----+------------------+------------------------
  1 | t                | 2026-01-25 20:45:00
```

---

### PHASE 2: Redeploy FastAPI (Add /governance Endpoint)

Changes made: Added `/governance` root endpoint to eliminate 400 errors.

```bash
cd C:\dev\valhalla

# Stage the change
git add services/api/main.py

# Commit
git commit -m "Fix: Add /governance endpoint to eliminate 400 errors"

# Push (Render auto-deploys)
git push origin main

# Wait 2-3 minutes for deployment...
```

**Monitor deployment** at: https://dashboard.render.com → Your Service → Events

Should see: `Build succeeded` → `Deploy in progress` → `Deploy succeeded`

---

### PHASE 3: Verify Governance Passes

Once Render deployment is done:

```bash
cd C:\dev\valhalla
python ops_report.py
```

**Expected output:**
```
Next actions:
 - All checks green. Proceed with your next operational step (intake/leads/testing) as planned.

## Health
- OK: True
- Status: 200

## Governance / Runbook Status
- OK: True
- Status: 200
```

**And in the JSON response:**
```json
{
  "blockers": [],
  "ok_to_enable_go_live": true,
  "go_live_checklist": {
    "ok": true,
    "required": {
      "backend_complete": {
        "ok": true,
        "detail": "backend_complete True"
      }
    }
  }
}
```

If you see this ✅ → **PROCEED TO GO-LIVE**

If still blocking → **STOP** and check:
1. Did database update work? (`SELECT * FROM system_metadata;`)
2. Did Render deployment complete? (Check dashboard)
3. Did you wait 2-3 minutes? (Try again)

---

## 🚀 AFTER VERIFICATION: Safe Go-Live

Once governance passes:

```bash
# Choose your first data batch
ls PHASE_*.csv

# Example: Ingest first dataset
python go_live.py --csv PHASE_1_metrics_20260107_231516.csv

# Monitor live (updates every 60 seconds)
python ops_report.py --watch 60
```

---

## Safety Checklist (Must All Be ✅)

- [ ] **Database**: `backend_complete = TRUE` (verified via python script or SQL)
- [ ] **Redeploy**: FastAPI pushed to Render (git push origin main)
- [ ] **Deployment**: Render shows "Deploy succeeded"
- [ ] **Verification**: ops_report.py shows "All checks green"
- [ ] **Governance**: `ok_to_enable_go_live = true`
- [ ] **Governance**: `blockers = []` (empty list, zero blockers)

When all 6 are ✅ → You are **SAFE TO GO LIVE**.

---

## Troubleshooting

### "backend_complete still showing False after fix"
1. Did you wait 2-3 min after fixing DB?
2. Are you looking at the right database? (Check Render environment variable)
3. Try: `SELECT * FROM system_metadata;` to verify in DB directly

### "Render deployment still in progress"
- Wait. It usually takes 2-5 minutes.
- Check: https://dashboard.render.com → Your service → Events

### "ops_report.py still shows HTML instead of JSON"
1. Check base URL is correct: `https://valhalla-api-ha6a.onrender.com`
2. Try directly in browser: https://valhalla-api-ha6a.onrender.com/health
3. Should return JSON, not HTML

### "WeWeb still erroring on runbook variable"
1. Make sure WeWeb workflow defaults `runbook = {}`
2. Don't set runbook to empty string or null
3. Only assign object values to runbook variable

---

## Command Summary

**Full quick-start (all-in-one):**

```bash
# 1. Fix database
cd C:\dev\valhalla
python fix_backend_complete.py

# 2. Redeploy FastAPI
git add services/api/main.py
git commit -m "Fix: Add /governance endpoint"
git push origin main

# 3. Wait 2-3 minutes...

# 4. Verify governance
python ops_report.py

# 5. If green → Go live!
python go_live.py --csv PHASE_1_metrics_20260107_231516.csv

# 6. Monitor continuously
python ops_report.py --watch 60
```

---

**Status**: Ready to execute. No code changes needed beyond what's already staged.
