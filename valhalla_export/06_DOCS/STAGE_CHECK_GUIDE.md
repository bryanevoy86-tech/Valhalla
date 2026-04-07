# System Stage Check — Quick Guide

## ▶️ HOW TO RUN IT

In PowerShell (from your repo root):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\stage_check.ps1
```

Or specify a custom URL:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\stage_check.ps1 -BaseUrl "http://localhost:8000"
```

---

## 🧠 HOW TO READ THE RESULT (THIS IS IMPORTANT)

### If you see:
```
STATUS: SYSTEM FUNCTIONAL AT CURRENT STAGE
```

**That means:**
- ✅ API is alive
- ✅ Governance works
- ✅ Runbook is authoritative
- ✅ Core wholesaling flow works
- ✅ Follow-ups auto-create
- ✅ Offer logic is bounded and safe

**➡️ You are exactly where you think you are.**

---

### If you see:
```
STATUS: SYSTEM FUNCTIONAL BUT BLOCKED FROM GO-LIVE
```

**That means:**
- ✅ Nothing is broken
- ✅ The system is intentionally refusing to advance
- ✅ Runbook blockers are doing their job

**➡️ This is success, not failure.**

Review the **RUNBOOK BLOCKERS** section above to see what policies or checks must be satisfied before production enable.

---

### If you see:
```
STATUS: GOVERNANCE NOT RESPONDING — DO NOT PROCEED
```

**That means:**
- ❌ The `/api/governance/runbook/status` endpoint is not reachable
- ❌ The API may be down or misconfigured
- ❌ Do not attempt go-live

**➡️ Check API logs and restart if needed.**

---

## 📋 What the Script Tests

1. **API Health** — `/docs` endpoint
2. **Governance Runbook** — Retrieves blocker/warning status
3. **Offer Policies** — Enables Toronto, ON test policy
4. **Lead-to-Deal Flow** — Creates test lead & deal
5. **Follow-Up Ladder** — Verifies speed-to-lead automation
6. **Offer Computation** — Validates offer logic bounds

---

## 🔑 Key Takeaway

The **Runbook Status** is the single source of truth. If it says you're good, you're good. If it has blockers, **that's intentional protection**, not a bug.

This is how Valhalla/Heimdall ensures you never go live in an unsafe state.
