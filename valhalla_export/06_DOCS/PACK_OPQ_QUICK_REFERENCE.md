## PACK O, P, Q — Quick Reference

### PACK O: Anchors Check
```bash
curl http://localhost:4000/core/anchors/check
```
**Returns:** File inventory + red flags
```json
{
  "ok": true,
  "present": ["cone_state.json", "audit_log.json"],
  "missing_required": [],
  "missing_optional": ["go_progress.json"],
  "red_flags": ["No leads logged yet (no intake flow exists)."]
}
```

### PACK P: Onboarding Payload
```bash
curl http://localhost:4000/core/onboarding
```
**Returns:** Everything needed on app open (lite + go + anchors + canon)
```json
{
  "lite": { "active_cone": "AA", ... },
  "go": { "session_id": "...", "status": "IN_PROGRESS", ... },
  "anchors": { "ok": true, ... },
  "canon": { "bands": [...], ... },
  "message": "Operate by Cone. Follow Go Next Step. If anchors show red flags, resolve first."
}
```

### PACK Q: Public Routes
```bash
# Health check
curl http://localhost:4000/public/healthz

# Lite dashboard (public read-only)
curl http://localhost:4000/public/lite/dashboard

# GO summary (public read-only)
curl http://localhost:4000/public/go/summary

# Full onboarding (public read-only)
curl http://localhost:4000/public/onboarding
```

### Files Created (5)
| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/core_gov/anchors/__init__.py` | Package docstring | 1 |
| `backend/app/core_gov/anchors/service.py` | File checks + red flags | ~55 |
| `backend/app/core_gov/anchors/router.py` | GET /anchors/check endpoint | 8 |
| `backend/app/core_gov/onboarding.py` | Unified payload function | ~35 |
| `backend/app/public_router.py` | Public route mirror | ~35 |

### Files Modified (2)
| File | Change | Purpose |
|------|--------|---------|
| `backend/app/core_gov/core_router.py` | +4 lines | Import anchors_router + onboarding_payload; include router; add endpoint |
| `backend/app/main.py` | +2 lines | Import public_router; include in app |

### Integration Pattern (Verified)

**core_router.py:**
```python
from .anchors.router import router as anchors_router
from .onboarding import onboarding_payload

core.include_router(anchors_router)  # Line 113

@core.get("/onboarding")             # Line 115-117
def onboarding():
    return onboarding_payload()
```

**main.py:**
```python
from .public_router import public as public_router
app.include_router(public_router)
```

### Design Principles

1. **Anchors:** Self-check before running GO (fail fast if critical files missing)
2. **Onboarding:** Single source of truth on app open (no multiple calls needed)
3. **Public Routes:** Read-only mirrors for external integration (non-breaking addition)

### Service Dependencies

- Anchors: pathlib.Path (standard library)
- Onboarding: lite_dashboard + go_summary + anchors_check + canon_snapshot
- Public Routes: lite_dashboard + go_summary + onboarding_payload

All services handle import failures gracefully via try/except in onboarding.py.

### Testing

**PACK O (Anchors):**
```bash
# Check if data/ exists and what files are present
curl http://localhost:4000/core/anchors/check

# Should return ok=true if cone_state.json and audit_log.json exist
```

**PACK P (Onboarding):**
```bash
# Get full operating truth in one call
curl http://localhost:4000/core/onboarding | jq .

# Check all 4 components populated
```

**PACK Q (Public):**
```bash
# Verify public endpoints accessible (no auth)
curl http://localhost:4000/public/healthz
curl http://localhost:4000/public/onboarding | jq .
```

### Operational Use

**For Dashboard (WeWeb):**
1. On app open: GET /core/onboarding → populate all UI
2. Before GO: GET /core/anchors/check → warn if red flags
3. For external partner: GET /public/onboarding → read-only integration

**For Operations:**
1. Monitor /public/healthz → basic health check
2. Check /core/anchors/check → identify system gaps
3. Review /core/onboarding → full operational state

