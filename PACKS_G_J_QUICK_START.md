# PACKS G-J: QUICK-START INTEGRATION CHECKLIST

## Pre-Deployment (Now)

- [x] All files created (12 files: models, services, routers)
- [x] All migrations created (4 files in correct sequence)
- [x] main.py updated (4 imports + 4 router registrations)
- [x] Documentation complete

## Deployment Order

### Step 1: Run Migrations (5 min)
```bash
cd c:\dev\valhalla\services\api
alembic upgrade head
```

**What happens**:
- Creates: market_policy (13 provinces seeded)
- Creates: followup_task
- Creates: buyer_liquidity_node + buyer_feedback_event
- Creates: offer_policy + offer_evidence

✅ Safe to run multiple times.

### Step 2: Start Server (2 min)
```bash
cd c:\dev\valhalla\services\api
$env:ENV="production"
$env:GO_LIVE_ENFORCE="1"
$env:DATABASE_URL="sqlite:///./test.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 3: Verify Migrations Worked (3 min)
```bash
curl http://localhost:8000/api/governance/market/policies
# Should show 13 provinces (BC, AB, SK, MB, ON, QC, NB, NS, PE, NL, YT, NT, NU)
```

### Step 4: Test Each Pack (10 min)

#### Pack G — Market Policy
```bash
# Test contact window validation
curl "http://localhost:8000/api/governance/market/can-contact?province=ON&weekday=2&hhmm=14:30&channel=SMS"
# Expected: {"ok": true, "reason": "within_window", ...}
```

#### Pack H — Follow-Up Ladder
```bash
# Create 6-step ladder
curl -X POST "http://localhost:8000/api/followups/ladder/create?lead_id=L123&province=ON&owner=bryan"
# Expected: {"ok": true, "tasks": [6 items with step 1-6]}

# Get due tasks
curl "http://localhost:8000/api/followups/due?limit=10"
# Expected: {"ok": true, "due": [...]}

# Get SLA
curl "http://localhost:8000/api/followups/sla"
# Expected: {"ok": true, "sla": {"count": 0, "within_30m": null, "within_2h": null}}
```

#### Pack I — Buyer Liquidity
```bash
# Get liquidity nodes
curl "http://localhost:8000/api/buyers/liquidity/nodes"
# Expected: {"ok": true, "nodes": []} (empty initially)

# Get liquidity score for ON/TORONTO
curl "http://localhost:8000/api/buyers/liquidity/score?province=ON&market=TORONTO&property_type=SFR"
# Expected: {"ok": true, "score": {"province": "ON", "market": "TORONTO", ...}}

# Record feedback
curl -X POST "http://localhost:8000/api/buyers/liquidity/feedback?province=ON&event=RESPONDED&buyer_id=B456"
# Expected: {"ok": true}
```

#### Pack J — Offer Strategy
```bash
# List policies (all disabled initially)
curl "http://localhost:8000/api/deals/offers/policies"
# Expected: empty (OfferPolicy disabled until you enable)

# Enable for ON
curl -X POST "http://localhost:8000/api/deals/offers/policies/upsert?province=ON&enabled=true&changed_by=bryan"
# Expected: {"ok": true}

# Compute offer
curl -X POST "http://localhost:8000/api/deals/offers/compute?province=ON&arv=450000&repairs=50000"
# Expected: {"ok": true, "calc": {"mao": 262500, "recommended_offer": 262500}, "evidence_id": 1, ...}
```

## Post-Deployment (Setup)

### Enable Policies by Market
```bash
# Start with 1 province, test it, then expand
curl -X POST "http://localhost:8000/api/deals/offers/policies/upsert?province=ON&market=ALL&enabled=true&changed_by=bryan&reason=Q1_launch"

# Later: expand to more provinces
curl -X POST "http://localhost:8000/api/deals/offers/policies/upsert?province=BC&market=ALL&enabled=true&changed_by=bryan"
```

### Update Contact Windows (if needed)
```bash
# Custom hours for specific market
curl -X POST "http://localhost:8000/api/governance/market/policies/upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "province": "ON",
    "market": "TORONTO",
    "enabled": true,
    "rules": {
      "contact_windows_local": [
        {"days": [0,1,2,3,4], "start": "08:00", "end": "21:00"}
      ],
      "channels_allowed": ["SMS", "CALL", "EMAIL"],
      "min_lead_score_to_contact": 0.75
    },
    "changed_by": "bryan",
    "reason": "Hot market, extend hours"
  }'
```

## Integration Points (Wire Into Your Code)

### 1. Before Sending Lead Contact
```python
from app.services.market_policy import get_effective_policy, is_contact_allowed

# Check if OK to contact
_, rules = get_effective_policy(db, "ON", "TORONTO")
ok, reason = is_contact_allowed(rules, weekday, hhmm, "SMS")
if not ok:
    return error(f"Cannot contact: {reason}")
```

### 2. After Offer Sent
```python
from app.services.followup_ladder import create_ladder

# Create 6-step automated followup
tasks = create_ladder(db, lead_id=lead.id, province="ON", market="TORONTO", owner="va1")
# Auto-emits KPI: ladder_created
```

### 3. Before Offering Multiple Times in Same Market
```python
from app.services.buyer_liquidity import liquidity_score

# Check if market is liquid enough
score_data = liquidity_score(db, "ON", "TORONTO", "SFR")
if score_data["score"] < 50:
    return error("Market too cold, skip this deal")
```

### 4. When Computing Offer
```python
from app.services.offer_strategy import compute_offer

# Get bounded offer
out = compute_offer(db, "ON", "TORONTO", arv=450000, repairs=50000)
recommended = out["calc"]["recommended_offer"]
# Auto-emits KPI: offer_generated
```

## Runbook Check (Production Gate)

```bash
# Before enabling production mode
curl http://localhost:8000/api/governance/runbook/status
# Should show: ok_to_enable_go_live=true (all blockers must be 0)
```

**Runbook checks**:
- ✅ go_live_checklist (backend done)
- ✅ kill_switch_clear (not engaged)
- ✅ env_sanity (ENV, DATABASE_URL set)
- ✅ risk_policies_present (at least 1 GLOBAL policy)
- ✅ regression_policies_present (at least 1 enabled)
- ✅ heimdall_charter_present (exists)
- ✅ market_policies_present (13 provinces seeded) ← **PACK G**
- ✅ followup_ladder_tables (exists) ← **PACK H**
- ✅ buyer_liquidity_tables (exists) ← **PACK I**
- ✅ offer_strategy_tables (exists) ← **PACK J**

## Daily Workflow (After Go-Live)

### Morning (Get Ready)
1. Check runbook: `GET /api/governance/runbook/status`
2. Get due followup tasks: `GET /api/followups/due?limit=50`
3. Assign to VAs/dialers: `POST /api/followups/task/{id}/complete`

### During Day (Execute)
1. Send SMS → Complete task
2. CALL back → Complete task
3. Record buyer response → `POST /api/buyers/liquidity/feedback`
4. Compute offer → `POST /api/deals/offers/compute`
5. Send offer → Risk policy gates it

### Evening (Monitor)
1. Check SLA: `GET /api/followups/sla` (should be 90%+ within 2h)
2. Liquidity scores: `GET /api/buyers/liquidity/nodes`
3. Offer volume: `GET /api/deals/offers/policies`

### Friday (Evaluate)
```bash
# Regression tripwire watches:
# - ladder_created (count > X?)
# - followup_completed (rate 90%+?)
# - buyer_feedback (response_rate trending?)
# - offer_generated (volume correct?)

# If any metric drops 20%+ → auto-throttle
# Check: POST /api/governance/regression/evaluate
```

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| OfferPolicy disabled | `GET /api/deals/offers/policies` shows enabled=false | `POST /api/deals/offers/policies/upsert` with enabled=true |
| Can't send SMS 20:30 | Contact window blocked | Update market policy with extended hours |
| No liquidity score | Haven't recorded feedback yet | `POST /api/buyers/liquidity/feedback` to seed |
| Ladder never completes | SLA shows 0% within_2h | Check due_tasks, manually complete via API |
| Runbook fails | Check individual endpoints | Market policies might not be seeded (rerun migration) |

## Success Metrics (Monitor)

- **Market Policy**: 100% of contacts within approved windows
- **Ladder**: 90%+ tasks completed within 2 hours of due time
- **Liquidity**: Response rate > 0.60 (60% of leads respond), Close rate > 0.30 (30% buy)
- **Offer**: Accepted rate > 0.40 (40% of offers accepted within 24h)

## File Locations

| Pack | Files | Location |
|------|-------|----------|
| G | Model, Schema, Service, Router | `app/models/market_policy.py`, `app/schemas/market_policy.py`, `app/services/market_policy.py`, `app/routers/market_policy.py` |
| H | Model, Service, Router | `app/models/followup_task.py`, `app/services/followup_ladder.py`, `app/routers/followup_ladder.py` |
| I | Models (2), Service, Router | `app/models/buyer_liquidity.py`, `app/services/buyer_liquidity.py`, `app/routers/buyer_liquidity.py` |
| J | Models (2), Service, Router | `app/models/offer_policy.py`, `app/models/offer_evidence.py`, `app/services/offer_strategy.py`, `app/routers/offer_strategy.py` |
| Migrations | 4 migration files | `alembic/versions/20260113_*` (market_policy, followup_ladder, buyer_liquidity, offer_strategy) |

## Go-Live Readiness

Once all steps complete:

✅ Run migrations
✅ Start server
✅ Test all endpoints
✅ Enable 1 OfferPolicy
✅ Wire into business logic
✅ Run runbook gate
✅ Enable production

**You're Canada-wide ready.**
