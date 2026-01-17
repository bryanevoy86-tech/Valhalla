# The Complete Pantheon: Five Gods + Orchestrator

## System Architecture

You now have a **complete governance system** for Valhalla consisting of five independent evaluation engines orchestrated through a single decision interface.

```
┌─────────────────────────────────────────────────────────────┐
│         Governance Orchestrator                             │
│       POST /api/governance/evaluate_all                     │
│  (Calls all gods, returns aggregated decision)              │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┼────────┬─────────┬──────────┐
         │       │        │         │          │
         ▼       ▼        ▼         ▼          ▼
      
      KING      QUEEN    ODIN     LOKI       TYR
      ════      ════     ════     ════       ════
      
   Risk/ROI   Energy/  Vertical  Downside/  Legal/
   Mission    Family   Focus     Ruin       Ethics
   Values     Burnout  Strategy  Correlation Hard-
                                 Complexity  Stops
      │       │        │         │          │
      └───────┼────────┼─────────┼──────────┘
              │
              ▼
        KingDecision
        (reused schema)
        
      .allowed (bool)
      .severity (info/warn/critical)
      .reasons (list)
      .notes (str)
```

## The Five Gods

### 1. KING - Risk & Mission Alignment
**File**: `services/api/app/routers/governance_king.py`

**Evaluates:**
- Investment size (max $500k without override)
- Return on Investment (min 12% expected)
- Repair/Unknown risk (max 30% of purchase)
- Ethical compliance (no predatory tactics)
- Mission alignment (cashflow vs equity vs speed)

**Severities:**
- ✓ info: Approved as-is
- ⚠️ warn: Approved but flagged for review
- ✗ critical: Denied (predatory or extreme risk)

**Typical Decision**: "King approves this deal. ROI is 20%, repairs are manageable, and mission-aligned."

---

### 2. QUEEN - Energy & Family Protection
**File**: `services/api/app/routers/governance_queen.py`

**Evaluates:**
- Hours per week (40h preferred, 55h hard cap)
- Parallel projects (3 max, 2 ideal)
- Evening/weekend protection (family time)
- Stress level (1-7 ok, 8+ problematic, 9-10 critical)
- Sprint duration (2-4 weeks ok, 5+ weeks unsustainable)

**Severities:**
- ✓ info: Sustainable workload
- ⚠️ warn: High hours but manageable
- ✗ critical: Unsustainable/burnout risk

**Typical Decision**: "Queen approves this sprint. 35 hours/week is healthy, no weekend work, stress is moderate."

---

### 3. ODIN - Vertical Strategy & Focus
**File**: `services/api/app/routers/governance_odin.py`

**Evaluates:**
- Active verticals count (max 5, ideal 2-3)
- Profit vs complexity (high profit + low complexity = good)
- Time to break-even (target 12-18 months)
- Mission criticality (core business vs distraction)
- Complexity score (1-10 scale)

**Severities:**
- ✓ info: Strategic alignment, clear value
- ⚠️ warn: Marginal project, borderline focus
- ✗ critical: Distraction, vertical overload, or unclear ROI

**Typical Decision**: "Odin approves this vertical. You have 2 active, this is high-profit, and breaks even in 14 months."

---

### 4. LOKI - Worst-Case Risk & Ruin Probability
**File**: `services/api/app/routers/governance_loki.py`

**Evaluates:**
- Worst-case loss vs capital at risk (max 1.5x multiplier)
- Probability of going to zero (max 5%)
- Portfolio correlation/entanglement (max 80%)
- Hidden complexity (unknown unknowns, 1-10 scale)

**Severities:**
- ✓ info: Modest downside, portfolio healthy
- ⚠️ warn: Borderline downside, manageable correlation
- ✗ critical: Extreme downside/ruin probability

**Typical Decision**: "Loki approves this deal. Worst case is 60k loss on 80k capital, ruin probability is 2%, correlation is 50%."

---

### 5. TYR - Legal & Ethical Hard-Stops
**File**: `services/api/app/routers/governance_tyr.py`

**Evaluates:**
- Legal violations (unlicensed practice, tax evasion, fraud, illegal recording)
- Ethical violations (exploiting vulnerable people, misleading marketing, incomplete disclosures)

**Severities:**
- ✓ info: All clear, no legal/ethical concerns
- ✗ critical: ANY violation = automatic HARD DENY (no warnings, no exceptions)

**Typical Decision**: 
- ✓ "Tyr sees no legal or ethical red-line violations."
- ✗ "Tyr rejects this. Tax evasion is a hard-line violation."

**KEY**: Tyr is the ONLY god that never warns. Violations are always critical denials.

---

## The Orchestrator - Unified Decision Engine

**File**: `services/api/app/routers/governance_orchestrator.py`

**Endpoint**: `POST /api/governance/evaluate_all`

**What it does:**
1. Takes a single request with context data
2. Calls all 5 gods (or a subset if specified)
3. Tracks worst severity across all gods
4. Identifies any critical denials
5. Returns unified decision + per-god details

**Response Schema** (`GovernanceAggregateDecision`):
```json
{
  "overall_allowed": true,
  "worst_severity": "warn",
  "blocked_by": [],
  "checks": [
    { "god": "king", "allowed": true, "severity": "info", ... },
    { "god": "queen", "allowed": true, "severity": "warn", ... },
    { "god": "odin", "allowed": true, "severity": "info", ... },
    { "god": "loki", "allowed": true, "severity": "info", ... },
    { "god": "tyr", "allowed": true, "severity": "info", ... }
  ],
  "summary": "Plan allowed with warnings. Worst severity: warn. No hard blocks from any god."
}
```

---

## Usage Patterns

### Pattern 1: Check a Deal Before Execution
```python
payload = {
    "context_type": "deal",
    "data": deal.to_dict(),
    "gods": None  # Check all 5
}
result = client.post("/api/governance/evaluate_all", json=payload).json()
if result["overall_allowed"]:
    execute_deal(deal)
else:
    notify_user(f"Deal blocked by: {result['blocked_by']}")
```

### Pattern 2: Validate New Vertical Addition
```python
payload = {
    "context_type": "new_vertical",
    "data": {
        "active_verticals": "3",
        "new_verticals": "1",
        "estimated_annual_profit": "150000",
        "distraction_score": "5"
    },
    "gods": ["odin", "queen"]  # Odin knows verticals, Queen knows capacity
}
result = client.post("/api/governance/evaluate_all", json=payload).json()
```

### Pattern 3: Pre-Check Before Heimdall Autonomous Build
```python
payload = {
    "context_type": "build_request",
    "data": build_request.to_dict(),
    "gods": ["king", "tyr"]  # King for feasibility, Tyr for legality
}
result = client.post("/api/governance/evaluate_all", json=payload).json()
if result["overall_allowed"]:
    heimdall.build(build_request)  # Only proceed if governance passes
```

---

## Key Guarantees

✅ **All Gods Must Approve** (except warnings are OK)
- Tyr's hard-stops block everything
- Critical from any god blocks overall decision
- Warnings allow execution but flag for review

✅ **Consistent Schema**
- All gods use same `KingEvaluationContext` input
- All return `KingDecision` output
- Orchestrator combines these into `GovernanceAggregateDecision`

✅ **Independent Gods**
- Each evaluates independently (no cross-talk)
- Each has own policy configuration
- Can be called individually or via orchestrator

✅ **Clear Audit Trail**
- Every god's decision is logged in response
- Severity tracking across pantheon
- Summary explains final decision

---

## Test Coverage

```
✓ 3/3 King tests (good deals, warnings, denials)
✓ 3/3 Queen tests (sane workload, high hours, burnout)
✓ 3/3 Odin tests (strong vertical, marginal, distraction)
✓ 3/3 Loki tests (modest downside, borderline, extreme)
✓ 3/3 Tyr tests (clean action, legal violation, ethical violation)
✓ 3/3 Orchestrator tests (all gods, hard-block, subset)

Total: 25/25 tests passing ✓
```

---

## Integration Roadmap

### Phase 1 (Now) ✓
- 5 independent gods implemented and tested
- Orchestrator fully functional
- All routes registered and accessible

### Phase 2 (Next)
- Wire into deal pipeline
- Add governance gate before deal execution
- Log all governance decisions

### Phase 3 (Later)
- Heimdall integration (governance check before autonomous builds)
- Profit allocation governance (Tyr checks before distribution)
- Portfolio rebalancing governance (multi-god approval)

---

## The Philosophy

**Heimdall cannot be allowed to self-modify or build new modules without governance.**

The five gods implement this philosophy:
- **King** ensures financial soundness
- **Queen** protects human sustainability
- **Odin** maintains strategic focus
- **Loki** guards against catastrophic loss
- **Tyr** enforces legal and ethical boundaries

Together they form a **governance spine** that prevents reckless autonomous action while allowing safe innovation.

---

## All Available Endpoints

```
POST /api/governance/king/evaluate
POST /api/governance/queen/evaluate
POST /api/governance/odin/evaluate
POST /api/governance/loki/evaluate
POST /api/governance/tyr/evaluate
POST /api/governance/evaluate_all        ← Main orchestrator endpoint
```

All endpoints accept the same input schema:
```json
{
  "context_type": "string",
  "data": { "key": "value", ... }
}
```

All return the same output schema (individual gods return `KingDecision`, orchestrator returns `GovernanceAggregateDecision`).

---

## Next: Connect to Your Business Logic

The pantheon is ready. Now integrate it into:
1. Deal approval workflow
2. Profit distribution
3. Heimdall autonomous operations
4. Portfolio rebalancing
5. New vertical creation

Each integration point simply calls `/api/governance/evaluate_all` with appropriate context data.
