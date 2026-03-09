# Regression Tripwire Implementation Complete ✓

The Regression Tripwire system—the **final control lever**—is now fully implemented. This auto-detection + auto-remediation engine prevents institutional self-destruction from performance drift.

## What Was Just Created

### 1. **Models** (3 files)
- [KPIEvent](app/models/kpi_event.py) → Records business metrics (domain/metric/success/value)
- [RegressionPolicy](app/models/regression_policy.py) → Defines per-(domain,metric) thresholds
- [RegressionState](app/models/regression_state.py) → Tracks tripwire status (triggered/baseline/current/drop%)

### 2. **Service** (1 file)
- [regression_tripwire.py](app/services/regression_tripwire.py)
  - `_rate_from_events()` → Computes success% or average value from KPI events
  - `evaluate()` → Sliding window comparison, auto-triggers THROTTLE or KILL_SWITCH actions
  - **Reuses existing enforcement levers**: `risk_guard._get_policy()` + `go_live.set_kill_switch()`

### 3. **Router** (1 file)
- [regression.py](app/routers/regression.py) → 5 REST endpoints:
  - `GET /api/governance/regression/policies` → List all regression policies
  - `POST /api/governance/regression/policies/upsert` → Create/update policy
  - `GET /api/governance/regression/state` → Show tripwire status
  - `POST /api/governance/regression/evaluate` → Trigger evaluation for one policy
  - `POST /api/governance/regression/kpi` → Record a KPI event

### 4. **Alembic Migration** (1 file)
- [20260113_regression_tripwire.py](alembic/versions/20260113_regression_tripwire.py)
  - Creates `kpi_event` table with (domain, metric, created_at) index
  - Creates `regression_policy` table with unique constraint on (domain, metric)
  - Creates `regression_state` table (singleton per policy)
  - Seeds 4 default policies (all disabled = safest):
    1. WHOLESALE / contract_rate → THROTTLE on 20% drop
    2. WHOLESALE / offer_accept_rate → THROTTLE on 15% drop
    3. BUYER_MATCH / match_success → THROTTLE on 25% drop
    4. CAPITAL / roi_event → KILL_SWITCH on 30% drop

### 5. **main.py Integration** (1 file updated)
- Added `from app.routers import regression as governance_regression`
- Added `app.include_router(governance_regression.router, prefix="/api")`

---

## Architecture: How The Tripwire Works

```
1. RECORD KPI
   POST /api/governance/regression/kpi
   { domain: "WHOLESALE", metric: "contract_rate", success: true }
   → KPIEvent stored with (domain, metric, created_at) index

2. POLICY DEFINES GATES
   regression_policy (WHOLESALE, contract_rate):
   • window_events=50        (recent 50 events)
   • baseline_events=200     (prior 200 events)
   • max_drop_fraction=0.20  (20% = trigger threshold)
   • action="THROTTLE"       (disable WHOLESALE risk policy)

3. EVALUATE SLIDING WINDOW
   POST /api/governance/regression/evaluate
   → Recent 50 contract_rate events (past N days)
   → Baseline 200 events (before that)
   → success_rate_current = 75%
   → success_rate_baseline = 95%
   → drop = (95% - 75%) / 95% = 21% > 20% threshold
   → TRIGGERED ✗

4. AUTO-ACTION: THROTTLE
   _get_risk_policy(db, "WHOLESALE").enabled = False
   → WHOLESALE engine cannot reserve exposure
   → All future WHOLESALE deals return: RiskCheckOut(ok=False, reason="policy_disabled")
   → Human sees /api/governance/risk/ledger/today: DENIED=[42, 19, 105]
   → Human reviews regression tripwire state
   → Human fixes: retrains offer-accept model, re-enables policy

5. OPTIONAL: KILL_SWITCH
   If action="KILL_SWITCH":
   → set_kill_switch(db, True, reason="Regression: CAPITAL.roi_event")
   → GO_LIVE_ENABLED=False globally
   → All PROD_EXEC blocked at middleware layer
   → System safe until manual override
```

---

## Weekly Cadence Integration

**Monday (10-min Control Plane Review):**
```
What broke? What denied? What drifted?

1. /api/governance/go-live/state
   → Check if kill_switch_engaged (if yes, tripwire triggered it)

2. /api/governance/risk/ledger/today
   → Count denial_count by reason
   → If "policy_disabled" reasons, regression tripwire auto-throttled

3. /api/governance/regression/state
   → List triggered tripwires
   → See baseline vs current vs drop% for context
   → Decide: "Retrain model + re-enable" or "Wait for more data"

4. /api/governance/heimdall/scorecard/today
   → Which domains' sandbox success_rate dropped overnight
   → Was production traffic sent before drift detected? (if heimdall prod_eligible gated it, answer is no)
```

**Tue-Thu (Throughput Experiments):**
- Run A/B tests on WHOLESALE offer logic, BUYER_MATCH algorithm, CAPITAL routing
- Record KPI events: `POST /api/governance/regression/kpi`
- Tripwire watches baseline vs current in background
- If experiment causes performance drop → auto-throttles = fail-safe learning

**Friday (Heimdall Sandbox Evolution):**
- Review Heimdall sandbox scorecard
- Decide: promote confidence thresholds for domains with >80% success rate?
- Update `heimdall_policy.min_confidence_prod` or `min_sandbox_trials`
- **Also**: `POST /api/governance/regression/policies/upsert` to update baselines after good week
  - Example: WHOLESALE contract_rate performed well all week → reset `regression_policy.baseline_events` to current week's performance

---

## How Tripwire Prevents Institutional Self-Destruction

| Scenario | Detection | Prevention |
|----------|-----------|-----------|
| Offer-accept algo starts drifting (80% → 50% acceptance) | KPI events show success drop | Auto-THROTTLE WHOLESALE engine → stops bad offers from scaling |
| Buyer-match starts failing (confidence scores become noise) | Match success drops below baseline | Auto-THROTTLE BUYER_MATCH → doesn't send bad matches |
| Capital routing breaks (ROI flips negative) | ROI_event values crash | Auto-KILL_SWITCH → system halts to protect balance sheet |
| Cascade: all engines degrading together | Multiple tripwires trigger | First THROTTLE fails to stabilize → next tripwire auto-KILL_SWITCH → manual intervention required |

---

## Next Steps: Deploy & Test

### Step 1: Run Migrations
```bash
cd services/api
alembic upgrade head
```
→ Creates kpi_event, regression_policy, regression_state tables + seeds 4 policies (all disabled)

### Step 2: Check Endpoints Exist
```bash
curl http://localhost:8000/api/governance/regression/policies
curl http://localhost:8000/api/governance/regression/state
```
→ Should return empty lists (no KPIs recorded yet, policies disabled)

### Step 3: Record KPI Events (Manual Test)
```bash
curl -X POST http://localhost:8000/api/governance/regression/kpi \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "success": true,
    "actor": "test_user"
  }'
```
→ Repeat 50+ times with random success/fail to simulate baseline

### Step 4: Enable a Policy & Trigger Evaluation
```bash
curl -X POST http://localhost:8000/api/governance/regression/policies/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "enabled": true,
    "changed_by": "test_user"
  }'

curl -X POST http://localhost:8000/api/governance/regression/evaluate \
  -d "domain=WHOLESALE&metric=contract_rate&actor=test_user"
```
→ If recent KPIs show enough drop → regression_state.triggered = true + risk policy disabled

### Step 5: Verify Risk Guard Enforcement
```bash
curl http://localhost:8000/api/governance/risk/policies
```
→ WHOLESALE risk_policy should show enabled=false (auto-disabled by tripwire)

### Step 6: Try a PROD_EXEC Deal (Should Fail)
- If go_live_enabled=true and risk reserves attempt WHOLESALE
- Should get: `RiskCheckOut(ok=False, reason="policy_disabled")`

---

## Summary: 4 Levers Complete ✓

| Lever | Purpose | Enforcement | Integration |
|-------|---------|-------------|-------------|
| **Go-Live State** | Single control plane (enabled/kill_switch) | Middleware blocks all PROD_EXEC if disabled | ExecutionClassMiddleware |
| **Risk Guard** | Daily loss/exposure/action caps per engine | Reserves before action, settles after | 2-line: `risk_reserve_or_raise()` + `risk_settle()` |
| **Heimdall Charter** | AI recommendation sandbox trial gates | Min confidence + success rate + trials required for prod | 2-line: `heimdall_require_prod_eligible()` |
| **Regression Tripwire** | Auto-detect performance drift | Compares recent vs baseline KPI events | Auto-THROTTLE risk policy or KILL_SWITCH |

**All systems work together:**
1. Go-Live blocks bad deploys before they start
2. Risk Guard limits daily damage from bad deployments  
3. Heimdall prevents untested AI recommendations from reaching customers
4. Regression Tripwire auto-throttles when performance degrades

**Result**: System that gets better every week, not worse.

