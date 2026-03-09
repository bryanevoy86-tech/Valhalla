# ENGINE ACTIVATION GOVERNOR - DETERMINISTIC PROMOTION

## What This Is

A **state machine** that locks down engine promotion. No emotional decisions. No "are we ready?" debates. Just metrics.

---

## Architecture

### 1. Engine Readiness Table

Tracks the state of every engine:

```
+-----------+--------+-------+-------+-------+
| Engine    | State  | Appr% | FP%   | N     |
+-----------+--------+-------+-------+-------+
| wholesale | READY  | 80%   | 8%    | 28    |
| arbitrage | SANDBOX| null  | null  | 0     |
| trading   | DISABLED| null | null  | 0     |
+-----------+--------+-------+-------+-------+
```

**States**:
- `DISABLED` - Engine off
- `SANDBOX` - Testing, effects blocked
- `READY` - Metrics qualify, awaiting promotion
- `LIVE` - Production execution

### 2. Readiness Rules

Each engine has specific thresholds:

```python
ENGINE_RULES = {
    "wholesaling": {
        "min_samples": 20,           # Must have 20+ decisions
        "max_fp_rate": 0.10,         # FP rate must be ≤ 10%
        "min_approval_rate": 0.75,   # Approval rate must be ≥ 75%
    },
    "arbitrage": {
        "min_samples": 30,
        "min_roi": 0.03,             # 3% minimum ROI
    },
    "trading_advisory": {
        "min_samples": 50,
        "max_drawdown": 0.05,        # 5% max drawdown
    },
}
```

### 3. Promotion Order (STRICT)

Enforced by code:

```
1. Wholesaling must reach LIVE first
2. Then arbitrage can be promoted
3. Then trading_advisory
```

Reason: Sequential validation prevents downstream issues.

### 4. Automatic Evaluation Job

Runs daily (or on-demand):

```
FOR each SANDBOX engine:
  IF metrics pass thresholds:
    state = READY
  ELSE:
    stay SANDBOX (keep testing)
```

### 5. Manual Promotion (Rare)

You promote READY → LIVE when confident:

```
POST /api/governance/engines/{engine}/promote
```

Preconditions:
- Engine must be READY
- Previous engines must be LIVE
- Enforcement is built-in

---

## How It Works

### Day 1: Initial State

```
curl -X GET https://api/api/governance/engines/readiness \
  -H "X-API-Key: YOUR_KEY"

Response:
{
  "engine_name": "wholesaling",
  "state": "SANDBOX",        ← Testing
  "approval_rate": null,
  "false_positive_rate": null,
  "sample_size": 0
}
```

### Days 1-7: Collect Decisions

You label items, system learns:

```
- Day 1: 2 labels → sample_size=2
- Day 2: 5 labels → sample_size=7
- Day 3: 8 labels → sample_size=15
- Day 4: 5 labels → sample_size=20 ✓ (min_samples met)
```

Metrics update via learning report:

```
approval_rate: 0.80 (80%)    ✓ (need 75%)
false_positive_rate: 0.08   ✓ (need ≤10%)
```

### Day 4-7: Auto-Evaluation

You run evaluation endpoint OR it runs on scheduler:

```
POST /api/governance/engines/wholesaling/evaluate

Response:
{
  "status": "promoted_to_ready",
  "samples": 20,
  "approval_rate": 0.80,
  "fp_rate": 0.08
}

Database updates:
  state: SANDBOX → READY
```

### Day 8: Manual Promotion

You decide to go LIVE:

```
POST /api/governance/engines/wholesaling/promote

Response:
{
  "ok": true,
  "engine": "wholesaling",
  "new_state": "LIVE"
}
```

### Day 8+: Production Execution

Now wholesaling executes for real:

1. User calls `/api/notify/email`
2. Guard checks: `require_engine_live(db, "wholesaling")`
3. If state is LIVE → execute
4. If state is not LIVE → throw 409 error, don't execute

```json
{
  "status_code": 409,
  "detail": {
    "title": "EngineNotLive",
    "message": "Engine 'wholesaling' not LIVE (current state: SANDBOX)"
  }
}
```

---

## API Endpoints

### List All Engines

```
GET /api/governance/engines/readiness

Response:
[
  {
    "engine_name": "wholesaling",
    "state": "READY",
    "approval_rate": 0.80,
    "false_positive_rate": 0.08,
    "sample_size": 20
  },
  ...
]
```

### Evaluate Specific Engine

```
POST /api/governance/engines/{engine_name}/evaluate

Response:
{
  "engine": "wholesaling",
  "evaluation": {
    "status": "promoted_to_ready",
    "samples": 20,
    "approval_rate": 0.80,
    "fp_rate": 0.08
  }
}
```

### Promote to LIVE (Manual)

```
POST /api/governance/engines/{engine_name}/promote

Preconditions:
- Engine must be READY (will verify and reject if not)
- Previous engines must be LIVE (will verify)

Response:
{
  "ok": true,
  "engine": "wholesaling",
  "new_state": "LIVE"
}
```

### Revert to SANDBOX (Testing Mode)

```
POST /api/governance/engines/{engine_name}/sandbox

Response:
{
  "ok": true,
  "engine": "wholesaling",
  "new_state": "SANDBOX"
}
```

### Disable Engine (Emergency)

```
POST /api/governance/engines/{engine_name}/disable

Response:
{
  "ok": true,
  "engine": "wholesaling",
  "new_state": "DISABLED"
}
```

---

## Integration Points

### 1. Notify Router (Outreach Execution)

```python
from app.core.engine_guard import require_engine_live

@router.post("/email")
def queue_email(payload, db):
    # First check: SANDBOX block (if applicable)
    try:
        enforce_engine("wholesaling", OUTREACH)
    except HTTPException as e:
        if e.status_code == 409:
            # Queue for approval
            return {...}
        raise
    
    # Second check: Governance (must be LIVE)
    require_engine_live(db, "wholesaling")  # ← HARD BLOCK if not LIVE
    
    # Now safe to execute
    Outbox(kind="email", ...)
```

### 2. Learning Report Updates Metrics

When you label items, metrics update:

```python
# In learning report:
{
  "quality_metrics": {
    "approval_rate": 0.80,         ← Updated
    "false_positive_rate": 0.08    ← Updated
  },
  "queue_metrics": {
    "sample_size": 20
  }
}
```

Then evaluation job reads these and promotes if ready.

### 3. Migration Creates Table

```sql
CREATE TABLE engine_readiness (
  id INTEGER PRIMARY KEY,
  engine_name VARCHAR(64) UNIQUE NOT NULL,
  state VARCHAR(16) NOT NULL DEFAULT 'DISABLED',
  approval_rate FLOAT,
  false_positive_rate FLOAT,
  sample_size INTEGER,
  evaluated_at TIMESTAMP
);
```

### 4. Seeding Sets Safe Defaults

Run after migration:

```bash
python -m services.api.scripts.seed_engine_readiness
```

Initializes:

```
wholesaling → SANDBOX
arbitrage → DISABLED
trading_advisory → DISABLED
```

---

## What This Prevents

❌ **Accidental early launch** - Guard checks state before execution
❌ **Arbitrage before wholesaling** - Promotion order enforced
❌ **Manual guessing** - Metrics are the source of truth
❌ **Regression without noticing** - State machine is explicit

---

## Workflow Example (7-Day Plan)

### Day 1-3: Collect Labels
- Run comprehensive test
- Label 5-10 items (good/bad/borderline)
- Approval rate starts climbing: 60% → 70%

### Day 4: Hit Thresholds
- 20+ labels collected
- Approval rate: 80%
- False positive rate: 8%
- Run: `POST /api/governance/engines/wholesaling/evaluate`
- Response: `"status": "promoted_to_ready"`
- State: SANDBOX → READY

### Day 5-7: Verify Stability
- No new issues in queue
- Metrics stay above thresholds
- Confidence high

### Day 8: Go Live
- Run: `POST /api/governance/engines/wholesaling/promote`
- State: READY → LIVE
- All future `/api/notify/email` calls now execute in production
- No more SANDBOX blocks for outreach

---

## Troubleshooting

### "Engine not LIVE" error

```
{
  "status_code": 409,
  "detail": {
    "title": "EngineNotLive",
    "message": "Engine 'wholesaling' not LIVE (current state: SANDBOX)"
  }
}
```

**Why**: Engine is not promoted yet.

**Fix**: 
1. Check readiness: `GET /api/governance/engines/readiness`
2. If READY, promote: `POST .../wholesaling/promote`
3. If SANDBOX, run evaluation: `POST .../wholesaling/evaluate`

### "Engine not READY" error

```
{
  "status_code": 409,
  "detail": "Engine not READY (current state: SANDBOX). Evaluate first."
}
```

**Why**: Can't promote SANDBOX directly to LIVE.

**Fix**: Must go through evaluation to reach READY state first.

### Promotion order violation

```
{
  "status_code": 409,
  "detail": "Arbitrage cannot go LIVE until wholesaling is LIVE"
}
```

**Why**: Sequential validation enforced.

**Fix**: Promote wholesaling first.

---

## Key Files

| File | Purpose |
|------|---------|
| `models/engine_readiness.py` | State machine table |
| `governance/engine_rules.py` | Thresholds per engine |
| `jobs/engine_readiness_job.py` | Evaluation logic |
| `core/engine_guard.py` | Promotion guard (used in routes) |
| `api/governance/router.py` | REST endpoints |
| `scripts/seed_engine_readiness.py` | Initial setup |
| `alembic/versions/20260203_engine_readiness.py` | Migration |

---

## Philosophy

This system embodies one principle:

**Engines cannot execute in production until metrics prove they're safe.**

No exceptions. No manual overrides without checks. No "we'll watch it closely."

The code decides. Metrics decide. You execute the decision.

---

## Success

By following this:

✅ No blowups from premature launch
✅ Wholesaling proven before other engines start
✅ Arbitrage can follow quickly (only needs samples)
✅ Trading only goes live after clear stability
✅ Historical record of when/why each engine launched
✅ Simple rollback: `POST .../sandbox` reverts to testing

This is how you scale safely.
