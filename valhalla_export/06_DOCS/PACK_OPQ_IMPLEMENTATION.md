## PACK O — Reality Anchors: System Invariants & Self-Check

**Theme:** Detect missing files, red flags, and system integrity gaps to prevent silent failures.

### Purpose

Reality anchors provide a self-check endpoint that validates the Valhalla system's invariants:
- **Required Files:** `cone_state.json`, `audit_log.json` (must exist for governance durability)
- **Optional Files:** `go_progress.json`, `go_session.json`, `weekly_audits.json`, `leads.json`, etc.
- **Red Flags:** Warnings about missing critical data (e.g., no leads intake, no weekly audits recorded)

### Endpoints

#### `GET /core/anchors/check`

**Description:** Check system invariants and flag gaps.

**Response:**
```json
{
  "ok": true,
  "present": ["cone_state.json", "audit_log.json", "weekly_audits.json", "leads.json"],
  "missing_required": [],
  "missing_optional": ["go_progress.json", "go_session.json"],
  "red_flags": ["No weekly audits yet (cadence not established)."]
}
```

**Field Meanings:**
- `ok` (bool): `true` if all required files exist
- `present` (list): Files found in data/ directory
- `missing_required` (list): Required files not found (system at risk)
- `missing_optional` (list): Optional files not found (operational gaps)
- `red_flags` (list): Human-readable warnings about system state

### Implementation

**File:** `backend/app/core_gov/anchors/service.py`

```python
REQUIRED_FILES = [
    "cone_state.json",      # Cone band tracking (required for governance)
    "audit_log.json",       # Event log (required for accountability)
]

OPTIONAL_FILES = [
    "go_progress.json",     # GO session progress tracking
    "go_session.json",      # Current GO session snapshot
    "weekly_audits.json",   # Weekly audit trail
    "leads.json",           # Intake leads
    "alerts.json",          # Alert queue
    "thresholds.json",      # Business rule thresholds
    "capital_usage.json",   # Capital tracking
]
```

**Logic:**
1. Check each file in `data/` directory
2. Separate into present / missing_required / missing_optional
3. Collect red flags:
   - "Missing required governance files (system may not be durable.)" if any required file missing
   - "No weekly audits yet (cadence not established.)" if weekly_audits.json missing
   - "No leads logged yet (no intake flow exists.)" if leads.json missing
4. Return aggregated response

### Integration

**Modified:** `backend/app/core_gov/core_router.py`
- Import: `from .anchors.router import router as anchors_router`
- Include: `core.include_router(anchors_router)`
- Result: Endpoint accessible at `/core/anchors/check`

### Use Case

**For Internal Dashboard:**
```python
async def check_system_health():
    resp = httpx.get("http://localhost:4000/core/anchors/check")
    if not resp.json()["ok"]:
        # Show red flag warnings
        warnings = resp.json()["red_flags"]
        return {"status": "DEGRADED", "warnings": warnings}
    return {"status": "HEALTHY"}
```

**For Operations:**
If `red_flags` is non-empty, ops should investigate and resolve before running GO Mode, since GO depends on reliable governance data.

---

## PACK P — Onboarding: Unified Operational Truth

**Theme:** Single endpoint returns everything needed on app open: "What do I see? What do I do?"

### Purpose

Onboarding provides a unified JSON response that combines:
1. **Lite Dashboard:** System overview (active cone, recent audits, capital usage)
2. **GO Summary:** Current GO session state and next step guidance
3. **Anchors Check:** System health warnings and file inventory
4. **Canon Snapshot:** Authoritative system configuration

This is the "operating truth" endpoint: one call gives you the full picture.

### Endpoint

#### `GET /core/onboarding`

**Description:** Get unified operational payload for app initialization.

**Response:**
```json
{
  "lite": {
    "active_cone": "AA",
    "current_band": "READY_FOR_DEAL",
    "recent_audits": [
      {
        "cone": "AA",
        "timestamp": "2026-01-01T10:00:00Z",
        "health": "OK"
      }
    ]
  },
  "go": {
    "session_id": "go_20260101_100000",
    "status": "IN_PROGRESS",
    "current_step": 3,
    "next_step": "Review capital limits before proceeding"
  },
  "anchors": {
    "ok": true,
    "present": ["cone_state.json", "audit_log.json"],
    "missing_required": [],
    "missing_optional": ["go_progress.json"],
    "red_flags": []
  },
  "canon": {
    "bands": [...],
    "engines": [...],
    "capital_limit_usd": 100000,
    "audit_cadence_hours": 24
  },
  "message": "Operate by Cone. Follow Go Next Step. If anchors show red flags, resolve first."
}
```

### Implementation

**File:** `backend/app/core_gov/onboarding.py`

```python
def onboarding_payload() -> dict:
    return {
        "lite": lite_dashboard(),
        "go": go_summary(),
        "anchors": anchors_check(),
        "canon": canon_snapshot(),
        "message": "Operate by Cone. Follow Go Next Step. If anchors show red flags, resolve first.",
    }
```

**Service Composition:**
- `lite_dashboard()` from health/lite.py
- `go_summary()` from go/summary_service.py
- `anchors_check()` from anchors/service.py
- `canon_snapshot()` from canon/service.py

### Integration

**Modified:** `backend/app/core_gov/core_router.py`
- Import: `from .onboarding import onboarding_payload`
- Endpoint: `@core.get("/onboarding")`
- Result: Accessible at `/core/onboarding`

### Use Case

**For WeWeb Dashboard Initialization:**
```javascript
// On app open, fetch once
const payload = await fetch("/api/core/onboarding").then(r => r.json());

// Populate all sections from single request
dashboard.cone.set(payload.lite.active_cone);
dashboard.nextStep.set(payload.go.next_step);
dashboard.warnings.set(payload.anchors.red_flags);
dashboard.config.set(payload.canon);
```

**For Automated Monitoring:**
```python
def check_system_ready():
    resp = httpx.get("http://localhost:4000/core/onboarding")
    data = resp.json()
    if data["anchors"]["red_flags"]:
        alert(f"System warnings: {data['anchors']['red_flags']}")
    if data["go"]["status"] == "FAILED":
        alert(f"GO session failed: {data['go']['last_error']}")
```

---

## PACK Q — Public vs Internal Route Grouping

**Theme:** Expose safe read-only endpoints under `/public/*` for external dashboards while keeping internal operations under `/core/*`.

### Purpose

PACK Q separates concerns:
- **`/core/*`** (Internal): Full governance API for internal app (accounting, capital, audits)
- **`/public/*`** (External): Read-only mirror routes for external dashboards, monitoring tools, and partner integrations

This is **non-breaking and additive**: no existing routes change.

### Public Endpoints

#### `GET /public/healthz`
Health check for external monitoring.
```json
{ "ok": true }
```

#### `GET /public/lite/dashboard`
Mirror of `/core/health/lite/dashboard`.
```json
{
  "active_cone": "AA",
  "current_band": "READY_FOR_DEAL",
  "recent_audits": [...]
}
```

#### `GET /public/go/summary`
Mirror of `/core/go/summary`.
```json
{
  "session_id": "go_20260101_100000",
  "status": "IN_PROGRESS",
  "current_step": 3,
  "next_step": "Review capital limits"
}
```

#### `GET /public/onboarding`
Mirror of `/core/onboarding` (full operational truth).
```json
{
  "lite": {...},
  "go": {...},
  "anchors": {...},
  "canon": {...},
  "message": "..."
}
```

### Implementation

**File:** `backend/app/public_router.py`

```python
from fastapi import APIRouter
from app.core_gov.health.lite import lite_dashboard

public = APIRouter(prefix="/public", tags=["Public"])

@public.get("/healthz")
def healthz_public():
    return {"ok": True}

@public.get("/lite/dashboard")
def lite_public():
    return lite_dashboard()

@public.get("/go/summary")
def go_summary_public():
    from app.core_gov.go.summary_service import go_summary
    return go_summary()

@public.get("/onboarding")
def onboarding_public():
    from app.core_gov.onboarding import onboarding_payload
    return onboarding_payload()
```

**Key Design:**
- Local imports inside endpoints to avoid circular dependency issues
- Each public endpoint directly calls internal service (no extra layer)
- Endpoints are read-only (no POST/PUT/DELETE)
- Same response format as internal counterparts

### Integration

**Modified:** `backend/app/main.py`
```python
from .public_router import public as public_router
app.include_router(public_router)
```

**Result:** All public routes registered and available immediately.

### Use Case

**External Monitoring Dashboard:**
```javascript
// Fetch from public endpoint (no auth needed)
const data = await fetch("https://api.acme.com/public/onboarding").then(r => r.json());

// Display health status
if (data.anchors.ok) {
  show("✓ System Healthy");
} else {
  show("⚠ System Issues:", data.anchors.red_flags);
}
```

**Partner Integration:**
```python
# Public endpoint safe to share with partners (read-only, non-confidential)
partner_client = httpx.Client(auth=None)  # No auth needed
summary = partner_client.get("https://api.acme.com/public/go/summary").json()
log(f"Current step: {summary['next_step']}")
```

### Security Notes

**What's Safe on `/public`:**
- System health (cone band, GO status)
- Generic guidance (next step)
- Configuration parameters
- Audit summaries (high-level)

**What Stays on `/core`:**
- Capital transaction details
- Lead PII
- Decision reasoning
- Audit event details
- Configuration changes

**CORS Configuration:**
External dashboards should be added to `CORS_ALLOWED_ORIGINS` in settings to call `/public/*` endpoints:
```python
CORS_ALLOWED_ORIGINS = [
    "https://dashboard.partner.com",
    "https://*.weweb.app",
    "http://localhost:5173",
]
```

---

## Summary: PACK O, P, Q

| PACK | Purpose | Files | Endpoints | Integration |
|------|---------|-------|-----------|-------------|
| **O** | System self-checks (missing files, red flags) | 3 (anchors/) | GET /core/anchors/check | core_router |
| **P** | Unified operational payload (lite + go + anchors + canon) | 1 (onboarding.py) | GET /core/onboarding | core_router |
| **Q** | Public read-only routes for external dashboards | 1 (public_router.py) | 4 endpoints /public/* | main.py |

**Key Sequences:**

1. **App Open:** Call `/core/onboarding` → get full operating truth
2. **Operator Check:** Call `/core/anchors/check` → identify system gaps before running GO
3. **Partner Access:** Call `/public/*` endpoints → safe read-only access

**Governance Integration:**
- Anchors feed into health checks (GO won't run if critical files missing)
- Onboarding centralizes "what do I do now" guidance
- Public routes support external governance oversight and partner integration

**Files Created This Session (PACK O, P, Q):**
- `backend/app/core_gov/anchors/__init__.py`
- `backend/app/core_gov/anchors/service.py` (anchors_check)
- `backend/app/core_gov/anchors/router.py` (GET /check)
- `backend/app/core_gov/onboarding.py` (onboarding_payload)
- `backend/app/public_router.py` (public routes)

**Files Modified:**
- `backend/app/core_gov/core_router.py` (+4 lines)
- `backend/app/main.py` (+2 lines)

**Total New Code:** ~150 lines | **New Endpoints:** 5 (/core/anchors/check, /core/onboarding, /public/*, 4 endpoints)

