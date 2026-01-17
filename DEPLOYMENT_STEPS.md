# DEPLOYMENT STEPS - 4 LEVERS INSTITUTIONAL GOVERNANCE STACK

## Pre-Deployment Checklist

- [ ] All 33 files created (models, services, routers, migrations, helpers)
- [ ] main.py updated with 4 new middleware + 4 new routers
- [ ] Database backup taken (just in case)
- [ ] Environment variables set: `ENV=production`, `GO_LIVE_ENFORCE=1`

---

## Step 1: Run Database Migrations

```bash
cd services/api

# Verify migration chain
alembic current
# Should show: 20260113_heimdall_charter (or whatever was last)

# Run all pending migrations (includes regression tripwire)
alembic upgrade head

# Verify tables created
alembic current
# Should now show: 20260113_regression_tripwire
```

**What was created**:
- `go_live_state` (1 row)
- `risk_policy` (4 seed rows)
- `risk_ledger_day` (empty, auto-creates)
- `risk_event` (empty)
- `heimdall_policy` (4 seed rows)
- `heimdall_scorecard_day` (empty, auto-creates)
- `heimdall_recommendation` (empty)
- `heimdall_event` (empty)
- `kpi_event` (empty)
- `regression_policy` (4 seed rows)
- `regression_state` (empty, auto-creates)

---

## Step 2: Start API Server

```bash
# From services/api directory
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with gunicorn for production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
```

---

## Step 3: Verify All Endpoints Exist

### Go-Live (Lever 1)
```bash
# Get go-live state
curl http://localhost:8000/api/governance/go-live/state
# Expected: { go_live_enabled: false, kill_switch_engaged: false, ... }

# Get checklist (should pass all checks = go-live enabled)
curl http://localhost:8000/api/governance/go-live/checklist

# Disable go-live (can only do if checklist passes or manual override)
curl -X POST http://localhost:8000/api/governance/go-live/disable \
  -H "Content-Type: application/json" \
  -d '{"actor": "deployment", "reason": "Testing enforcement"}'

# Try accessing protected endpoint while go-live disabled
curl http://localhost:8000/api/deals
# Expected: 403 Forbidden (GoLiveMiddleware blocks it)
# Exception: /api/governance, /api/system/status, /health, /docs not blocked

# Re-enable go-live
curl -X POST http://localhost:8000/api/governance/go-live/enable \
  -H "Content-Type: application/json" \
  -d '{"actor": "deployment"}'
```

### Risk Guard (Lever 2)
```bash
# List risk policies
curl http://localhost:8000/api/governance/risk/policies
# Expected: [
#   { engine: "GLOBAL", max_daily_loss: 250, max_daily_exposure: 1500, ... },
#   { engine: "WHOLESALE", max_daily_loss: 200, max_daily_exposure: 1000, ... },
#   { engine: "CAPITAL", max_daily_loss: 150, ... },
#   { engine: "NOTIFY", enabled: false, ... }
# ]

# Get today's risk ledger
curl http://localhost:8000/api/governance/risk/ledger/today
# Expected: [
#   { engine: "WHOLESALE", exposure_used: 0, open_risk_reserved: 0, ... }
# ]

# Test risk reserve (check only)
curl -X POST http://localhost:8000/api/governance/risk/check-and-reserve \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "WHOLESALE",
    "amount": 50000,
    "actor": "test"
  }'
# Expected: ok=True (within $1000 daily exposure)

# Test with over-limit amount
curl -X POST http://localhost:8000/api/governance/risk/check-and-reserve \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "WHOLESALE",
    "amount": 2000000,
    "actor": "test"
  }'
# Expected: ok=False, reason="would_exceed_policy"
```

### Heimdall Confidence Charter (Lever 3)
```bash
# List heimdall policies
curl http://localhost:8000/api/governance/heimdall/policies
# Expected: [
#   { domain: "WHOLESALE_OFFER", min_confidence_prod: 0.92, prod_use_enabled: false, ... },
#   { domain: "BUYER_MATCH", min_confidence_prod: 0.90, prod_use_enabled: false, ... },
#   ...
# ]

# Get today's heimdall scorecard (empty, no recommendations yet)
curl http://localhost:8000/api/governance/heimdall/scorecard/today

# Create a test recommendation
curl -X POST http://localhost:8000/api/governance/heimdall/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE_OFFER",
    "confidence": 0.95,
    "recommendation": { "offer_id": 123, "price": 1500 },
    "evidence": { "model": "v2.1", "prediction_score": 0.95 },
    "actor": "heimdall_ai"
  }'
# Expected: prod_eligible=false (because prod_use_enabled=false)
```

### Regression Tripwire (Lever 4)
```bash
# List regression policies
curl http://localhost:8000/api/governance/regression/policies
# Expected: [
#   { domain: "WHOLESALE", metric: "contract_rate", window_events: 50, ... },
#   { domain: "WHOLESALE", metric: "offer_accept_rate", ... },
#   { domain: "BUYER_MATCH", metric: "match_success", ... },
#   { domain: "CAPITAL", metric: "roi_event", action: "KILL_SWITCH", ... }
# ]

# Get regression state (empty, no evaluations yet)
curl http://localhost:8000/api/governance/regression/state

# Record a KPI event
curl -X POST http://localhost:8000/api/governance/regression/kpi \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "success": true,
    "actor": "system"
  }'
# Expected: { ok: true, id: 1 }
```

---

## Step 4: Seed Test Data (Optional)

### Fill regression_policy baseline with test KPI events
```bash
#!/bin/bash

# Record 200 "baseline" KPI events with 95% success
for i in {1..190}; do
  curl -s -X POST http://localhost:8000/api/governance/regression/kpi \
    -H "Content-Type: application/json" \
    -d '{"domain":"WHOLESALE","metric":"contract_rate","success":true,"actor":"test_seed"}' &
done
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/governance/regression/kpi \
    -H "Content-Type: application/json" \
    -d '{"domain":"WHOLESALE","metric":"contract_rate","success":false,"actor":"test_seed"}' &
done
wait

# Enable the policy
curl -X POST http://localhost:8000/api/governance/regression/policies/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "WHOLESALE",
    "metric": "contract_rate",
    "enabled": true,
    "changed_by": "test_deployment"
  }'

# Evaluate (should show baseline=0.95, current=0.95, drop=0, triggered=false)
curl -X POST http://localhost:8000/api/governance/regression/evaluate \
  -d "domain=WHOLESALE&metric=contract_rate&actor=test"

# Now record 50 "current" KPI events with 75% success (simulating degradation)
for i in {1..37}; do
  curl -s -X POST http://localhost:8000/api/governance/regression/kpi \
    -H "Content-Type: application/json" \
    -d '{"domain":"WHOLESALE","metric":"contract_rate","success":true,"actor":"test_degrade"}' &
done
for i in {1..13}; do
  curl -s -X POST http://localhost:8000/api/governance/regression/kpi \
    -H "Content-Type: application/json" \
    -d '{"domain":"WHOLESALE","metric":"contract_rate","success":false,"actor":"test_degrade"}' &
done
wait

# Evaluate again (should show baseline=0.95, current=0.75, drop=0.211, triggered=true)
curl -X POST http://localhost:8000/api/governance/regression/evaluate \
  -d "domain=WHOLESALE&metric=contract_rate&actor=test"

# Verify risk policy was auto-disabled
curl http://localhost:8000/api/governance/risk/policies | grep WHOLESALE
# Should show: "enabled": false, "reason": "Regression tripwire: WHOLESALE.contract_rate drop=0.211"

# Try to reserve WHOLESALE (should fail)
curl -X POST http://localhost:8000/api/governance/risk/check-and-reserve \
  -H "Content-Type: application/json" \
  -d '{"engine":"WHOLESALE","amount":50000,"actor":"test"}'
# Expected: ok=False, reason="policy_disabled"
```

---

## Step 5: Verify Monday Control Plane Works

```bash
#!/bin/bash

echo "=== MONDAY CONTROL PLANE REVIEW ==="

echo ""
echo "1. Go-Live State:"
curl -s http://localhost:8000/api/governance/go-live/state | jq .

echo ""
echo "2. Risk Ledger (Today):"
curl -s http://localhost:8000/api/governance/risk/ledger/today | jq .

echo ""
echo "3. Regression State:"
curl -s http://localhost:8000/api/governance/regression/state | jq .

echo ""
echo "4. Heimdall Scorecard (Today):"
curl -s http://localhost:8000/api/governance/heimdall/scorecard/today | jq .

echo ""
echo "=== DECISION ==="
echo "Review outputs above. Is system healthy?"
echo ""
```

---

## Step 6: Documentation Handoff

**Documents created for operator**:
1. [4_LEVERS_COMPLETE.md](4_LEVERS_COMPLETE.md) - Full architecture overview
2. [REGRESSION_TRIPWIRE_COMPLETE.md](REGRESSION_TRIPWIRE_COMPLETE.md) - Tripwire details
3. [REGRESSION_TRIPWIRE_QUICK_REFERENCE.md](REGRESSION_TRIPWIRE_QUICK_REFERENCE.md) - Quick commands

**Key runbooks**:
- **Monday morning**: Run control plane review (Step 5 script)
- **Tue-Thu**: Record KPI events via `POST /api/governance/regression/kpi`
- **Friday**: Review Heimdall scorecard, update thresholds if needed
- **Anytime tripwire fires**: Check regression state, fix algorithm, re-enable policy

---

## Step 7: Production Environment Variables

Set before deploying to production:

```bash
# Required for go-live enforcement
export ENV=production
export GO_LIVE_ENFORCE=1

# Database (if using external DB)
export DATABASE_URL=postgresql://user:pass@host:5432/valhalla

# Optional: retention settings
export RETENTION_ENABLED=true
export RETENTION_CRON_MINUTES=30
```

---

## Verification Checklist

After deployment, verify:

- [ ] `alembic current` shows `20260113_regression_tripwire`
- [ ] All 11 tables exist in database:
  ```sql
  SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%state%' OR name LIKE '%policy%' OR name LIKE '%ledger%' OR name LIKE '%event%' OR name LIKE '%scorecard%' OR name LIKE '%recommendation%' OR name LIKE '%kpi%';
  ```
- [ ] Go-live endpoints respond (200 OK):
  - GET `/api/governance/go-live/state`
  - GET `/api/governance/go-live/checklist`
- [ ] Risk endpoints respond (200 OK):
  - GET `/api/governance/risk/policies`
  - GET `/api/governance/risk/ledger/today`
- [ ] Heimdall endpoints respond (200 OK):
  - GET `/api/governance/heimdall/policies`
  - GET `/api/governance/heimdall/scorecard/today`
- [ ] Regression endpoints respond (200 OK):
  - GET `/api/governance/regression/policies`
  - GET `/api/governance/regression/state`
- [ ] GoLiveMiddleware blocks requests when go_live_enabled=false (except exempts)
- [ ] ExecutionClassMiddleware blocks PROD_EXEC when kill_switch_engaged
- [ ] Risk guard reserves/settles correctly
- [ ] Regression tripwire can record KPI events
- [ ] Regression tripwire can evaluate and auto-trigger

---

## Rollback Plan

If critical issues discovered:

```bash
# Rollback to previous migration
alembic downgrade 20260113_heimdall_charter

# Or disable enforcement entirely (emergency mode)
# Set ENV=development
export ENV=development

# Or disable go-live enforcement
export GO_LIVE_ENFORCE=0

# Restart API server
```

---

## Post-Deployment Monitoring

**Daily checks**:
- Monitor `/api/governance/regression/state` for unexpected triggers
- Monitor `/api/governance/risk/ledger/today` for policy disables
- Monitor API error logs for regression service issues

**Weekly checklist**:
- Run Monday control plane review (Step 5)
- Review tripwire baseline accuracy
- Check MTTR for remediation
- Update regression thresholds if needed

---

## Success Criteria

✓ **Go-Live State**:
- [ ] All PROD_EXEC blocked when go_live_enabled=false
- [ ] Checklist validates backend_complete + packs_installed
- [ ] Kill-switch engages/releases correctly

✓ **Risk Guard**:
- [ ] Dual-control (GLOBAL + engine) enforced
- [ ] Daily ledger tracks usage correctly
- [ ] Policies auto-disable via regression tripwire

✓ **Heimdall Charter**:
- [ ] Sandbox scorecard tracks daily performance
- [ ] Production gate requires min_confidence + min_trials + min_success_rate
- [ ] prod_use_enabled flag controls enablement

✓ **Regression Tripwire**:
- [ ] KPI events recorded with index
- [ ] Sliding window evaluation compares recent vs baseline
- [ ] Auto-THROTTLE disables risk policy
- [ ] Auto-KILL_SWITCH engages when needed

✓ **System Integration**:
- [ ] All 4 levers work together (not in isolation)
- [ ] Monday control plane review works end-to-end
- [ ] Weekly cadence (Tue-Thu throughput, Friday evolution) supported

---

## Contacts & Escalation

**Critical Issues**: Rollback via environment variables (ENV=development)
**Regression Tripwire Fires**: Check `/api/governance/regression/state`, read regression policy reason
**Policies Disabled**: Review risk/regression/heimdall state, verify business logic, re-enable after fix
**Database Issues**: Check Alembic migration history, verify all tables created

