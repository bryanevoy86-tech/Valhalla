# Payment Management System - API Quick Reference

## Core Endpoints

### Payments Registry

```
# Create payment
POST /core/payments
  name: "Netflix"
  amount: 16.99
  cadence: "monthly"
  currency: "CAD"
  due_day: 15
  kind: "subscription"
  payee: "Netflix Inc."
  autopay_enabled: true

# List payments
GET /core/payments
GET /core/payments?status=active
GET /core/payments?status=active&limit=50

# Get specific payment
GET /core/payments/{payment_id}

# Update payment
PATCH /core/payments/{payment_id}
  { "amount": 17.99, "status": "active" }

# Get next due date
GET /core/payments/{payment_id}/next_due
→ { "payment_id": "...", "next_due": "2026-02-15" }

# Get schedule
GET /core/payments/schedule/upcoming
GET /core/payments/schedule/upcoming?days=30&limit=500
→ { "items": [
    { "date": "2026-01-15", "payment_id": "...", "name": "Netflix", "amount": 16.99, ... },
    ...
  ]}

# Import from bills & subs
POST /core/payments/import_from_bills_and_subs
→ { "created": 12, "warnings": [...] }

# Export all
GET /core/payments/export
GET /core/payments/export?days=90
→ { "payments": [...], "upcoming": [...], "confirmations": [...] }

# Push reminders
POST /core/payments/push_reminders
POST /core/payments/push_reminders?days_ahead=5
```

### Autopay Management

```
# Enable/disable autopay
POST /core/payments/{payment_id}/autopay_enabled
POST /core/payments/{payment_id}/autopay_enabled?enabled=true
→ { "ok": true, "payment": {...} }

# Mark verified
POST /core/payments/{payment_id}/autopay_verified
POST /core/payments/{payment_id}/autopay_verified?verified=true&proof_note="Email confirmed"
→ { "ok": true, "payment": {...} }

# Get autopay playbook
GET /core/autopay/playbook
GET /core/autopay/playbook?country=CA
→ { "country": "CA", "steps": [...] }
```

### Payment Confirmations

```
# Log confirmation
POST /core/pay_confirm
  payment_id: "pay_xxx"
  paid_on: "2026-01-04"
  amount: 16.99
  currency: "CAD"
  method: "PAD"
  ref: "XXXX1234"

# List confirmations
GET /core/pay_confirm
GET /core/pay_confirm?payment_id=pay_xxx
GET /core/pay_confirm?date_from=2026-01-01&date_to=2026-01-31

# Post confirmation to ledger
POST /core/pay_confirm/{confirm_id}/post_to_ledger
→ { "ok": true, "tx": {...} }
```

### Reconciliation

```
# Check reconciliation status
GET /core/reconcile/payments
GET /core/reconcile/payments?days=30
→ {
    "ok": true,
    "matched": 8,
    "missing": [
      { "date": "2026-01-04", "payment_id": "...", "name": "...", "amount": 99.99 }
    ],
    "due_count": 10
  }

# Push missing payment alerts
POST /core/reconcile/payments/push_alerts
POST /core/reconcile/payments/push_alerts?days=30
→ { "created": 2, "warnings": [...] }
```

### Failure Playbook

```
# Get failure playbook
GET /core/fail_playbooks/payment_failed
→ {
    "steps": [
      "1) Confirm whether the bank declined (NSF) or vendor rejected...",
      ...
    ],
    "templates": {
      "vendor_call": "Hi, this is regarding a failed payment draft...",
      "bank_call": "Hi, I need to confirm why a pre-authorized debit..."
    }
  }
```

### Shield Lite (Protection Mode)

```
# Get current state
GET /core/shield_lite
→ {
    "updated_at": "...",
    "enabled": true,
    "active": false,
    "reason": "",
    "triggered_at": "",
    "notes": ""
  }

# Activate protection
POST /core/shield_lite/activate
POST /core/shield_lite/activate?reason=buffer_risk&notes="..."
→ { "ok": true, "state": {...} }

# Deactivate protection
POST /core/shield_lite/deactivate
POST /core/shield_lite/deactivate?notes="Buffer recovered"
→ { "ok": true, "state": {...} }

# Auto-check shield
POST /core/shield_lite/auto_check
POST /core/shield_lite/auto_check?buffer_min=500.0
→ {
    "ok": true,
    "triggered": false,
    "budget_impact": {...}
  }
```

### Audit Log

```
# List audit log
GET /core/audit_log
GET /core/audit_log?limit=200
→ { "items": [
    { "id": "aud_...", "ts": "...", "area": "payments", "action": "create", "ref_id": "pay_...", "meta": {...} },
    ...
  ]}

# Append to audit log
POST /core/audit_log
  area: "payments"
  action: "manual_override"
  ref_id: "pay_xxx"
  meta: { "reason": "Customer request" }
```

## Integrated Dashboard Endpoints

### Personal Board

```
GET /core/personal_board
→ {
    "payments_upcoming": { "items": [...] },
    "payments_reconcile": { "ok": true, "matched": 8, "missing": [...] },
    "shield_lite": { "enabled": true, "active": false, ... },
    ...
  }
```

### Cashflow (Enhanced)

```
GET /core/cashflow
GET /core/cashflow?days=30
→ {
    "items": [...],
    "payments": [...],
    "estimated_total": 5432.10,
    ...
  }
```

## Heimdall Actions (AI Agent)

```
# Safe Actions (Explore Mode)
payments.schedule       → {"items": [...]}
payments.reconcile      → {"ok": true, "matched": ..., "missing": [...]}
payments.push_reminders → {"created": 5, "warnings": [...]}
shield.auto_check       → {"ok": true, "triggered": false, ...}
shield.state            → {"enabled": true, "active": false, ...}

# Exec Actions (Execute Mode)
pay_confirm.create      → {"id": "pc_...", "payment_id": "...", ...}
payments.autopay_verified → {"ok": true, "payment": {...}}
```

## Data Models

### Payment
```json
{
  "id": "pay_xxxxxxxxxxxx",
  "name": "Netflix",
  "kind": "subscription|bill|other",
  "payee": "Netflix Inc.",
  "amount": 16.99,
  "currency": "CAD",
  "cadence": "once|weekly|biweekly|monthly|quarterly|yearly",
  "due_day": 1-31,
  "next_due_override": "2026-02-15",
  "autopay_enabled": true,
  "autopay_verified": true,
  "account_id": "",
  "status": "active|paused|cancelled",
  "notes": "any notes",
  "created_at": "2026-01-04T...",
  "updated_at": "2026-01-04T..."
}
```

### Scheduled Payment
```json
{
  "date": "2026-01-15",
  "payment_id": "pay_xxx",
  "name": "Netflix",
  "kind": "subscription",
  "amount": 16.99,
  "currency": "CAD",
  "autopay_enabled": true,
  "autopay_verified": true
}
```

### Confirmation
```json
{
  "id": "pc_xxxxxxxxxxxx",
  "payment_id": "pay_xxx",
  "paid_on": "2026-01-04",
  "amount": 16.99,
  "currency": "CAD",
  "method": "PAD|eTRANSFER|CARD|MANUAL",
  "ref": "XXXX1234",
  "notes": "any notes",
  "created_at": "2026-01-04T..."
}
```

## Quick Examples

### Scenario 1: Create and schedule a new bill

```bash
# 1. Create the payment
curl -X POST http://localhost:8000/core/payments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Utility Bill",
    "amount": 125.00,
    "cadence": "monthly",
    "due_day": 5,
    "kind": "bill",
    "status": "active"
  }'
# Returns: { "id": "pay_abc123", ... }

# 2. Get upcoming schedule
curl http://localhost:8000/core/payments/schedule/upcoming?days=30

# 3. Enable autopay
curl -X POST http://localhost:8000/core/payments/pay_abc123/autopay_enabled?enabled=true

# 4. Mark verified
curl -X POST http://localhost:8000/core/payments/pay_abc123/autopay_verified?verified=true&proof_note="Email confirmed by utility company"
```

### Scenario 2: Log and reconcile a payment

```bash
# 1. Log confirmation
curl -X POST http://localhost:8000/core/pay_confirm \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_abc123",
    "paid_on": "2026-01-05",
    "amount": 125.00,
    "method": "PAD",
    "ref": "PAD20260105"
  }'

# 2. Check reconciliation
curl http://localhost:8000/core/reconcile/payments?days=30

# 3. Push alerts for any missing
curl -X POST http://localhost:8000/core/reconcile/payments/push_alerts
```

### Scenario 3: Activate budget protection

```bash
# 1. Check current state
curl http://localhost:8000/core/shield_lite

# 2. Auto-check and trigger if needed
curl -X POST http://localhost:8000/core/shield_lite/auto_check?buffer_min=500.0

# 3. Manual activation if needed
curl -X POST http://localhost:8000/core/shield_lite/activate?reason=emergency&notes="Unexpected expense"
```

## Error Handling

All endpoints return standardized responses:

```json
// Success
{ "ok": true, "data": {...} }
{ "id": "...", "name": "...", ...properties... }
{ "created": 5, "warnings": [...] }

// Error (4xx)
{ "detail": "payment_id and paid_on required" }

// Error (5xx)
{ "ok": false, "error": "payments unavailable: ImportError: ..." }
```

## Rate Limiting

- Payment create: No limit
- Payment list: No limit
- Schedule generation: Caches internally
- Reconciliation: Heavy operation, may take 1-2 seconds for large datasets
- Alerts: Batched, up to 100 per call

## Data Retention

- Payments: Unlimited (until deleted)
- Confirmations: 200,000 rolling window (oldest purged)
- Audit log: 200,000 rolling window
- Shield state: 1 record (overwritten)

---

**Last Updated:** January 4, 2026
