# HEIMDALL V0.1 SCOPE DEFINITION

**Version:** 0.1 (Operator-Assist Layer, NOT Autonomous)  
**Release Date:** March 26, 2026

---

## CORE MISSION

Heimdall v0.1 is a **practical, auditable operator-assist layer** that helps humans manage the deal pipeline safely and intelligently.

Heimdall is **NOT**:
- An autonomous system
- An empire builder
- A decision-maker
- A rules engine that bypasses human judgment
- A scheduler or event-driven orchestrator

Heimdall IS:
- An analyzer
- A recommender
- An approval processor
- An auditor of its own actions
- A safe, transparent operator tool

---

## CAPABILITY A: ANALYZE DEAL

**Endpoint:** `POST /api/heimdall/deals/{deal_id}/analyze`

**Input:** (optional) context payload

**What Heimdall does:**
1. Load deal from persistent database
2. Load related offer (if exists)
3. Load related contract (if exists)
4. Load buyer match state (if exists)
5. Fetch recent audit timeline (last 5-10 events)
6. Summarize current state
7. Identify missing data
8. Flag risk/blocker conditions
9. Return structured analysis

**Output Schema:**

```json
{
  "deal_id": 1,
  "analysis_timestamp": "2026-03-26T15:30:00Z",
  "current_state": {
    "stage": "preliminary_analysis",
    "status": "active",
    "created_at": "2026-03-26T14:00:00Z",
    "arv": 450000.00,
    "repairs_cost": 65000.00,
    "offer_price": 280000.00,
    "mao": 300000.00
  },
  "offer_state": {
    "exists": true,
    "offer_id": 5,
    "offer_price": 280000.00,
    "emd_amount": 5000.00,
    "status": "draft",
    "closing_window_days": 45
  },
  "contract_state": {
    "exists": true,
    "contract_id": 2,
    "status": "draft",
    "signing_status": null
  },
  "buyer_match_state": {
    "exists": true,
    "buyer_id": 3,
    "buyer_name": "Midwest Investments",
    "match_score": 0.92,
    "match_status": "pending"
  },
  "missing_fields": [
    "contract.content",
    "contract.signing_status"
  ],
  "blocker_flags": [
    "contract_content_empty",
    "buyer_match_not_approved"
  ],
  "risk_flags": [
    "high_repair_ratio (14.4%)",
    "emd_below_2pct_offer",
    "no_signed_contract"
  ],
  "recent_timeline": [
    {
      "timestamp": "2026-03-26T15:00:00Z",
      "action": "deal_buyer_match",
      "actor": "system",
      "summary": "Matched buyer ID 3, score 0.92"
    },
    {
      "timestamp": "2026-03-26T14:30:00Z",
      "action": "contract_created",
      "actor": "system",
      "summary": "Contract ID 2 created"
    }
  ],
  "recommendations": {
    "next_valid_stages": [
      "offer_ready",
      "under_contract"
    ],
    "recommended_stage": "offer_ready",
    "recommendation_reason": "Offer is valid and buyer matched. Next: prepare for contract stage or move to offer stage",
    "can_advance_now": false,
    "why_cannot_advance": "Contract content is empty. Must fill contract terms before advancing to under_contract."
  }
}
```

**Key principles:**
- No magic - only use data that exists in DB
- Transparent - explain every flag
- Safe - never recommend action that violates stage rules
- Helpful - explain WHY, not just WHAT

---

## CAPABILITY B: IDENTIFY BLOCKERS

**Integral to Analyze (no separate endpoint)**

**What counts as a blocker:**

```
CRITICAL Blockers (prevent next stage):
├─ Contract required but missing (for under_contract → closed)
├─ Buyer match required but missing (for preliminary → offer_ready)
├─ Offer required but missing (for lead → preliminary)
├─ Deal score missing (some transitions)
└─ Fields marked required for stage are empty

SOFT Blockers (warnings, not blocking):
├─ Very high repair ratio (>50%)
├─ Price below market comps
├─ EMD too low
├─ No signed contract for late-stage deal
└─ Active buyer match still "pending"

RISK Flags (informational):
├─ Deal older than 30 days with no activity
├─ Multiple price adjustments in timeline
├─ Frequent stage changes
└─ Long time stuck in one stage
```

**Blocker detection rules:**

```python
if stage == "lead_received":
    # No offer yet - next stage is preliminary_analysis
    no_blockers()

elif stage == "preliminary_analysis":
    # Need basic deal data + offer
    blocker_if(not deal.arv, "Missing ARV")
    blocker_if(not deal.repairs, "Missing repair cost estimate")
    recommend_next = "offer_ready"

elif stage == "offer_ready":
    # Need offer + preferably buyer match
    blocker_if(not offer_exists, "No offer created")
    blocker_if(offer.status not in ["draft", "sent"], "Offer not ready")
    soft_blocker_if(not buyer_match_exists, "No buyer matched yet")
    recommend_next = "under_contract"

elif stage == "under_contract":
    # Need valid contract file + signing status tracking
    blocker_if(not contract_exists, "No contract attached")
    blocker_if(not contract.content, "Contract content empty")
    soft_blocker_if(not contract.signing_status, "No signing status")
    recommend_next = "closed"
```

---

## CAPABILITY C: RECOMMEND NEXT STEP

**What Heimdall recommends:**

1. **Analyze current state** (via Analyze capability)
2. **Identify blockers** (via Identify Blockers)
3. **Check valid transitions** (via stage enum)
4. **Return recommendation**

**Example recommendations:**

```
Stage: preliminary_analysis
Blockers: [arv_missing, repair_cost_missing]
Recommendation: "Cannot advance yet. Supply ARV and repair cost estimate."

---

Stage: offer_ready
Blockers: []
Soft Blockers: [no_buyer_match]
Recommendation: "Ready to advance to under_contract. 
              Recommended: Match buyer first (matched name: Midwest Inv, score 0.92), 
              then prepare contract."

---

Stage: under_contract
Blockers: [contract_content_empty]
Recommendation: "Cannot advance to closed until contract content entered.
               Fill contract terms, then approve advancement to closed."
```

**Key:** Recommendation is never a command. It's always:
- Transparent about why
- Respectful of human judgment
- Explainable in plain English

---

## CAPABILITY D: EXECUTE ONE CONTROLLED ACTION

**Endpoint:** `POST /api/heimdall/deals/{deal_id}/advance-stage`

**Input:**

```json
{
  "requested_stage": "offer_ready",
  "approved_by": "operator@company.com",
  "reason": "Offer is ready, buyer matched with 0.92 score",
  "override_reason": null
}
```

**What Heimdall does:**

1. Load deal from DB
2. Validate current stage
3. Validate requested stage (is transition legal?)
4. Check for blockers
   - If critical blockers exist AND no override_reason: REJECT
   - If critical blockers exist AND override_reason provided: LOG OVERRIDE + PROCEED
5. Update deal.status in database
6. Create TWO audit events:
   - One for recommendation that led to approval
   - One for actual stage advancement
7. Return success/failure

**Output:**

```json
{
  "deal_id": 1,
  "action": "stage_advanced",
  "previous_stage": "preliminary_analysis",
  "new_stage": "offer_ready",
  "approved_by": "operator@company.com",
  "timestamp": "2026-03-26T15:35:00Z",
  "audit_log_ids": [1024, 1025],
  "result": "success",
  "notes": "Stage advanced successfully",
  "blocker_overrides": []
}
```

**Edge cases:**

```
1. Invalid transition (e.g., skip from lead → under_contract)
   → REJECT with explanation

2. Valid transition but blockers present
   → REJECT unless override_reason provided

3. Valid transition, blockers present, override supplied
   → PROCEED but LOG OVERRIDE in audit

4. Valid transition, no blockers
   → PROCEED normally

5. Deal doesn't exist
   → 404 error

6. Unauthorized (bad API key)
   → 401 error
```

---

## AUDIT REQUIREMENTS FOR HEIMDALL

**Every Heimdall action creates audit entries:**

### Analyze Action
- **Action:** `heimdall_analyzed_deal`
- **Fields:**
  - actor: "Heimdall_v0.1"
  - entity_type: "deal"
  - entity_id: deal_id
  - action: "heimdall_analyzed_deal"
  - result: "success" (always, unless error)
  - metadata:
    - blockers_found: []
    - risks_found: []
    - recommended_stage: "offer_ready"

### Recommendation Action
- **Action:** `heimdall_recommended_stage`
- **Fields:** (same as analyze, but separate event)
  - metadata:
    - from_stage: "preliminary_analysis"
    - to_stage: "offer_ready"
    - reason: "Offer ready, buyer matched"
    - can_advance: false
    - blockers: ["contract_content_empty"]

### Stage Advancement Action
- **Action:** `heimdall_stage_advanced`
- **Fields:**
  - actor: "Heimdall_v0.1"
  - entity_type: "deal"
  - entity_id: deal_id
  - action: "heimdall_stage_advanced"
  - previous_value: "preliminary_analysis"
  - new_value: "offer_ready"
  - result: "success"
  - metadata:
    - approved_by: "operator@company.com"
    - reason: "Offer ready, proceeding"
    - override_used: false

### Stage Advancement Rejection
- **Action:** `heimdall_stage_advance_rejected`
- **Fields:**
  - result: "rejected"
  - metadata:
    - requested_stage: "closed"
    - blocker: "contract_content_empty"
    - override_available: true

---

## SCOPE BOUNDARIES (V0.1)

### ✅ IN SCOPE

- Deal analysis from persistent DB
- Simple blocker detection (missing fields, rule violations)
- Stage transition validation
- Stage advancement with approval
- Audit logging of all actions
- Operator-driven workflow

### ❌ OUT OF SCOPE

- Autonomous triggering
- Multi-step workflows
- External API calls
- Email/SMS notifications
- Contract signing
- Payment processing
- Buyer creation/modification
- Predictive scoring
- AI/ML integration
- Global orchestration

---

## SAFETY MODEL

Heimdall v0.1 is safe because:

1. **No side effects outside DB** - only reads dealstate, writes to audit + stage
2. **Operator approval required** - every stage change needs explicit approval
3. **Immutable audit trail** - all actions logged and tamper-proof
4. **No secrets/credentials** - no API keys, no external integrations
5. **No async/scheduled work** - only synchronous request/response
6. **Clear boundaries** - stage rules are deterministic, not fuzzy

---

## KNOWN LIMITATIONS (V0.1)

1. **No multi-stage workflows** - one stage at a time
2. **Limited blocker intelligence** - basic rule-based, not predictive
3. **No buyer/contract autonomy** - can observe but not modify
4. **Basic auth** - builder key only, no user-level tracking
5. **No email integration** - no notifications
6. **String-based stages** - should be enum but works fine

---

## SUCCESS CRITERIA

Heimdall v0.1 succeeds if:

- ✅ Can analyze a deal from DB
- ✅ Can identify and explain blockers
- ✅ Can recommend valid next stage
- ✅ Can advance stage only with explicit approval
- ✅ Rejects invalid transitions
- ✅ Logs all actions to audit trail
- ✅ Has tests covering all scenarios
- ✅ Has runnable API demo
- ✅ Takes no external side effects
- ✅ Documents what it cannot do

---

**This scope is NARROW by design. Heimdall v0.1 is a safe, simple, auditable operator tool - not an empire.**
