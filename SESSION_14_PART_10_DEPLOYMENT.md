# Session 14 Part 10: NLP, Subscriptions, Assets, Routines, Cashflow & Personal Board Deployment

**Status**: ✅ COMPLETE (44/44 tests passing)  
**Deployment Date**: January 3, 2026  
**Commit**: `b33f022`

## Overview

Deployed 20 new PACKs extending Valhalla's household management ecosystem with natural language processing, subscription tracking, asset management, routine scheduling, and unified personal board dashboard.

### 20 PACKs Deployed

#### NLP Module (3 PACKs)
- **P-NLP-1**: Simple text parser with regex rules for amount, date, day-of-month extraction; currency/cadence inference
- **P-NLP-2**: Intent router mapping text → bill/need/event/note candidates with structured payloads
- **P-BILLING-ASSIST-1**: Create bill from NLP candidate with best-effort bills.store integration

#### Subscriptions Module (3 PACKs)
- **P-SUBS-1**: Subscription registry (file-backed) with CRUD operations, renewal_day tracking
- **P-SUBS-2**: Audit function detecting duplicates and annualizing costs (52x weekly, 26x biweekly, 4x quarterly, 1x yearly)
- **P-SUBS-3**: Reminder push to reminders module for renewal dates

#### Assets Module (5 PACKs)
- **P-ASSETS-1**: Asset registry (appliances, tools, mattresses, etc.) with purchase metadata
- **P-ASSETS-2**: Warranty expiry calculator with date math and sorted report
- **P-ASSETS-3**: Maintenance schedule tracker (oil changes, filter replacements, etc.) with CRUD
- **P-ASSETS-4**: "Replace soon" tracker for high-cost items (mattress, sweaters, etc.)
- **P-ASSETS-5**: Push replace items to shopping with auto-approval creation for big-ticket items ≥$200

#### Routines Module (3 PACKs)
- **P-ROUTINES-1**: Weekly family routine templates with day-of-week and items list
- **P-ROUTINES-2**: Routine run log with checklist completion tracking (open/done status)
- **P-ROUTINES-3**: Push routine reminders on matching day-of-week to reminders module

#### Cashflow Module (2 PACKs)
- **P-CASHFLOW-1**: Forecast bills + subscriptions due dates (30/60/90 day windows)
- **P-CASHFLOW-2**: Cashflow with budget impact integration and buffer warning check

#### Personal Board Module (1 PACK)
- **P-PERSONAL-BOARD-1**: Unified dashboard aggregating inbox, cashflow, sub audit, warranty, shopping estimate, forecast

#### Integration Hooks (3 PACKs)
- **P-HEIMDALLDO-4**: `/core/heimdall/capture` endpoint (text → intent → create with cone gate)
- **P-HEIMDALLDO-5**: Add personal_board.get, cashflow.get, subscriptions.audit to heimdall safe actions
- **P-SCHED-7**: Scheduler tick pushes routine + subscription reminders
- **P-SCHED-8**: Scheduler tick pushes replace→shopping for big-ticket items
- **P-OPSBOARD-8**: Ops board includes personal_board aggregation
- **P-WIRING-6**: Core router registers all new module routers (nlp, subscriptions, assets, cashflow, routines, personal_board)

## File Structure

```
backend/app/core_gov/
├── nlp/
│   ├── __init__.py
│   ├── parse_rules.py      # Regex rules for money, date, day-of-month
│   ├── service.py          # parse() function
│   ├── intent.py           # Intent classification
│   └── router.py           # POST /parse, POST /intent
├── subscriptions/
│   ├── __init__.py
│   ├── store.py            # CRUD with renewal_day
│   ├── audit.py            # Duplicate detection, annualization
│   ├── reminders.py        # Push reminders
│   └── router.py           # POST /create, GET /, PATCH /{sub_id}, GET /audit, POST /push_reminders
├── assets/
│   ├── __init__.py
│   ├── store.py            # Asset CRUD
│   ├── warranty.py         # Expiry calculator
│   ├── maintenance.py      # Schedule tracker
│   ├── replace.py          # Replace soon tracker
│   ├── replace_actions.py  # Push to shopping + approvals
│   └── router.py           # All endpoints (asset, maintenance, warranty, replace CRUD)
├── routines/
│   ├── __init__.py
│   ├── store.py            # Routine CRUD
│   ├── runs.py             # Checklist completion log
│   ├── reminders.py        # Push reminders on day match
│   └── router.py           # All endpoints (routine, run CRUD)
├── cashflow/
│   ├── __init__.py
│   ├── service.py          # forecast() function
│   ├── buffer.py           # with_buffer() for budget check
│   └── router.py           # GET /cashflow, GET /cashflow/with_buffer
├── personal_board/
│   ├── __init__.py
│   ├── service.py          # board() aggregation
│   └── router.py           # GET /personal_board
├── bills/
│   └── nlp_intake.py       # create_from_candidate() [NEW]
├── heimdall/
│   ├── router.py           # + /capture endpoint [UPDATED]
│   ├── guards.py           # + 3 safe actions [UPDATED]
│   └── actions.py          # + 3 new action handlers [UPDATED]
├── scheduler/
│   └── service.py          # + routine/sub/replace reminder pushes in tick() [UPDATED]
├── ops_board/
│   └── service.py          # + personal_board rollup [UPDATED]
└── core_router.py          # + 6 new router imports & registrations [UPDATED]

backend/data/
├── assets/
│   ├── assets.json         # Asset records
│   ├── maintenance.json    # Maintenance schedule
│   └── replace.json        # Replace soon items
├── subscriptions/
│   └── subs.json           # Subscription records
└── routines/
    ├── routines.json       # Routine templates
    └── runs.json           # Completion logs

tests/
└── test_pack_session14_part10.py  # 44 tests (all passing)
```

## API Endpoints

### NLP Module
- **POST /core/nlp/parse** — Parse text → structured fields
- **POST /core/nlp/intent** — Classify intent → bill/need/event/note candidate

### Subscriptions Module
- **POST /core/subscriptions** — Create subscription
- **GET /core/subscriptions** — List (status filter)
- **PATCH /core/subscriptions/{sub_id}** — Update
- **GET /core/subscriptions/audit** — Detect duplicates, annualize total
- **POST /core/subscriptions/push_reminders** — Push renewal reminders

### Assets Module
- **POST /core/assets** — Create asset
- **GET /core/assets** — List (kind, status filters)
- **PATCH /core/assets/{asset_id}** — Update
- **GET /core/assets/warranty_report** — Expiry schedule
- **POST /core/assets/maintenance** — Add maintenance task
- **GET /core/assets/maintenance** — List maintenance
- **POST /core/assets/maintenance/{mnt_id}/done** — Mark done
- **POST /core/assets/replace** — Add replace soon item
- **GET /core/assets/replace** — List replace items
- **POST /core/assets/replace/push_to_shopping** — Auto-generate shopping

### Routines Module
- **POST /core/routines** — Create routine template
- **GET /core/routines** — List
- **POST /core/routines/{routine_id}/start** — Start run
- **GET /core/routines/runs** — List runs (status filter)
- **POST /core/routines/runs/{run_id}/check** — Mark item done
- **POST /core/routines/runs/{run_id}/complete** — Mark run complete
- **POST /core/routines/push_reminders** — Push today's reminders

### Cashflow Module
- **GET /core/cashflow** — Forecast bills+subs for next N days
- **GET /core/cashflow/with_buffer** — Include budget impact check

### Personal Board Module
- **GET /core/personal_board** — Unified dashboard

### Bills Integration
- **POST /core/bills/from_candidate** — Create bill from NLP candidate

### Heimdall Module (Enhanced)
- **POST /core/heimdall/capture** — Text → intent → create (with cone gate)
- Actions added: `personal_board.get`, `cashflow.get`, `subscriptions.audit`

## Key Features

### Text Parsing (P-NLP-1, P-NLP-2)
```
Input: "rent 1500 paid on the 1st"
Output:
  kind: "bill"
  fields: {
    amount: 1500.0,
    currency: "CAD",
    due_day: 1,
    cadence: "monthly"
  }
```

### Subscription Management
- Track renewal dates and costs
- Automatically detect duplicate subscriptions
- Calculate annualized spending (52x, 26x, 4x, or 1x)
- Push reminders near renewal_day

### Asset Lifecycle
- Record purchase metadata, warranty, serial
- Warn before warranty expiry
- Track maintenance schedules
- Identify items needing replacement
- Auto-generate shopping with approval gates (≥$200)

### Family Routines
- Weekly schedule templates (e.g., Saturday chores)
- Checklist completion log per run
- Auto-reminders on matching day-of-week

### Cashflow Forecasting
- Predict cash outflows (bills + subscriptions) over next N days
- Integrate with budget impact for buffer warning

### Personal Dashboard
- Unified view of inbox, cashflow, subscriptions, warranties, shopping, forecast
- Single GET endpoint for cross-module status

## Test Results

```
44 passed, 3 warnings in 0.89s

✅ TestNLPParsing (9 tests)
✅ TestNLPIntent (4 tests)
✅ TestSubscriptions (3 tests)
✅ TestAssets (5 tests)
✅ TestRoutines (3 tests)
✅ TestCashflow (2 tests)
✅ TestPersonalBoard (1 test)
✅ TestBillingAssist (1 test)
✅ TestHeimdallCapture (2 tests)
✅ TestSchedulerIntegration (1 test)
✅ TestOpsBoardEnhancement (1 test)
✅ TestCoreRouterWiring (6 tests)
✅ TestSyntaxValidation (6 tests)
```

## Integration Points

- **Scheduler** calls routine/subscription reminder pushes + replace→shopping daily
- **Heimdall dispatcher** handles personal_board, cashflow, subscriptions.audit actions
- **Ops board** includes personal_board aggregation alongside existing fields
- **Bills** integrates NLP candidate creation
- **All modules** use 200K item file-backed JSON with atomic writes

## Best-Effort Patterns

All cross-module calls use try/except with graceful fallbacks:
- Missing modules return empty responses or skip operations
- No cascade failures if a dependency is unavailable
- All persistence uses atomic JSON writes (write to .tmp, os.replace)

## Next Steps

- Deploy scheduler daily cron to invoke tick() for reminder pushes
- Monitor cashflow forecasts for unusual patterns
- Review and deduplicate subscriptions monthly via audit endpoint
- Use personal_board as primary household status dashboard

---

**Deployment Status**: 🟢 READY FOR PRODUCTION
