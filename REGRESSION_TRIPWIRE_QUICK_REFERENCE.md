# REGRESSION TRIPWIRE - QUICK REFERENCE

## What It Does
Auto-detects performance degradation and throttles or kills engines to prevent scaling damage.

## How It Works

### 1. Record KPI Events (Continuous)
```bash
curl -X POST http://localhost:8000/api/governance/regression/kpi \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "success": true,
    "actor": "system"
  }'
```
→ KPIEvent stored with (domain, metric, created_at) index

### 2. Define Regression Policies (One-time Setup)
```bash
curl -X POST http://localhost:8000/api/governance/regression/policies/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "window_events": 50,
    "baseline_events": 200,
    "min_events_to_enforce": 50,
    "max_drop_fraction": 0.20,
    "action": "THROTTLE",
    "enabled": true,
    "changed_by": "bryan"
  }'
```
→ Enables tripwire for (WHOLESALE, contract_rate)

### 3. Evaluate Sliding Window (Friday Weekly or Manual Trigger)
```bash
curl -X POST http://localhost:8000/api/governance/regression/evaluate \
  -d "domain=WHOLESALE&metric=contract_rate&actor=bryan"
```
→ Compares recent 50 events vs baseline 200 events
→ If drop >= 20%, auto-THROTTLE: disables WHOLESALE risk policy
→ Next deal attempts will hit risk guard DENIED

### 4. Monday Review: Check Regression State
```bash
curl http://localhost:8000/api/governance/regression/state
```
Response:
```json
[
  {
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "triggered": true,
    "baseline": 0.95,
    "current": 0.75,
    "drop_fraction": 0.211,
    "last_triggered_at": "2026-01-13T14:32:00",
    "note": "TRIGGERED drop=0.211 action=THROTTLE"
  }
]
```

### 5. Human Action: Fix & Re-enable
```bash
# Retrain model, fix algorithm
# Then re-enable:
curl -X POST http://localhost:8000/api/governance/regression/policies/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "enabled": true,
    "changed_by": "bryan",
    "reason": "Retrained offer-accept model v2.1"
  }'
```
→ WHOLESALE engine now accepts deals again

---

## Auto-Actions

### THROTTLE
When policy action="THROTTLE" and tripwire triggers:
```python
# Auto-executed by regression_tripwire.evaluate()
risk_policy = _get_risk_policy(db, "WHOLESALE")
risk_policy.enabled = False  # ← Disables WHOLESALE engine
risk_policy.reason = "Regression tripwire: WHOLESALE.contract_rate drop=21%"
```
→ Next `risk_guard.reserve_exposure(db, "WHOLESALE", ...)` returns:
```
RiskCheckOut(ok=False, reason="policy_disabled")
```
→ Deal booking fails → No damage at scale

### KILL_SWITCH
When policy action="KILL_SWITCH" and tripwire triggers:
```python
# Auto-executed by regression_tripwire.evaluate()
go_live.set_kill_switch(db, True, reason="Regression: CAPITAL.roi_event drop=35%")
```
→ Global kill switch engaged → All PROD_EXEC blocked at middleware
→ System halts to protect balance sheet

---

## Seed Policies (All Disabled = Safest)

| Domain | Metric | Window | Baseline | Drop% | Action | Purpose |
|--------|--------|--------|----------|-------|--------|---------|
| WHOLESALE | contract_rate | 50 | 200 | 20% | THROTTLE | Stop bad offers if acceptance drops |
| WHOLESALE | offer_accept_rate | 50 | 200 | 15% | THROTTLE | Stop if offer-gen regression |
| BUYER_MATCH | match_success | 50 | 200 | 25% | THROTTLE | Stop bad buyer matches if accuracy drops |
| CAPITAL | roi_event | 50 | 200 | 30% | KILL_SWITCH | Halt system if capital ROI flips |

---

## Integration with Other Levers

### Tripwire → Risk Guard
```
regression_tripwire.evaluate()
  if triggered and action="THROTTLE":
    _get_risk_policy(db, domain).enabled = False
    
Next deal attempt:
  risk_guard.reserve_exposure(db, domain, ...)
    pol = _get_policy(db, domain)  ← Finds disabled policy
    if not pol.enabled:
      return RiskCheckOut(ok=False, reason="policy_disabled")
```

### Tripwire → Go-Live
```
regression_tripwire.evaluate()
  if triggered and action="KILL_SWITCH":
    go_live.set_kill_switch(db, True, ...)
    
Next PROD_EXEC request:
  ExecutionClassMiddleware
    state = go_live.read_state()
    if state.kill_switch_engaged:
      return 403 Forbidden
```

---

## Key Tables

**kpi_event** (business metrics)
```
id, domain, metric, success (bool), value (float), actor, correlation_id, detail, created_at
Index: (domain, metric, created_at) ← For fast recent/baseline queries
```

**regression_policy** (thresholds)
```
id, domain, metric, window_events (50), baseline_events (200), min_events_to_enforce (50),
max_drop_fraction (0.20), action (THROTTLE|KILL_SWITCH), enabled (bool),
changed_by, reason, updated_at
Unique: (domain, metric)
```

**regression_state** (tripwire status)
```
id, domain, metric, triggered (bool), baseline (float), current (float), drop_fraction (float),
last_checked_at, last_triggered_at, note
Unique: (domain, metric)
```

---

## Testing Flow

1. **Record KPIs** (simulate baseline)
   ```bash
   # Call POST /api/governance/regression/kpi in loop 200 times
   # with success=true (95% success rate) to establish baseline
   ```

2. **Enable Policy**
   ```bash
   curl -X POST .../policies/upsert \
     -d "domain=WHOLESALE&metric=contract_rate&enabled=true"
   ```

3. **Trigger Evaluation**
   ```bash
   curl -X POST .../evaluate \
     -d "domain=WHOLESALE&metric=contract_rate"
   ```
   → Should return: triggered=false (baseline is good)

4. **Inject Degradation**
   ```bash
   # Call POST /api/governance/regression/kpi 50 times
   # with success=false (20% success rate) to simulate regression
   ```

5. **Evaluate Again**
   ```bash
   curl -X POST .../evaluate \
     -d "domain=WHOLESALE&metric=contract_rate"
   ```
   → Should return: triggered=true, drop_fraction=0.789
   → Risk policy should be disabled

6. **Verify Risk Guard Blocked**
   ```bash
   curl -X POST /api/governance/risk/check-and-reserve \
     -d "engine=WHOLESALE&amount=10000"
   ```
   → Should return: ok=False, reason="policy_disabled"

7. **Fix & Re-enable**
   ```bash
   curl -X POST .../policies/upsert \
     -d "domain=WHOLESALE&metric=contract_rate&enabled=true"
   ```
   → Next risk reserve should succeed

---

## Common Scenarios

**Scenario 1: Offer-Accept Algorithm Drifts**
- Baseline: 95% acceptance rate
- Current: 60% acceptance rate (drop = 37%)
- Tripwire triggers → THROTTLE WHOLESALE
- User sees: risk_guard denials spike
- User action: Retrain model, merge fix, re-enable policy
- Result: Bad algorithm never scaled to production

**Scenario 2: Buyer-Match Accuracy Drops**
- Baseline: 85% match success
- Current: 70% match success (drop = 18% < 25% threshold)
- Tripwire does NOT trigger (threshold not met)
- System continues but monitors closely
- Friday review: Is trend worsening? If yes → lower threshold

**Scenario 3: Capital ROI Flips Negative**
- Baseline: +$500 avg profit per deal
- Current: -$300 avg loss per deal (massive regression)
- Tripwire triggers → KILL_SWITCH
- All PROD_EXEC blocked globally
- Human emergency response required to re-enable

---

## Monday Control Plane Integration

```
1. Check go_live state:
   curl /api/governance/go-live/state
   → If kill_switch_engaged: "Why? Check regression state."

2. Check risk denials:
   curl /api/governance/risk/ledger/today
   → Count reason="policy_disabled"
   → Which engine is throttled?

3. Check regression state:
   curl /api/governance/regression/state
   → triggered=true entries
   → What drifted and when?

4. Decide:
   - "System degraded, fix required" → Manual remediation
   - "Good week, baselines accurate" → Friday: promote thresholds
   - "Threshold too aggressive" → Loosen max_drop_fraction
```

---

## Metrics to Track Weekly

- **Tripwire triggers per week**: Should be 0 or 1 (means experiment caused issues)
- **Auto-throttle vs auto-kill ratio**: Should favor THROTTLE (graceful degradation)
- **MTTR (Mean Time To Remediate)**: How fast do engineers fix after tripwire fires?
- **False positive rate**: Legitimate performance variance vs real regression?

If MTTR > 4 hours → Lower thresholds to fail faster
If false positives > 10% → Raise max_drop_fraction

---

## File Locations

- Models: `services/api/app/models/{kpi_event,regression_policy,regression_state}.py`
- Service: `services/api/app/services/regression_tripwire.py`
- Router: `services/api/app/routers/regression.py`
- Migration: `services/api/alembic/versions/20260113_regression_tripwire.py`
- Integration: `services/api/app/main.py` (added governance_regression router)

