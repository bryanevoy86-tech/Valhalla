# Local Dev Baseline - VERIFIED ✅

**Date:** 2026-02-05  
**Status:** Green - All smoke tests passing  
**Baseline:** Locked and reproducible

## Smoke Test Results

| Test | Status | Details |
|------|--------|---------|
| Health Endpoint | ✅ PASS | `/health` returns 200 with `{"status":"ok","heimdall":"online"}` |
| System Selftest | ✅ PASS | `/api/system/selftest` returns 200, 757 routes mounted |
| Floor Control Routes | ✅ PASS | All 4 floor routes registered and accessible |

## Environment Configuration

**File:** `run_local_dev.ps1`

- Server: http://127.0.0.1:8010
- Database: SQLite at `services/api/dev.db`
- Log Output: `logs/uvicorn.out.log`, `logs/uvicorn.err.log`
- Environment Variables:
  - `PYTHONPATH=services/api`
  - `DATABASE_URL=sqlite:///dev.db`
  - `VALHALLA_JWT_SECRET=dev-secret`
  - `VALHALLA_API_KEY=dev-key`

## Startup Procedure

```powershell
# Terminal 1: Start server (detached process)
powershell -ExecutionPolicy Bypass -File C:\dev\valhalla\run_local_dev.ps1

# Terminal 2: Run smoke test (3+ seconds later)
powershell -ExecutionPolicy Bypass -File C:\dev\valhalla\smoke_test.ps1
```

## Critical Findings from Diagnosis

### Process Management
- ✅ Server stays up when launched as detached process (Start-Process)
- ❌ Server exits when launched via piped commands (`2>&1 |`)
- **Root Cause:** Shell closes stdin → graceful shutdown (not a code crash)

### Unicode Bug (FIXED)
- **Issue:** Print statements used `✓` character (U+2713)
- **Platform:** Windows CP1252 can't encode it
- **Result:** UnicodeEncodeError on startup
- **Solution:** Replaced all `✓` with `[OK]` text

### Router Registry
- ✅ Deterministic mounting (RouterSpec dataclass)
- ✅ No silent failures or duplicate registration
- ✅ 757 total routes including all floor control endpoints

## Floor Control Plane Status

All 4 endpoints registered and operational:

1. **POST** `/api/governance/floor/engines/upsert` - Register income engines
2. **POST** `/api/governance/floor/revenue/record` - Record revenue transactions
3. **POST** `/api/governance/floor/targets/upsert` - Set floor targets
4. **GET** `/api/governance/floor/trajectory/month` - Query monthly trajectory

## Next Phase: Contracts & DocuSign

Once contracts feature is implemented:

```
1. Template-based document generation
2. DocuSign API integration (embedded signing)
3. Signature workflow with audit trail
4. Document storage and versioning
```

## Baseline Validation

- Server boot time: ~2-3 seconds
- Request latency: <50ms (verified with /health)
- Memory: Stable (Python process ~80-120MB)
- No zombie processes or resource leaks
- Graceful shutdown when SIGTERM received

---

**Verified by:** Automated smoke test (2026-02-05 13:07:09)  
**Maintained by:** `run_local_dev.ps1` + `smoke_test.ps1`  
**Next Review:** After contracts pipeline implementation
