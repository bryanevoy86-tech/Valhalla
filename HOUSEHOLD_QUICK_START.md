# Household/Financial System - Quick Reference

## Endpoints Summary

| Endpoint | Method | Purpose | PACK |
|----------|--------|---------|------|
| `/core/accounts` | POST | Create account | P-ACCTS-1 |
| `/core/accounts` | GET | List accounts (optionally filter by status) | P-ACCTS-1 |
| `/core/ledger` | POST | Create transaction | P-LEDGERL-1 |
| `/core/ledger` | GET | List transactions (filter by kind/category/account_id) | P-LEDGERL-1 |
| `/core/ledger/month` | GET | Monthly report (query: prefix=YYYY-MM) | P-LEDGERL-2 |
| `/core/goals` | POST | Create goal | P-GOALS-1 |
| `/core/goals` | GET | List goals (optionally filter by status) | P-GOALS-1 |
| `/core/autopay/checklist/{obligation_id}` | GET | Get 5-step setup checklist | P-AUTOPAY-1 |
| `/core/shopping-list` | GET/POST | Shopping list operations | P-SHOP-1 |
| `/core/shopping-list/followups` | GET | Get shopping followups | P-SHOP-1 |

## Core Concepts

### Accounts (P-ACCTS-1)
- **ID Prefix:** `acc_`
- **Status:** `active`, `inactive`
- **Kind:** `checking`, `savings`, `credit`, `loan`, custom
- **Masked:** Boolean flag for sensitive account numbers
- **Currency:** ISO 4217 code (USD, EUR, GBP, etc.)

### Transactions (P-LEDGERL-1)
- **ID Prefix:** `tx_`
- **Kind:** `income`, `expense`, `transfer`
- **Category:** Free text (groceries, utilities, gas, entertainment, etc.)
- **Account ID:** Links to account (optional, allows unaccounted tracking)
- **Date:** ISO 8601 format (YYYY-MM-DD)
- **Amount:** Decimal with 2-place precision

### Ledger Reports (P-LEDGERL-2)
- **Aggregation:** Monthly (query prefix: YYYY-MM)
- **Metrics:** Total income, total expense, net (income - expense)
- **Category Breakdown:** Expense subtotals by category with transaction count
- **Example Query:** `GET /core/ledger/month?prefix=2026-02`

### Goals (P-GOALS-1)
- **ID Prefix:** `gol_`
- **Priority:** `low`, `normal`, `high` (auto-sorted in listings)
- **Status:** `active`, `paused`, `done`
- **Target Amount:** Decimal savings goal
- **Due Date:** ISO 8601 format
- **Vault ID:** Account ID where goal savings are held
- **Sorting:** Primary by priority (high→normal→low), secondary by due date

### Autopay Checklists (P-AUTOPAY-1)
- **Stateless:** No data storage (generates on request)
- **Input:** Obligation ID (bill reference)
- **Output:** 5-step checklist with titles and descriptions
- **Safety:** Safe-calls to budget_obligations (graceful if unavailable)

## Common Workflows

### Track Household Expenses
```
1. Create account → GET account ID
2. Create expense transactions → Amount, category, account_id
3. Query monthly report → GET /core/ledger/month?prefix=YYYY-MM
4. View expense breakdown → expense_by_category array in response
```

### Save for a Goal
```
1. Create account (dedicated vault) → GET account ID
2. Create goal → target_amount, vault_id, due_date, priority
3. Create income transaction → kind=income, account_id=vault_id
4. List goals → GET /core/goals (sorted by priority)
5. Track progress → Compare sum of incomes vs target_amount
```

### Set Up Bill Autopay
```
1. Get obligation ID (from bill_payments module)
2. Request checklist → GET /core/autopay/checklist/{obligation_id}
3. Follow 5-step setup guide
4. Create expense transaction → Record first autopay debit
```

## Data Query Parameters

### Ledger Transactions
```
GET /core/ledger?kind=expense&category=groceries&account_id=acc_123&limit=50
```
- `kind` - Filter by income|expense|transfer
- `category` - Filter by category string (partial match ok)
- `account_id` - Filter by account ID
- `limit` - Max results (default varies)

### Accounts
```
GET /core/accounts?status=active
```
- `status` - Filter by active|inactive

### Goals
```
GET /core/goals?status=active
```
- `status` - Filter by active|paused|done

## Response Examples

### Create Account Response
```json
{
  "id": "acc_550e8400",
  "name": "Joint Checking",
  "kind": "checking",
  "currency": "USD",
  "masked": true,
  "notes": "Primary household account",
  "status": "active",
  "created_at": "2026-02-15T10:30:00Z"
}
```

### Create Transaction Response
```json
{
  "id": "tx_6ba7b810",
  "date": "2026-02-15",
  "kind": "expense",
  "amount": 125.50,
  "category": "groceries",
  "account_id": "acc_550e8400",
  "notes": "Costco shopping",
  "created_at": "2026-02-15T14:22:15Z"
}
```

### Monthly Report Response
```json
{
  "month": "2026-02",
  "income": 5000.00,
  "expense": 1250.50,
  "net": 3749.50,
  "expense_by_category": [
    {
      "category": "groceries",
      "total": 450.00,
      "count": 8
    },
    {
      "category": "utilities",
      "total": 200.00,
      "count": 2
    },
    {
      "category": "entertainment",
      "total": 150.00,
      "count": 5
    }
  ]
}
```

### Create Goal Response
```json
{
  "id": "gol_9f7c6e5d",
  "title": "Summer Vacation",
  "target_amount": 5000.00,
  "due_date": "2026-06-01",
  "vault_id": "acc_vacation_fund",
  "priority": "high",
  "status": "active",
  "notes": "Family trip to Europe",
  "created_at": "2026-02-15T09:45:00Z"
}
```

### Autopay Checklist Response
```json
{
  "obligation_id": "bill_electric_123",
  "name": "Electric Bill",
  "steps": [
    {
      "step": 1,
      "title": "Verify account info",
      "description": "Confirm billing account number and service address"
    },
    {
      "step": 2,
      "title": "Choose payment method",
      "description": "Select bank account or credit card for autopay"
    },
    {
      "step": 3,
      "title": "Set up autopay",
      "description": "Authorize recurring payments at your financial institution"
    },
    {
      "step": 4,
      "title": "Confirm billing dates",
      "description": "Verify payment schedule and due dates"
    },
    {
      "step": 5,
      "title": "Monitor first payment",
      "description": "Track first autopay transaction to ensure accuracy"
    }
  ]
}
```

## Error Handling

### 400 Bad Request (Validation Error)
```json
{
  "detail": "name required (got empty string)"
}
```

### 404 Not Found
```json
{
  "detail": "account acc_xyz not found"
}
```

### 500 Server Error
- Rare; indicates infrastructure issue
- Check logs for details

## Storage Locations

- Accounts: `backend/data/accounts/items.json`
- Transactions: `backend/data/ledger_light/tx.json`
- Goals: `backend/data/goals/items.json`
- Shopping List: `backend/data/shopping_list/items.json`

## Testing

Run full test suite:
```bash
pytest backend/tests/test_pack_shopping_ledger_goals.py -v
```

Run specific test class:
```bash
pytest backend/tests/test_pack_shopping_ledger_goals.py::TestAccounts -v
```

Run single test:
```bash
pytest backend/tests/test_pack_shopping_ledger_goals.py::TestAccounts::test_create_account -v
```

## Implementation Files

### New Modules (18 files total)

**Accounts (4 files):**
- `backend/app/core_gov/accounts/__init__.py`
- `backend/app/core_gov/accounts/store.py`
- `backend/app/core_gov/accounts/service.py`
- `backend/app/core_gov/accounts/router.py`

**Ledger Light (5 files):**
- `backend/app/core_gov/ledger_light/__init__.py`
- `backend/app/core_gov/ledger_light/store.py`
- `backend/app/core_gov/ledger_light/service.py`
- `backend/app/core_gov/ledger_light/router.py`
- `backend/app/core_gov/ledger_light/reports.py`

**Goals (4 files):**
- `backend/app/core_gov/goals/__init__.py`
- `backend/app/core_gov/goals/store.py`
- `backend/app/core_gov/goals/service.py`
- `backend/app/core_gov/goals/router.py`

**Autopay Checklists (3 files):**
- `backend/app/core_gov/autopay_checklists/__init__.py`
- `backend/app/core_gov/autopay_checklists/service.py`
- `backend/app/core_gov/autopay_checklists/router.py`

**Shopping List Updates (1 file):**
- `backend/app/core_gov/shopping_list/ops.py`

### Modified Files
- `backend/app/core_gov/core_router.py` (added 4 router imports + 4 include_router calls)

### Test Files
- `backend/tests/test_pack_shopping_ledger_goals.py` (35 tests, 100% pass rate)

---

**Quick Start:** Create an account, add transactions, check monthly report → Full household expense tracking in 3 API calls!
