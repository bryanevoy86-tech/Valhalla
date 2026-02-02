# VALHALLA PHASE 1 — Enable Go-Live (Governance Gate)

**Status**: Ready for deployment
**Engines**: DORMANT (no execution)
**Outcome**: `go_live_enabled = true`, `kill_switch_engaged = false`

---

## ✅ What We've Done Locally

1. **Created Heimdall Secret Rotation Tool**
   - Location: [services/api/tools/heimdall_rotate_secrets.py](../../services/api/tools/heimdall_rotate_secrets.py)
   - Generates high-entropy secrets locally (never written to disk)
   - Copy/paste ready for Render environment

2. **Created Go-Live Enable Script**
   - Location: [valhalla/enable_go_live.py](../enable_go_live.py)
   - Fetches current state, verifies checklist, enables go_live
   - Ready to run after deployment

---

## 🚀 PHASE 1 Execution (Right Now)

### STEP 1: Push Code to Render

```bash
# From repo root
git add -A
git commit -m "PHASE 1: Enable governance go-live endpoints

- add routers/go_live.py (already in repo)
- ensure main.py includes router (already done, line 147)
- enable go_live_enabled = true via API"

git push origin main
```

**What Render Does**:
- Builds Docker image
- Runs migrations
- Deploys new code
- Endpoints go live

**Expected time**: ~3-5 minutes

---

### STEP 2: Verify Endpoints Are Live

```bash
# Check health first
curl -s https://valhalla-api-ha6a.onrender.com/health

# Should return 200 OK
```

---

### STEP 3: Check Current Go-Live State

```bash
curl -s https://valhalla-api-ha6a.onrender.com/api/governance/go-live/state | python -m json.tool
```

**Expected response**:
```json
{
  "go_live_enabled": false,
  "kill_switch_engaged": false,
  "updated_at": "2026-02-02T...",
  "changed_by": null,
  "reason": null
}
```

---

### STEP 4: Enable Go-Live (Locally)

```bash
cd valhalla
python enable_go_live.py --api https://valhalla-api-ha6a.onrender.com
```

**What it does**:
1. Checks current state
2. Verifies checklist is clear
3. Sets `go_live_enabled = true`
4. Sets `kill_switch_engaged = false`
5. Prints new state

**Output example**:
```
================================================================================
VALHALLA PHASE 1 — Enable Go-Live
================================================================================

[STEP 1] Checking current state...
Current state:
  go_live_enabled: false
  kill_switch_engaged: false

[STEP 2] Verifying checklist...
Checklist status: {"ok": true, "blockers": []}

[STEP 3] Enabling go_live.enabled = true...
✓ Go-live ENABLED
New state:
  go_live_enabled: true
  kill_switch_engaged: false
  updated_at: 2026-02-02T...
  changed_by: heimdall-phase-1
```

---

### STEP 5: Verify with Runbook Status

```bash
curl -s https://valhalla-api-ha6a.onrender.com/api/governance/runbook/status | python -m json.tool
```

**Expected**:
- `go_live.enabled: true` ← This changed
- `go_live.kill_switch: false` ← This is off
- All other checks passing

---

## 🔒 What Did NOT Happen (This is Safe)

❌ No engines promoted to SANDBOX
❌ No engines promoted to LIVE
❌ No automatic execution started
❌ No secrets rotated yet
❌ No money moves / real outreach

---

## ✓ What DID Happen (What You Verify)

✅ `go_live_enabled = true` → Engines CAN now advance (when you promote them)
✅ `kill_switch_engaged = false` → Master lock is OFF
✅ Engines remain DORMANT → No automatic behavior
✅ State is persistent → Render DB holds it
✅ Only you can promote engines next (PHASE 2)

---

## 📋 PHASE 1 Checklist

- [ ] Code pushed to Render (`git push`)
- [ ] Render deployment complete (check dashboard)
- [ ] Health endpoint responds (curl /health)
- [ ] Go-live endpoints exist (curl /api/governance/go-live/state)
- [ ] Current state shows `go_live_enabled: false`
- [ ] Run `enable_go_live.py` script
- [ ] New state shows `go_live_enabled: true`
- [ ] Runbook status shows correct flags
- [ ] Engines still DORMANT (verified manually)

---

## 🎯 Next: PHASE 2 (After This)

Once PHASE 1 is confirmed:

```bash
# Move ONE engine to SANDBOX
python valhalla/promote_engine.py --engine wholesaling --state sandbox

# Validate in SANDBOX (no real impact)
# Then promote to LIVE (one at a time)
```

---

## 🆘 Troubleshooting

**Q: Endpoints return 404?**
- A: Code not deployed yet. Check Render dashboard. Is deployment complete?

**Q: Checklist returns blockers?**
- A: Script will warn you. Review blockers, then `--force` flag if you understand them.

**Q: Can't run `enable_go_live.py` locally?**
- A: Needs `requests` library. Install: `pip install requests`

**Q: Want to DISABLE go_live again?**
- A: `curl -X POST https://valhalla-api-ha6a.onrender.com/api/governance/go-live/disable -H "Content-Type: application/json" -d '{"changed_by":"you","reason":"disabling for safety"}'`

---

## 📚 Related Files

- [services/api/app/routers/go_live.py](../../services/api/app/routers/go_live.py) — API endpoints
- [services/api/app/models/go_live_state.py](../../services/api/app/models/go_live_state.py) — Database model
- [services/api/app/services/go_live.py](../../services/api/app/services/go_live.py) — Business logic
- [services/api/tools/heimdall_rotate_secrets.py](../../services/api/tools/heimdall_rotate_secrets.py) — Secret rotation (PHASE 3)

---

**Ready to proceed? Do these steps in order, then report back: "go_live is enabled. Engines are still dormant."**
