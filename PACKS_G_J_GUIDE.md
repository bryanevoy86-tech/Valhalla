# PACKS G-J IMPLEMENTATION GUIDE

## Overview
Packs G, H, I, J form the operational backbone for Canada-wide wholesaling at scale:
- **Pack G**: Market Policy (province-specific rules + contact windows)
- **Pack H**: Follow-Up Ladder (enforced 6-step automation)
- **Pack I**: Buyer Liquidity Graph (real-time market depth signals)
- **Pack J**: Offer Strategy (bounded offer engine + evidence traces)

**Status**: ✅ All files created, migrations ready, main.py integrated

---

## PACK G — Market Policy (Canada-Wide Province Routing)

### What It Does
Rules per province/market. Stores contact windows (days/times), allowed channels (SMS/CALL/EMAIL), min lead score.

**Files Created**:
- `models/market_policy.py` - Province/market + JSON rules storage
- `schemas/market_policy.py` - Input validation (Pydantic)
- `services/market_policy.py` - Query logic + contact window validation
- `routers/market_policy.py` - 4 REST endpoints

### Key Functions

**Upsert Policy** (create or update):
```python
POST /api/governance/market/policies/upsert
{
  "province": "ON",
  "market": "TORONTO",
  "enabled": true,
  "rules": {
    "contact_windows_local": [
      {"days": [0,1,2,3,4], "start": "09:00", "end": "20:00"},
      {"days": [5], "start": "10:00", "end": "18:00"}
    ],
    "channels_allowed": ["SMS", "CALL", "EMAIL"],
    "min_lead_score_to_contact": 0.65
  },
  "changed_by": "bryan",
  "reason": "Q1 expansion"
}
```

**Get Effective Policy** (best match):
```python
GET /api/governance/market/effective?province=ON&market=TORONTO
# Returns: found, rules (province+market fallback to province+ALL)
```

**Check Contact Allowed** (real-time gate):
```python
GET /api/governance/market/can-contact?province=ON&market=TORONTO&weekday=2&hhmm=14:30&channel=SMS
# Returns: {"ok": true/false, "reason": "within_window", ...}
```

### Safe Defaults (Pre-seeded)
- All 13 provinces get seeded with "ALL" market
- Business hours: Mon-Fri 09:00-20:00, Sat 10:00-18:00
- Channels: SMS, CALL, EMAIL
- Min lead score: 0.65

### Integration Pattern
```python
from app.services.market_policy import get_effective_policy, is_contact_allowed

# Before sending SMS
_, rules = get_effective_policy(db, "ON", "TORONTO")
ok, reason = is_contact_allowed(rules, weekday=2, hhmm="14:30", channel="SMS")
if not ok:
    return error(f"contact_denied: {reason}")

# Send SMS
```

---

## PACK H — Follow-Up Ladder (SLA-Enforced Automation)

### What It Does
6-step enforced cadence: SMS → CALL → SMS → CALL → SMS → CALL over 7 days.

**Files Created**:
- `models/followup_task.py` - Task state (due_at, completed, channel, step)
- `services/followup_ladder.py` - Ladder creation + SLA snapshot
- `routers/followup_ladder.py` - 4 REST endpoints

### Key Functions

**Create Ladder** (initial):
```python
POST /api/followups/ladder/create?lead_id=L123&province=ON&market=TORONTO&owner=bryan&correlation_id=offer_456
# Returns: [{"id": 1, "due_at": "2026-01-13T15:30:00Z", "channel": "SMS", "step": 1}, ...]
```

**Complete Task** (manual mark done):
```python
POST /api/followups/task/42/complete?actor=va1&correlation_id=offer_456
# Emits KPI: followup_completed with step, channel
```

**Get Due Tasks** (pull for dialer/dispatcher):
```python
GET /api/followups/due?limit=50
# Returns: [{"id": 42, "due_at": "...", "channel": "SMS", "step": 2, "owner": "va1"}, ...]
```

**SLA Snapshot** (quality metric):
```python
GET /api/followups/sla
# Returns: {"count": 500, "within_30m": 0.92, "within_2h": 0.98}
```

### Default Ladder
| Step | Delay | Channel |
|------|-------|---------|
| 1 | 0 min | SMS |
| 2 | 30 min | CALL |
| 3 | 3 hours | SMS |
| 4 | 1 day | CALL |
| 5 | 3 days | SMS |
| 6 | 7 days | CALL |

### Integration Pattern
```python
from app.services.followup_ladder import create_ladder
from app.services.kpi import emit_kpi

# After sending initial offer
tasks = create_ladder(db, lead_id="L123", province="ON", market="TORONTO", owner="bryan")
# KPI already emitted: ladder_created with task count

# In your dialer UI
from app.services.followup_ladder import due_tasks
due = due_tasks(db, limit=50)  # Pull next batch to call
for task in due:
    # Execute task (SMS or CALL)
    complete_task(db, task.id, actor="va1")  # Emits KPI: followup_completed
```

---

## PACK I — Buyer Liquidity Graph (Market Depth Signals)

### What It Does
Real-time aggregated buyer responsiveness per (province, market, property_type).

**Files Created**:
- `models/buyer_liquidity.py` - 2 models: BuyerLiquidityNode + BuyerFeedbackEvent
- `services/buyer_liquidity.py` - Record feedback + liquidity scoring
- `routers/buyer_liquidity.py` - 3 REST endpoints

### Key Models

**BuyerLiquidityNode** (aggregated state):
```python
province: "ON"
market: "TORONTO"
property_type: "SFR"
buyer_count: 125
active_buyer_count: 87
avg_response_rate: 0.68  # percent
avg_close_rate: 0.34     # percent
updated_at: datetime
```

**BuyerFeedbackEvent** (immutable audit trail):
```python
buyer_id: "B456"
province: "ON"
market: "TORONTO"
property_type: "SFR"
event: "RESPONDED" | "NO_RESPONSE" | "BOUGHT" | "PASSED"
correlation_id: trace_id
```

### Key Functions

**Record Feedback** (emit from dialer/closer):
```python
POST /api/buyers/liquidity/feedback?province=ON&market=TORONTO&property_type=SFR&event=RESPONDED&buyer_id=B456
# Updates node: avg_response_rate += 0.01, active_buyer_count += 1
# Emits KPI: buyer_feedback
```

**Get Liquidity Score** (decision gate):
```python
GET /api/buyers/liquidity/score?province=ON&market=TORONTO&property_type=SFR
# Returns: {
#   "buyer_count": 125,
#   "active_buyer_count": 87,
#   "avg_response_rate": 0.68,
#   "avg_close_rate": 0.34,
#   "score": 101.35  # weighted: active*0.5 + resp_rate*50 + close_rate*50
# }
```

**List All Nodes** (dashboard):
```python
GET /api/buyers/liquidity/nodes
# Returns all markets you've contacted
```

### Integration Pattern
```python
from app.services.buyer_liquidity import record_feedback, liquidity_score

# After buyer responds to offer
record_feedback(db, "ON", "TORONTO", "SFR", "RESPONDED", buyer_id="B456", correlation_id=trace_id)

# Before launching offer campaign
score_data = liquidity_score(db, "ON", "TORONTO", "SFR")
if score_data["score"] < 50:  # Market too cold
    return {"ok": False, "reason": "low_liquidity"}
```

---

## PACK J — Offer Strategy (Bounded Offer Engine)

### What It Does
Compute MAO (max allowable offer) using classic wholesaling formula:
```
MAO = (ARV × max_arv_multiplier) - repairs - fees_buffer
```

Stores evidence trace for audit + KPI emission for regression tracking.

**Files Created**:
- `models/offer_policy.py` - Province/market + math parameters
- `models/offer_evidence.py` - Computed offer with comps + assumptions
- `services/offer_strategy.py` - Compute logic
- `routers/offer_strategy.py` - 3 REST endpoints

### Key Models

**OfferPolicy** (rules):
```python
province: "ON"
market: "TORONTO"
enabled: True
max_arv_multiplier: 0.70  # MAO = ARV * 0.70 - repairs - fees
default_assignment_fee: 10000
default_fees_buffer: 2500
```

**OfferEvidence** (immutable record):
```python
province: "ON"
market: "TORONTO"
arv: 450000.00
repairs: 50000.00
fees_buffer: 2500.00
mao: 262500.00  # computed
recommended_offer: 262500.00
comps_json: {...}  # comp analysis if provided
assumptions_json: {...}
correlation_id: trace_id
```

### Key Functions

**List Policies**:
```python
GET /api/deals/offers/policies
# Returns all province/market offer rules
```

**Upsert Policy** (create/update offer rule):
```python
POST /api/deals/offers/policies/upsert?province=ON&market=TORONTO&enabled=true&max_arv_multiplier=0.70&changed_by=bryan
```

**Compute Offer** (generate MAO):
```python
POST /api/deals/offers/compute?province=ON&market=TORONTO&arv=450000&repairs=50000
# Returns: {
#   "policy": {"max_arv_multiplier": 0.70, ...},
#   "calc": {
#     "arv": 450000,
#     "repairs": 50000,
#     "fees_buffer": 2500,
#     "mao": 262500,
#     "recommended_offer": 262500
#   },
#   "evidence_id": 789
# }
# Emits KPI: offer_generated with evidence_id
```

### Integration Pattern
```python
from app.services.offer_strategy import compute_offer
from app.core.risk_guard_helpers import risk_reserve_or_raise

# In your deal intake workflow
out = compute_offer(db, "ON", "TORONTO", arv=450000, repairs=50000, correlation_id=trace_id)
recommended = out["calc"]["recommended_offer"]  # 262500

# Then reserve risk for assignment fee
try:
    risk_reserve_or_raise(db, "WHOLESALE", recommended, actor="system")
    send_offer(buyer, recommended)
except:
    # Risk policy blocked
    return error("risk_denied")
```

---

## Migration Sequence (CRITICAL)

Run in this exact order:

```bash
cd services/api
alembic upgrade head
# This runs all 4 migrations in sequence:
# 1. 20260113_market_policy (seeds 13 provinces with safe defaults)
# 2. 20260113_followup_ladder
# 3. 20260113_buyer_liquidity
# 4. 20260113_offer_strategy
```

All migrations are safe to run multiple times (unique constraints prevent duplicates).

---

## KPI Emission (Automatic)

All 4 packs automatically emit KPIs when actions complete:

| Action | Domain | Metric | Success | Detail |
|--------|--------|--------|---------|--------|
| Create ladder | WHOLESALE | ladder_created | true | {"tasks": 6} |
| Complete followup | WHOLESALE | followup_completed | true | {"task_id": 42, "step": 2, "channel": "SMS"} |
| Record buyer feedback | BUYER_MATCH | buyer_feedback | true | {"event": "RESPONDED", "province": "ON", ...} |
| Generate offer | WHOLESALE | offer_generated | true | {"evidence_id": 789, "province": "ON"} |

→ These auto-feed into Regression Tripwire for KPI evaluation daily.

---

## Safe Defaults (Day 1)

After migrations run, you have:

**13 provinces** (BC, AB, SK, MB, ON, QC, NB, NS, PE, NL, YT, NT, NU):
- Market: ALL
- Contact windows: Mon-Fri 09:00-20:00, Sat 10:00-18:00
- Channels: SMS, CALL, EMAIL
- Min lead score: 0.65

**OfferPolicy**: Safe defaults seeded but DISABLED until you explicitly enable by province.

→ **No policies active until you enable them** (prevents accidental mass offers).

---

## Mentor Order (Go-Live Sequence)

1. **Run migrations** → 13 provinces seeded with safe contact windows
2. **Enable offer policies** → Start with 1 province: `POST /api/deals/offers/policies/upsert?province=ON&...&enabled=true`
3. **Test workflow**:
   - Create ladder: `POST /api/followups/ladder/create`
   - Mark due: `GET /api/followups/due`
   - Complete task: `POST /api/followups/task/42/complete`
   - Record feedback: `POST /api/buyers/liquidity/feedback`
   - Compute offer: `POST /api/deals/offers/compute`
4. **Add more provinces** once flow is proven (never add all 13 at once)
5. **Monitor KPIs** → Regression tripwire watches ladder_created, followup_completed, buyer_feedback, offer_generated
6. **Friday evaluation** → Review offer_accept_rate + contract_rate across all provinces

---

## Endpoints Summary (20 total)

### Pack G — Market Policy (4)
- `GET /api/governance/market/policies` - List all
- `POST /api/governance/market/policies/upsert` - Create/update
- `GET /api/governance/market/effective` - Get best match
- `GET /api/governance/market/can-contact` - Real-time gate

### Pack H — Follow-Up Ladder (4)
- `POST /api/followups/ladder/create` - Create 6-step ladder
- `POST /api/followups/task/{id}/complete` - Mark task done
- `GET /api/followups/due` - Get due tasks
- `GET /api/followups/sla` - SLA metrics

### Pack I — Buyer Liquidity (3)
- `GET /api/buyers/liquidity/nodes` - List all nodes
- `GET /api/buyers/liquidity/score` - Get market depth
- `POST /api/buyers/liquidity/feedback` - Record event

### Pack J — Offer Strategy (3)
- `GET /api/deals/offers/policies` - List all
- `POST /api/deals/offers/policies/upsert` - Create/update
- `POST /api/deals/offers/compute` - Compute MAO

**Grand Total**: 14 + 5 runbook endpoints + 6 go-live + 5 risk + 5 heimdall + 5 regression = **42 REST endpoints** (all governance + operations integrated)

---

## Testing Checklist

```bash
# 1. Run migrations
cd services/api && alembic upgrade head

# 2. Verify provinces seeded
curl http://localhost:8000/api/governance/market/policies
# Should show 13 provinces with "ALL" market

# 3. Create ladder
curl -X POST "http://localhost:8000/api/followups/ladder/create?lead_id=L123&province=ON&owner=bryan"
# Should return 6 tasks with step 1-6

# 4. Test contact window
curl "http://localhost:8000/api/governance/market/can-contact?province=ON&weekday=2&hhmm=14:30&channel=SMS"
# Should return {"ok": true, "reason": "within_window"}

# 5. Test offer compute (make sure OfferPolicy is ENABLED for ON first)
curl -X POST "http://localhost:8000/api/deals/offers/compute?province=ON&arv=450000&repairs=50000"
# Should return recommended_offer, evidence_id, etc.

# 6. Record buyer feedback
curl -X POST "http://localhost:8000/api/buyers/liquidity/feedback?province=ON&event=RESPONDED&buyer_id=B456"

# 7. Check liquidity score
curl "http://localhost:8000/api/buyers/liquidity/score?province=ON"

# 8. Verify KPIs were emitted
curl http://localhost:8000/api/governance/runbook/status
# runbook should show all policies present
```

---

## Common Workflows

### Scenario 1: Lead Comes In
```python
# 1. Check contact window before calling/SMSing
ok, reason = is_contact_allowed(rules, weekday, hhmm, channel)

# 2. Create followup ladder
tasks = create_ladder(db, lead_id="L123", province="ON", market="TORONTO", owner="va1")

# 3. Get first task (should be SMS in 0 minutes)
due = due_tasks(db, limit=1)  # [task with step=1, channel=SMS]

# 4. Send SMS → complete task 1
complete_task(db, task.id, actor="va1")  # KPI: followup_completed

# 5. Monitor with SLA
sla = sla_snapshot(db)  # within_30m %, within_2h %
```

### Scenario 2: Offer Flow
```python
# 1. Get property
arv = 450000
repairs = 50000

# 2. Check buyer liquidity first
score = liquidity_score(db, "ON", "TORONTO", "SFR")
if score["score"] < 50:
    return error("market too cold")

# 3. Compute offer
offer = compute_offer(db, "ON", "TORONTO", arv, repairs)
recommended = offer["calc"]["recommended_offer"]  # 262500
evidence_id = offer["evidence_id"]

# 4. Reserve risk (prevents over-committing)
risk_reserve_or_raise(db, "WHOLESALE", recommended, actor="system")

# 5. Send offer
send_offer(buyer, recommended)

# 6. Record buyer response (manual or API)
record_feedback(db, "ON", "TORONTO", "SFR", "RESPONDED", buyer_id=buyer.id)
# liquidity_score will update: avg_response_rate goes up

# 7. If buyer buys
record_feedback(db, "ON", "TORONTO", "SFR", "BOUGHT", buyer_id=buyer.id)
# avg_close_rate goes up → market gets hotter → easier to offer next time
```

---

## Notes

- **Market Policy**: Contact windows are LOCAL time. Store lead_timezone and convert before checking.
- **Ladder**: Default assumes fast human response. Adjust delays per market/province as you learn.
- **Liquidity**: Score is simple aggregate. Build decision rules (offer only if score > X).
- **Offer**: MAO formula is classic wholesaling. Adjust `max_arv_multiplier` per market (maybe 0.65 in hot markets, 0.75 in cold).

All 4 packs emit KPIs → Regression Tripwire watches daily → Auto-throttles if metrics drop → Runbook gate prevents go-live if policies missing.

**You're now Canada-wide ready.**
