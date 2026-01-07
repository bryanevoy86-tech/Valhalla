# ⚡ QUICK START: SANDBOX ACTIVATION

**TL;DR - Get Sandbox Running in 1 Command**

```bash
python SANDBOX_ACTIVATION.py
```

---

## 📋 What This Does

✅ Verifies all 30 blocks active  
✅ Enables sandbox with isolated DB  
✅ Activates dry-run protection  
✅ Starts worker process  
✅ Verifies scheduler heartbeat  
✅ Ingests 3 test leads  
✅ Initializes Ops Cockpit  
✅ Runs full end-to-end test  
✅ Generates activation report  
✅ Keeps system live for monitoring  

---

## 🎯 Step-by-Step

### 1. Navigate to Project
```bash
cd c:\dev\valhalla
```

### 2. Activate Python Environment (if needed)
```bash
.\.venv\Scripts\Activate.ps1
```

### 3. Run Activation
```bash
python SANDBOX_ACTIVATION.py
```

### 4. Monitor Output
- Console shows real-time status
- Logs saved to `sandbox_activation.log`
- Report saved to `sandbox_activation_report.json`

---

## ✅ All 30 Blocks

| Batch | Blocks | Status |
|-------|--------|--------|
| **Batch 1** | 1-10 | ✅ ACTIVE |
| **Batch 2** | 11-20 | ✅ ACTIVE |
| **Batch 3** | 21-30 | ✅ ACTIVE |
| **Total** | 30 | ✅ ALL VERIFIED |

---

## 🎯 Activation Steps

1. **Confirm all 30 blocks** → ✅ VERIFIED
2. **Enable sandbox service** → ✅ READY
3. **Turn on dry-run mode** → ✅ PROTECTED
4. **Start worker process** → ✅ RUNNING
5. **Verify scheduler** → ✅ HEARTBEAT ACTIVE
6. **Launch lead collection** → ✅ 3 TEST LEADS LOADED
7. **Monitor Ops Cockpit** → ✅ LIVE
8. **Run sandbox test** → ✅ EXECUTING

---

## 📊 Key Files

| File | Purpose |
|------|---------|
| `SANDBOX_ACTIVATION.py` | Main activation script |
| `sandbox_activation.log` | Detailed activation logs |
| `sandbox_activation_report.json` | Structured status report |
| `FINAL_SANDBOX_ACTIVATION_CHECKLIST.md` | Full checklist |

---

## 🔍 Quick Status Check

After activation runs, check:

```bash
# View activation log
type sandbox_activation.log

# View activation report (Windows)
type sandbox_activation_report.json

# Or (PowerShell)
Get-Content sandbox_activation_report.json | ConvertFrom-Json | Format-List
```

---

## 🟢 When It's Working

You'll see:
- ✅ ALL BLOCKS CONFIRMED ACTIVE
- ✅ Sandbox service enabled
- ✅ Dry-run mode active
- ✅ Worker process running
- ✅ Scheduler heartbeat verified
- ✅ 3 test leads ingested
- ✅ Ops Cockpit live
- ✅ Full test completed
- ✅ **SANDBOX READY FOR PRODUCTION**

---

## 🆘 Troubleshooting

**If script fails:**
1. Check Python version: `python --version` (need 3.8+)
2. Check imports: `python -c "from services.sandbox_and_stability import *"`
3. Check logs: `type sandbox_activation.log`

**If activation incomplete:**
1. Review the log file
2. Check specific block status
3. Verify database connection
4. Check worker process

---

## 📞 What Happens Next

### During Activation:
- All 30 blocks initialize
- Test leads flow through system
- A/B tests created
- Scripts promoted
- Packets generated
- Outcomes evaluated
- Scores calculated
- All logged as dry-run

### After Activation:
- System stays live
- Monitor Ops Cockpit
- Process real leads when ready
- Review audit trail
- Deploy to production

---

## ✨ Features

- **30 Blocks:** All activation blocks active
- **Sandbox:** Isolated environment
- **Dry-Run:** All actions protected
- **Tests:** 3 sample leads included
- **Monitoring:** Real-time Ops Cockpit
- **Logging:** Full audit trail
- **Reports:** JSON status report

---

**Ready? Run this:**

```bash
python SANDBOX_ACTIVATION.py
```

**That's it! System will be live in ~5 minutes.** 🚀

---

*Quick Reference Guide*  
*January 7, 2026*  
*All 30 Blocks Ready*
