# Deal Stage Rules - Sprint 2 Core Pipeline

**Status**: ✅ DEFINED & IMPLEMENTED  
**Implementation**: Enforced in `services/api/app/deals/service.py` via `update_deal_stage()`

---

## Stage Definitions

### Deal Lifecycle: 11 Named Stages

```
lead_received → intake_review → underwrite_ready → offer_ready → offer_sent → 
contract_pending → contract_signed → buyer_matching → dispo_ready → closed → dead
```

| Stage | Duration | Owner | Purpose |
|-------|----------|-------|---------|
| **lead_received** | Entry | Intake | Lead converted to deal record |
| **intake_review** | 1 day | Underwriter | Initial property/deal review |
| **underwrite_ready** | 3-5 days | Underwriter | Financials vetted, ready to make offer |
| **offer_ready** | Same day | System/Admin | Offer generated & reviewed |
| **offer_sent** | 24-48 h | Admin | Offer delivered to seller/agent |
| **contract_pending** | 3-5 days | Legal | Offer accepted, contract drafted |
| **contract_signed** | 1 day | Admin | All parties signed contract |
| **buyer_matching** | 2-7 days | Matching engine | Matching buyers to deal |
| **dispo_ready** | Same day | Admin | Deal assigned/ready to close |
| **closed** | Exit | System | Money received, deal complete |
| **dead** | Terminal | System | Deal rejected/expired (no recovery) |

---

## Allowed Transitions (State Machine)

### Forward Transitions (Happy Path)

From `lead_received`:
- ✅ to `intake_review` — Processing begins
- ✅ to `dead` — Reject immediately (bad lead)

From `intake_review`:
- ✅ to `underwrite_ready` — Underwriting complete
- ✅ to `dead` — Failed underwriting

From `underwrite_ready`:
- ✅ to `offer_ready` — Offer created
- ✅ to `dead` — Deal fails financial test

From `offer_ready`:
- ✅ to `offer_sent` — Offer delivered
- ✅ to `dead` — Offer rejected

From `offer_sent`:
- ✅ to `contract_pending` — Offer accepted
- ✅ to `dead` — Offer expired/withdrawn

From `contract_pending`:
- ✅ to `contract_signed` — Contract executed
- ✅ to `dead` — Negotiation failed

From `contract_signed`:
- ✅ to `buyer_matching` — Begin buyer search
- ✅ to `dead` — Deal falls through (inspections, etc)

From `buyer_matching`:
- ✅ to `dispo_ready` — Buyer matched
- ✅ to `dead` — No qualified buyer found

From `dispo_ready`:
- ✅ to `closed` — Deal assigned/closes
- ✅ to `dead` — Assignment failed

From `closed`:
- ✅ to `dead` — De-assignment or recovery needed

From `dead`:
- ❌ No transitions allowed (terminal state)

### Blocked Transitions (Will Raise ValueError)

Any transition not listed in allowed_transitions above will be rejected with:
```
ValueError: "Cannot transition from {old_stage} to {new_stage}"
```

Example rejected transitions:
- `lead_received` → `offer_ready` (must go through intake first)
- `contract_signed` → `offer_sent` (cannot reverse)
- `closed` → `contract_pending` (no recover to mid-pipeline)
- `dead` → anything (terminal)

---

## Override Mechanism

### Controlled Override with Logging

If a transition violates stage rules but is necessary:

```python
# From FastAPI endpoint
stage_update = DealStageUpdate(
    new_stage="closed",
    override_reason="Emergency closure - buyer approved override due to funding deadline"
)

# Service enforces:
# 1. Check if transition is valid
# 2. If NOT valid but override_reason provided:
#    - Log warning to console
#    - Create audit_logs entry with override_reason
#    - PROCEED with the transition
# 3. If NOT valid and NO override_reason:
#    - Reject with ValueError
```

### Expected Use Cases for Override

- Emergency manual intervention (legal/compliance requirement)
- Correction of data entry error
- Recovery from stuck/orphaned deals
- Management override for operational reasons

### Audit Trail

Every stage transition (including overrides) is logged to `deal_stage_history` table:

```sql
INSERT INTO deal_stage_history (
    deal_id,
    old_stage,
    new_stage,
    override_reason,
    created_at
) VALUES (
    {deal_id},
    '{old_stage}',
    '{new_stage}',
    '{override_reason}',  -- NULL if normal transition
    NOW()
);
```

---

## API Usage (HTTP Endpoints)

### Normal Stage Transition

```bash
PATCH /api/deals/{deal_id}/stage
Content-Type: application/json

{
  "new_stage": "offer_ready"
}
```

Response: 200 OK
```json
{
  "id": 42,
  "deal_id": 42,
  "stage": "offer_ready",
  "updated_at": "2026-03-26T15:30:00"
}
```

### Invalid Stage Transition (Rejected)

```bash
PATCH /api/deals/42/stage

{
  "new_stage": "offer_sent"
}
```

Response: 400 Bad Request
```json
{
  "detail": "Cannot transition from offer_ready to offer_sent"
}
```

### Override Transition

```bash
PATCH /api/deals/42/stage

{
  "new_stage": "closed",
  "override_reason": "Legal override - funding deadline emergency"
}
```

Response: 200 OK (proceeds despite violating normal rules)

---

## Implementation Details

### Transition Check (services/api/app/deals/service.py)

```python
ALLOWED_STAGE_TRANSITIONS = {
    "lead_received": ["intake_review", "dead"],
    "intake_review": ["underwrite_ready", "dead"],
    # ... etc
}

def update_deal_stage(db, deal_id, stage_update):
    old_stage = db_deal.stage
    new_stage = stage_update.new_stage
    
    allowed = ALLOWED_STAGE_TRANSITIONS.get(old_stage, [])
    if new_stage not in allowed:
        if not stage_update.override_reason:
            raise ValueError(f"Cannot transition from {old_stage} to {new_stage}")
        print(f"WARNING: Override applied: {override_reason}")
    
    # Log to deal_stage_history
    # Update deal.stage
    # Commit
```

---

##Enforced Business Rules

### Rule 1: No Backward Steps
- Cannot move from `contract_signed` back to `offer_sent`
- Deals only move forward (or to dead)
- Recovery must use override

### Rule 2: Terminal Dead State
- Once in `dead`, deal cannot be revived
- Dead deals are archived, never reactivated
- No transitions allowed from `dead`

### Rule 3: Linear Progress (No Shortcuts)
- Cannot skip from `lead_received` directly to `offer_sent`
- Must go through underwriting
- Enforces deal quality gates

### Rule 4: Override Visibility
- Every override is logged with reason
- Audit trail shows who/when overrode
- Enables post-mortems and governance

---

## Testing & Validation

### Test Cases in `tests/test_smoke_core_pipeline.py`

```python
# Normal forward transition
def test_lead_to_intake():
    deal = create_deal(stage="lead_received")
    assert update_stage(deal, "intake_review") == "intake_review"

# Blocked backward transition
def test_backward_blocked():
    deal = create_deal(stage="contract_signed")
    with pytest.raises(ValueError, match="Cannot transition"):
        update_stage(deal, "offer_sent")

# Valid alternative (death)
def test_any_stage_to_dead():
    for stage in ALL_STAGES:
        deal = create_deal(stage=stage)
        assert update_stage(deal, "dead") == "dead"

# Override allows rule violation
def test_override_bypasses_rule():
    deal = create_deal(stage="offer_ready")
    assert update_stage(
        deal, "closed", 
        override_reason="Emergency"
    ) == "closed"

# Dead is truly terminal
def test_dead_terminal():
    deal = create_deal(stage="dead")
    with pytest.raises(ValueError):
        update_stage(deal, "closed")
```

---

## Future Enhancements (Post-Sprint-2)

- Add time-based auto-progression (e.g., auto close after 30 days in `dispo_ready`)
- Add notifications on stage transitions
- Add conditional rules (e.g., "can only close if contract exists")
- Add role-based stage restrictions (e.g., "only Underwriter can update to underwrite_ready")
- Add stage-specific required fields (e.g., "contract_id required to enter contract_signed")

---

**Status**: Ready for Sprint 2 smoke tests  
**File**: `services/api/app/deals/service.py` - Line 23 (ALLOWED_STAGE_TRANSITIONS)
