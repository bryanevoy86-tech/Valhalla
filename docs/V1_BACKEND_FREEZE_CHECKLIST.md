# Valhalla Legacy Inc — V1 Backend Freeze Checklist

## Purpose
This checklist defines the backend surface that is considered frozen for V1 WeWeb integration.

Once an item here is marked complete, its API contract should not change unless a bug requires it.

---

## V1 Backend Freeze Rules

- No new major backend features until WeWeb Phase 1 is connected.
- No response shape changes on frozen endpoints unless required to fix a real bug.
- No renaming routes after freeze without updating the contract sheet.
- Only bug fixes, stability fixes, and documentation updates are allowed after freeze.
- New ideas go into backlog, not into the live V1 contract.

---

## Freeze Status

### Core Health
- [x] `/health` returns 200 OK
- [x] backend starts clean with no critical errors
- [x] logs show stable startup
- [x] JSON persistence working
- [x] audit logging working

### Heimdall Core
- [x] `/api/jarvis/dashboard`
- [x] `/api/jarvis/hot-contacts`
- [x] `/api/jarvis/next-actions`
- [x] `/api/jarvis/recommend-action`
- [x] `/api/jarvis/run-playbook`

### Task Engine
- [x] `/api/jarvis/create-task`
- [x] `/api/jarvis/tasks`
- [x] `/api/jarvis/auto-generate-tasks`
- [x] `/api/jarvis/complete-task`

### Outcome + Learning Loop
- [x] `/api/jarvis/record-outcome`
- [x] `/api/jarvis/tasks-needing-outcome`
- [x] `/api/jarvis/feedback/{contact_id}`

### Data + State
- [x] contact store persists correctly
- [x] task store persists correctly
- [x] outcome store persists correctly
- [x] interaction history persists correctly
- [x] channel feedback persists correctly

### Safety / Go-Live
- [ ] system status route exists
- [ ] safe/live mode clearly exposed
- [ ] blockers can be returned to frontend
- [ ] warnings can be returned to frontend

---

## V1 Frozen Endpoints

These endpoints are part of the frozen contract for WeWeb Phase 1:

- GET `/health`
- GET `/api/jarvis/dashboard`
- GET `/api/jarvis/next-actions`
- GET `/api/jarvis/tasks`
- GET `/api/jarvis/tasks-needing-outcome`
- POST `/api/jarvis/create-task`
- POST `/api/jarvis/complete-task`
- POST `/api/jarvis/record-outcome`
- POST `/api/jarvis/auto-generate-tasks`

---

## Allowed Changes After Freeze

Allowed:
- bug fixes
- missing field fixes
- better error handling
- audit/logging improvements
- performance improvements
- documentation updates

Not allowed:
- changing route names
- changing JSON shapes casually
- adding unrelated new modules
- changing field names without updating contract sheet
- moving core V1 logic to a different route structure

---

## WeWeb Phase 1 Dependency

WeWeb Phase 1 will only depend on:
- health check
- next actions
- tasks
- complete task
- record outcome

If these are stable, WeWeb can proceed safely.

---

## Final Freeze Decision

Backend V1 Freeze Status:
- [ ] NOT FROZEN
- [ ] FROZEN FOR WEWEB PHASE 1

Date Frozen:
- YYYY-MM-DD

Frozen By:
- Bryan / Heimdall
