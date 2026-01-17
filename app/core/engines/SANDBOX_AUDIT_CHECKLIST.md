# SANDBOX Enforcement Audit Checklist

## Rule
**SANDBOX blocks real-world effects, not real data.**

Real-world effects:
- `outreach` (SMS, email, call)
- `dispo` / disposition send
- `contract` send/sign
- money movement
- broker execution
- any webhook / external notify
- any irreversible commit to external system

Safe in SANDBOX:
- data ingest
- scoring & computation
- recommendations
- logging & simulation
- internal tasks

## Enforcement Pattern

Every endpoint that touches a real-world effect **must** start with:

```python
from app.core.engines.require import require
from app.core.engines.actions import OUTREACH  # or DISPOSITION_SEND, etc.

@router.post("/send")
def send():
    require("wholesaling", OUTREACH)
    # ... proceed with send logic
```

## Audit Checklist (5-minute test)

1. **Set state**: `wholesaling` = `SANDBOX`
2. **Test read-only endpoint** (scoring, list, get): Should work ✓
3. **Test side-effect endpoint** (send, outreach, export): Must return 409 EngineBlocked ✓
4. **Set state**: `wholesaling` = `ACTIVE`
5. **Re-test side-effect endpoint**: Should proceed (if runbook clear) ✓

If any side-effect succeeds in SANDBOX → bug in that endpoint.

## Known Guarded Endpoints

- `POST /api/outcomes` — records evidence (no external effect)
- `POST /api/intake` — stores raw data (no external effect)
- `POST /api/intake/admin/promote` — marks CLEAN (no external effect)
- `POST /api/engines/transition` — transitions state (guarded by Heimdall policy)

## Endpoints Requiring Audit

Search your codebase for these patterns and ensure **each** calls `require()`:

```
POST /api/dispo/send        → require("wholesaling", DISPOSITION_SEND)
POST /api/outreach/*        → require("wholesaling", OUTREACH)
POST /api/contracts/*/send  → require("wholesaling", CONTRACT_SEND)
POST /api/*/export          → require(engine, action)
POST /api/*/webhook         → require(engine, action)
POST /api/*/publish         → require(engine, action)
POST /api/*/finalize        → require(engine, action)
POST /api/*/submit          → require(engine, action)
```

## Hard Truth

SANDBOX is only as strong as your worst unguarded endpoint.

One forgotten `require()` = one leak.

So the audit is not optional—it's the foundation.
