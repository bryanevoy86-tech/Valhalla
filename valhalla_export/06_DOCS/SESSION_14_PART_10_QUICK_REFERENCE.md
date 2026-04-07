# Session 14 Part 10: Quick Reference & API Examples

## Text Parsing & Intent Detection

### Parse Text
```bash
POST /core/nlp/parse
{
  "text": "rent 1500 paid on the 1st CAD"
}

Response:
{
  "ok": true,
  "kind": "bill",
  "raw": "rent 1500 paid on the 1st CAD",
  "fields": {
    "amount": 1500.0,
    "currency": "CAD",
    "date": "",
    "due_day": 1,
    "cadence": "monthly"
  }
}
```

### Get Intent
```bash
POST /core/nlp/intent
{
  "text": "running low on milk"
}

Response:
{
  "ok": true,
  "intent": "shopping.quick_add_candidate",
  "candidate": {
    "name": "milk",
    "est_total": 0.0,
    "category": "household",
    "notes": "running low on milk"
  }
}
```

### Text→Intent→Create (Heimdall)
```bash
POST /core/heimdall/capture
{
  "text": "internet 79.99 due on 15th",
  "mode": "explore"  # or "execute" (requires cone approval)
}

Response:
{
  "ok": true,
  "mode": "explore",
  "intent": {
    "ok": true,
    "intent": "bill.create_candidate",
    "candidate": {...}
  },
  "created": null  # created only if mode=execute
}
```

## Subscription Management

### Create Subscription
```bash
POST /core/subscriptions
{
  "name": "Netflix",
  "amount": 15.99,
  "cadence": "monthly",
  "renewal_day": 1,
  "currency": "CAD",
  "category": "entertainment"
}

Response:
{
  "id": "sub_abc123xyz",
  "name": "Netflix",
  "amount": 15.99,
  "currency": "CAD",
  "cadence": "monthly",
  "renewal_day": 1,
  "status": "active",
  "created_at": "2026-01-03T...",
  "updated_at": "2026-01-03T..."
}
```

### List Subscriptions
```bash
GET /core/subscriptions?status=active&limit=50
```

### Audit Subscriptions
```bash
GET /core/subscriptions/audit

Response:
{
  "active_count": 5,
  "annualized_total": 487.80,
  "duplicates": [
    [
      {"id": "sub_1", "name": "hulu"},
      {"id": "sub_2", "name": "hulu"}
    ]
  ]
}
```

### Push Reminders
```bash
POST /core/subscriptions/push_reminders?days_ahead=7
```

## Asset Lifecycle

### Create Asset
```bash
POST /core/assets
{
  "name": "Refrigerator",
  "kind": "appliance",
  "purchase_date": "2023-01-15T00:00:00",
  "purchase_price": 1200.0,
  "warranty_months": 24,
  "serial": "RF-2023-001",
  "location": "Kitchen"
}
```

### Warranty Report
```bash
GET /core/assets/warranty_report?limit=50

Response:
{
  "items": [
    {
      "id": "ast_xyz",
      "name": "Refrigerator",
      "purchase_date": "2023-01-15T00:00:00",
      "expires": "2025-01-15",
      "months": 24
    }
  ]
}
```

### Add Maintenance
```bash
POST /core/assets/maintenance
{
  "asset_id": "ast_xyz",
  "title": "Oil change",
  "cadence": "quarterly",
  "due_date": "2026-02-15"
}
```

### Replace Soon Item
```bash
POST /core/assets/replace
{
  "title": "Mattress",
  "within_days": 60,
  "est_cost": 800.0,
  "notes": "King size, memory foam"
}
```

### Push Replace to Shopping
```bash
POST /core/assets/replace/push_to_shopping?threshold=200.0
```

## Family Routines

### Create Routine
```bash
POST /core/routines
{
  "title": "Saturday Chores",
  "freq": "weekly",
  "day_of_week": "sat",
  "items": ["vacuum", "laundry", "bathrooms", "kitchen"],
  "notes": "Weekly household maintenance"
}
```

### Start Routine Run
```bash
POST /core/routines/{routine_id}/start
{
  "run_date": "2026-01-04"  # optional, defaults to today
}

Response:
{
  "id": "run_abc123",
  "routine_id": "rt_xyz",
  "run_date": "2026-01-04",
  "done": [],
  "status": "open",
  "created_at": "2026-01-03T..."
}
```

### Check Item
```bash
POST /core/routines/runs/{run_id}/check
{
  "item": "vacuum"
}
```

### Complete Run
```bash
POST /core/routines/runs/{run_id}/complete
```

## Cashflow Forecasting

### 30-Day Forecast
```bash
GET /core/cashflow?days=30

Response:
{
  "days": 30,
  "items": [
    {
      "date": "2026-01-15",
      "type": "bill",
      "name": "Rent",
      "amount": 1500.0,
      "currency": "CAD"
    }
  ],
  "estimated_total": 3500.0,
  "warnings": []
}
```

### Cashflow with Buffer Check
```bash
GET /core/cashflow/with_buffer?days=30&buffer_min=500.0

Response:
{
  "cashflow": {...},
  "budget_impact": {...}
}
```

## Personal Dashboard

### Get Full Board
```bash
GET /core/personal_board

Response:
{
  "inbox": {...},
  "cashflow_30": {...},
  "subscriptions_audit": {...},
  "warranty_report": {...},
  "shopping_estimate": {...},
  "runout_forecast": {...}
}
```

## Heimdall Dispatcher (Enhanced)

### Execute Personal Board
```bash
POST /core/heimdall/do
{
  "mode": "explore",
  "action": "personal_board.get",
  "data": {}
}
```

### Execute Cashflow
```bash
POST /core/heimdall/do
{
  "mode": "explore",
  "action": "cashflow.get",
  "data": {"days": 60}
}
```

### Audit Subscriptions
```bash
POST /core/heimdall/do
{
  "mode": "explore",
  "action": "subscriptions.audit",
  "data": {}
}
```

## File Structure Reference

| Module | Data File | ID Prefix |
|--------|-----------|-----------|
| subscriptions | `backend/data/subscriptions/subs.json` | `sub_` |
| assets | `backend/data/assets/assets.json` | `ast_` |
| maintenance | `backend/data/assets/maintenance.json` | `mnt_` |
| replace | `backend/data/assets/replace.json` | `rep_` |
| routines | `backend/data/routines/routines.json` | `rt_` |
| runs | `backend/data/routines/runs.json` | `run_` |

## Workflow Examples

### Complete Flow: From Voice to Bill Creation
```
1. User: "internet bill 80 paid on 15th"
2. POST /core/heimdall/capture
   {
     "text": "internet bill 80 paid on 15th",
     "mode": "execute"
   }
3. System:
   - Parses text → bill kind
   - Infers fields (amount=80, due_day=15, cadence=monthly)
   - Gets intent (bill.create_candidate)
   - Cone policy check
   - Creates bill record
   - Logs action to heimdall.log
```

### Approval Workflow: Replace→Shopping→Approval
```
1. Asset item (mattress) marked "replace within 60 days"
2. Scheduler tick → push_replace_to_shopping()
3. Creates shopping item (est_cost=$800)
4. Since $800 ≥ $200 threshold → auto-creates approval request
5. User sees in approvals queue
6. Approves → shopping transitions to "approved" status
```

### Dashboard Monitoring
```
1. Personal calls GET /core/personal_board
2. Gets aggregated view:
   - Pending inbox items
   - Next 30 days of cashflow
   - Subscription audit (duplicates, total)
   - Warranty expiry dates
   - Shopping estimate
   - Inventory runout forecast
3. Single call replaces 6 module calls
```

## Deployment Complete ✅

All 20 PACKs tested and deployed. Routers registered in core_router. Integration hooks in scheduler, heimdall, ops_board. Ready for production use.
