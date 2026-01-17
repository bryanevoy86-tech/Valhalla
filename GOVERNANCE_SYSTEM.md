# Valhalla Governance System: Complete Architecture

## Overview

The Valhalla governance system is a 5-god pantheon that evaluates business decisions and gates critical actions. Gods don't just evaluate—they **enforce**: unapproved deals are blocked at 409 CONFLICT before pipeline execution.

**Test Status:** ✅ 23/23 Tests Passing (100% coverage)

## The Five Gods

### 1. **King** - Valuation Discipline
**Purpose:** Ensures deals have realistic profit margins and don't overpay.

**Blocking Rules:**
- ❌ ROI < 0.15 (15% minimum return)
- ❌ Purchase price > ARV (upside-down deal)

**Endpoint:** `POST /api/governance/king`

**Example Block:**
```json
{
  "allowed": false,
  "severity": "CRITICAL",
  "reasons": ["ROI 5.6% below minimum 15%"],
  "god": "king"
}
```

---

### 2. **Queen** - Lifestyle & Sustainability
**Purpose:** Protects team from burnout and unrealistic expectations.

**Blocking Rules:**
- ❌ Hours per week > 50 (burnout risk)
- ❌ Stress level > 8 (extreme stress)
- ❌ Holding months > 18 (property tie-up)
- ❌ Both high hours (>45) AND high stress (>6)

**Endpoint:** `POST /api/governance/queen`

**Example Block:**
```json
{
  "allowed": false,
  "severity": "HIGH",
  "reasons": ["Extreme hours (60) + stress (8): burnout risk"],
  "god": "queen"
}
```

---

### 3. **Odin** - Market Wisdom
**Purpose:** Cross-references market data and historical patterns.

**Blocking Rules:**
- ❌ Price > MAO + 10% (overpaying vs market average)
- ❌ Repairs cost > 30% of purchase price (renovation is too heavy)

**Endpoint:** `POST /api/governance/odin`

**Example Block:**
```json
{
  "allowed": false,
  "severity": "MEDIUM",
  "reasons": ["Purchase $285k exceeds MAO limit $275k by $10k"],
  "god": "odin"
}
```

---

### 4. **Loki** - Worst-Case Scenario
**Purpose:** Stress-tests downside risk and catastrophic loss probability.

**Blocking Rules:**
- ❌ Ruin probability > 25% (too likely to lose everything)
- ❌ Loss amount > purchase price (catastrophic downside)
- ❌ Months to break-even > holding period (can't recover in time)

**Endpoint:** `POST /api/governance/loki`

**Example Block:**
```json
{
  "allowed": false,
  "severity": "CRITICAL",
  "reasons": ["Ruin probability 45% exceeds 25% threshold"],
  "god": "loki"
}
```

---

### 5. **Tyr** - Legal Compliance
**Purpose:** Hard-stop on legal violations and ethical red flags.

**Blocking Rules:**
- ❌ Tax evasion flag = true (absolute dealbreaker)
- ❌ Money laundering flag = true (absolute dealbreaker)
- ❌ Anti-money laundering failure = true (regulatory violation)

**Endpoint:** `POST /api/governance/tyr`

**Example Block:**
```json
{
  "allowed": false,
  "severity": "CRITICAL",
  "reasons": ["Tax evasion detected: DISQUALIFIED"],
  "god": "tyr"
}
```

---

## System Architecture

### Layer 1: Individual God Routers
Each god has a dedicated FastAPI router that evaluates against its specific criteria.

**Files:**
- `app/routers/governance_king.py`
- `app/routers/governance_queen.py`
- `app/routers/governance_odin.py`
- `app/routers/governance_loki.py`
- `app/routers/governance_tyr.py`

**Pattern:**
```python
@router.post("/king", response_model=GovernanceDecision)
def evaluate_king(req: GovernanceEvaluationRequest) -> GovernanceDecision:
    # Extract data
    data = req.data
    # Evaluate against blocking rules
    if condition_fails:
        return GovernanceDecision(
            god="king",
            allowed=False,
            severity="CRITICAL",
            reasons=["violation reason"]
        )
    return GovernanceDecision(god="king", allowed=True, severity="NONE", reasons=[])
```

---

### Layer 2: Governance Orchestrator
Calls all five gods sequentially, aggregates decisions, and returns unified verdict.

**Endpoint:** `POST /api/governance/evaluate_all`

**Request:**
```json
{
  "context_type": "deal",
  "data": {
    "purchase_price": "250000",
    "arv": "340000",
    "repairs": "30000",
    "hours_per_week": "40",
    "stress_level": "5",
    "mao": "260000",
    "ruin_probability": "0.1",
    "loss_amount": "50000",
    "holding_months": "6",
    "tax_evasion": "false",
    "money_laundering": "false",
    "aml_failure": "false"
  },
  "gods": null  // null = evaluate all 5
}
```

**Response:**
```json
{
  "overall_allowed": true,
  "worst_severity": "NONE",
  "blocked_by": [],
  "checks": [
    {
      "god": "king",
      "allowed": true,
      "severity": "NONE",
      "reasons": []
    },
    // ... other gods ...
  ]
}
```

**File:** `app/routers/governance_orchestrator.py`

**Key Logic:**
- Calls all gods (or specified subset) in parallel via TestClient
- If ANY god blocks (allowed=false), overall_allowed=false
- Aggregates worst severity (CRITICAL > HIGH > MEDIUM > LOW > NONE)
- Returns full decision history for audit trail

---

### Layer 3: Governance-Gated Deal Pipeline
Gates real deal execution behind governance approval.

**Endpoint:** `POST /api/flow/full_deal_with_governance`

**Request:** Full deal payload with nested deal/underwriting/governance flags

**Workflow:**
1. Extract deal financials and governance flags
2. Calculate ROI = (ARV - price - repairs) / price
3. Build governance data dict (ALL values as strings - **critical**)
4. Call `/api/governance/evaluate_all`
5. **If governance rejects:** Return 409 CONFLICT with governance details
6. **If governance approves:** Call `/api/flow/full_deal_pipeline` and attach `_governance` snapshot

**Response on Rejection (409):**
```json
{
  "detail": {
    "message": "Governance blocked this deal.",
    "governance": {
      "overall_allowed": false,
      "worst_severity": "CRITICAL",
      "blocked_by": ["tyr"],
      "checks": [
        {
          "god": "tyr",
          "allowed": false,
          "severity": "CRITICAL",
          "reasons": ["Tax evasion detected: DISQUALIFIED"]
        }
        // ... other gods ...
      ]
    }
  }
}
```

**Response on Approval (200/201):**
```json
{
  "deal_id": 123,
  "lead_id": 456,
  // ... full pipeline response ...
  "_governance": {
    "overall_allowed": true,
    // ... governance snapshot ...
  }
}
```

**File:** `app/routers/flow_governance_gate.py` (155 lines)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────┐
│  POST /api/flow/full_deal_with_governance │
│  (Deal + Underwriting + Governance Flags) │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Extract Financials
        │ - Calculate ROI
        │ - Build Gov Data Dict
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────────────┐
        │ POST /governance/evaluate_all
        │ (Call All 5 Gods)
        └────────┬─────────────────┘
                 │
       ┌─────────┼──────────┬──────────┬─────────┐
       ▼         ▼          ▼          ▼         ▼
     KING     QUEEN       ODIN      LOKI      TYR
    ┌────┐   ┌────┐   ┌────┐   ┌────┐   ┌────┐
    │ROI │ │Life│ │Mkt │ │Risk│ │Legal│
    └────┘   └────┘   └────┘   └────┘   └────┘
       │         │       │        │       │
       └─────────┴───────┴────────┴───────┘
                 │
         ┌───────▼─────────┐
         │ Aggregate Result
         │ (all_allowed + worst_severity + blocked_by)
         └───────┬─────────┘
                 │
         ┌───────▼──────────────┐
         │ Check overall_allowed
         └─────────┬────────┬──────────┐
                   │        │          │
              FALSE│        │TRUE      └─────────┐
                   │        │                    │
         ┌─────────▼───┐    │        ┌───────────▼────┐
         │ Return 409  │    │        │Call /flow/full_
         │ (Governance)│    │        │deal_pipeline &
         │ CONFLICT    │    │        │Attach Gov Data
         └─────────────┘    │        └────────┬────────┘
                            │                 │
                            │        ┌────────▼──────┐
                            │        │Return 200/201
                            │        │(with success  │
                            │        │ data + _gov)  │
                            │        └───────────────┘
                            │
                            └──→ Request blocked, no action
```

---

## Test Coverage

### Individual Gods: 15 Tests ✅
- **King:** 3 tests (ROI boundaries, ARV violations)
- **Queen:** 3 tests (burnout, stress, months)
- **Odin:** 3 tests (MAO exceeded, repairs excessive)
- **Loki:** 3 tests (ruin probability, loss amount, break-even)
- **Tyr:** 3 tests (tax evasion, money laundering, AML)

### Orchestrator: 3 Tests ✅
- All gods called in sequence
- Worst severity aggregation
- Partial evaluation (specific gods)

### Governance Gate: 5 Tests ✅
- ✅ Clean deal passes governance (all gods approve)
- ✅ Tyr blocks tax evasion (hard-stop)
- ✅ Queen blocks burnout scenario (stress + hours)
- ✅ Loki blocks extreme downside (ruin probability)
- ✅ Governance snapshot attached for audit

**Total: 23/23 Tests Passing**

---

## Implementation Details

### Critical Pattern: String Conversion
All governance data values MUST be strings (Pydantic V2 requirement):

```python
gov_data = {
    "purchase_price": str(price_dec),  # "250000"
    "hours_per_week": str(hours),      # "40"
    "stress_level": str(stress),       # "5"
    "tax_evasion": str(bool(flag)),    # "False" or "True"
}
```

### Circular Import Avoidance
Use deferred imports in endpoint code:

```python
def _get_client():
    from app.main import app as main_app
    return TestClient(main_app)

@router.post("/king")
def evaluate_king(req: GovernanceEvaluationRequest):
    client = _get_client()  # Import only when called, not at module load
    # ... use client ...
```

### Decimal Arithmetic for ROI
Financial calculations use Decimal to avoid floating-point errors:

```python
roi = (arv - price - repairs) / price  # All Decimal objects
# Result: Decimal('0.316')  # 31.6% ROI
```

---

## HTTP Status Codes

| Status | Meaning | When |
|--------|---------|------|
| **201** | Deal Created | Governance approved + pipeline executed successfully |
| **200** | OK | Governance approved (pipeline not executed in some flows) |
| **409** | Conflict | Governance REJECTED deal (god blocked it) |
| **500** | Server Error | System error (governance rules misconfigured) |

---

## Gods Decision Matrix

| God | Severity | Hard Block? | Example Block |
|-----|----------|-------------|---------------|
| **King** | CRITICAL | Yes* | ROI < 15% |
| **Queen** | HIGH | Yes* | Burnout risk |
| **Odin** | MEDIUM | Yes* | Repairs > 30% |
| **Loki** | CRITICAL | Yes* | Ruin prob > 25% |
| **Tyr** | CRITICAL | YES (absolute) | Tax evasion |

*Any blocked god causes overall rejection (409)
Tyr's blocks are absolute dealbreakers (non-negotiable)

---

## Next Steps & Extensions

### Currently Ready
- ✅ Full 5-god evaluation system
- ✅ Orchestrator combining all decisions
- ✅ Governance gate blocking unapproved deals
- ✅ Audit trail via governance snapshot

### Available for Future Work
1. **God Customization:** Adjustable thresholds per user/region
2. **Appeal Workflow:** Re-evaluate with waived criteria
3. **Audit Logging:** Record all governance decisions to database
4. **Metrics Dashboard:** Track approval rates by god
5. **Machine Learning:** Predict approval likelihood before submission
6. **A/B Testing:** Compare different god configurations

---

## File Structure

```
services/api/
├── app/
│   ├── routers/
│   │   ├── governance_king.py       # Valuation discipline
│   │   ├── governance_queen.py      # Lifestyle protection
│   │   ├── governance_odin.py       # Market wisdom
│   │   ├── governance_loki.py       # Downside risk
│   │   ├── governance_tyr.py        # Legal compliance
│   │   ├── governance_orchestrator.py # Call all 5
│   │   └── flow_governance_gate.py  # Gate deal pipeline
│   ├── schemas/
│   │   └── governance.py            # Pydantic models
│   └── main.py                      # Router registration
└── tests/
    ├── test_governance_king.py
    ├── test_governance_queen.py
    ├── test_governance_odin.py
    ├── test_governance_loki.py
    ├── test_governance_tyr.py
    ├── test_governance_orchestrator.py
    └── test_flow_governance_gate.py
```

---

## Summary

The Valhalla governance system turns the pantheon from evaluators into enforcers. Five gods with different expertise (valuation, lifestyle, market, risk, legal) work together:

1. **King** ensures profitable deals
2. **Queen** protects team well-being
3. **Odin** grounds in market reality
4. **Loki** stress-tests catastrophic risk
5. **Tyr** enforces legal boundaries

When ANY god objects, the deal is **rejected at 409 CONFLICT** before pipeline execution. When all approve, the deal proceeds with governance metadata attached for audit.

**The gods don't just talk—they govern.**
