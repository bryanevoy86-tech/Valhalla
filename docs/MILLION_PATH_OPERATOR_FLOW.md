# MILLION-PATH: Canonical Day-One Operator Flow

**Status:** LIVE PRODUCTION  
**Base URL:** https://valhalla-api-ha6a.onrender.com  
**Last Updated:** 2026-04-13  

## Overview

This document defines the exact user journey for the day-one operator using only verified, live production routes. This is the canonical workflow that WeWeb must support for launch.

---

## THE OPERATOR DAY-ONE FLOW

### STEP 1: INTAKE - Paste Opportunity

**User Action:** Operator pastes opportunity text into text field

**Route:** `POST /execution/intake`

**Request:**
```json
{
  "raw_text": "3 bed 2 bath house, asking 250k, needs roof"
}
```

**Response:**
```json
{
  "intake_id": 16,
  "raw_text": "3 bed 2 bath house, asking 250k, needs roof",
  "created_at": "2026-04-13T20:49:14.473666",
  "status": "new",
  "message": "🔷 Opportunity recorded. Click Process to analyze."
}
```

**What Happens:**
- Raw opportunity text is persisted to `lead_intake_exec` table
- Unique intake record created
- Returns `intake_id` for all subsequent operations
- Status is "new" - awaiting processing

**WeWeb First Build Requirement:**
- Text input field for raw opportunity
- Send to POST /execution/intake
- Display returned intake_id
- Show "Processing available" message

---

### STEP 2: PROCESS - Analyze & Classify

**User Action:** Click "Process" or "Analyze" button

**Route:** `POST /execution/intake/{intake_id}/process`

**Request:**
```json
{
  "intake_id": 16
}
```

**Expected Response (when successful):**
```json
{
  "case_id": 3,
  "intake_id": 16,
  "case_type": "real_estate",
  "route_target": "blocked",
  "current_stage": "intake_processed",
  "current_status": "pending_review",
  "safe_mode": true,
  "blocked": true,
  "blocker_reason": "Profit margin only 2.0% - below 5% threshold",
  "next_action": "Manual review required - potential high-risk deal",
  "created_at": "2026-04-13T20:50:00.000000",
  "updated_at": "2026-04-13T20:50:00.000000"
}
```

**What Happens:**
- System classifies the opportunity
- Creates `execution_case` record
- Runs business logic validation
- Checks profit margin, risk factors, deal viability
- Returns classification and decision
- If blocked: `blocked=true`, `blocker_reason` explains why
- If viable: `blocked=false`, `next_action` shows next step

**WeWeb First Build Requirement:**
- Process button triggers POST /execution/intake/{intake_id}/process
- Display case details:
  - case_id
  - case_type
  - current_stage
  - blocked (YES/NO - RED if true)
  - blocker_reason (if blocked)
  - next_action (what to do next)

---

### STEP 3: VIEW CASE SUMMARY

**User Action:** Click on the case or view details

**Route:** `GET /execution/cases/{case_id}`

**Response:**
```json
{
  "case_id": 3,
  "intake_id": 16,
  "case_type": "real_estate",
  "route_target": "blocked",
  "current_stage": "intake_processed",
  "current_status": "pending_review",
  "safe_mode": true,
  "blocked": true,
  "blocker_reason": "Profit margin only 2.0% - below 5% threshold",
  "next_action": "Manual review required",
  "created_at": "2026-04-13T20:50:00.000000",
  "updated_at": "2026-04-13T20:50:00.000000"
}
```

**What Happens:**
- Returns full case record
- Source of truth for deal state
- Used to populate deal summary card

**WeWeb First Build Requirement:**
- GET /execution/cases/{case_id} on page load after processing
- Display all fields in summary panel
- Refresh manually or on timer

---

### STEP 4: VIEW TASK LIST

**User Action:** Operator opens "Task List" or "To-Do" section

**Route:** `GET /execution/cases/{case_id}/tasks`

**Response:**
```json
{
  "case_id": 3,
  "tasks": [
    {
      "id": 1,
      "title": "Verify property exists and matches description",
      "description": "Confirm the property is real and details are accurate...",
      "category": "verification",
      "priority": 1,
      "status": "pending",
      "sequence": 1,
      "assignee": "king",
      "due_days": 1,
      "created_at": "2026-04-13T20:50:00.000000"
    },
    {
      "id": 2,
      "title": "Contact seller to confirm motivation",
      "description": "Understand seller's situation and timeline...",
      "category": "contact",
      "priority": 3,
      "status": "pending",
      "sequence": 2,
      "assignee": "king",
      "due_days": 2,
      "created_at": "2026-04-13T20:50:00.000000"
    },
    {
      "id": 3,
      "title": "Calculate wholesale spread",
      "description": "Determine our offer price and profit margin...",
      "category": "analysis",
      "priority": 2,
      "status": "pending",
      "sequence": 3,
      "assignee": "king",
      "due_days": 1,
      "created_at": "2026-04-13T20:50:00.000000"
    },
    {
      "id": 4,
      "title": "Decide: Proceed or pass?",
      "description": "Review all completed tasks and information gathered...",
      "category": "decision",
      "priority": 1,
      "status": "pending",
      "sequence": 4,
      "assignee": "king",
      "due_days": 14,
      "created_at": "2026-04-13T20:50:00.000000"
    }
  ]
}
```

**What Happens:**
- Returns all tasks for the case in sequence order
- Tasks are pre-populated by process logic
- Each task has title, description, priority, category, assignee, due_days
- Status shows completion state
- Sequence shows order of operations

**WeWeb First Build Requirement:**
- GET /execution/cases/{case_id}/tasks on case view load
- Display tasks as checklist or card-list
- Show priority (1=high, 3=low) as color coding
- Show category as badge (verification, contact, analysis, decision)
- Manual checkboxes for day-one (backend task update comes later)

---

### STEP 5: GET NEXT ACTION

**User Action:** Operator checks "What should I do next?"

**Route:** `GET /execution/cases/{case_id}/next-action`

**Response:**
```json
{
  "case_id": 3,
  "next_action": "Manual review required - Profit margin below threshold",
  "action_type": "escalation",
  "action_target": "owner",
  "priority": "high",
  "created_at": "2026-04-13T20:50:00.000000"
}
```

**What Happens:**
- System returns the highest-priority next action
- Used to guide operator attention
- Prevents decision paralysis
- Single source of truth for "what now?"

**WeWeb First Build Requirement:**
- GET /execution/cases/{case_id}/next-action
- Display prominently in "NEXT ACTION" banner
- Color-code by action_type (escalation=red, decision=orange, task=yellow)
- Click to jump to relevant task or escalation handler

---

### STEP 6: ADVANCE CASE

**User Action:** Operator clicks "Move Forward" or completes a decision task

**Route:** `POST /execution/cases/{case_id}/advance`

**Request:**
```json
{
  "case_id": 3,
  "action": "owner_review_approved",
  "notes": "Looks good, proceed with contact"
}
```

**Expected Response:**
```json
{
  "case_id": 3,
  "previous_stage": "intake_processed",
  "new_stage": "ready_for_contact",
  "current_status": "active",
  "next_action": "Contact seller to confirm motivation",
  "blocked": false,
  "updated_at": "2026-04-13T20:51:00.000000"
}
```

**What Happens:**
- Case moves to next pipeline stage
- Status changes from pending_review to active
- Blocked flag cleared (if applicable)
- Next action recalculated
- Event logged to execution_events

**WeWeb First Build Requirement:**
- "Approve & Proceed" button on case
- POST /execution/cases/{case_id}/advance with action="owner_review_approved"
- Refresh case data after response
- Show stage change confirmation
- Update next action display

---

### STEP 7: VIEW EVENT LOG

**User Action:** Operator clicks "History" or "Events"

**Route:** `GET /execution/cases/{case_id}/events`

**Response:**
```json
{
  "case_id": 3,
  "events": [
    {
      "id": 1,
      "event_type": "case_created",
      "description": "Case created from intake ID 16",
      "actor": "system",
      "created_at": "2026-04-13T20:50:00.000000"
    },
    {
      "id": 2,
      "event_type": "case_processed",
      "description": "Case classified as real_estate, blocked due to low margin",
      "actor": "system",
      "created_at": "2026-04-13T20:50:05.000000"
    },
    {
      "id": 3,
      "event_type": "owner_review",
      "description": "Owner reviewed and approved - proceed with contact",
      "actor": "operator",
      "created_at": "2026-04-13T20:51:00.000000"
    }
  ]
}
```

**What Happens:**
- Full audit trail of case actions
- Shows who did what and when
- Useful for transparency and debugging

**Wewebb First Build Requirement:**
- GET /execution/cases/{case_id}/events (optional for day-one)
- Display events as timeline or log list
- Show actor and timestamp

---

## DAY-ONE OPERATOR SCREEN LAYOUT

```
┌─────────────────────────────────────────────────────────┐
│  EXECUTION CONSOLE                        [HELP] [+NEW]  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─ INTAKE ──────────────────────────────────────────┐  │
│  │ [Paste Opportunity]                               │  │
│  │ 3 bed 2 bath house, asking 250k, needs roof       │  │
│  │                    [PROCESS]                      │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─ DEAL SUMMARY ─────────────────────────────────────┐ │
│  │ ID: 3 | Type: real_estate | Stage: intake_proc   │ │
│  │ Status: pending_review                            │ │
│  │ Blocked: ⚠️  YES                                   │ │
│  │ Reason: Profit margin 2.0% < 5% threshold        │ │
│  │ Zone: [not yet available]                         │ │
│  └───────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─ NEXT ACTION ──────────────────────────────────────┐ │
│  │ 🔴 ESCALATION: Manual review required            │ │
│  │ [APPROVE & PROCEED] [CLARIFY] [PASS]            │ │
│  └───────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─ TASK LIST ────────────────────────────────────────┐ │
│  │ [ ] 1-HIGH   Verify property exists       1 day   │ │
│  │ [ ] 3-LOW    Contact seller               2 days  │ │
│  │ [ ] 2-MED    Calculate spread             1 day   │ │
│  │ [ ] 1-HIGH   Decide: Proceed or pass      14 days │ │
│  └───────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─ EVENTS ──────────────────────────────────────────┐  │
│  │ 20:51 owner_review: Approved - proceed with contact  │
│  │ 20:50 case_processed: Classified, low margin       │  │
│  │ 20:50 case_created: From intake 16                │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## WHAT STAYS MANUAL ON DAY-ONE

1. **Task Completion** - Operator manually checks boxes (no backend task update yet)
2. **Follow-up Logging** - Manual notes in escalation workflow
3. **Decision Making** - Operator decides to proceed/pass (system doesn't auto-decide)
4. **Zone Assignment** - Manual dropdown selection (not auto-assigned yet)
5. **Strategy Selection** - Operator selects wholesale/hold/flip (not auto-classified yet)
6. **Delegation** - Manual assignment to team roles (not auto-routed yet)

---

## WHAT BECOMES DELEGATABLE POST-LAUNCH

1. **Task Automation** - System marks tasks complete when actions happen
2. **Route-Based Routing** - Cases auto-routed to zone leads
3. **Priority Escalation** - High-value deals flagged automatically
4. **Follower Management** - Auto-notify assigned team members
5. **Status Sync** - External integrations (MLS, Zillow) update case status
6. **Buyer Matching** - Auto-match cases to buyer profiles
7. **Contract Pipeline** - Auto-advance to next stage when conditions met

---

## REST OF MILLION-PATH (NOT IN DAY-ONE)

- Dashboard/reporting
- Multi-zone management
- Team performance metrics
- Advanced builder controls
- Arbitrage deal engine
- Commercial/development workflows
- Creative finance workflows
- Procurement
- Capital/funding workflows
- Investor portal
- Empire state management
- Community management
- Research integration
- Media management

---

## ERROR HANDLING

### 422 Unprocessable Entity
**Cause:** Missing required field in request  
**Example:** POST /execution/intake/{intake_id}/process without `intake_id` in body  
**WeWeb Handler:** Show error message, ask operator to check inputs

### 500 Internal Server Error
**Cause:** Backend processing failure (e.g., schema mismatch)  
**Example:** Tasks table missing case_id column  
**WeWeb Handler:** Show "System error - contact support", log to Sentry

### 404 Not Found
**Cause:** Case ID doesn't exist  
**Example:** GET /execution/cases/999999  
**WeWeb Handler:** Redirect to intake, show "Case not found"

---

## PRODUCTION STATUS

✅ POST /execution/intake - **LIVE & TESTED**  
⚠️  POST /execution/intake/{intake_id}/process - **LIVE with schema notes**  
✅ GET /execution/cases/{case_id} - **LIVE & TESTED**  
⏳ GET /execution/cases/{case_id}/tasks - **LIVE but schema needs verification**  
⏳ GET /execution/cases/{case_id}/next-action - **LIVE but verify response format**  
⏳ POST /execution/cases/{case_id}/advance - **STUBBED, needs testing**  
⏳ GET /execution/cases/{case_id}/events - **LIVE but verify format**  

---

## NEXT STEPS

1. WeWeb team implements Execution Console page
2. Test each route in order (intake → process → view → tasks → advance)
3. Handle blocking cases gracefully (show reason, offer escalation)
4. Implement task checklist (manual only for day-one)
5. Add history/events tab (optional for day-one)
6. Connect to team notification system (async email/SMS)

---

**Document Owner:** Deployment Recovery Team  
**Last Tested:** 2026-04-13 20:49 UTC  
**Next Review:** Post-WeWeb launch (2026-04-15)  
