# Obligations Registry API Reference

**Base URL:** `/core/obligations`  
**Authentication:** Bearer token (if configured)  
**Response Format:** JSON  
**Timezone:** UTC (ISO 8601 timestamps)

---

## Table of Contents

1. [PACK 1: Core CRUD (5 endpoints)](#pack-1-core-crud)
2. [PACK 2: Recurrence Engine (3 endpoints)](#pack-2-recurrence-engine)
3. [PACK 3: Reserve & Coverage (4 endpoints)](#pack-3-reserve--coverage)
4. [Schemas](#schemas)
5. [Error Handling](#error-handling)

---

## PACK 1: Core CRUD

### 1.1 Create Obligation

**Endpoint:** `POST /core/obligations`

**Description:** Create a new recurring obligation (bill, payment, subscription)

**Request Body:**
```json
{
  "name": "Rent",
  "amount": 1500.0,
  "currency": "CAD",
  "frequency": "monthly",
  "due_day": 1,
  "category": "housing",
  "priority": "A",
  "status": "active",
  "pay_from": "personal",
  "autopay": {
    "enabled": false
  },
  "recurrence": {
    "interval": 1,
    "day_of_month": 1,
    "timezone": "America/Toronto"
  },
  "tags": ["essential"],
  "meta": {"landlord_contact": "john@example.com"}
}
```

**Response:** `201 Created`
```json
{
  "id": "ob_6038e7c40571",
  "name": "Rent",
  "amount": 1500.0,
  "currency": "CAD",
  "frequency": "monthly",
  "due_day": 1,
  "category": "housing",
  "priority": "A",
  "status": "active",
  "pay_from": "personal",
  "autopay": {
    "enabled": false,
    "verified": false,
    "method": null,
    "payee": null,
    "reference": null,
    "notes": null
  },
  "recurrence": {
    "frequency": "monthly",
    "interval": 1,
    "day_of_month": 1,
    "day_of_week": null,
    "start_date": "2026-01-02",
    "next_due_date": "2026-02-01",
    "timezone": "America/Toronto"
  },
  "tags": ["essential"],
  "meta": {"landlord_contact": "john@example.com"},
  "created_at": "2026-01-02T14:30:45Z",
  "updated_at": "2026-01-02T14:30:45Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/core/obligations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Internet",
    "amount": 79.99,
    "currency": "CAD",
    "frequency": "monthly",
    "due_day": 15,
    "category": "utilities",
    "priority": "B",
    "autopay": {"enabled": true}
  }'
```

**Status Codes:**
- `201` - Obligation created
- `400` - Validation error (missing name/amount, invalid due_day, etc.)

---

### 1.2 List Obligations

**Endpoint:** `GET /core/obligations`

**Query Parameters:**
| Param | Type | Example | Default |
|-------|------|---------|---------|
| `status` | string | `active`, `paused`, `archived` | - |
| `frequency` | string | `monthly`, `quarterly` | - |
| `category` | string | `housing`, `utilities` | - |
| `priority` | string | `A`, `B`, `C`, `D` | - |
| `pay_from` | string | `personal` | - |

**Response:** `200 OK`
```json
{
  "count": 3,
  "obligations": [
    {
      "id": "ob_6038e7c40571",
      "name": "Rent",
      "amount": 1500.0,
      "currency": "CAD",
      "frequency": "monthly",
      "due_day": 1,
      "category": "housing",
      "priority": "A",
      "status": "active",
      "pay_from": "personal",
      "autopay": {...},
      "recurrence": {...},
      "created_at": "2026-01-02T14:30:45Z",
      "updated_at": "2026-01-02T14:30:45Z"
    }
  ]
}
```

**cURL Examples:**
```bash
# Get all active obligations
curl http://localhost:8000/core/obligations?status=active

# Get all housing expenses
curl http://localhost:8000/core/obligations?category=housing

# Get high-priority (A) items
curl http://localhost:8000/core/obligations?priority=A
```

**Status Codes:**
- `200` - Success

---

### 1.3 Get Single Obligation

**Endpoint:** `GET /core/obligations/{id}`

**Path Parameters:**
| Param | Type | Example |
|-------|------|---------|
| `id` | string | `ob_6038e7c40571` |

**Response:** `200 OK`
```json
{
  "id": "ob_6038e7c40571",
  "name": "Rent",
  "amount": 1500.0,
  "currency": "CAD",
  "frequency": "monthly",
  "due_day": 1,
  "category": "housing",
  "priority": "A",
  "status": "active",
  "pay_from": "personal",
  "autopay": {
    "enabled": false,
    "verified": false,
    "method": null,
    "payee": null,
    "reference": null,
    "notes": null
  },
  "recurrence": {
    "frequency": "monthly",
    "interval": 1,
    "day_of_month": 1,
    "start_date": "2026-01-02",
    "next_due_date": "2026-02-01",
    "timezone": "America/Toronto"
  },
  "tags": ["essential"],
  "meta": {"landlord_contact": "john@example.com"},
  "created_at": "2026-01-02T14:30:45Z",
  "updated_at": "2026-01-02T14:30:45Z"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/core/obligations/ob_6038e7c40571
```

**Status Codes:**
- `200` - Success
- `404` - Obligation not found

---

### 1.4 Update Obligation (PATCH)

**Endpoint:** `PATCH /core/obligations/{id}`

**Description:** Selectively update obligation fields. Only provided fields are updated.

**Request Body:**
```json
{
  "amount": 1600.0,
  "status": "paused",
  "priority": "B",
  "due_day": 5
}
```

**Response:** `200 OK`
```json
{
  "id": "ob_6038e7c40571",
  "name": "Rent",
  "amount": 1600.0,
  "currency": "CAD",
  "frequency": "monthly",
  "due_day": 5,
  "category": "housing",
  "priority": "B",
  "status": "paused",
  "pay_from": "personal",
  "autopay": {...},
  "recurrence": {...},
  "created_at": "2026-01-02T14:30:45Z",
  "updated_at": "2026-01-02T14:35:20Z"
}
```

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/core/obligations/ob_6038e7c40571 \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1600.0,
    "status": "active"
  }'
```

**Status Codes:**
- `200` - Updated
- `400` - Validation error
- `404` - Not found

---

### 1.5 Verify Autopay

**Endpoint:** `POST /core/obligations/{id}/verify_autopay`

**Description:** Mark autopay as verified and enable if confirmed. Use after setting up bank autopay.

**Request Body:**
```json
{
  "verified": true,
  "method": "bank_autopay",
  "payee": "LANDLORD INC",
  "reference": "UNIT 12"
}
```

**Response:** `200 OK`
```json
{
  "id": "ob_6038e7c40571",
  "verified": true,
  "enabled": true,
  "method": "bank_autopay",
  "payee": "LANDLORD INC",
  "reference": "UNIT 12",
  "next_run_due": "2026-02-01",
  "setup_guide_url": "/core/obligations/ob_6038e7c40571/autopay_guide"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/core/obligations/ob_6038e7c40571/verify_autopay \
  -H "Content-Type: application/json" \
  -d '{
    "verified": true,
    "method": "bank_autopay",
    "payee": "LANDLORD INC",
    "reference": "UNIT 12"
  }'
```

**Supported Methods:**
- `bank_autopay` - Set up with bank
- `credit_card` - Automatic charge
- `e_transfer` - E-transfer payment
- `manual` - Manual payment reminder

**Status Codes:**
- `200` - Verified and enabled
- `400` - Validation error
- `404` - Not found

---

## PACK 2: Recurrence Engine

### 2.1 Generate Upcoming Runs

**Endpoint:** `POST /core/obligations/runs/generate`

**Query Parameters:**
| Param | Type | Required | Example |
|-------|------|----------|---------|
| `start_date` | string | ✓ | `2026-01-15` |
| `end_date` | string | ✓ | `2026-03-15` |

**Description:** Generate all scheduled payment runs between two dates

**Response:** `200 OK`
```json
{
  "count": 8,
  "runs": [
    {
      "id": "run_a1b2c3d4e5f6",
      "obligation_id": "ob_6038e7c40571",
      "name": "Rent",
      "amount": 1500.0,
      "currency": "CAD",
      "due_date": "2026-02-01",
      "priority": "A",
      "pay_from": "personal",
      "autopay_enabled": false,
      "autopay_verified": false,
      "status": "scheduled",
      "created_at": "2026-01-02T14:30:45Z"
    },
    {
      "id": "run_x7y8z9a0b1c2",
      "obligation_id": "ob_internet123",
      "name": "Internet",
      "amount": 79.99,
      "currency": "CAD",
      "due_date": "2026-02-15",
      "priority": "B",
      "pay_from": "personal",
      "autopay_enabled": true,
      "autopay_verified": true,
      "status": "scheduled",
      "created_at": "2026-01-02T14:30:45Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/core/obligations/runs/generate?start_date=2026-01-15&end_date=2026-03-15"
```

**Notes:**
- Max 120 runs returned (prevents runaway generation)
- Results sorted by due_date, then priority
- Automatically calculates next due dates
- Includes autopay status for each run

**Status Codes:**
- `200` - Generated successfully
- `400` - Invalid date format or range

---

### 2.2 List Scheduled Runs

**Endpoint:** `GET /core/obligations/runs`

**Query Parameters:**
| Param | Type | Default | Example |
|-------|------|---------|---------|
| `limit` | integer | 200 | 100 |
| `offset` | integer | 0 | 50 |
| `status` | string | - | `scheduled` |

**Response:** `200 OK`
```json
{
  "count": 127,
  "limit": 50,
  "offset": 50,
  "total": 127,
  "runs": [
    {
      "id": "run_a1b2c3d4e5f6",
      "obligation_id": "ob_6038e7c40571",
      "name": "Rent",
      "amount": 1500.0,
      "currency": "CAD",
      "due_date": "2026-02-01",
      "priority": "A",
      "pay_from": "personal",
      "autopay_enabled": false,
      "autopay_verified": false,
      "status": "scheduled",
      "created_at": "2026-01-02T14:30:45Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/core/obligations/runs?limit=50&offset=0"
```

**Status Codes:**
- `200` - Success

---

### 2.3 Upcoming 30 Days (Quick Check)

**Endpoint:** `GET /core/obligations/upcoming_30`

**Description:** Convenience endpoint for upcoming 30 days without date parameters

**Response:** `200 OK`
```json
{
  "count": 4,
  "start_date": "2026-01-02",
  "end_date": "2026-02-01",
  "runs": [
    {
      "id": "run_a1b2c3d4e5f6",
      "obligation_id": "ob_6038e7c40571",
      "name": "Rent",
      "amount": 1500.0,
      "currency": "CAD",
      "due_date": "2026-02-01",
      "priority": "A",
      "pay_from": "personal",
      "autopay_enabled": false,
      "autopay_verified": false,
      "status": "scheduled",
      "created_at": "2026-01-02T14:30:45Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/core/obligations/upcoming_30
```

**Status Codes:**
- `200` - Success

---

## PACK 3: Reserve & Coverage

### 3.1 Recalculate Reserves

**Endpoint:** `POST /core/obligations/reserves/recalculate`

**Query Parameters:**
| Param | Type | Default | Range |
|-------|------|---------|-------|
| `buffer_multiplier` | float | 1.25 | ≥ 1.0 |

**Description:** Recalculate required cash reserve based on all active obligations

**Response:** `200 OK`
```json
{
  "monthly_required": 1579.99,
  "buffer_required": 1974.99,
  "buffer_multiplier": 1.25,
  "coverage": {
    "available_cash": 2500.0,
    "covered": true,
    "shortfall": null
  },
  "breakdown_by_category": {
    "housing": 1500.0,
    "utilities": 79.99
  },
  "updated_at": "2026-01-02T14:45:30Z"
}
```

**cURL Examples:**
```bash
# Use default 1.25x buffer
curl -X POST http://localhost:8000/core/obligations/reserves/recalculate

# Use custom 1.5x buffer
curl -X POST http://localhost:8000/core/obligations/reserves/recalculate?buffer_multiplier=1.5

# Use conservative 2.0x buffer
curl -X POST http://localhost:8000/core/obligations/reserves/recalculate?buffer_multiplier=2.0
```

**Status Codes:**
- `200` - Calculated successfully
- `400` - Invalid buffer multiplier (< 1.0)

---

### 3.2 Get Reserve State

**Endpoint:** `GET /core/obligations/reserves`

**Description:** Retrieve current reserve calculation state

**Response:** `200 OK`
```json
{
  "monthly_required": 1579.99,
  "buffer_required": 1974.99,
  "buffer_multiplier": 1.25,
  "coverage": {
    "available_cash": 2500.0,
    "covered": true,
    "shortfall": null
  },
  "breakdown_by_category": {
    "housing": 1500.0,
    "utilities": 79.99
  },
  "updated_at": "2026-01-02T14:45:30Z"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/core/obligations/reserves
```

**Status Codes:**
- `200` - Success

---

### 3.3 Obligations Status (Dashboard)

**Endpoint:** `GET /core/obligations/status`

**Query Parameters:**
| Param | Type | Default |
|-------|------|---------|
| `buffer_multiplier` | float | 1.25 |

**Description:** Summarized status for dashboard display

**Response:** `200 OK`
```json
{
  "ok": true,
  "covered": true,
  "monthly_required": 1579.99,
  "buffer_required": 1974.99,
  "available_cash": 2500.0,
  "autopay_verified": 1,
  "autopay_total": 2,
  "obligations_count": 2,
  "obligations_paused": 0,
  "note": "All obligations covered and 1/2 autopays verified",
  "updated_at": "2026-01-02T14:45:30Z"
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/core/obligations/status?buffer_multiplier=1.25"
```

**Status Codes:**
- `200` - Success

---

### 3.4 Autopay Setup Guide

**Endpoint:** `GET /core/obligations/{id}/autopay_guide`

**Path Parameters:**
| Param | Type | Example |
|-------|------|---------|
| `id` | string | `ob_6038e7c40571` |

**Description:** Step-by-step guide for setting up autopay for a specific obligation

**Response:** `200 OK`
```json
{
  "obligation_id": "ob_6038e7c40571",
  "obligation_name": "Rent",
  "amount": 1500.0,
  "due_day": 1,
  "next_due": "2026-02-01",
  "guide": [
    {
      "step": 1,
      "title": "Access Your Bank",
      "description": "Log into your online banking portal or mobile app"
    },
    {
      "step": 2,
      "title": "Navigate to Payments",
      "description": "Look for 'Payments', 'Transfers', or 'Bill Payments' section"
    },
    {
      "step": 3,
      "title": "Select Payee",
      "description": "Choose existing payee or add new: LANDLORD INC"
    },
    {
      "step": 4,
      "title": "Enter Amount",
      "description": "Amount: CAD $1500.00"
    },
    {
      "step": 5,
      "title": "Set Schedule",
      "description": "Frequency: Monthly, Day: 1st"
    },
    {
      "step": 6,
      "title": "Set Reference",
      "description": "Payment note/reference: UNIT 12"
    },
    {
      "step": 7,
      "title": "Review",
      "description": "Verify all details before confirming"
    },
    {
      "step": 8,
      "title": "Confirm Setup",
      "description": "Complete setup and verify in your banking system"
    }
  ]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/core/obligations/ob_6038e7c40571/autopay_guide
```

**Status Codes:**
- `200` - Success
- `404` - Obligation not found

---

## Schemas

### Frequency Enum
```
"weekly", "biweekly", "monthly", "quarterly", "annually"
```

### Status Enum
```
"active", "paused", "archived"
```

### Priority Enum
```
"A", "B", "C", "D"  (Cone-style priority)
```

### Category Examples
```
"housing", "utilities", "subscriptions", "insurance", "transportation", 
"food", "health", "education", "entertainment", "other"
```

### Recurrence Object
```json
{
  "frequency": "monthly",
  "interval": 1,
  "day_of_month": 1,
  "day_of_week": null,
  "start_date": "2026-01-02",
  "next_due_date": "2026-02-01",
  "timezone": "America/Toronto"
}
```

### AutopayConfig Object
```json
{
  "enabled": false,
  "verified": false,
  "method": null,
  "payee": null,
  "reference": null,
  "notes": null
}
```

---

## Error Handling

### Common Error Responses

**400 - Bad Request (Validation Error)**
```json
{
  "detail": "Validation error: amount must be >= 0"
}
```

**404 - Not Found**
```json
{
  "detail": "Obligation not found: ob_invalid_id"
}
```

**500 - Internal Server Error**
```json
{
  "detail": "Internal server error. Check logs."
}
```

### Validation Rules
- `name`: Required, non-empty string
- `amount`: Required, must be ≥ 0
- `currency`: Valid ISO 4217 code (CAD, USD, etc.)
- `due_day`: 1-31
- `frequency`: One of 5 enum values
- `buffer_multiplier`: Must be ≥ 1.0
- `start_date`/`end_date`: ISO 8601 format (YYYY-MM-DD)

---

## Pagination

### List Endpoints Pagination
```json
{
  "count": 50,
  "total": 127,
  "limit": 50,
  "offset": 0,
  "results": [...]
}
```

Use `limit` and `offset` for pagination:
```bash
curl "http://localhost:8000/core/obligations/runs?limit=50&offset=0"
curl "http://localhost:8000/core/obligations/runs?limit=50&offset=50"
```

---

## Rate Limiting

Currently no rate limiting. Subject to change with infrastructure.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-02 | Initial release: PACK 1-3 complete |

---

## Support

For issues, contact the governance team or check logs at `/logs/`.
