# GO-LIVE RUNBOOK + KPI HELPERS - IMPLEMENTATION COMPLETE ✅

**Status**: Ready for deployment
**Files Created**: 4 new files + 1 modified
**Integration**: Complete in main.py

---

## What Was Created

### 1. Runbook Service (Check-Based Production Gate)
**File**: `services/api/app/services/runbook.py`
- `build_runbook(db)` - Returns structured status with blockers/warnings/info
- `render_runbook_markdown(runbook)` - Returns human-readable markdown
- Checks:
  - ✅ Go-live checklist (backend_complete + required_packs)
  - ✅ Kill-switch disengaged
  - ✅ ENV sanity (ENV, DATABASE_URL, GO_LIVE_ENFORCE)
  - ✅ Risk policies present (GLOBAL + engines)
  - ✅ Regression policies present
  - ✅ Heimdall policies present

### 2. Runbook Router (2 Endpoints)
**File**: `services/api/app/routers/runbook.py`
- `GET /api/governance/runbook/status` → JSON structured checks
- `GET /api/governance/runbook/markdown` → Plain text markdown

### 3. KPI Service (Event Emission)
**File**: `services/api/app/services/kpi.py`
- `emit_kpi(db, domain, metric, success, value, actor, correlation_id, detail)` → int (event_id)
- Handles dict/string detail serialization
- One-liner for recording business metrics

### 4. KPI Helpers (Easy Patterns)
**File**: `services/api/app/core/kpi_helpers.py`
- `kpi_success(db, domain, metric, ...)` - Success event
- `kpi_fail(db, domain, metric, ...)` - Failure event
- `kpi_value(db, domain, metric, value, ...)` - Numeric metric
- `kpi_timed_step(db, domain, metric, ...)` - Auto success/fail context manager

### 5. main.py Integration
**Modified**: `services/api/app/main.py`
- Added: `from app.routers import runbook as governance_runbook`
- Added: `app.include_router(governance_runbook.router, prefix="/api")`

---

## Quick Start (Copy/Paste)

### 1. Check Go-Live Readiness
```bash
curl http://localhost:8000/api/governance/runbook/status
# Returns: {"ok_to_enable_go_live": true/false, "blockers": [...], ...}

curl http://localhost:8000/api/governance/runbook/markdown
# Returns: Human-readable checklist
```

### 2. Emit Success KPI
```python
from app.core.kpi_helpers import kpi_success

kpi_success(db, "WHOLESALE", "offer_sent", actor="broker", correlation_id="offer_123")
```

### 3. Emit Failure KPI
```python
from app.core.kpi_helpers import kpi_fail

kpi_fail(db, "WHOLESALE", "lead_rejected", 
         actor="heimdall", correlation_id="lead_456",
         detail={"reason": "low_motivation", "score": 0.32})
```

### 4. Emit Numeric KPI
```python
from app.core.kpi_helpers import kpi_value

kpi_value(db, "CAPITAL", "roi_event", value=2500.50, actor="settlement", correlation_id="deal_789")
```

### 5. Auto Success/Fail (Context Manager)
```python
from app.core.kpi_helpers import kpi_timed_step

with kpi_timed_step(db, "BUYER_MATCH", "algorithm_run", actor="matcher"):
    result = run_matching_algorithm()
    # Success KPI auto-recorded if succeeds
    # Fail KPI auto-recorded if exception
```

---

## Use Cases

### Pre-Go-Live Checklist
```bash
# Check all levers are ready
curl http://localhost:8000/api/governance/runbook/markdown

# Should show:
# ✅ go_live_checklist
# ✅ kill_switch_clear
# ✅ env_sanity
# ✅ risk_policies_present
# ✅ regression_policies_present
# ✅ heimdall_charter_present
```

### During Experiment (Record Metrics)
```python
# When offer sent
kpi_success(db, "WHOLESALE", "offer_sent", ...)

# When contract accepted
kpi_success(db, "WHOLESALE", "contract_accepted", ...)

# When profit recorded
kpi_value(db, "WHOLESALE", "profit", value=500.0, ...)

# When algorithm crashes
kpi_fail(db, "BUYER_MATCH", "match_failed", detail={"error": "..."})
```

### Friday Regression Evaluation
```bash
# Regression tripwire will see:
# - Recent 50 offer_sent events (current week)
# - Baseline 200 offer_sent events (previous period)
# - Calculate success rate drop
# - If > 20% drop: auto-throttle WHOLESALE policy

# All metrics from kpi_success/kpi_fail/kpi_value
```

---

## Integration Pattern

**Everywhere you execute a business action**:

```python
from app.core.kpi_helpers import kpi_success, kpi_fail, kpi_timed_step
from app.core.risk_guard_helpers import risk_reserve_or_raise, risk_settle

# 1. Reserve risk
try:
    risk_reserve_or_raise(db, "WHOLESALE", amount, ...)
    kpi_success(db, "WHOLESALE", "risk_reserved", ...)
except:
    kpi_fail(db, "WHOLESALE", "risk_denied", ...)
    return error

# 2. Get AI recommendation
with kpi_timed_step(db, "WHOLESALE", "recommendation", ...):
    rec = get_recommendation()

# 3. Execute action
with kpi_timed_step(db, "WHOLESALE", "action_executed", ...):
    result = execute_action(rec)

# 4. Settle risk
risk_settle(db, "WHOLESALE", reserved, loss, ...)
kpi_success(db, "WHOLESALE", "risk_settled", ...)

# 5. Record outcome
if success:
    kpi_success(db, "WHOLESALE", "outcome_success", detail={"profit": 500})
else:
    kpi_fail(db, "WHOLESALE", "outcome_failed", detail={"reason": "..."})
```

**Result**: Every action automatically emits to regression tripwire for continuous monitoring.

---

## Runbook Check Details

| Check | Status Meaning | Action |
|-------|----------------|--------|
| go_live_checklist | ❌ | Fix: Install missing pack or complete backend |
| go_live_checklist | ✅ | Proceed to kill-switch check |
| kill_switch_clear | ❌ | Fix: Release kill-switch via `/api/governance/go-live/kill-switch/release` |
| kill_switch_clear | ✅ | Proceed to env sanity |
| env_sanity | ❌ | Fix: Set ENV=production, DATABASE_URL, GO_LIVE_ENFORCE=1 |
| env_sanity | ✅ | Proceed to policy checks |
| risk_policies_present | ❌ | Fix: Run `alembic upgrade head` to seed policies |
| regression_policies_present | ❌ | Fix: Run `alembic upgrade head` to seed policies |
| heimdall_charter_present | ❌ | Fix: Run `alembic upgrade head` to seed policies |
| All ✅ | GREEN | `ok_to_enable_go_live=true` → Safe to enable production |

---

## KPI Parameters

### Common to All Functions
```python
db              # Session (required)
domain          # "WHOLESALE", "BUYER_MATCH", "CAPITAL" (required)
metric          # "offer_sent", "contract_accepted", "roi_event" (required)
actor           # Optional: "broker", "heimdall", "system", etc.
correlation_id  # Optional: trace ID to link related events
detail          # Optional: Dict or string with extra context
```

### Specific Functions
```python
# kpi_value only:
value           # Float: the numeric value to record

# kpi_timed_step:
# (context manager, same params as others)
```

---

## Database Note

**No migrations needed** — both runbook and KPI helpers use existing tables:
- go_live_state (for runbook checks)
- risk_policy, regression_policy, heimdall_policy (for runbook checks)
- kpi_event (for KPI helpers)

All tables created by earlier migrations (20260113_*).

---

## Files Summary

| File | Purpose | Status |
|------|---------|--------|
| services/api/app/services/runbook.py | Build runbook + render | ✅ Created |
| services/api/app/routers/runbook.py | 2 endpoints | ✅ Created |
| services/api/app/services/kpi.py | emit_kpi() | ✅ Created |
| services/api/app/core/kpi_helpers.py | Convenience functions | ✅ Created |
| services/api/app/main.py | Integration | ✅ Modified |

---

## Next Steps

1. **No migrations needed** (uses existing tables)
2. **Restart server** to pick up new routes/helpers
3. **Test runbook endpoint**: `curl http://localhost:8000/api/governance/runbook/status`
4. **Start emitting KPIs**: Import helpers in business logic
5. **Friday regression evaluation** will see all emitted KPIs

---

## Full Documentation

See [RUNBOOK_KPI_QUICK_START.md](RUNBOOK_KPI_QUICK_START.md) for:
- Detailed endpoint examples
- Real-world flow walkthroughs
- Combined Monday control plane review
- All function signatures

---

## Summary

✅ **Runbook**: Single gate to verify all 4 levers before go-live
✅ **KPI Helpers**: Zero-boilerplate patterns for emitting metrics
✅ **Integration**: Complete in main.py
✅ **Ready**: Deploy and start emitting KPIs from business logic

