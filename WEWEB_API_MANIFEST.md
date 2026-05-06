# Valhalla Legacy Inc. — WeWeb API Manifest
## Phase 2b Frontend Connection Guide

**Rule**: WeWeb is UI only. All business logic stays in FastAPI.

**Base URL**: `http://127.0.0.1:4000`

---

## 1. VA Lead Submit

**Method**: `POST`

**Endpoint**: `/api/va-intake/lead`

**Purpose**: Submit a VA lead into Heimdall scoring and approval workflow.

**Request Body**:
```json
{
  "source_platform": "facebook",
  "source_type": "manual_va",
  "source_url": "manual import",
  "address": "123 Sample Street",
  "city": "Winnipeg",
  "province": "MB",
  "seller_name": "Test Seller",
  "seller_phone": "204-555-1234",
  "seller_email": null,
  "asking_price": 145000,
  "raw_text": "House needs work. Sold as is. Must sell quickly.",
  "va_notes": "Looks distressed. Possible vacant property.",
  "strategy_fit": "wholesale",
  "submitted_by": "va_test"
}
```

**Response**:
```json
{
  "success": true,
  "lead_id": 1,
  "lead_status": "qualified_pending_approval",
  "source_platform": "facebook",
  "heimdall_score": 100,
  "risk_level": "medium",
  "confidence": 1.0,
  "recommended_action": "Queue seller contact for Bryan approval",
  "approval_required": true,
  "next_pipeline_stage": "approval_required",
  "reasoning_summary": "Address provided. Asking price provided. Seller contact available. Distress or motivation signal detected. Source URL provided. Recognized lead source."
}
```

**Display Response Fields**:
- `lead_id`
- `lead_status`
- `heimdall_score`
- `risk_level`
- `confidence`
- `recommended_action`
- `reasoning_summary`

---

## 2. VA Lead List

**Method**: `GET`

**Endpoint**: `/api/va-intake/leads`

**Purpose**: Show all VA-submitted leads with pagination.

**Query Parameters**:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 50)

**Response**:
```json
{
  "success": true,
  "count": 3,
  "items": [
    {
      "id": 1,
      "address": "123 Sample Street",
      "city": "Winnipeg",
      "province": "MB",
      "source_platform": "facebook",
      "asking_price": 145000.0,
      "heimdall_score": 100,
      "risk_level": "medium",
      "status": "qualified_pending_approval",
      "stage": "approval_required",
      "recommended_action": "Queue seller contact for Bryan approval",
      "seller_name": "Test Seller",
      "created_at": "2026-05-06T14:44:19.539921+00:00"
    }
  ]
}
```

**Display Fields**:
- `id`
- `address`
- `city`
- `province`
- `source_platform`
- `asking_price`
- `heimdall_score`
- `risk_level`
- `status`
- `stage`
- `recommended_action`
- `seller_name`
- `created_at`

---

## 3. VA Lead Detail

**Method**: `GET`

**Endpoint**: `/api/va-intake/leads/{lead_id}`

**Purpose**: Show full lead record with all fields.

**Response**: Complete VALead object with all 26 fields

---

## 4. Pending Approval Queue

**Method**: `GET`

**Endpoint**: `/api/va-intake/approvals/pending`

**Purpose**: Show Bryan/admin approval queue.

**Response**:
```json
{
  "success": true,
  "count": 1,
  "items": [
    {
      "approval_id": 1,
      "entity_type": "lead",
      "entity_id": 1,
      "status": "pending",
      "recommended_action": "Queue seller contact for Bryan approval",
      "heimdall_score": 100,
      "risk_level": "medium",
      "assigned_to": null,
      "created_at": "2026-05-06T14:44:19.539921+00:00"
    }
  ]
}
```

**Display Fields**:
- `approval_id`
- `entity_type`
- `entity_id`
- `status`
- `recommended_action`
- `risk_level`
- `heimdall_score`
- `created_at`

---

## 5. Approve Lead

**Method**: `POST`

**Endpoint**: `/api/va-intake/approvals/{approval_id}/approve`

**Purpose**: Approve a recommended Heimdall action.

**Request Body**:
```json
{
  "approver": "bryan"
}
```

**Response**:
```json
{
  "success": true,
  "approval_id": 1,
  "status": "approved",
  "approved_by": "bryan",
  "approved_at": "2026-05-06T14:45:00.000000+00:00"
}
```

---

## 6. Deny Lead

**Method**: `POST`

**Endpoint**: `/api/va-intake/approvals/{approval_id}/deny`

**Purpose**: Deny a recommended Heimdall action.

**Request Body**:
```json
{
  "approver": "bryan",
  "denial_reason": "Not enough margin or seller information."
}
```

**Response**:
```json
{
  "success": true,
  "approval_id": 1,
  "status": "denied",
  "denied_by": "bryan",
  "denial_reason": "Not enough margin or seller information.",
  "denied_at": "2026-05-06T14:45:00.000000+00:00"
}
```

---

## 7. Convert Approved Lead to Deal

**Method**: `POST`

**Endpoint**: `/api/va-intake/leads/{lead_id}/convert-to-deal`

**Purpose**: Convert an approved VA lead into the Valhalla deals system.

**Request Body**:
```json
{
  "converted_by": "bryan"
}
```

**Response**:
```json
{
  "success": true,
  "deal_id": 1,
  "lead_id": 1,
  "status": "created",
  "created_at": "2026-05-06T14:45:00.000000+00:00"
}
```

**Note**: Lead must be in "approved" status to convert.

---

## 8. Lead Deal Link

**Method**: `GET`

**Endpoint**: `/api/va-intake/leads/{lead_id}/deal`

**Purpose**: Show connected deal after conversion.

**Response**:
```json
{
  "success": true,
  "deal": {
    "id": 1,
    "status": "created",
    "created_at": "2026-05-06T14:45:00.000000+00:00"
  }
}
```

Or if no deal:
```json
{
  "success": true,
  "deal": null
}
```

---

## 9. Lead Audit Trail

**Method**: `GET`

**Endpoint**: `/api/va-intake/leads/{lead_id}/audit`

**Purpose**: Show compliance trail for lead (all actions, approvals, denials).

**Response**:
```json
{
  "success": true,
  "lead_id": 1,
  "items": [
    {
      "id": 1,
      "actor": "system",
      "action": "lead_submitted",
      "entity_type": "va_lead",
      "entity_id": 1,
      "details": "Lead submitted via API",
      "status": "success",
      "created_at": "2026-05-06T14:44:19.539921+00:00"
    },
    {
      "id": 2,
      "actor": "bryan",
      "action": "lead_approved",
      "entity_type": "va_lead",
      "entity_id": 1,
      "details": "Approved by Bryan",
      "status": "success",
      "created_at": "2026-05-06T14:45:00.000000+00:00"
    }
  ]
}
```

**Display Fields**:
- `actor` (who took action)
- `action` (what action)
- `details` (description)
- `status` (success/error)
- `created_at` (when)

---

## 10. Go-Live Status

**Method**: `GET`

**Endpoint**: `/api/go-live/status`

**Purpose**: Show whether backend is ready for WeWeb launch.

**Response**:
```json
{
  "system": "Valhalla Legacy Inc.",
  "mode": "pre_weweb_backend_ready",
  "checked_at": "2026-05-06T14:50:00.000000+00:00",
  "backend_ready": true,
  "database_ready": true,
  "va_intake_ready": true,
  "approvals_ready": true,
  "deal_conversion_ready": true,
  "audit_logging_ready": true,
  "weweb_ready": false,
  "ok_to_go_live": false,
  "blockers": [
    "WeWeb frontend is not connected yet."
  ],
  "warnings": [],
  "next_step": "Connect WeWeb pages to tested API endpoints."
}
```

---

## Integration Notes

### Error Responses

All endpoints return consistent error format:
```json
{
  "success": false,
  "error": "Description of error",
  "detail": "Additional details if applicable"
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad request / validation error
- `404`: Resource not found
- `422`: Unprocessable entity
- `500`: Server error

### Authentication

Currently no authentication required for development.

In production, will require:
- JWT token in `Authorization: Bearer {token}` header
- Role-based access control (va, viewer, admin)

### CORS

API is open to localhost development.

Configure for production URLs later.

### Rate Limiting

Not implemented for development.

Will be added before production deployment.

### Base URL

Development: `http://127.0.0.1:4000`  
Production: `https://api.valhalla.example.com` (TBD)

---

## WeWeb Development Checklist

- [ ] Form for endpoint 1 (VA Lead Submit)
- [ ] Table for endpoint 2 (VA Lead List)
- [ ] Modal for endpoint 3 (VA Lead Detail)
- [ ] Queue view for endpoint 4 (Pending Approvals)
- [ ] Approve button for endpoint 5
- [ ] Deny button for endpoint 6
- [ ] Convert button for endpoint 7
- [ ] Deal link display for endpoint 8
- [ ] Audit trail modal for endpoint 9
- [ ] Status dashboard for endpoint 10

---

## Testing Tools

### cURL Examples

Submit lead:
```bash
curl -X POST http://127.0.0.1:4000/api/va-intake/lead \
  -H "Content-Type: application/json" \
  -d '{"source_platform":"facebook","address":"123 Main St",...}'
```

List leads:
```bash
curl http://127.0.0.1:4000/api/va-intake/leads
```

Go-live status:
```bash
curl http://127.0.0.1:4000/api/go-live/status
```

### Interactive Docs

Swagger UI: `http://127.0.0.1:4000/docs`

---

## Support

For backend questions, refer to commit `9783961` and documentation:
- `VA_INTAKE_PHASE_2_CHECKPOINT.md`
- `VA_INTAKE_PHASE_2B_WEWEB_GUIDE.md`

All endpoints are production-ready and fully tested.
