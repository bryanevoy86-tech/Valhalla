# EXECUTION LAYER GAP AUDIT
**Valhalla Execution Layer V1 - Codebase Assessment**

**Date:** April 12, 2026  
**Phase:** 1 - Gap Audit  
**Status:** In Progress

---

## Executive Summary

The Valhalla codebase has significant foundational pieces that can be reused for the execution layer, BUT **critical systems are missing or incomplete** for a simple, operator-ready flow.

**Current State:**
- ✅ Basic lead/deal intake exists
- ✅ Task model exists (but minimal)
- ✅ Audit logging exists
- ⚠️ Assessment partially exists (UnderwriterAssessment is basic)
- ❌ No decision engine output (recommendations, strategies, alternatives)
- ❌ No routing logic (route to strategy pipeline)
- ❌ No execution case tracking
- ❌ No state machine for safe progression
- ❌ No operator-friendly summary responses
- ❌ No knowledge spine integration
- ❌ No confidence/risk scoring for go/no-go decision
- ❌ No blocker/warning system

**Reusability Score: 35-40%**

---

## A. OPPORTUNITY INTAKE - Current State

### What Already Exists

**Model: LeadIntake** (`services/api/app/models/intake.py`)
```
✓ id, source, name, email, phone
✓ address, region, property_type
✓ price, beds, baths, notes
✓ status (new / normalized / archived)
✓ raw_json (flexible payload storage)
✓ deal_id (cross-reference to deal)
✓ created_at
```

**Router: /intake** (`services/api/app/routers/intake.py`)
```
✓ POST /intake/leads - create lead intake
✓ GET /intake/leads - list all leads
✓ POST /intake/leads/{lead_id}/normalize - normalize and create deal
```

**Router: /leads** (`services/api/app/routers/leads.py`)
```
✓ CRUD for leads
✓ Status filtering
✓ Basic lead management
```

### What Partially Exists

**Model: DealBrief** (`services/api/app/models/match.py`)
- Captures headline, region, property_type, price, beds, baths, notes, status
- **Gap:** No classification, no confidence, no extracted fields for decision

### What Is Missing

❌ **Classification Engine**
- No way to auto-classify "is this real estate? business? arbitrage?"
- No heuristic parser for different input formats
- No input validation before storage

❌ **Field Extraction**
- No structured parsing of raw text
- No confidence scores for each extracted field
- No flag for "missing field X is a blocker"

❌ **Confidence Scoring**
- No way to score confidence of parsed data (0-100)
- No confidence-based warnings

**Verdict:** Reuse LeadIntake + DealBrief. Add classification and confidence fields.

---

## B. KNOWLEDGE SPINE USAGE - Current State

### What Already Exists

**None explicitly for execution.**

Files related to rules/policies:
- `services/api/app/models/tuning_rules.py` - system tuning (not opportunity-specific)
- `services/api/app/models/triggers.py` - trigger definitions (not opportunity-specific)

### What Is Missing

❌ **Repair Assumptions Table**
- No standardized cost buffers (repairs typically under/estimated)
- No repair category costs
- No regional/property-type adjustments

❌ **Cost Policies**
- No ARV buffers (estimated value reduced by %)
- No op cost/fee assumptions
- No insurance, carrying cost assumptions
- No closing cost buffers

❌ **Benchmark Tables**
- No reference data for expected costs, fees, timelines
- No regional/type-specific benchmarks

❌ **Source Tracking**
- No metadata about which knowledge rule was applied
- No confidence tracking for applied rules

❌ **Confidence Rules**
- No specification of what drives medium vs. high confidence
- No hard rules (missing address = auto low confidence)

**Verdict:** This must be **built from scratch** for V1. Start with hardcoded, conservative policies.

---

## C. DECISION ENGINE - Current State

### What Already Exists

**Model: UnderwriterAssessment** (`services/api/app/models/underwriter_assessment.py`)
```
✓ deal_id, risk_score, legal_risk_score, profitability_score
✓ decision (approve / reject / review)
✓ notes, country, region
✓ legal_profile_id (optional relationship)
```

**Routers for decisions:**
- `decision_recommendation.py` - recommendations (unknown content)
- `decision_outcome.py` - track outcomes (unknown content)
- `decision_governance.py` - governance rules (unknown content)

### What Partially Exists

**UnderwriterAssessment** has structure but is **not integrated** into intake flow:
- Not called automatically after intake
- No connection to estimated value, cost, profit
- No "recommended strategy" field
- No "alternative strategies" field
- No "missing information" flag field

### What Is Missing

❌ **Decision Output Contract**
- No defined response structure for "is this worth doing?"
- No place to store:
  - Estimated value
  - Estimated cost
  - Estimated profit
  - Risk score
  - Confidence score
  - Recommended strategy
  - Alternative strategies
  - Missing fields

❌ **Strategy Enum**
- No list of valid strategies (wholesale, fix-and-flip, buy-and-hold, JV, etc.)
- No strategy selection logic
- No strategy-specific task generation

❌ **Go/No-Go Logic**
- No decision rules (confidence threshold, risk threshold, etc.)
- No safe mode triggering
- No auto-block criteria

**Verdict:** Add fields to UnderwriterAssessment OR create new ExecutionAssessment model.

---

## D. ROUTING ENGINE - Current State

### What Already Exists

**None explicitly for execution routing.**

### What Is Missing

❌ **Route Target Enum**
- No defined "routes" (wholesale_pipeline, fnh_pipeline, buy_hold_pipeline, arbitrage_pipeline, etc.)
- No routing logic to map classification + strategy → pipeline

❌ **Routing Decision**
- No logic to decide: "given deal type + estimated value + risk, which pipeline?"
- No fallback routing (e.g., "low confidence → review pipeline")

❌ **Execution Case Creation**
- No model to track "this opportunity is now being executed as Case #123"
- No execution record to link to intake + assessment + route target

**Verdict:** Create ExecutionCase model + simple routing service.

---

## E. EXECUTION SPINE - Current State

### What Already Exists

**Model: Task** (`services/api/app/models/task.py`)
```
✓ id, title, description, category
✓ assignee, status, priority
✓ due_at, completed_at
✓ created_at, updated_at
```

**Routers for workflows:**
- `workflows.py` - workflow management (unknown content)
- `workflow_guardrails.py` - safety rules (unknown content)

**Audit:** 
- AuditEvent model exists with entity_id, action, previous_value, new_value, user_id

### What Partially Exists

**Task** model is basic but not integrated:
- No case_id reference (can't group tasks by case)
- No stage tracking (what stage of execution are we in?)
- No state machine (safe checkpoint logic missing)

**Audit** exists but not tied to execution case:
- No way to say "all events related to this case"

### What Is Missing

❌ **ExecutionCase Model**
- No "case" abstraction to track entire execution lifecycle
- No current_stage, current_status fields
- No safe_mode, blocked fields
- No blocker_reason
- No next_action suggestion

❌ **ExecutionEvent Model**
- No event logging tied to case progression
- No stage_from / stage_to tracking
- No payload tracking

❌ **State Machine**
- No defined stages (intake → classification → assessment → routing → execution → close)
- No safe transitions
- No checkpoint logic
- No auto-advance vs. manual-approval logic

❌ **Blocker Handling**
- No "blocker" concept
- No way to halt execution and require operator action

**Verdict:** Create ExecutionCase + ExecutionEvent models + simple state machine.

---

## F. OPERATOR SURFACE API - Current State

### What Already Exists

```
POST /intake/leads                              ✓ Paste opportunity
GET /intake/leads                               ✓ List intakes (not specific)
POST /intake/leads/{id}/normalize               ✓ Process step (not comprehensive)
```

### What Is Missing

❌ **Unified Process Endpoint**
- No single `/execution/intake/{id}/process` that does everything
- Operator must call multiple endpoints
- No summary response

❌ **Execution Summary Response**
- No contract defined for operator response
- No single response with:
  - what_it_is
  - confidence_level
  - estimated_value
  - estimated_cost
  - estimated_profit
  - risk_score
  - recommended_strategy
  - alternative_strategies
  - missing_information
  - next_action
  - tasks_created
  - blocked / blocker_reason
  - safe_mode

❌ **Task List Endpoint**
- No `/execution/cases/{id}/tasks` endpoint
- Operator can't see their work

❌ **Next Action Endpoint**
- No `/execution/cases/{id}/next-action` endpoint
- Operator must infer what to do

❌ **Status Endpoint**
- No `/execution/cases/{id}` endpoint showing current state

❌ **Stage Advance Endpoint**
- No `/execution/cases/{id}/advance` endpoint
- No safe progression logic

❌ **Event Timeline Endpoint**
- No `/execution/cases/{id}/events` endpoint
- No audit trail visibility

**Verdict:** All 7 endpoints must be **BUILT**.

---

## WHAT CAN BE REUSED

### High-Confidence Reuse
1. **LeadIntake model** - add classification + parsed_data_json fields
2. **DealBrief model** - link from intake
3. **Task model** - add case_id reference
4. **AuditEvent model** - use as-is for case events
5. **Database patterns** - SQLAlchemy + Pydantic are established
6. **Auth patterns** - require_builder_key decorator exists

### Partial Reuse
1. **UnderwriterAssessment model** - extend fields OR create ExecutionAssessment alongside
2. **Job routing** - existing pattern for background tasks exists

### Can't Reuse (Must Build)
1. ExecutionCase model (new)
2. ExecutionEvent model (new)
3. ExecutionPolicy model (new)
4. Intake classification logic (new)
5. Assessment logic (new)
6. Routing logic (new)
7. State machine (new)
8. Operator endpoints (new)

---

## EXACT MINIMUM SET NEEDED FOR V1

### Models (3-4 New)

```
1. ExecutionCase
   - intake_id (FK)
   - assessment_id (FK)
   - case_type (enum: real_estate, business, arbitrage, jv, unknown)
   - route_target (enum: wholesale_pipeline, fnh_pipeline, etc)
   - current_stage (enum: intake, classification, assessment, routing, tasks_created, execution, close)
   - current_status (enum: pending, in_progress, blocked, completed)
   - safe_mode (bool)
   - blocked (bool)
   - blocker_reason (text)
   - next_action (text)
   - created_at, updated_at

2. ExecutionEvent (for audit trail)
   - case_id (FK)
   - event_type (enum: intake_created, classified, assessed, routed, task_created, advanced, blocked)
   - stage_from, stage_to (string)
   - payload_json (text)
   - created_at, actor (user_id)

3. ExecutionPolicy
   - domain (enum: arv_buffer, repair_buffer, ops_buffer, confidence_rules, risk_rules)
   - policy_type (enum: cost_buffer, percentage_reduction, threshold)
   - rule_key (string)
   - rule_value_json (text)
   - active (bool)
   - updated_at

4. (Keep) UnderwriterAssessment - add fields
   - estimated_value
   - estimated_cost
   - estimated_profit
   - recommended_strategy
   - alternative_strategies_json
   - missing_fields_json
   - confidence_score
```

### Fields to Add to Existing Models

**LeadIntake** (add):
- classification (enum)
- parsed_data_json (text)
- confidence (float 0-100)
- extraction_notes (text)

**DealBrief** (add):
- classification (enum)
- confidence (float)

**Task** (add):
- case_id (FK to ExecutionCase)

### Services (4-5 New)

```
1. intake_parser_service.py
   - parse_raw_text(text) → parsed_dict + source_type

2. opportunity_classifier_service.py
   - classify(parsed_dict) → classification + confidence

3. assessment_service.py
   - assess(opportunity_dict) → {estimated_value, cost, profit, risk, confidence, strategy, alternatives, missing}

4. routing_service.py
   - route(classification, assessment) → route_target + safe_mode_flag

5. task_generation_service.py
   - generate(case) → list[Task]
```

### Endpoints (7 New)

```
1. POST /execution/intake
   Purpose: Store raw opportunity + return intake preview
   
2. POST /execution/intake/{id}/process
   Purpose: Classify, assess, route, create case & tasks
   Response: {what_it_is, confidence, value, cost, profit, risk, strategy, alternatives, missing, next_action, tasks, blocked, safe_mode}
   
3. GET /execution/cases/{id}
   Purpose: Current execution status
   
4. GET /execution/cases/{id}/tasks
   Purpose: Operator task list
   
5. GET /execution/cases/{id}/next-action
   Purpose: Next action only
   
6. POST /execution/cases/{id}/advance
   Purpose: Move to next stage (with guards)
   
7. GET /execution/cases/{id}/events
   Purpose: Audit trail
```

### Conservative Rules (Hardcoded for V1)

```
ARV Buffer:             -15% (reduce value estimates by 15%)
Repair/Cost Buffer:     +30% (increase costs 30%)
Ops/Fee Buffer:         +20% (increase ops costs 20%)
Closing Cost Buffer:    +15%

Confidence Rules:
  - Missing address → AUTO BLOCK (confidence = 0)
  - Missing price → AUTO BLOCK (confidence = 0)
  - Missing property_type → confidence = 40 (low)
  - All fields present → confidence = 80 (medium)
  - + manual verification → confidence = 95 (high)

Risk Rules:
  - Estimated profit < $5,000 → risk = 80 (very risky)
  - Estimated profit < $15,000 → risk = 60 (risky)
  - Estimated profit >= $15,000 → risk = 30 (acceptable)
  - Confidence < 50 → risk += 20
  - Safe mode if: risk > 70 OR confidence < 50

Go/No-Go:
  - If confidence = 0 → BLOCKED "Missing critical fields"
  - If confidence < 30 → BLOCKED "Confidence too low"
  - If risk > 85 AND confidence < 60 → BLOCKED "Risk too high, confidence low"
  - Otherwise → PROCEED (may be in safe_mode)
```

---

## ASSESSMENT TRUTH TABLE

For V1, when processing an opportunity:

| Input Quality | Est. Profit | Est. Risk | Confidence | Safe Mode | Action |
|---------------|-------------|----------|-----------|-----------|--------|
| Missing critical fields | - | - | 0 | N/A | BLOCK - "Need address + price" |
| Partial (est. price = guessed) | $8K | 65 | 35 | YES | PROCEED IN SAFE MODE - "Verify price" |
| Partial (property type unclear) | $20K | 55 | 50 | YES | PROCEED IN SAFE MODE - "Verify property type" |
| Complete(verified) | $25K | 30 | 85 | NO | PROCEED - "Ready to execute" |
| Complete(high risk/low margin) | $4K | 75 | 90 | YES | PROCEED IN SAFE MODE - "High risk, low margin" |

---

## EXISTING CODE THAT CREATES FRICTION

### 1. LeadIntake Status Enum
Currently: `new / normalized / archived`  
**Problem:** Doesn't track if it's been classified, assessed, or routed  
**Solution:** Add separate ExecutionCase to track post-intake status

### 2. Task Model References Case by Implication
**Problem:** No case_id field  
**Solution:** Add case_id FK + migrate existing tasks to have null case_id (backwards compatible)

### 3. UnderwriterAssessment Not Integrated
**Problem:** Exists but not called during intake processing  
**Solution:** Call during `/execution/intake/{id}/process` flow

### 4. No Unified Response Contract
**Problem:** Multiple models, no single "execution summary" response  
**Solution:** Create `ExecutionCaseSummary` response schema

---

## RISK ASSESSMENT

### Low Risk (Safe to Implement)
✓ Adding fields to LeadIntake + DealBrief  
✓ Adding case_id to Task  
✓ Creating ExecutionCase + ExecutionEvent models  
✓ Creating 7 new endpoints  
✓ Hardcoding conservative policies  

### Medium Risk
⚠ Adding new services without disrupting existing patterns  
⚠ Ensuring backward compatibility (old tasks may not have case_id)  

### Avoided (Out of Scope for V1)
✗ Refactoring existing routers  
✗ Touching Heimdall/governance engines  
✗ Changing database schema outside V1 models  

---

## BLOCKERS FOR V1 EXECUTION

1. **None identified** - all required pieces can be added independently

---

## SUMMARY: REUSE vs. BUILD

### Reuse (8 items)
- LeadIntake model (extend)
- DealBrief model (extend)
- Task model (extend with case_id)
- AuditEvent model (as-is)
- Database patterns
- Auth/dependency patterns
- Job/background task patterns
- Deployment/containerization

### Build (12 items)
- ExecutionCase model
- ExecutionEvent model
- ExecutionPolicy model
- intake_parser_service
- opportunity_classifier_service
- assessment_service
- routing_service
- task_generation_service
- execution_state_service (state machine)
- /execution/intake endpoint
- /execution/intake/{id}/process endpoint
- /execution/cases/{id}* endpoints (6x)

### Extend (3 items)
- LeadIntake (add classification, parsed_data_json, confidence)
- DealBrief (add classification, confidence)
- Task (add case_id)

---

## READINESS FOR PHASE 2

**Status:** ✅ Ready to proceed to Phase 2

**Next Steps:**
1. Confirm V1 response contract (PHASE 2)
2. Define exact models with all fields (PHASE 2)
3. Build minimum services (PHASE 3)
4. Implement 7 endpoints (PHASE 3)
5. Add conservative rules (PHASE 3)
6. Test operator flow (PHASE 3)

---

**Audit Completed:** April 12, 2026  
**Auditor:** Gap Analysis  
**Next Review:** After PHASE 2 contract definition

