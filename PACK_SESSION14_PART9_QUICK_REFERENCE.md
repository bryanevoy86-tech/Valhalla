# Session 14 Part 9 - Quick Reference Guide

## 20 PACKs Deployed

### Usage Forecast (3 PACKs)
```bash
POST /core/forecast/usage
  inv_id: "inv_xxx"
  qty_used: 2.5
  used_on: "2026-01-03"
  
GET /core/forecast/inventory/{inv_id}?window_days=30

GET /core/forecast/rollup?limit=20&window_days=30
```

### Approvals Queue (2 PACKs)
```bash
POST /core/approvals
  title: "Approve purchase: Widget"
  action: "approve_purchase"
  
GET /core/approvals?status=pending

POST /core/approvals/{approval_id}/decide?decision=approve
```

### Heimdall Master Dispatcher (3 PACKs)
```bash
# Explore mode (read-only, safe)
POST /core/heimdall/do
  {
    "mode": "explore",
    "action": "shopping.generate_from_inventory",
    "data": {"limit": 50}
  }

# Execute mode (state-changing, requires approval)
POST /core/heimdall/do
  {
    "mode": "execute",
    "action": "shopping.bought",
    "data": {"shopping_id": "sh_xxx"}
  }

# Plan (preview without execution)
POST /core/heimdall/plan
  {"action": "budget.impact", "data": {"buffer_min": 500}}

# View action history
GET /core/heimdall/actions?limit=200
```

### Shopping Integrations (3 PACKs)
```bash
# Fast add
POST /core/shopping/quick_add?name=milk&est_total=4.50

# Generate from schedule needs
POST /core/shopping/generate_from_needs?within_days=30&limit=50

# Request approvals for big-ticket items
POST /core/shopping/request_approvals?threshold=200.0
```

### Receipts Management (3 PACKs)
```bash
POST /core/receipts
  vendor: "Walmart"
  amount: 125.50
  date: "2026-01-03"
  category: "groceries"

GET /core/receipts?category=groceries&date_from=2026-01-01

POST /core/receipts/{receipt_id}/post_ledger
  (best-effort ledger integration)
```

### Scheduler Integration
```
Daily /core/scheduler/tick now includes:
  - Generate shopping from schedule needs (P-NEEDS2SHOP-2)
  - Request approvals for big-ticket items (P-SCHED-6)
```

### Ops Board Enhancement
```bash
GET /core/ops_board/today
  ...
  "approvals_pending": [...],      # New in P-OPSBOARD-7
  "heimdall_actions": [...]        # New in P-OPSBOARD-7
```

---

## Key Features

### Safety Gates
- **Cone Integration:** execute mode blocked if cone policy denies
- **Approval Requirements:** shopping.bought requires approval if item ≥$200
- **Action Logging:** All heimdall actions immutably logged for audit

### Auto-Generation
- **Inventory → Shopping:** Automatic when stock low
- **Schedule Needs → Shopping:** Automatic from upcoming needs events
- **Shopping → Approvals:** Automatic for high-cost items (≥$200)

### Integration Points
1. **Forecast:** Tracks inventory consumption, predicts depletion
2. **Approvals:** Gates spending decisions, audit trail
3. **Heimdall:** Unified command dispatcher with safety modes
4. **Receipts:** Lightweight tracking, ledger integration
5. **Scheduler:** Daily tick orchestrates all auto-generation

---

## Common Workflows

### Workflow 1: Mark Item Out, Auto-Forecast + Auto-Shopping
```
User: POST /core/inventory/out_of?name=milk&qty_to_set=0
  ↓
Auto: Log usage event in forecast (P-FORECAST-2)
Auto: Add to shopping list (P-INVENTORY-3)
Auto: Check if needs approval (P-APPROVALS-2)
```

### Workflow 2: Daily Scheduler Tick
```
Scheduler: /core/scheduler/tick (every day)
  ↓
1. Generate shopping from schedule needs (P-NEEDS2SHOP-2)
2. Request approvals for big-ticket items (P-SCHED-6)
3. (Existing: bills reminders, calendar reminders, etc.)
```

### Workflow 3: Buy Item with Approval
```
User: POST /core/heimdall/do
  { "mode": "execute", "action": "shopping.bought", 
    "data": {"shopping_id": "sh_xxx"} }
  ↓
Check: Is item ≥$200? (P-SAFETY-APPROVAL-1)
Check: Does approval exist and approved? (P-SAFETY-APPROVAL-1)
Check: Does cone policy allow? (P-HEIMDALLDO-2)
Auto: Create receipt placeholder (P-RECEIPTS-3)
Log: Action recorded in heimdall audit trail (P-ACTIONS-LOG-1)
```

### Workflow 4: Planning Mode (No Execution)
```
User: POST /core/heimdall/plan
  { "action": "budget.impact", "data": {} }
  ↓
Result: Preview impact without changing state (P-HEIMDALLDO-3)
```

---

## Testing

Run all Session 14 Part 9 tests:
```bash
pytest tests/test_pack_session14_part9.py -v
# Result: 20/20 PASSING ✅
```

---

## Data Locations

```
/backend/data/forecast/usage_events.json     — Usage log (200K limit)
/backend/data/approvals/approvals.json       — Approval queue
/backend/data/heimdall/actions.json          — Action audit trail (200K limit)
/backend/data/receipts/receipts.json         — Receipt metadata
/backend/data/shopping/...                   — Shopping data
/backend/data/inventory/...                  — Inventory data
/backend/data/schedule/...                   — Schedule data
```

---

## Troubleshooting

### Action blocked by cone
**Issue:** `POST /core/heimdall/do` returns 403 "cone denied"  
**Solution:** Check cone policy configuration; adjust if overly restrictive

### Approval required error
**Issue:** `shopping.bought` blocked for item ≥$200  
**Solution:** Create approval (`POST /core/approvals`) then approve it (`POST /core/approvals/{id}/decide`)

### Forecast shows null days_left
**Issue:** Burn rate is 0 (no usage logged yet)  
**Solution:** Log usage events via `POST /core/forecast/usage` first, or mark inventory "out of"

### Receipt ledger integration fails
**Issue:** `POST /core/receipts/{id}/post_ledger` returns error  
**Solution:** Graceful failure (best-effort); receipts still created even if ledger unavailable

---

## Git History

```
32ba400 Add comprehensive Session 14 Part 9 deployment documentation
24d80a1 Deploy 20 PACKs: Forecast Engine, Approvals Queue, Heimdall Master Actions...
aa1d526 Deploy 20 new PACKs: Underwriting, Bills, Budget, Pipeline, JV filtering...
```

---

**Status:** ✅ Session 14 Part 9 COMPLETE  
**Total Lines:** ~600 lines of code  
**Test Coverage:** 20/20 PASSING  
**Production Ready:** YES
