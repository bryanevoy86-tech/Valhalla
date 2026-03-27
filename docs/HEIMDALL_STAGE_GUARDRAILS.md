# HEIMDALL STAGE GUARDRAILS

**Purpose:** Define valid deal stage transitions, requirements, and constraints

**Date:** March 26, 2026  
**Version:** Heimdall v0.1

---

## STAGE DEFINITIONS

### Stage: `draft`
**Description:** Initial deal state (usually not visible in UI)  
**Triggers:** Deal created but not yet qualified  
**Requirements:** None  
**Valid transitions:** → `lead_received`  
**What operator sees:** "Deal created, awaiting lead data"

---

### Stage: `lead_received`
**Description:** Lead captured, deal qualification in progress  
**Triggers:** Lead details entered  
**Requirements:** None (basic lead info is soft requirement)  
**Valid transitions:** → `preliminary_analysis`  
**What operator sees:** "Lead qualified, ready for analysis"

---

### Stage: `preliminary_analysis`
**Description:** Initial deal evaluation and metrics  
**Triggers:** ARV and repair cost estimated  
**Requirements:** 
- ✅ ARV provided (deal.arv > 0)
- ✅ Repair cost estimated (deal.repairs >= 0)
- ❌ NOT required: buyer match, contract, offer
**Valid transitions:** → `offer_ready`  
**What operator sees:** "Preliminary analysis complete, ready to create offer"  
**Heimdall blockers if missing:**
- `missing_arv` (critical)
- `missing_repair_cost` (critical)

---

### Stage: `offer_ready`
**Description:** Financial terms prepared and ready for seller  
**Triggers:** Offer created and reviewed  
**Requirements:**
- ✅ Offer must exist (offer_id > 0)
- ✅ Offer status must be "draft" or "sent"
- ❌ NOT required: buyer match, contract (but buyer matching recommended)
**Valid transitions:** → `under_contract`  
**What operator sees:** "Offer ready, next: buyer match + contract"  
**Heimdall blockers if missing:**
- `no_offer_created` (critical)

---

### Stage: `under_contract`
**Description:** Legal agreement underway  
**Triggers:** Contract document prepared and parties notified  
**Requirements:**
- ✅ Contract must exist (contract_id > 0)
- ✅ Contract must have content filled (contract.content not empty)
- ❌ NOT required: signatures yet, but should track signing_status
**Valid transitions:** → `closed`  
**What operator sees:** "Contract active, tracking signing status"  
**Heimdall blockers if missing:**
- `no_contract` (critical)
- `contract_content_empty` (critical)

---

### Stage: `closed`
**Description:** Deal finalized and closed  
**Triggers:** All signatures collected, contract fully executed  
**Requirements:**
- ✅ Contract must exist
- ✅ Contract must show signing_status = "fully_executed" or similar
- ❌ NOT required: funding transferred (out of scope for v0.1)
**Valid transitions:** None (terminal state)  
**What operator sees:** "Deal closed"  
**Heimdall blockers if missing:**
- `contract_not_signed` (critical)

---

## TRANSITION RULES

### Valid Transitions (State Machine)

```
draft 
  ↓
lead_received 
  ↓
preliminary_analysis 
  ↓
offer_ready 
  ↓
under_contract 
  ↓
closed (terminal)
```

**Rule 1:** Only move to the next state in sequence  
(**Exception:** Override allowed with explanation)

**Rule 2:** No skipping states  
E.g., `lead_received` → `under_contract` is invalid  
(**Exception:** Override allowed with explanation)

**Rule 3:** No backward transitions  
(`closed` → `under_contract` is never allowed, even with override)

**Rule 4:** Every transition must be approved  
(Operator supplies: approved_by, reason)

---

## BLOCKER RULES

### For Each Stage, Heimdall Checks:

#### `lead_received` → `preliminary_analysis`
- ❌ BLOCK if: No ARV provided
- ❌ BLOCK if: No repair estimate provided
- ✅ ALLOW if: Both ARV and repairs provided

Example blocker message:
```
"Cannot advance to preliminary_analysis: Missing ARV and repair cost estimate. 
 Fill in deal.arv and deal.repairs in the system."
```

---

#### `preliminary_analysis` → `offer_ready`
- ❌ BLOCK if: No offer exists
- ✅ ALLOW if: Offer created (regardless of buyer match)

Example blocker message:
```
"Cannot advance to offer_ready: No offer created yet.
 Create an offer with offer_price, emd_amount, and closing_window_days."
```

---

#### `offer_ready` → `under_contract`
- ❌ BLOCK if: No contract created
- ❌ BLOCK if: Contract exists but content is empty
- ✅ ALLOW if: Contract has content

Example blocker message:
```
"Cannot advance to under_contract: Contract content is empty.
 Fill in the contract terms and then try advancing."
```

---

#### `under_contract` → `closed`
- ❌ BLOCK if: No contract signing status recorded
- ✅ ALLOW if: Contract exists and signing is tracked

Example blocker message:
```
"Cannot advance to closed: Contract signing status not recorded.
 Update contract with signing status (e.g., 'fully_executed')."
```

---

## RISK FLAGS (NON-BLOCKING)

These don't prevent advancement but are logged and displayed:

| Risk | Trigger | Severity | Action |
|------|---------|----------|--------|
| high_repair_ratio | repairs > 50% of ARV | Yellow | Verify math, consider renegotiation |
| emd_too_low | EMD < 1% of offer price | Yellow | Verify terms with seller |
| repair_spread | Large difference between est. and actual | Orange | Update estimate once known |
| no_buyer_match | Deal in offer stage with no buyer matched | Blue | Run buyer matching |
| stale_deal | Deal unchanged for 30+ days | Orange | Follow up on status |
| frequent_stage_changes | Multiple transitions in short time | Yellow | Verify no mistakes |

---

## OVERRIDE RULES

### When Override is Allowed

Override is allowed when:
- ✅ Blocker exists but operator reasons it's acceptable
- ✅ Operator provides explicit override_reason
- ✅ Operator provides approved_by
- ✅ Action is still logged to audit as "override_used=true"

### When Override is NOT Allowed

Override is NOT allowed for:
- ❌ Backward transitions (e.g., closed → under_contract)
- ❌ Skipping more than one stage (e.g., lead → under_contract) - should skip one at a time
- ❌ Invalid stages (e.g., stage name not in enum)

---

## AUDIT LOGGING FOR STAGE CHANGES

Every stage change creates these audit entries:

### 1. Analysis Event
```json
{
  "action": "heimdall_analyzed_deal",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "metadata": {
    "current_stage": "preliminary_analysis",
    "recommended_stage": "offer_ready",
    "blockers": [],
    "risks": ["no_buyer_match"]
  }
}
```

### 2. Recommendation Event
```json
{
  "action": "heimdall_recommended_stage",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "metadata": {
    "from_stage": "preliminary_analysis",
    "to_stage": "offer_ready",
    "reason": "ARV and repairs provided, offer ready",
    "override_used": false
  }
}
```

### 3. Stage Advancement Event
```json
{
  "action": "heimdall_stage_advanced",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "previous_value": "preliminary_analysis",
  "new_value": "offer_ready",
  "metadata": {
    "approved_by": "operator@company.com",
    "reason": "Offer reviewed and ready",
    "override_used": false
  }
}
```

### 4. Rejection Event (if blocked)
```json
{
  "action": "heimdall_stage_advance_rejected",
  "actor": "Heimdall_v0.1",
  "deal_id": 1,
  "metadata": {
    "requested_stage": "offer_ready",
    "blocker": "no_offer_created",
    "override_available": true,
    "reason_for_override_needed": "Create offer first, then try again"
  }
}
```

---

## EXAMPLE WORKFLOWS

### Happy Path: Lead → Closed in 4 Steps

```
1. Create deal (draft)
2. Add ARV + repairs → HEIMDALL ANALYZES → recommends preliminary_analysis
3. Operator: POST /api/heimdall/deals/1/advance-stage
   { "requested_stage": "preliminary_analysis", "approved_by": "alice@co.com", "reason": "Data ready" }
   → ✅ Success: stage = preliminary_analysis

4. Create offer → HEIMDALL ANALYZES → recommends offer_ready
5. Operator: POST /api/heimdall/deals/1/advance-stage
   { "requested_stage": "offer_ready", "approved_by": "bob@co.com", "reason": "Offer sent to seller" }
   → ✅ Success: stage = offer_ready

6. Create contract + buyer match → HEIMDALL ANALYZES → recommends under_contract
7. Operator: POST /api/heimdall/deals/1/advance-stage
   { "requested_stage": "under_contract", "approved_by": "charlie@co.com", "reason": "Contract ready" }
   → ✅ Success: stage = under_contract

8. Update contract signing_status → HEIMDALL ANALYZES → recommends closed
9. Operator: POST /api/heimdall/deals/1/advance-stage
   { "requested_stage": "closed", "approved_by": "diana@co.com", "reason": "Fully signed" }
   → ✅ Success: stage = closed
```

---

### Blocked Path: Missing Data

```
1. Create deal (draft)
2. Operator tries to advance to preliminary_analysis WITHOUT ARV/repairs
3. POST /api/heimdall/deals/1/advance-stage
   { "requested_stage": "preliminary_analysis", "approved_by": "alice@co.com", "reason": "Ready" }
   → ❌ REJECTED: Blockers = ["missing_arv", "missing_repair_cost"]
   → Heimdall recommends: "Add deal.arv and deal.repairs, then try again"

4. Operator fills in data
5. Retry advance
   → ✅ Success
```

---

### Override Path: Known Issue

```
1. Deal is in under_contract stage
2. Contract exists but content field is empty (blocking closed advancement)
3. Operator knows content is in external system and wants to close anyway
4. POST /api/heimdall/deals/1/advance-stage
   {
     "requested_stage": "closed",
     "approved_by": "alice@co.com",
     "reason": "Closing deal",
     "override_reason": "Contract content in DocuSign, not in system yet"
   }
   → ✅ Success: stage = closed
   → Audit logs: override_used=true, override_reason captured
```

---

## CONSTRAINTS FOR HEIMDALL

Heimdall v0.1 respects stage rules ALWAYS:

- ✅ Validates transitions before allowing
- ✅ Checks required blockers for each stage
- ✅ Logs all decisions to audit trail
- ✅ Requires explicit approval from operator
- ✅ Allows override only with reason + approval
- ❌ Never skips stages without acknowledgment
- ❌ Never moves backward in stage
- ❌ Never modifies deal data directly (only status field)

---

## NEXT PHASE (After v0.1)

Future phases can add:
- Automatic stage advancement (when all blockers clear + timer expires)
- Multi-deal workflows
- Notification triggers on stage changes
- Advanced risk scoring integrations
- External API callbacks

But v0.1 is intentionally SIMPLE and OPERATOR-DRIVEN.

---

## TESTING STAGE RULES

See `tests/test_heimdall_v0_1.py` for:
- Valid transition test
- Invalid transition rejection test
- Blocker detection test
- Override test
- Audit logging verification test
