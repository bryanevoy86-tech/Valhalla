# WEWEB EXECUTION CONSOLE CONTRACT

**Version**: 1.0  
**Base URL**: `http://localhost:4000` (dev) or configured production URL  
**Protocol**: HTTP/JSON  
**Content-Type**: `application/json`  
**Auth**: None (execution layer is open)  

---

## ENDPOINT 1: Create Intake from Raw Text

### Request

```http
POST /execution/intake
Content-Type: application/json

{
  "raw_text": "string (required, max 2000 chars)",
  "source_type": "string (optional: email, form, manual_entry, etc)"
}
```

### Field Details

| Field | Type | Required | Max Length | Example | Notes |
|-------|------|----------|-----------|---------|-------|
| `raw_text` | string | Yes | 2000 | "3 bed 2 bath house asking $250k, needs roof repair ~$15k" | Raw opportunity description |
| `source_type` | string | No | - | "manual_entry" | Hint about input type (for logging) |

### Response: 200 OK

```json
{
  "intake_id": 1,
  "raw_text": "3 bed 2 bath house asking $250k...",
  "created_at": "2026-04-12T14:30:00Z",
  "status": "new",
  "message": "✓ Opportunity recorded. Click Process to analyze."
}
```

### Response Model: `IntakePreview`

| Field | Type | Format | Required | Example |
|-------|------|--------|----------|---------|
| `intake_id` | integer | int64 | Yes | 1 |
| `raw_text` | string | - | Yes | "3 bed 2 bath house..." |
| `created_at` | string | ISO 8601 datetime | Yes | "2026-04-12T14:30:00Z" |
| `status` | string | enum: new, normalized, archived | Yes | "new" |
| `message` | string | - | Yes | "Click Process to analyze" |

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 400 | "raw_text is required" | Missing required field |
| 413 | "raw_text too long (max 2000 chars)" | Exceeds size limit |
| 500 | "Failed to create intake: {error}" | Database error |

### Example cURL

```bash
curl -X POST http://localhost:4000/execution/intake \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "3 bed 2 bath fixer-upper at 456 Oak St, asking $150k, ARV likely $280k after $50k repairs",
    "source_type": "manual_entry"
  }'
```

---

## ENDPOINT 2: Process Intake through Full Pipeline

### Request

```http
POST /execution/intake/{intake_id}/process
Content-Type: application/json

{
  "intake_id": 1,
  "override_confidence": 75.0
}
```

### Path Parameters

| Param | Type | Required | Example |
|-------|------|----------|---------|
| `intake_id` | integer | Yes | 1 |

### Query/Body Parameters

| Field | Type | Required | Format | Range | Example | Notes |
|-------|------|----------|--------|-------|---------|-------|
| `override_confidence` | float | No | 0-100 | 0 to 100 | 75.0 | Manually override parser confidence |

### Response: 200 OK (Full Pipeline Result)

```json
{
  "case_id": 1,
  "intake_id": 1,
  "classification": "real_estate",
  "what_it_is": "This appears to be a residential wholesale opportunity",
  "estimated_value": 238000,
  "estimated_cost": 150000,
  "estimated_profit": 88000,
  "confidence_level": "medium",
  "confidence_score": 75,
  "risk_score": 2.4,
  "recommended_strategy": "buy_and_hold",
  "alternative_strategies": ["fix_and_flip", "wholesale"],
  "missing_information": ["Actual property condition", "Title status"],
  "current_stage": "intake_processed",
  "safe_mode": true,
  "blocked": false,
  "blocker_reason": null,
  "next_action": "Verify property condition with site visit",
  "tasks_created": 4,
  "created_at": "2026-04-12T14:32:00Z",
  "processing_time_seconds": 0.423
}
```

### Response Model: `ExecutionCaseSummary`

| Field | Type | Format | Required | Example | Notes |
|-------|------|--------|----------|---------|-------|
| `case_id` | integer | - | Yes | 1 | Unique case ID for future queries |
| `intake_id` | integer | - | Yes | 1 | Link back to source intake |
| `classification` | string | enum | Yes | "real_estate" | Type: real_estate, business, arbitrage, jv, unknown |
| `what_it_is` | string | - | Yes | "Residential wholesale opportunity" | Plain language summary |
| `estimated_value` | float | currency | Yes | 238000 | ARV after -15% buffer |
| `estimated_cost` | float | currency | Yes | 150000 | Total cost (purchase + repairs + ops) |
| `estimated_profit` | float | currency | Yes | 88000 | Value - Cost |
| `confidence_level` | string | enum | Yes | "medium" | low, medium, high |
| `confidence_score` | float | 0-100 | Yes | 75 | Parser confidence in extraction |
| `risk_score` | float | 0-100 | Yes | 2.4 | Execution risk (lower is better) |
| `recommended_strategy` | string | enum | Yes | "buy_and_hold" | wholesale, fnh, buy_and_hold, jv, manual_review, blocked |
| `alternative_strategies` | array[string] | - | Yes | ["fix_and_flip"] | Other viable paths |
| `missing_information` | array[string] | - | Yes | ["Property condition"] | Fields blocking higher confidence |
| `current_stage` | string | - | Yes | "intake_processed" | Workflow stage |
| `safe_mode` | boolean | - | Yes | true | Requires manual approval |
| `blocked` | boolean | - | Yes | false | Deal rejected automatically |
| `blocker_reason` | string or null | - | No | null | Why blocked (if blocked=true) |
| `next_action` | string | - | Yes | "Verify property condition" | Operator's next step |
| `tasks_created` | integer | - | Yes | 4 | Number of action items created |
| `created_at` | string | ISO 8601 datetime | Yes | "2026-04-12T14:32:00Z" | When case was created |
| `processing_time_seconds` | float | - | Yes | 0.423 | Pipeline execution time |

### Pipeline Stages

**Stage 1: Parse**
- Extract: bedrooms, bathrooms, price, ARV, repair costs, etc.
- Source: Raw text regex parsing
- Output: `extracted_fields` dictionary

**Stage 2: Classify**
- Determine: real_estate, business, arbitrage, jv, or unknown
- Source: Keyword matching (50+ keywords per category)
- Output: `classification` string

**Stage 3: Assess**
- Calculate: Conservative valuation with buffers
- Buffers: ARV -15%, Repairs +30%, Operating +20%
- Output: `assessment` dict with value, cost, profit, confidence, risk

**Stage 4: Route**
- Decide: Which execution pipeline?
- Options: wholesale, fnh, buy_and_hold, jv, manual_review, blocked
- Output: `routing` with selected pipeline and alternatives

**Stage 5: Generate Tasks**
- Create: 1-8 operator tasks based on pipeline
- Order: By sequence/priority
- Output: Task list saved to database

### Business Logic

**Blocking Rules:**
- If estimated_profit ≤ 0: blocked = true, reason = "Negative or zero profit"
- If margin < 5%: blocked = true, reason = "Insufficient margin"

**Safe Mode Rules:**
- If confidence_score < 50 but not blocked: safe_mode = true
- Operator must approve to advance

**Risk Scoring:**
- 0-20: Very safe (green)
- 20-50: Moderate (yellow)
- 50-70: Risky (orange)
- 70+: Very risky (red), usually blocked

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "Intake not found" | intake_id doesn't exist |
| 400 | "Invalid override_confidence" | Not 0-100 |
| 500 | "Processing failed: {error}" | Pipeline error |

### Example cURL

```bash
curl -X POST http://localhost:4000/execution/intake/1/process \
  -H "Content-Type: application/json" \
  -d '{
    "intake_id": 1,
    "override_confidence": 85
  }'
```

---

## ENDPOINT 3: Get Case Summary

### Request

```http
GET /execution/cases/{case_id}
```

### Path Parameters

| Param | Type | Required | Example |
|-------|------|----------|---------|
| `case_id` | integer | Yes | 1 |

### Response: 200 OK

```json
{
  "case_id": 1,
  "intake_id": 1,
  "classification": "real_estate",
  "what_it_is": "Residential wholesale opportunity",
  "estimated_value": 238000,
  "estimated_cost": 150000,
  "estimated_profit": 88000,
  "confidence_level": "medium",
  "confidence_score": 75,
  "risk_score": 2.4,
  "recommended_strategy": "buy_and_hold",
  "alternative_strategies": [],
  "missing_information": [],
  "current_stage": "tasks_created",
  "safe_mode": false,
  "blocked": false,
  "blocker_reason": null,
  "next_action": "Schedule property inspection",
  "tasks_created": 4,
  "created_at": "2026-04-12T14:32:00Z",
  "processing_time_seconds": 0.0
}
```

### Response Model: `ExecutionCaseSummary` (same as Endpoint 2)

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "Case not found" | case_id doesn't exist |
| 500 | "Failed to retrieve case: {error}" | Database error |

### Example cURL

```bash
curl http://localhost:4000/execution/cases/1
```

---

## ENDPOINT 4: Get Operator Task List

### Request

```http
GET /execution/cases/{case_id}/tasks
```

### Path Parameters

| Param | Type | Required | Example |
|-------|------|----------|---------|
| `case_id` | integer | Yes | 1 |

### Response: 200 OK

```json
{
  "case_id": 1,
  "task_count": 4,
  "tasks": [
    {
      "id": 1,
      "case_id": 1,
      "title": "Verify property address and ownership",
      "instructions": "Contact county assessor or check MLS property card",
      "status": "pending",
      "priority": 1,
      "sequence": 1,
      "category": "verification",
      "due_at": null,
      "guidance_url": null
    },
    {
      "id": 2,
      "case_id": 1,
      "title": "Estimate repair costs",
      "instructions": "Get contractor quotes for roof and HVAC",
      "status": "pending",
      "priority": 2,
      "sequence": 2,
      "category": "analysis",
      "due_at": null,
      "guidance_url": null
    }
  ]
}
```

### Response Model: `ExecutionTaskListResponse`

| Field | Type | Content | Required | Example |
|-------|------|---------|----------|---------|
| `case_id` | integer | - | Yes | 1 |
| `task_count` | integer | Number of tasks | Yes | 4 |
| `tasks` | array | Array of `ExecutionTaskOut` | Yes | [...] |

### Task Object Fields: `ExecutionTaskOut`

| Field | Type | Format | Required | Example | Notes |
|-------|------|--------|----------|---------|-------|
| `id` | integer | - | Yes | 1 | Task ID |
| `case_id` | integer | - | Yes | 1 | Parent case |
| `title` | string | verb phrase | Yes | "Verify property address" | What to do |
| `instructions` | string | - | Yes | "Call county assessor" | How to do it |
| `status` | string | enum | Yes | "pending" | pending, in_progress, done |
| `priority` | integer | 1-10 | Yes | 1 | 1=urgent, 10=low |
| `sequence` | integer | - | Yes | 1 | Sort order |
| `category` | string | enum | Yes | "verification" | verification, contact, analysis, logistics |
| `due_at` | string or null | ISO 8601 | No | null | Deadline (if set) |
| `guidance_url` | string or null | URL | No | null | Help link (if available) |

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "Case not found" | case_id doesn't exist |
| 500 | "Failed to retrieve tasks: {error}" | Database error |

### Example cURL

```bash
curl http://localhost:4000/execution/cases/1/tasks
```

---

## ENDPOINT 5: Get Next Single Action

### Request

```http
GET /execution/cases/{case_id}/next-action
```

### Path Parameters

| Param | Type | Required | Example |
|-------|------|----------|---------|
| `case_id` | integer | Yes | 1 |

### Response: 200 OK

```json
{
  "case_id": 1,
  "action": "Verify property square footage",
  "why": "Current estimate is from Zillow - need actual to calculate ARV correctly",
  "how": "Contact seller or pull MLS property card for exact SF",
  "priority": "urgent",
  "blocking": true
}
```

### Response Model: `ExecutionNextActionResponse`

| Field | Type | Format | Required | Example | Notes |
|-------|------|--------|----------|---------|-------|
| `case_id` | integer | - | Yes | 1 | Case ID |
| `action` | string | - | Yes | "Verify property SF" | What to do now |
| `why` | string | - | Yes | "Need actual SF for ARV" | Why it matters |
| `how` | string | - | Yes | "Call seller or check MLS" | Step-by-step |
| `priority` | string | enum | Yes | "urgent" | urgent, normal, optional |
| `blocking` | boolean | - | Yes | true | Blocks progression? |

### Logic

- Returns first pending task if any exist
- If no pending tasks: suggests "Review case and decide to proceed or pass"
- Emphasizes priority: urgent=blocking/high priority, normal=can wait

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "Case not found" | case_id doesn't exist |
| 500 | "Failed to retrieve next action: {error}" | Database error |

### Example cURL

```bash
curl http://localhost:4000/execution/cases/1/next-action
```

---

## ENDPOINT 6: Advance Case to Next Stage

### Request

```http
POST /execution/cases/{case_id}/advance
Content-Type: application/json

{
  "target_stage": "execution",
  "operator_notes": "All verifications complete, ready to proceed"
}
```

### Path Parameters

| Param | Type | Required | Example |
|-------|------|----------|---------|
| `case_id` | integer | Yes | 1 |

### Body: `AdvanceCaseRequest`

| Field | Type | Required | Max Length | Example |
|-------|------|----------|-----------|---------|
| `target_stage` | string | Yes | - | "execution" |
| `operator_notes` | string | No | 500 | "All verifications complete" |

### Response: 200 OK

```json
{
  "success": true,
  "case_id": 1,
  "new_stage": "execution",
  "message": "Case advanced to execution stage"
}
```

### Response Model: `AdvanceCaseResponse`

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `success` | boolean | Yes | true |
| `case_id` | integer | Yes | 1 |
| `new_stage` | string | Yes | "execution" |
| `message` | string | Yes | "Case advanced to execution stage" |

### Business Rules

- **Cannot advance if blocked**: Returns 400 "Case is blocked: {reason}"
- **Cannot advance in safe_mode**: Returns 400 "Safe mode active - manual approval required"
- **Creates event log**: Logs stage transition to audit trail

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "Case not found" | case_id doesn't exist |
| 400 | "Case is blocked: {reason}" | Case.blocked = true |
| 400 | "Safe mode active - manual approval required" | Case.safe_mode = true |
| 500 | "Failed to advance case: {error}" | Database error |

### Example cURL

```bash
curl -X POST http://localhost:4000/execution/cases/1/advance \
  -H "Content-Type: application/json" \
  -d '{
    "target_stage": "execution",
    "operator_notes": "Looks good to proceed"
  }'
```

---

## ENDPOINT 7: Get Audit Trail / Event Log

### Request

```http
GET /execution/cases/{case_id}/events
```

### Path Parameters

| Param | Type | Required | Example |
|-------|------|----------|---------|
| `case_id` | integer | Yes | 1 |

### Response: 200 OK

```json
{
  "case_id": 1,
  "event_count": 3,
  "events": [
    {
      "id": 3,
      "case_id": 1,
      "event_type": "case_advanced",
      "timestamp": "2026-04-12T14:35:00Z",
      "actor": "operator",
      "description": "Case advanced to execution stage",
      "stage_from": "intake_processed",
      "stage_to": "execution",
      "payload": {"stage_from": "intake_processed", "stage_to": "execution"}
    },
    {
      "id": 2,
      "case_id": 1,
      "event_type": "task_created",
      "timestamp": "2026-04-12T14:32:30Z",
      "actor": "system",
      "description": "Task created: Verify property address",
      "stage_from": null,
      "stage_to": null,
      "payload": {}
    },
    {
      "id": 1,
      "case_id": 1,
      "event_type": "intake_processed",
      "timestamp": "2026-04-12T14:32:00Z",
      "actor": "system",
      "description": "Intake processed through full pipeline",
      "stage_from": "intake",
      "stage_to": "intake_processed",
      "payload": {}
    }
  ]
}
```

### Response Model: `ExecutionEventLogResponse`

| Field | Type | Content | Required | Example |
|-------|------|---------|----------|---------|
| `case_id` | integer | - | Yes | 1 |
| `event_count` | integer | Total events | Yes | 3 |
| `events` | array | Array of `ExecutionEventOut` | Yes | [...] |

### Event Object Fields: `ExecutionEventOut`

| Field | Type | Format | Required | Example | Notes |
|-------|------|--------|----------|---------|-------|
| `id` | integer | - | Yes | 1 | Event ID |
| `case_id` | integer | - | Yes | 1 | Parent case |
| `event_type` | string | enum | Yes | "intake_processed" | intake_processed, task_created, case_advanced |
| `timestamp` | string | ISO 8601 datetime | Yes | "2026-04-12T14:32:00Z" | When event occurred |
| `actor` | string | - | Yes | "system" | Who triggered: system or operator |
| `description` | string | - | Yes | "Intake processed" | Human-readable summary |
| `stage_from` | string or null | - | No | "intake" | Previous stage |
| `stage_to` | string or null | - | No | "intake_processed" | New stage |
| `payload` | object | JSON | Yes | {...} | Event metadata |

### Event Types

| Type | Actor | Meaning |
|------|-------|---------|
| `intake_processed` | system | Intake moved through full pipeline |
| `task_created` | system | Task generated |
| `case_advanced` | operator | Operator advanced case stage |

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "Case not found" | case_id doesn't exist |
| 500 | "Failed to retrieve events: {error}" | Database error |

### Example cURL

```bash
curl http://localhost:4000/execution/cases/1/events
```

---

## COMMON PATTERNS

### Field Naming Conventions

- Timestamp fields: `created_at`, `updated_at`, `timestamp` (always ISO 8601)
- Boolean operations: `safe_mode`, `blocked`, `success`
- Numeric: `case_id`, `task_id`, `priority` (1-10), `confidence_score` (0-100), amounts in cents or dollars
- Enums: Lowercase with underscores (e.g., `real_estate`, `buy_and_hold`)

### Null Handling

- Optional fields may be `null` (e.g., `blocker_reason` when not blocked)
- Arrays are never `null`, always present (possibly empty)
- Dates are always present if field exists

### Pagination

- Not implemented (fixed responses per route)
- Endpoint 4 returns all tasks for case
- Endpoint 7 returns all events for case

---

## STATUS CODES SUMMARY

| Code | Meaning | Common Reasons |
|------|---------|----------------|
| 200 | Success | Request processed |
| 400 | Bad request | Invalid input, blocked case, safe_mode active |
| 404 | Not found | Case/intake/task doesn't exist |
| 500 | Server error | Database error, processing error |

---

## READY FOR WEWEB INTEGRATION

All 7 endpoints are:
- ✅ Implemented and tested
- ✅ Database-backed (persists to SQLite)
- ✅ Documented with exact schema
- ✅ Ready for direct browser/API calls (no special WeWeb integration needed)

Next step: PHASE 3 - Verify builder routes work
