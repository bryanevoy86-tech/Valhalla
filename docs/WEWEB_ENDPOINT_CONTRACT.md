# Valhalla Legacy Inc — WeWeb Endpoint Contract (V1)

## Purpose
This document defines the frozen API contract for WeWeb Phase 1.

Do not change these response shapes casually.
If a field must change, update this file first.

---

## Base Rules

- Base URL comes from environment config in WeWeb
- All protected requests must use the configured auth/header rule
- Responses should remain JSON
- `ok` should always be present on success responses
- `agent` should remain `"Heimdall"` on Heimdall endpoints
- SAFE/LIVE state should be read from `/api/jarvis/system-status`

---

## 1) Health Check

### Endpoint
```
GET /health
```

### Purpose
Simple backend liveness check.

### Success Response
```json
{
  "ok": true
}
```

### WeWeb Usage
- first connection test
- simple "System Online" badge

---

## 2) System Status

### Endpoint
```
GET /api/jarvis/system-status
```

### Purpose
Returns current system mode and go-live readiness.

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "system": {
    "mode": "SAFE",
    "can_execute_live_actions": false,
    "blockers": [],
    "warnings": []
  }
}
```

### Fields
- `system.mode`: `"SAFE"` or `"LIVE"`
- `system.can_execute_live_actions`: boolean
- `system.blockers`: array of strings
- `system.warnings`: array of strings

### WeWeb Usage
- show SAFE/LIVE badge
- display blockers/warnings
- disable risky buttons if not live

---

## 3) Dashboard

### Endpoint
```
GET /api/jarvis/dashboard
```

### Purpose
High-level summary for top-line Heimdall overview.

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "message": "Heimdall has analyzed your live contact system",
  "generated_at": "2026-04-09T00:00:00+00:00",
  "summary": {
    "total_contacts": 2,
    "open_contacts": 2,
    "high_priority_contacts": 1,
    "top_contact": "Sarah Collins",
    "top_contact_score": 82
  }
}
```

### Fields
- `summary.total_contacts`: integer
- `summary.open_contacts`: integer
- `summary.high_priority_contacts`: integer
- `summary.top_contact`: string or null
- `summary.top_contact_score`: integer or null

### Wewebb Usage
- dashboard summary cards
- top contact display

---

## 4) Next Actions

### Endpoint
```
GET /api/jarvis/next-actions
```

### Purpose
Returns ranked actions Heimdall recommends next.

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "generated_at": "2026-04-09T00:00:00+00:00",
  "count": 2,
  "items": [
    {
      "contact_id": 2,
      "contact_name": "Sarah Collins",
      "priority": "high",
      "heimdall_score": 101,
      "action": "Follow up via email",
      "channel": "email",
      "reason": "Warm seller lead with recent activity.",
      "script": "Hi Sarah, just wanted to follow up and see if you're still open to discussing the property.",
      "why": [
        "Stale urgency boost (+15)",
        "Positive outcome history (+8)",
        "Best channel chosen from historical feedback: email"
      ],
      "heat_score": 81,
      "days_stale": 5,
      "status": "open"
    }
  ]
}
```

### Fields
- `count`: integer
- `items[]`: ranked actions array
  - `contact_id`: integer
  - `contact_name`: string
  - `priority`: `"high"` | `"medium"` | `"low"`
  - `heimdall_score`: integer
  - `action`: string
  - `channel`: string
  - `reason`: string or null
  - `script`: string or null
  - `why`: array of strings (explainability)
  - `heat_score`: integer
  - `days_stale`: integer
  - `status`: string

### WeWeb Usage
- action queue list
- primary operator page
- "what should I do now?" widget

---

## 5) Create Task

### Endpoint
```
POST /api/jarvis/create-task
```

### Purpose
Creates a manual task.

### Request Body
```json
{
  "contact_id": 2,
  "action": "Call immediately",
  "priority": "high"
}
```

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "task": {
    "id": 1,
    "contact_id": 2,
    "action": "Call immediately",
    "priority": "high",
    "status": "pending",
    "created_at": "2026-04-09T00:00:00+00:00",
    "completed_at": null,
    "completion_notes": null,
    "outcome_recorded": false
  }
}
```

### Fields
- `task.id`: integer
- `task.contact_id`: integer
- `task.action`: string
- `task.priority`: `"high"` | `"medium"` | `"low"`
- `task.status`: `"pending"` | `"completed"`

### WeWeb Usage
- create task button
- manual task forms

---

## 6) Tasks

### Endpoint
```
GET /api/jarvis/tasks
```

### Purpose
Returns pending tasks only.

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "count": 2,
  "tasks": [
    {
      "id": 2,
      "contact_id": 2,
      "action": "Follow up via email",
      "priority": "high",
      "status": "pending",
      "created_at": "2026-04-09T00:00:00+00:00",
      "completed_at": null,
      "completion_notes": null,
      "outcome_recorded": false
    }
  ]
}
```

### WeWeb Usage
- task queue page
- pending work list

---

## 7) Auto-Generate Tasks

### Endpoint
```
POST /api/jarvis/auto-generate-tasks
```

### Purpose
Creates tasks from top ranked actions while skipping duplicates.

### Request Body
```json
{
  "limit": 3
}
```

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "generated_at": "2026-04-09T00:00:00+00:00",
  "requested_limit": 3,
  "created_count": 2,
  "skipped_count": 1,
  "created": [],
  "skipped": []
}
```

### Fields
- `requested_limit`: integer
- `created_count`: integer
- `skipped_count`: integer
- `created[]`: created task results array
- `skipped[]`: duplicate-skipped results array

### WeWeb Usage
- "generate today's tasks" button

---

## 8) Complete Task

### Endpoint
```
POST /api/jarvis/complete-task
```

### Purpose
Marks a task as completed and stores notes.

### Request Body
```json
{
  "task_id": 2,
  "notes": "Called and left voicemail"
}
```

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "message": "Task marked as completed",
  "task": {
    "id": 2,
    "contact_id": 2,
    "action": "Follow up via email",
    "priority": "high",
    "status": "completed",
    "created_at": "2026-04-09T00:00:00+00:00",
    "completed_at": "2026-04-09T00:10:00+00:00",
    "completion_notes": "Called and left voicemail",
    "outcome_recorded": false
  },
  "next_step": "Record outcome for this completed task"
}
```

### WeWeb Usage
- mark task complete button
- modal for completion notes

---

## 9) Tasks Needing Outcome

### Endpoint
```
GET /api/jarvis/tasks-needing-outcome
```

### Purpose
Returns completed tasks that still need an outcome recorded.

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "count": 1,
  "items": [
    {
      "id": 2,
      "contact_id": 2,
      "action": "Follow up via email",
      "priority": "high",
      "status": "completed",
      "created_at": "2026-04-09T00:00:00+00:00",
      "completed_at": "2026-04-09T00:10:00+00:00",
      "completion_notes": "Called and left voicemail",
      "outcome_recorded": false
    }
  ]
}
```

### WeWeb Usage
- outcome queue page
- "what still needs feedback?" card

---

## 10) Record Outcome

### Endpoint
```
POST /api/jarvis/record-outcome
```

### Purpose
Records an outcome and optionally links it to a task and channel.

### Request Body
```json
{
  "contact_id": 2,
  "task_id": 2,
  "result": "no_response",
  "channel": "phone",
  "notes": "Voicemail left, no callback yet"
}
```

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "outcome": {
    "id": 1,
    "contact_id": 2,
    "result": "no_response",
    "notes": "Voicemail left, no callback yet",
    "channel": "phone",
    "task_id": 2,
    "timestamp": "2026-04-09T00:20:00+00:00"
  },
  "feedback": {
    "contact_id": 2,
    "channel": "phone",
    "result": "no_response",
    "notes": "Voicemail left, no callback yet",
    "created_at": "2026-04-09T00:20:00+00:00"
  },
  "task": {
    "id": 2,
    "outcome_recorded": true
  }
}
```

### Fields
- `result`: expected examples include:
  - `success`
  - `deal`
  - `no_response`
  - `lost`

### WeWeb Usage
- record result modal
- learning loop completion

---

## 11) Feedback History

### Endpoint
```
GET /api/jarvis/feedback/{contact_id}
```

### Purpose
Returns channel/result feedback history for one contact.

### Success Response
```json
{
  "ok": true,
  "agent": "Heimdall",
  "contact_id": 2,
  "count": 3,
  "items": [
    {
      "contact_id": 2,
      "channel": "sms",
      "result": "no_response",
      "notes": "Text sent, no reply",
      "created_at": "2026-04-09T00:00:00+00:00"
    },
    {
      "contact_id": 2,
      "channel": "email",
      "result": "success",
      "notes": "Email got response",
      "created_at": "2026-04-09T00:05:00+00:00"
    }
  ]
}
```

### WeWeb Usage
- contact detail page
- channel effectiveness display

---

## Error Handling Contract

### General Rules
- success responses include `ok: true`
- validation errors return HTTP 400
- not found returns HTTP 404
- server errors return HTTP 500

### Example 400
```json
{
  "detail": "task_id is required"
}
```

### Example 404
```json
{
  "detail": "Task not found"
}
```

---

## WeWeb Phase 1 Core Subset

WeWeb Phase 1 should only use these endpoints:

- `GET /health`
- `GET /api/jarvis/system-status`
- `GET /api/jarvis/next-actions`
- `GET /api/jarvis/tasks`
- `GET /api/jarvis/tasks-needing-outcome`
- `POST /api/jarvis/complete-task`
- `POST /api/jarvis/record-outcome`

This keeps the first frontend pass small and stable.

Later phases can add:
- Auto-generate tasks
- Create manual tasks
- Feedback history
- Dashboard

---

## Freeze Note

**This contract is frozen for WeWeb Phase 1.**

Do not casually rename routes or change response fields until Phase 1 is complete.

If a change is required:
1. Update this document first
2. Get sign-off from WeWeb team
3. Commit the contract change
4. Then implement the backend change

This protects both teams.
