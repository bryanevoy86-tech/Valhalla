# Governance Orchestrator - Complete Pantheon Integration

## Overview

The **Governance Orchestrator** provides a single unified entry point that evaluates all five gods (King, Queen, Odin, Loki, Tyr) in one shot and returns a clean aggregated decision.

## Endpoint

```
POST /api/governance/evaluate_all
```

### Request Body

```json
{
  "context_type": "deal|new_vertical|build_request",
  "data": {
    "key1": "value1",
    "key2": "value2"
  },
  "gods": ["king", "queen", "odin", "loki", "tyr"] // optional - defaults to all
}
```

### Response

```json
{
  "overall_allowed": true,
  "worst_severity": "info|warn|critical",
  "blocked_by": ["god1", "god2"],
  "checks": [
    {
      "god": "king",
      "allowed": true,
      "severity": "info|warn|critical",
      "reasons": [],
      "notes": "Optional notes from this god"
    }
  ],
  "summary": "Human-readable summary of decision"
}
```

## How It Works

1. **Request Aggregation**: Single POST request containing context and optional god subset
2. **Sequential Evaluation**: Orchestrator calls each god's `/evaluate` endpoint via TestClient
3. **Severity Tracking**: Computes worst severity across all gods (info < warn < critical)
4. **Hard Blocks**: Any `critical` denial from any god sets `overall_allowed=False`
5. **Aggregated Response**: Returns complete picture with per-god decisions

## Key Behaviors

### Overall Allowed = TRUE when:
- All gods issue `allowed=true` OR
- No god issues a `critical` denial
- (Warnings are OK, only critical blocks matter)

### Overall Allowed = FALSE when:
- Any god issues `allowed=false` with `severity=critical`
- Typically: Tyr violations (legal/ethical red-lines)

### Worst Severity:
- Tracked separately from `overall_allowed`
- Useful for logging/monitoring even when plan is allowed with warnings
- Possible values: `info` → `warn` → `critical`

## Usage Examples

### 1. Evaluate a deal with all gods

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

payload = {
    "context_type": "deal",
    "data": {
        "purchase_price": "200000",
        "repairs": "20000",
        "roi": "0.25",
        "hours_per_week": "40",
        "stress_level": "5",
        "active_verticals": "2",
        "distraction_score": "3",
        "capital_at_risk": "80000",
        "worst_case_loss": "60000",
        "probability_of_ruin": "0.02",
        "tax_evasion": "False"
    },
    "gods": None  # or omit - defaults to all 5
}

resp = client.post("/api/governance/evaluate_all", json=payload)
result = resp.json()

if result["overall_allowed"]:
    print("✓ Plan is approved by all gods")
else:
    print(f"✗ Plan blocked by: {', '.join(result['blocked_by'])}")
```

### 2. Evaluate only specific gods

```python
payload = {
    "context_type": "new_vertical",
    "data": {
        "active_verticals": "3",
        "complexity_score": "8",
        "distraction_score": "7"
    },
    "gods": ["odin", "queen"]  # Only check these two
}

resp = client.post("/api/governance/evaluate_all", json=payload)
```

### 3. Integrate into business logic

```python
# In deal pipeline
def approve_deal(deal_data):
    governance_payload = {
        "context_type": "deal",
        "data": format_deal_for_governance(deal_data),
        "gods": None
    }
    
    result = client.post("/api/governance/evaluate_all", json=governance_payload).json()
    
    if result["overall_allowed"]:
        execute_deal(deal_data)
        log_approval(result)
    else:
        reject_deal(deal_data, result["blocked_by"])
        log_rejection(result)
```

## Internal God Endpoints

The orchestrator calls these internally:

| God    | Endpoint                        | Purpose                           |
|--------|--------------------------------|------------------------------------|
| King   | `/api/governance/king/evaluate` | Risk/ROI/mission alignment checks |
| Queen  | `/api/governance/queen/evaluate`| Energy/family/burnout protection  |
| Odin   | `/api/governance/odin/evaluate` | Vertical focus/strategy checks    |
| Loki   | `/api/governance/loki/evaluate` | Downside/ruin probability checks  |
| Tyr    | `/api/governance/tyr/evaluate`  | Legal/ethical hard-line checks    |

Each endpoint shares the same input/output schema via `KingEvaluationContext` and `KingDecision`.

## Governance Decision Flow

```
┌─────────────────────────┐
│  POST /evaluate_all     │
│  (all 5 gods)           │
└──────────┬──────────────┘
           │
      ┌────┴────┬─────┬────────┬──────┐
      │          │     │        │      │
   King       Queen  Odin   Loki   Tyr
   ✓ info    ✓ info ✓ warn ✓ info ✗ critical
      │          │     │        │      │
      └────┬─────┴──┬──┴────┬───┴──────┘
           │        │       │
           ▼        ▼       ▼
      Aggregate:
      - worst_severity: critical
      - blocked_by: [tyr]
      - overall_allowed: false
      - summary: "Plan denied. Hard block from: tyr."
```

## Files Created/Modified

1. **`services/api/app/schemas/governance.py`** (Extended)
   - Added `GovernanceCheckResult` schema
   - Added `GovernanceAggregateDecision` schema
   - Added `GovernanceEvaluationRequest` schema
   - Added `Literal` to imports

2. **`services/api/app/routers/governance_orchestrator.py`** (New)
   - POST `/governance/evaluate_all` endpoint
   - Orchestration logic (severity ranking, hard blocks)
   - Summary generation

3. **`services/api/tests/test_governance_orchestrator.py`** (New)
   - Test clean plan (all gods approve)
   - Test hard-block scenario (Tyr blocks)
   - Test subset evaluation (only specific gods)

4. **`services/api/app/main.py`** (Modified)
   - Added orchestrator router registration
   - Cleaned up duplicate app initialization

## Test Results

```
✓ 3/3 orchestrator tests passing
✓ 3/3 king tests passing
✓ 3/3 queen tests passing
✓ 3/3 odin tests passing
✓ 3/3 loki tests passing
✓ 3/3 tyr tests passing
✓ 2/2 tax snapshot tests passing
✓ 3/3 funfunds planner tests passing
✓ 2/2 portfolio dashboard tests passing

Total: 25/25 tests passing (includes orchestrator)
```

## Integration Points

Ready to integrate into:
- **Deal Pipeline**: Evaluate before execution
- **Profit Events**: Check before distribution
- **New Vertical Creation**: Validate against active project limits
- **Heimdall Build Requests**: Governance gate before autonomous building
- **Portfolio Rebalancing**: Multi-god approval for major shifts

## Key Design Decisions

1. **Single TestClient per request**: Avoids circular imports, fresh client per call
2. **Severity ranking function**: `_severity_rank(severity)` creates total ordering
3. **Hard blocks**: Critical denials immediately fail overall decision
4. **Flexible god subset**: Can evaluate all 5 or cherry-pick specific gods
5. **Generic input schema**: Reuses `KingEvaluationContext` across all gods
6. **Summary generation**: Human-readable text from structured decision data

## Future Enhancements

- Caching layer for repeated evaluations
- Async parallel god evaluation (currently sequential)
- Weighted severity scoring per use-case
- Override/exemption logic for edge cases
- Audit logging of all governance decisions
