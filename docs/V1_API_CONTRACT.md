# V1 API Contract Freeze

**Version:** 1.0  
**Date:** March 29, 2026  
**Backend:** https://valhalla-api-ha6a.onrender.com  
**Status:** STABLE FOR V1 FRONTEND INTEGRATION  

---

## Table of Contents

1. [Lead Management (Intake)](#lead-management-intake)
2. [Deal Management](#deal-management)
3. [Audit & Traceability](#audit--traceability)
4. [Governance & Go-Live](#governance--go-live)
5. [Health & Documentation](#health--documentation)
6. [Error Handling](#error-handling)
7. [Authentication](#authentication)

---

## Lead Management (Intake)

### Create Lead

```
POST /api/leads/
```

**Description:** Create a new lead record.

**Request Body (JSON):**
```json
{
  "lead_name": "string",           // REQUIRED: Contact name
  "lead_email": "string",          // REQUIRED: Email address
  "lead_phone": "string",          // REQUIRED: Phone number
  "property_address": "string",    // REQUIRED: Street address
  "property_city": "string",       // REQUIRED: City
  "property_state": "string",      // REQUIRED: State (e.g., "CA")
  "property_zip": "string",        // REQUIRED: ZIP code
  "estimated_arv": "number",       // REQUIRED: Estimated After-Repair Value
  "source": "string",              // REQUIRED: Lead source (e.g., "website", "email", "api")
  "lead_status": "string",         // REQUIRED: Initial status (e.g., "new", "qualified")
  "notes": "string"                // OPTIONAL: Additional notes
}
```

**Success Response (201 Created):**
```json
{
  "id": "uuid-string",
  "lead_name": "John Doe",
  "lead_email": "john@example.com",
  "lead_phone": "+1-555-0100",
  "property_address": "123 Main St",
  "property_city": "San Francisco",
  "property_state": "CA",
  "property_zip": "94102",
  "estimated_arv": 1200000,
  "source": "website",
  "lead_status": "new",
  "notes": "High priority",
  "created_at": "2026-03-29T10:30:00Z",
  "updated_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` — Missing required field or invalid data type
- `422 Unprocessable Entity` — Validation failed (e.g., invalid email)
- `500 Internal Server Error` — Database write failed

**Example Error:**
```json
{
  "detail": "Lead must have lead_email"
}
```

---

### List Leads

```
GET /api/leads/?skip=0&limit=100&status=qualified
```

**Description:** Retrieve paginated list of all leads with optional filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip (for pagination) |
| `limit` | integer | 100 | Max records to return (max 1000) |
| `status` | string | (none) | Filter by lead_status (optional) |

**Success Response (200 OK):**
```json
[
  {
    "id": "uuid-1",
    "lead_name": "John Doe",
    "lead_email": "john@example.com",
    "lead_phone": "+1-555-0100",
    "property_address": "123 Main St",
    "property_city": "San Francisco",
    "property_state": "CA",
    "property_zip": "94102",
    "estimated_arv": 1200000,
    "source": "website",
    "lead_status": "qualified",
    "notes": "High priority",
    "created_at": "2026-03-29T10:30:00Z",
    "updated_at": "2026-03-29T10:30:00Z"
  },
  {
    "id": "uuid-2",
    "lead_name": "Jane Smith",
    ...
  }
]
```

**Error Responses:**
- `400 Bad Request` — Invalid query parameter (e.g., `limit=invalid`)
- `500 Internal Server Error` — Database read failed

---

### Get Lead by ID

```
GET /api/leads/{lead_id}
```

**Description:** Retrieve a single lead record by ID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `lead_id` | UUID | The lead's unique ID |

**Success Response (200 OK):**
```json
{
  "id": "uuid-string",
  "lead_name": "John Doe",
  "lead_email": "john@example.com",
  "lead_phone": "+1-555-0100",
  "property_address": "123 Main St",
  "property_city": "San Francisco",
  "property_state": "CA",
  "property_zip": "94102",
  "estimated_arv": 1200000,
  "source": "website",
  "lead_status": "qualified",
  "notes": "High priority",
  "created_at": "2026-03-29T10:30:00Z",
  "updated_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` — Lead ID does not exist
- `500 Internal Server Error` — Database read failed

---

### Update Lead Status

```
PUT /api/leads/{lead_id}/status
```

**Description:** Update the status of a lead (qualified, rejected, follow-up, etc.).

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `lead_id` | UUID | The lead's unique ID |

**Request Body (JSON):**
```json
{
  "status": "qualified"  // New status value
}
```

**Valid Status Values:**
- `"new"` — Fresh lead, not yet reviewed
- `"qualified"` — Lead meets investment criteria
- `"rejected"` — Lead does not meet criteria
- `"follow-up"` — Lead requires additional follow-up
- `"converted"` — Lead converted to deal

**Success Response (200 OK):**
```json
{
  "id": "uuid-string",
  "lead_name": "John Doe",
  "lead_email": "john@example.com",
  "property_address": "123 Main St",
  "property_city": "San Francisco",
  "property_state": "CA",
  "property_zip": "94102",
  "estimated_arv": 1200000,
  "source": "website",
  "lead_status": "qualified",
  "notes": "High priority",
  "created_at": "2026-03-29T10:30:00Z",
  "updated_at": "2026-03-29T11:45:00Z"  // Updated timestamp
}
```

**Error Responses:**
- `404 Not Found` — Lead ID does not exist
- `400 Bad Request` — Invalid status value
- `422 Unprocessable Entity` — Validation failed
- `500 Internal Server Error` — Database write failed

---

### Delete Lead

```
DELETE /api/leads/{lead_id}
```

**Description:** Delete a lead record.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `lead_id` | UUID | The lead's unique ID |

**Success Response (204 No Content):**
```
(empty body)
```

**Error Responses:**
- `404 Not Found` — Lead ID does not exist
- `500 Internal Server Error` — Database write failed

---

## Deal Management

### Create Deal

```
POST /api/deals
```

**Description:** Create a new deal brief record. Requires builder key authentication.

**Authentication:**
- Header: `X-Builder-Key: <key_value>` (required)

**Request Body (JSON):**
```json
{
  "headline": "string",          // REQUIRED: Deal title
  "region": "string",            // REQUIRED: Geographic region (e.g., "SF Bay Area")
  "property_type": "string",     // REQUIRED: Type (e.g., "single-family", "multi-family")
  "price": "number",             // REQUIRED: Purchase/list price
  "beds": "integer",             // REQUIRED: Number of bedrooms
  "baths": "integer",            // REQUIRED: Number of bathrooms
  "notes": "string",             // OPTIONAL: Additional details
  "status": "string"             // OPTIONAL: Deal status (e.g., "active", "pending")
}
```

**Success Response (201 Created):**
```json
{
  "id": "uuid-string",
  "headline": "Prime SF Investment - Excellent Condition",
  "region": "SF Bay Area",
  "property_type": "single-family",
  "price": 1500000,
  "beds": 3,
  "baths": 2,
  "notes": "Recently renovated, turnkey property",
  "status": "active",
  "created_at": "2026-03-29T10:30:00Z",
  "updated_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` — Missing or invalid builder key
- `400 Bad Request` — Missing required field
- `422 Unprocessable Entity` — Validation failed
- `500 Internal Server Error` — Database write failed

---

### List Deals

```
GET /api/deals?status=active&limit=50
```

**Description:** Retrieve paginated list of deal briefs with optional filtering. Requires builder key.

**Authentication:**
- Header: `X-Builder-Key: <key_value>` (optional for this endpoint in V1, required in future)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | (none) | Filter by deal status (optional) |
| `limit` | integer | 500 | Max records to return (capped at 500) |

**Valid Status Values:**
- `"active"` — Deal is currently available
- `"pending"` — Deal under review
- `"closed"` — Deal completed
- `"withdrawn"` — Deal withdrawn

**Success Response (200 OK):**
```json
[
  {
    "id": "uuid-1",
    "headline": "Prime SF Investment - Excellent Condition",
    "region": "SF Bay Area",
    "property_type": "single-family",
    "price": 1500000,
    "beds": 3,
    "baths": 2,
    "notes": "Recently renovated, turnkey property",
    "status": "active",
    "created_at": "2026-03-29T10:30:00Z",
    "updated_at": "2026-03-29T10:30:00Z"
  },
  {
    "id": "uuid-2",
    ...
  }
]
```

**Error Responses:**
- `400 Bad Request` — Invalid query parameter
- `500 Internal Server Error` — Database read failed

---

### Get Deal by ID

```
GET /api/deals/{deal_id}
```

**Description:** Retrieve a single deal brief by ID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `deal_id` | UUID | The deal's unique ID |

**Success Response (200 OK):**
```json
{
  "id": "uuid-string",
  "headline": "Prime SF Investment - Excellent Condition",
  "region": "SF Bay Area",
  "property_type": "single-family",
  "price": 1500000,
  "beds": 3,
  "baths": 2,
  "notes": "Recently renovated, turnkey property",
  "status": "active",
  "created_at": "2026-03-29T10:30:00Z",
  "updated_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found` — Deal ID does not exist
- `500 Internal Server Error` — Database read failed

---

## Audit & Traceability

### Log Audit Event

```
POST /api/audit/
```

**Description:** Log an audit event (automated or manual).

**Request Body (JSON):**
```json
{
  "action": "string",            // REQUIRED: Action taken (e.g., "created", "updated", "deleted")
  "entity_type": "string",       // REQUIRED: Entity type (e.g., "Lead", "Deal", "Account")
  "entity_id": "string",         // REQUIRED: ID of entity affected
  "previous_value": "string",    // OPTIONAL: Previous state (for update actions)
  "new_value": "string",         // OPTIONAL: New state (for update actions)
  "user_id": "string",           // OPTIONAL: User who performed action
  "notes": "string"              // OPTIONAL: Additional notes
}
```

**Success Response (201 Created):**
```json
{
  "id": "uuid-string",
  "action": "created",
  "entity_type": "Lead",
  "entity_id": "lead-uuid",
  "previous_value": null,
  "new_value": "{\"lead_name\": \"John Doe\"}",
  "user_id": "user-uuid",
  "notes": "Lead created via website form",
  "created_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` — Missing required field
- `422 Unprocessable Entity` — Validation failed
- `500 Internal Server Error` — Database write failed

---

### Get System Audit Log

```
GET /api/audit/?limit=200
```

**Description:** Retrieve recent system-wide audit events.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 200 | Max records to return (max 1000) |

**Success Response (200 OK):**
```json
[
  {
    "id": "uuid-1",
    "action": "created",
    "entity_type": "Lead",
    "entity_id": "lead-uuid",
    "previous_value": null,
    "new_value": "{\"lead_name\": \"John Doe\"}",
    "user_id": "user-uuid",
    "notes": "Lead created via website form",
    "created_at": "2026-03-29T10:30:00Z"
  },
  {
    "id": "uuid-2",
    "action": "updated",
    "entity_type": "Lead",
    "entity_id": "lead-uuid",
    "previous_value": "new",
    "new_value": "qualified",
    "user_id": "user-uuid",
    "notes": "Lead qualified after review",
    "created_at": "2026-03-29T10:45:00Z"
  }
]
```

**Error Responses:**
- `400 Bad Request` — Invalid query parameter
- `500 Internal Server Error` — Database read failed

---

### Get Deal Audit Trail

```
GET /api/audit/deals/{deal_id}
```

**Description:** Retrieve complete audit trail for a specific deal.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `deal_id` | UUID | The deal's unique ID |

**Success Response (200 OK):**
```json
[
  {
    "id": "audit-uuid-1",
    "action": "created",
    "entity_type": "Deal",
    "entity_id": "deal-uuid",
    "previous_value": null,
    "new_value": "{\"headline\": \"Prime SF...\"}",
    "user_id": "user-uuid",
    "notes": "Deal created",
    "created_at": "2026-03-29T10:30:00Z"
  },
  {
    "id": "audit-uuid-2",
    "action": "updated",
    "entity_type": "Deal",
    "entity_id": "deal-uuid",
    "previous_value": "pending",
    "new_value": "active",
    "user_id": "user-uuid",
    "notes": "Deal activated",
    "created_at": "2026-03-29T11:00:00Z"
  }
]
```

**Error Responses:**
- `404 Not Found` — Deal ID does not exist
- `500 Internal Server Error` — Database read failed

---

## Governance & Go-Live

### Get Go-Live Status

```
GET /api/governance/go-live/state
```

**Description:** Get current go-live mode (enabled, disabled, maintenance).

**Success Response (200 OK):**
```json
{
  "state": "enabled",                    // "enabled" | "disabled" | "maintenance"
  "mode": "production",                  // "production" | "sandbox" | "maintenance"
  "last_updated": "2026-03-29T10:30:00Z",
  "reason": "System ready for transactions"
}
```

**Error Responses:**
- `500 Internal Server Error` — Governance system error

---

### Get Go-Live Checklist

```
GET /api/governance/go-live/checklist
```

**Description:** Get detailed go-live readiness checklist.

**Success Response (200 OK):**
```json
{
  "go_live_ready": true,
  "items": [
    {
      "name": "Database Schema",
      "status": "ok",
      "details": "All tables present and initialized"
    },
    {
      "name": "Lead Intake",
      "status": "ok",
      "details": "Lead creation and retrieval operational"
    },
    {
      "name": "Deal Management",
      "status": "ok",
      "details": "Deal CRUD operational"
    },
    {
      "name": "Audit Logging",
      "status": "ok",
      "details": "Audit trail functional"
    },
    {
      "name": "Governance Policy",
      "status": "ok",
      "details": "Go-live policies configured"
    }
  ]
}
```

**Error Responses:**
- `500 Internal Server Error` — Governance system error

---

### Get Runbook Status

```
GET /api/governance/runbook/status
```

**Description:** Get system runbook status including blockers and warnings.

**Success Response (200 OK):**
```json
{
  "ok_to_enable_go_live": true,
  "blockers": [],
  "warnings": [],
  "execution_mode": "production",
  "status_summary": {
    "system_health": "ok",
    "schema_initialized": true,
    "migrations_clean": true,
    "all_routers_mounted": true
  },
  "checked_at": "2026-03-29T10:30:00Z"
}
```

**Error Responses:**
- `500 Internal Server Error` — Governance system error

---

### Get Risk Reserve Status

```
GET /api/governance/risk/ledger/today
```

**Description:** Get today's risk reserve (daily capital safety allocation).

**Success Response (200 OK):**
```json
{
  "date": "2026-03-29",
  "total_reserve": 500000,
  "allocated": 250000,
  "available": 250000,
  "utilization_percent": 50,
  "policy": "default",
  "description": "Daily risk reserve managed within policy limits"
}
```

**Error Responses:**
- `500 Internal Server Error` — Governance system error

---

## Health & Documentation

### Health Check

```
GET /health
```

**Description:** Backend health status (used by load balancer and monitoring).

**Success Response (200 OK):**
```json
{
  "status": "ok",
  "service": "valhalla-backend",
  "version": "1.0",
  "timestamp": "2026-03-29T10:30:00Z"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "reason": "Database connection failed"
}
```

---

### OpenAPI Documentation

```
GET /docs
```

**Description:** Interactive OpenAPI Swagger UI documentation.

**Response:** HTML Swagger UI with live endpoint testing

---

### OpenAPI Schema JSON

```
GET /openapi.json
```

**Description:** OpenAPI 3.0 specification in JSON format.

**Response:** Full OpenAPI schema for integration with frontend tools

---

## Error Handling

### Standard Error Response Format

All errors return JSON with consistent structure:

```json
{
  "detail": "Human-readable error message",
  "type": "error_code",                    // Optional: Machine-readable error type
  "status_code": 400,                      // HTTP status code
  "timestamp": "2026-03-29T10:30:00Z"      // Optional: When error occurred
}
```

### HTTP Status Codes Used

| Code | Meaning | Common Cause |
|------|---------|--------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `204` | No Content | Delete successful, no response body |
| `400` | Bad Request | Invalid request format or parameters |
| `401` | Unauthorized | Missing or invalid authentication |
| `404` | Not Found | Resource does not exist |
| `422` | Unprocessable Entity | Request valid but semantics failed (validation) |
| `500` | Internal Server Error | Backend error (database, logic, etc.) |
| `503` | Service Unavailable | External service unreachable (e.g., Heimdall) |

### Common Error Examples

**Validation Error (422):**
```json
{
  "detail": "Lead must have valid email address",
  "type": "validation_error"
}
```

**Not Found (404):**
```json
{
  "detail": "Lead not found",
  "type": "not_found"
}
```

**Authentication Error (401):**
```json
{
  "detail": "Invalid builder key",
  "type": "auth_error"
}
```

---

## Authentication

### Bearer Token (Future)

**Header:** `Authorization: Bearer <token>`

**Status:** Not implemented in V1, planned for Phase 2

### Builder Key (Current)

**Header:** `X-Builder-Key: <key_value>`

**Used By:**
- `POST /api/deals` (required)
- `GET /api/deals` (optional in V1, required in Phase 2)

**Status:** Implemented, currently permissive for V1 backend verification

### User Session (Planned)

**Status:** Not implemented in Phase 1, planned for authenticated Phase 2

---

## Data Types & Formats

### UUID Format

All IDs use UUID v4 format:
```
550e8400-e29b-41d4-a716-446655440000
```

### Timestamp Format

All timestamps use ISO 8601 UTC format:
```
2026-03-29T10:30:00Z
```

### Currency

All monetary values are floats (dollars):
```json
{
  "price": 1500000.00,
  "estimated_arv": 1250000.50
}
```

---

## Rate Limiting (Future)

**Status:** Not implemented in V1

**Planned:** Implement in Phase 2
- Leads endpoints: 100 req/min per IP
- Deals endpoints: 50 req/min per IP (builder key limited)
- Audit endpoints: 200 req/min per IP
- Governance endpoints: 100 req/min per IP

---

## Multi-Region & Failover

**Status:** V1 Single Region

**Current:** Render (us-east-1 equivalent)

**Planned:** Multi-region support in Phase 3

---

## Versioning Strategy

**Current Version:** 1.0 (stable for V1 product launch)

**Versioning:** URL-based (future versions will use `/api/v2/`, '/api/v3/`, etc.)

**Backward Compatibility:** V1 frozen; breaking changes deferred to V2

---

## Contract Validation

This contract is active as of **2026-03-29** and locked for V1 launch.

**Signature:** Approved by backend team for frontend integration  
**Last Updated:** 2026-03-29 10:30 UTC  
**Next Review:** Post-launch monitoring

---

**Use this contract as:**
1. ✅ Truth source for frontend WeWeb build
2. ✅ Reference for integration tests
3. ✅ Admin guide for backend API behavior
4. ✅ Baseline for performance/load testing
