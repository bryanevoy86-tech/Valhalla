# INSTITUTIONAL GOVERNANCE STACK - VISUAL ARCHITECTURE

## System Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│ REQUEST (Deal, Offer, Capital Route, etc.)                             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                    ┌──────────▼────────────┐
                    │ GoLiveMiddleware      │
                    │ (Coarse Enforcement)  │
                    │ if NOT go_live_enabled│
                    │ → BLOCK               │ ← LEVER 1: Go-Live State
                    └──────────┬────────────┘
                               │
        ┌──────────────────────▼──────────────────────┐
        │ ExecutionClassMiddleware (Precise)          │
        │ ┌─────────────────────────────────────────┐│
        │ │ Classify endpoint: OBSERVE/SANDBOX/PROD ││
        │ │ if PROD_EXEC & kill_switch → BLOCK      ││ ← LEVER 1: Kill Switch
        │ │ if PROD_EXEC & heimdall gate fail → BLOCK││ ← LEVER 3: Heimdall
        │ └─────────────────────────────────────────┘│
        └──────────────────────┬───────────────────────┘
                               │
        ┌──────────────────────▼──────────────────────┐
        │ BUSINESS LOGIC (Deal Booking, etc.)        │
        │ ┌─────────────────────────────────────────┐│
        │ │ risk_reserve_or_raise(                  ││
        │ │   db, engine="WHOLESALE", amount=15000  ││ ← LEVER 2: Risk Reserve
        │ │ )                                       ││
        │ │ Check: GLOBAL policy pass? YES          ││
        │ │ Check: WHOLESALE policy pass? YES       ││
        │ │ Reserve: exposure_used += 15000         ││
        │ │ Reserve: open_risk_reserved += 15000    ││
        │ └─────────────────────────────────────────┘│
        │ [EXECUTE ACTION]                            │
        │ ┌─────────────────────────────────────────┐│
        │ │ heimdall_require_prod_eligible(         ││
        │ │   db, recommendation_id                 ││ ← LEVER 3: Heimdall Gate
        │ │ )                                       ││
        │ │ Check: prod_use_enabled? YES            ││
        │ │ Check: confidence >= 92%? YES           ││
        │ │ Check: trials >= 75? YES                ││
        │ │ Check: success_rate >= 82%? YES         ││
        │ │ Gate decision: PROD_ELIGIBLE            ││
        │ └─────────────────────────────────────────┘│
        │ [SEND TO CUSTOMER]                          │
        │ ┌─────────────────────────────────────────┐│
        │ │ risk_settle(                            ││
        │ │   db, engine="WHOLESALE",               ││ ← LEVER 2: Risk Settle
        │ │   reserved_amount=15000,                ││
        │ │   realized_loss=500                     ││
        │ │ )                                       ││
        │ │ Release: open_risk_reserved -= 15000    ││
        │ │ Apply: realized_loss += 500             ││
        │ │ Log: RiskEvent (immutable audit)        ││
        │ └─────────────────────────────────────────┘│
        └──────────────────────┬───────────────────────┘
                               │
        ┌──────────────────────▼──────────────────────┐
        │ RECORD KPI EVENT                           │
        │ POST /api/governance/regression/kpi        │
        │ { domain: "WHOLESALE",                     │ ← LEVER 4: KPI Recording
        │   metric: "contract_rate",                 │
        │   success: true }                          │
        │                                             │
        │ Index: (domain, metric, created_at)        │
        │ Purpose: Continuous baseline tracking      │
        └──────────────────────┬───────────────────────┘
                               │
        ┌──────────────────────▼──────────────────────┐
        │ FRIDAY WEEKLY: EVALUATE REGRESSION          │
        │ POST /api/governance/regression/evaluate    │
        │ { domain: "WHOLESALE",                      │ ← LEVER 4: Evaluation
        │   metric: "contract_rate" }                 │
        │                                             │
        │ Recent 50 events: 75% success (current)    │
        │ Baseline 200 events: 95% success           │
        │ Drop = (95-75)/95 = 21%                    │
        │                                             │
        │ if drop >= max_drop_fraction(20%):         │
        │   TRIGGERED = True                          │
        │   if action == "THROTTLE":                  │
        │     _get_risk_policy(db, "WHOLESALE")      │ ← Reuses LEVER 2
        │     .enabled = False                        │
        │     ↓ Next risk reserve: DENIED             │
        │   if action == "KILL_SWITCH":               │
        │     go_live.set_kill_switch(db, True)      │ ← Reuses LEVER 1
        │     ↓ Next PROD_EXEC: BLOCKED              │
        └─────────────────────────────────────────────┘
```

---

## Weekly Operational Timeline

```
MON      TUE         WED         THU         FRI        SAT/SUN
│        │           │           │           │          │
│        A/B Tests   Throughput  Throughput  Analysis   Rest
│        Running     Metrics     Learning    & Promote
│                    Recording
│        └──────────────────────────────────┘
│             Continuous KPI Recording
│
CONTROL      └───────────────────────────────────────┐
PLANE        Friday PM: Evaluate Regression         │
REVIEW       (sliding window comparison)             │
              Auto-throttle if drift detected        │
└─────────────────────────────────────────────────────┘
  10 min          │
  Review          │ If tripwire fired:
  "What broke?"   │ - Algorithm drifted
  "What denied?"  │ - Risk policy disabled
  "What drifted?" │ - System auto-throttled
                  │
                  └─→ Weekend: Fix algorithm
                      Monday: Re-enable + measure MTTR
```

---

## Policy Hierarchy (Dual-Control)

```
GLOBAL POLICY (Death Star - Blocks All Engines)
├─ Exposure: $1500/day
├─ Loss: $250/day
├─ Actions: 1000/day
└─ Enforced on ALL requests

    ├─ WHOLESALE ENGINE (Light Saber - Precise Constraint)
    │  ├─ Exposure: $1000/day (can't exceed GLOBAL)
    │  ├─ Loss: $200/day (can't exceed GLOBAL)
    │  ├─ Actions: 500/day
    │  └─ Must pass GLOBAL AND WHOLESALE both
    │
    ├─ CAPITAL ENGINE (Light Saber - Different Constraint)
    │  ├─ Exposure: $750/day (can't exceed GLOBAL)
    │  ├─ Loss: $150/day (can't exceed GLOBAL)
    │  ├─ Actions: 250/day
    │  └─ Must pass GLOBAL AND CAPITAL both
    │
    └─ NOTIFY ENGINE (Disabled - Logging Only)
       └─ All actions blocked
```

---

## Success Metrics

```
REAL-TIME MONITORING:
├─ go_live_enabled          (Boolean: system on?)
├─ kill_switch_engaged      (Boolean: emergency brake?)
├─ risk_ledger.exposure_used (Float: $spent today)
└─ risk_ledger.denial_count (Integer: actions blocked)

DAILY RESET (UTC midnight):
├─ risk_ledger.exposure_used    → 0
├─ risk_ledger.realized_loss    → 0
├─ risk_ledger.actions_count    → 0
└─ heimdall_scorecard           → new row

WEEKLY EVALUATION (Friday):
├─ regression_state.triggered   (Did tripwire fire?)
├─ regression_state.drop_fraction (Magnitude of drift)
├─ heimdall_scorecard.success_rate > 80%? (Ready to promote?)
└─ Risk denials reason analysis (Why blocked?)

MONTHLY STRATEGY (Strategic review):
├─ MTTR (Mean Time To Remediate) < 2 hours?
├─ Denial rate < 5% (not over-restrictive)?
├─ Tripwire false positives < 10% (accurate thresholds)?
└─ Throughput growth (shipping more deals safely?)
```

---

## Error Recovery Paths

```
ALGORITHM DRIFTS (Offer-Accept Rate Drops 95% → 75%)
════════════════════════════════════════════════════════
Friday:    Tripwire: 21% drop > 20% threshold → TRIGGERED
           Auto-action: disable WHOLESALE risk policy

Monday:    Operator review:
           - Risk ledger: 42 denials, reason="policy_disabled"
           - Regression state: WHOLESALE.contract_rate triggered
           - Decision: investigate algorithm

Fix:       Engineer finds bug in v2.0
           Rolls back to v1.9
           Tests in sandbox (POST /sandbox/trial)

Re-enable: POST /policies/upsert (enable WHOLESALE)
           Tests live deals, monitors denials

Measure:   MTTR = 16 hours (discovered Monday AM, fixed by Tuesday)
           Impact: 0 customer harm (auto-throttle prevented bad scale)
           Lesson: Add validation check to prevent v2.0 regression


PERFORMANCE DEGRADES SLOWLY (Not Tripwire)
═══════════════════════════════════════════════════
Friday W1:  KPI: baseline 85%, current 80% (6% drop)
            Threshold 25%, so no trigger

Friday W2:  KPI: 85% baseline (old), current 75% (12% drop)
            Still below 25% threshold

Friday W3:  Operator notices trend: 85% → 80% → 75%
            Takes proactive action:
            POST /policies/upsert (lower max_drop_fraction 25% → 20%)

Friday W4:  KPI: baseline 75%, current 70% (7% drop)
            Still below 20% threshold
            System healthy

Learning:  By observing trends (not just single points),
           operator can prevent issues before they explode


CATASTROPHIC FAILURE (Capital ROI Flips Negative)
══════════════════════════════════════════════════════
Friday:    KPI: baseline +$500, current -$300
           Drop = 160% (massive regression)
           Tripwire action = "KILL_SWITCH"

Auto-triggered:
           go_live.set_kill_switch(db=True)
           ↓
           All PROD_EXEC return 403 Forbidden
           System halts gracefully

No cascade: Risk policy didn't matter (already halted)
           Heimdall gate didn't matter (already halted)
           Go-live middleware blocked everything

Emergency response:
           Page on-call engineer (automated)
           Engineer investigates root cause
           Fixes critical bug in capital router
           Tests in sandbox
           Re-enables: POST /kill-switch/release

Outcome:   System protected balance sheet
           No $1M losses (would have from scaling)
           MTTR critical (15 min vs 15 hours if manual)
```

---

## Integration Pattern (2-Line Drop-In)

```
BEFORE (No governance):
────────────────────
def book_deal(offer_price, buyer_id):
    deal = create_deal(offer_price, buyer_id)
    return deal

AFTER (With governance):
───────────────────────
def book_deal(offer_price, buyer_id):
    # Line 1: Check & reserve capacity
    risk_reserve_or_raise(db, "WHOLESALE", offer_price, actor="book_deal")
    
    # Execute business logic
    deal = create_deal(offer_price, buyer_id)
    
    # Line 2: Settle & apply loss
    actual_profit = evaluate_deal(deal)
    risk_settle(db, "WHOLESALE", reserved_amount=offer_price, 
               realized_loss=abs(max(0, -actual_profit)))
    
    return deal

Only 2 new lines needed for institutional-grade risk control!
```

---

## Operational Checklist

```
MONDAY MORNING (10 minutes):
✓ curl /api/governance/go-live/state
  → Check: enabled? kill_switch?
  
✓ curl /api/governance/risk/ledger/today
  → Count denials by reason
  → If denials spike: expected or concerning?
  
✓ curl /api/governance/regression/state
  → Any tripwire triggered?
  → What drifted and by how much?
  
✓ curl /api/governance/heimdall/scorecard/today
  → Any domain's success_rate dropped overnight?
  → Confidence declining?
  
Decision:
  - System healthy → continue experiments
  - Tripwire fired → investigate root cause
  - Denials high → check if experimental
  - Confidence low → consider retraining

FRIDAY AFTERNOON (30 minutes):
✓ Review all scorecard success_rates > 80%
  → Candidate domains for production promotion
  
✓ Evaluate regression baselines
  → Were experiments successful?
  → Update baseline for next week?
  
✓ Adjust policies if needed
  → Confidence thresholds too strict?
  → Regression thresholds too sensitive?
  → Risk caps limiting throughput unnecessarily?
  
Decision:
  - Promote domains to prod_use_enabled=true
  - Update confidence minimums based on sandbox success
  - Adjust regression drop_fraction if too many false positives
```
