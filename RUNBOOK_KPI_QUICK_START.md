# GO-LIVE RUNBOOK + KPI HELPERS - QUICK START

## Part 1: Go-Live Runbook (Production Checklist)

**Purpose**: Single authoritative operational truth. Checks all 4 levers are ready before go-live.

### Endpoints

```bash
# JSON status (structured checks)
curl http://localhost:8000/api/governance/runbook/status

# Markdown version (human-readable)
curl http://localhost:8000/api/governance/runbook/markdown
```

### Example Response (JSON)

```json
{
  "generated_at": "2026-01-13T15:30:00Z",
  "blockers": [
    {
      "id": "go_live_checklist",
      "ok": false,
      "severity": "BLOCKER",
      "message": "Go-live checklist must pass before enabling production execution",
      "detail": {
        "ok": false,
        "backend_complete": true,
        "required_packs": {
          "A": "installed",
          "B": "installed",
          "C": "installed"
        }
      }
    }
  ],
  "warnings": [],
  "info": [
    {
      "id": "kill_switch_clear",
      "ok": true,
      "severity": "BLOCKER",
      "message": "Kill-switch must be disengaged for production execution",
      "detail": {
        "kill_switch_engaged": false,
        "go_live_enabled": false,
        "updated_at": "2026-01-13T15:20:00"
      }
    },
    {
      "id": "env_sanity",
      "ok": true,
      "severity": "BLOCKER",
      "message": "ENV and DATABASE_URL must be set correctly in production",
      "detail": {
        "ENV": "production",
        "GO_LIVE_ENFORCE": "1",
        "DATABASE_URL_set": true
      }
    }
  ],
  "ok_to_enable_go_live": false
}
```

### Example Response (Markdown)

```markdown
# Valhalla Go-Live Runbook

Generated: `2026-01-13T15:30:00.123456Z`

## Blockers

- ❌ **go_live_checklist** — Go-live checklist must pass before enabling production execution
- ✅ **kill_switch_clear** — Kill-switch must be disengaged for production execution

## Warnings

- ✅ None

## Info / Passing Checks

- ✅ **env_sanity** — ENV and DATABASE_URL must be set correctly in production
- ✅ **enforcement_expected_in_prod** — Go-live enforcement currently ON (recommended ON in production)
- ✅ **risk_policies_present** — Risk policies present
- ✅ **regression_policies_present** — Regression policies present
- ✅ **heimdall_charter_present** — Heimdall charter policies present
```

### What The Runbook Checks

| Check | Severity | Meaning |
|-------|----------|---------|
| go_live_checklist | BLOCKER | Backend complete + required packs installed |
| kill_switch_clear | BLOCKER | Kill-switch not engaged |
| env_sanity | BLOCKER | ENV + DATABASE_URL properly set |
| enforcement_expected_in_prod | INFO | GO_LIVE_ENFORCE enabled in production |
| risk_policies_present | BLOCKER | Risk policies exist (GLOBAL + others) |
| regression_policies_present | BLOCKER | Regression policies exist |
| heimdall_charter_present | BLOCKER | Heimdall policies exist |

### Usage Pattern

**Before enabling go-live in production**:
```bash
# Check JSON status
curl http://localhost:8000/api/governance/runbook/status | jq .ok_to_enable_go_live
# Should return: true

# Or read markdown
curl http://localhost:8000/api/governance/runbook/markdown
# Look for any blockers = ❌
```

**If blockers exist**:
1. Fix the issue (e.g., install missing pack, enable policies)
2. Re-check runbook status
3. Once all blockers cleared → safe to enable go-live

---

## Part 2: KPI Helpers (Easy KPI Emission)

**Purpose**: Simple patterns for emitting KPI events everywhere in your code without boilerplate.

### Basic Patterns

#### 1. Success KPI
```python
from app.core.kpi_helpers import kpi_success
from app.core.db import SessionLocal

db = SessionLocal()

# When offer successfully sent
kpi_success(
    db, 
    domain="WHOLESALE",
    metric="offer_sent",
    actor="offer_engine",
    correlation_id="offer_123"
)
```

#### 2. Failure KPI
```python
from app.core.kpi_helpers import kpi_fail

# When a lead is filtered out
kpi_fail(
    db,
    domain="WHOLESALE",
    metric="lead_rejected",
    actor="heimdall",
    correlation_id="lead_456",
    detail={"reason": "low_motivation", "score": 0.32}
)
```

#### 3. Numeric Value KPI
```python
from app.core.kpi_helpers import kpi_value

# Record ROI after deal executes
kpi_value(
    db,
    domain="CAPITAL",
    metric="roi_event",
    value=2500.50,
    actor="settlement_engine",
    correlation_id="deal_789"
)
```

#### 4. Auto Success/Fail (Context Manager)
```python
from app.core.kpi_helpers import kpi_timed_step

# Automatically records success if block completes, fail if exception
with kpi_timed_step(
    db,
    domain="BUYER_MATCH",
    metric="match_algorithm_run",
    actor="matcher",
    correlation_id="match_999",
    detail={"input_count": 100}
):
    # Your algorithm code here
    result = run_buyer_matching()
    # If no exception → success KPI recorded
    # If exception → fail KPI with error recorded

# Usage: if algorithm crashes, fail KPI recorded automatically
```

### Real-World Example: Wholesaling Flow

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.kpi_helpers import kpi_success, kpi_fail, kpi_timed_step
from app.core.risk_guard_helpers import risk_reserve_or_raise

router = APIRouter()

@router.post("/wholesale/send-offer")
def send_offer(offer_data: dict, db: Session = Depends(get_db)):
    corr_id = offer_data.get("correlation_id")
    
    # 1. Reserve risk capacity
    try:
        risk_reserve_or_raise(
            db, engine="WHOLESALE", amount=offer_data["amount"],
            actor="offer_sender", correlation_id=corr_id
        )
        kpi_success(db, "WHOLESALE", "risk_reserved", actor="system", correlation_id=corr_id)
    except RuntimeError as e:
        kpi_fail(db, "WHOLESALE", "risk_denied", actor="system", correlation_id=corr_id, 
                detail={"reason": str(e)})
        return {"ok": False, "reason": str(e)}
    
    # 2. Get AI recommendation with auto success/fail
    with kpi_timed_step(
        db, "WHOLESALE", "heimdall_recommendation",
        actor="heimdall", correlation_id=corr_id
    ):
        rec = get_heimdall_recommendation(offer_data)
        if not rec.prod_eligible:
            raise ValueError("Recommendation not production eligible")
    
    # 3. Send offer to buyer
    with kpi_timed_step(
        db, "WHOLESALE", "offer_sent",
        actor="broker", correlation_id=corr_id,
        detail={"offer_id": offer_data["id"]}
    ):
        buyer_response = send_to_buyer(rec)
    
    # 4. Record response
    if buyer_response.get("accepted"):
        kpi_success(
            db, "WHOLESALE", "contract_accepted",
            actor="buyer", correlation_id=corr_id,
            detail={"response_time_sec": buyer_response.get("response_seconds")}
        )
        
        # Settle risk
        risk_settle(db, "WHOLESALE", reserved_amount=offer_data["amount"],
                   realized_loss=0, actor="system", correlation_id=corr_id)
        kpi_success(db, "WHOLESALE", "risk_settled", actor="system", correlation_id=corr_id)
    else:
        kpi_fail(
            db, "WHOLESALE", "contract_declined",
            actor="buyer", correlation_id=corr_id
        )
    
    return {"ok": True, "response": buyer_response}
```

### KPI Helpers Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `kpi_success(db, domain, metric, ...)` | Record success event | None (commits to DB) |
| `kpi_fail(db, domain, metric, ...)` | Record failure event | None (commits to DB) |
| `kpi_value(db, domain, metric, value, ...)` | Record numeric metric | None (commits to DB) |
| `kpi_timed_step(db, domain, metric, ...)` | Context manager for auto success/fail | None (yields, commits) |

### All Parameters (Optional)

```python
# Common to all functions:
db              # SQLAlchemy session (required)
domain          # "WHOLESALE", "BUYER_MATCH", "CAPITAL", etc. (required)
metric          # "offer_sent", "contract_accepted", "roi_event", etc. (required)
actor           # Who performed the action ("offer_engine", "heimdall", "system", etc.)
correlation_id  # Trace ID to link related events
detail          # Dict or string with additional context

# Specific to kpi_value:
value           # Numeric value to record (float)

# Specific to kpi_timed_step:
# (same as others, but wraps code block)
```

### Integration Points

**In deal booking**:
```python
kpi_success(db, "WHOLESALE", "offer_sent", ...)
kpi_success(db, "WHOLESALE", "contract_accepted", ...)
```

**In lead filtering**:
```python
kpi_fail(db, "WHOLESALE", "lead_rejected", detail={"reason": "..."})
```

**In settlement**:
```python
kpi_value(db, "CAPITAL", "profit_event", value=profit_amount)
```

**In matching**:
```python
with kpi_timed_step(db, "BUYER_MATCH", "match_algorithm_run"):
    matches = algorithm.run()
    # Auto success if completes, auto fail if crashes
```

---

## Combined Example: Monday Control Plane Review

```bash
#!/bin/bash

echo "=== GO-LIVE RUNBOOK ==="
curl -s http://localhost:8000/api/governance/runbook/markdown

echo ""
echo "=== RISK LEDGER ==="
curl -s http://localhost:8000/api/governance/risk/ledger/today | jq .

echo ""
echo "=== REGRESSION TRIPWIRES ==="
curl -s http://localhost:8000/api/governance/regression/state | jq .

echo ""
echo "=== RECENT KPI EVENTS ==="
sqlite3 :memory: "SELECT domain, metric, success, COUNT(*) as count FROM kpi_event WHERE created_at >= datetime('now', '-1 day') GROUP BY domain, metric, success ORDER BY domain, metric"
```

---

## Summary

**Runbook**: Single endpoint to check all 4 levers before go-live
- `GET /api/governance/runbook/status` (JSON)
- `GET /api/governance/runbook/markdown` (Human-readable)

**KPI Helpers**: Easy patterns for emitting metrics everywhere
- `kpi_success()` - success event
- `kpi_fail()` - failure event
- `kpi_value()` - numeric metric
- `kpi_timed_step()` - auto success/fail context manager

**Result**: Zero boilerplate, maximum observability. Every action emits KPIs for regression tripwire to monitor.
