# WeWeb Backend Contract

**Generated**: 2026-05-19  
**Backend Context**: d:\dev\services\api  
**Canonical App**: from app.main import app  
**Total Active Endpoints**: 902 paths, 1088 operations  
**OpenAPI Version**: 3.1.0  

---

## Summary by Business Area

### Health / Go-Live (17 endpoints)

#### /health
- **Method**: GET
- **Purpose**: Health check for service availability
- **Auth**: No
- **Response**: 200 OK (JSON object)
- **Common Errors**: 503 Service Unavailable
- **WeWeb Usage**: Dashboard initialization, connection validation

#### /healthz
- **Method**: GET  
- **Purpose**: Kubernetes-style health probe  
- **Auth**: No
- **Response**: 200 OK (empty)
- **Common Errors**: 503 Service Unavailable
- **WeWeb Usage**: Background health monitoring

#### /api/go-live/status
- **Method**: GET
- **Purpose**: Current go-live activation status
- **Auth**: Yes (Session token)
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"status": "active|inactive", "mode": "string", "timestamp": "ISO8601"}`
- **Common Errors**: 401 Unauthorized, 403 Forbidden
- **WeWeb Usage**: Go-live dashboard, activation control, permission gates

#### /api/go-live/enable
- **Method**: POST
- **Purpose**: Enable go-live mode (admin only)
- **Auth**: Yes (Admin)
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"mode": "sandbox|production"}`
- **Response**: `{"status": "enabled", "mode": "string"}`
- **Common Errors**: 401 Unauthorized, 403 Forbidden, 400 Bad Request
- **WeWeb Usage**: Go-live activation button

#### /api/go-live/disable
- **Method**: POST
- **Purpose**: Disable go-live mode
- **Auth**: Yes (Admin)
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"status": "disabled"}`
- **Common Errors**: 401 Unauthorized, 403 Forbidden
- **WeWeb Usage**: Go-live deactivation, emergency stop

---

### VA Intake / Lead Management (28 endpoints)

#### /api/va-intake/leads
- **Method**: GET
- **Purpose**: List all VA leads (paginated)
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `skip=0, limit=50, status=string, stage=string`
- **Response**: `{"leads": [{"id": "", "name": "", "phone": "", "status": "", ...}], "total": 0}`
- **Common Errors**: 401 Unauthorized, 422 Unprocessable Entity
- **WeWeb Usage**: Lead intake list, filtering, pagination

#### /api/va-intake/lead (POST)
- **Method**: POST
- **Purpose**: Create or import a new VA lead
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"name": "", "phone": "", "email": "", "property_address": "", "property_value": 0, "equity": 0}`
- **Response**: `{"id": "", "name": "", "status": "created", "timestamp": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 409 Conflict (duplicate)
- **WeWeb Usage**: Lead intake form submission

#### /api/va-intake/leads/{lead_id}
- **Method**: GET
- **Purpose**: Get detailed lead information
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"id": "", "name": "", "phone": "", "email": "", "property": {}, "audit_trail": [], "status": "", "last_action": ""}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Lead detail view, audit history display

#### /api/va-intake/leads/{lead_id}/convert-to-deal
- **Method**: POST
- **Purpose**: Convert approved VA lead to active deal
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"deal_type": "wholesale|brrrr|flip", "estimated_arv": 0, "notes": ""}`
- **Response**: `{"deal_id": "", "status": "created", "lead_id": "", "timestamp": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 404 Not Found, 409 Conflict
- **WeWeb Usage**: Lead to deal conversion workflow

#### /api/va-intake/approvals/pending
- **Method**: GET
- **Purpose**: Get all pending VA lead approvals
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `skip=0, limit=50, priority=string`
- **Response**: `{"approvals": [{"id": "", "lead_id": "", "lead_name": "", "status": "pending", ...}], "total": 0}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: Approval queue display, filtering

#### /api/va-intake/approvals/{approval_id}/approve
- **Method**: POST
- **Purpose**: Approve a VA lead for processing
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"notes": "", "approved_by": "email"}`
- **Response**: `{"approval_id": "", "status": "approved", "timestamp": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Approval workflow - approve button

#### /api/va-intake/approvals/{approval_id}/deny
- **Method**: POST
- **Purpose**: Deny a VA lead for processing
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"reason": "string", "denied_by": "email"}`
- **Response**: `{"approval_id": "", "status": "denied", "timestamp": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 404 Not Found
- **Wewebb Usage**: Approval workflow - deny button

---

### Deals Management (63 endpoints)

#### /api/deals
- **Method**: GET
- **Purpose**: List all deals (paginated, filterable)
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `skip=0, limit=50, status=string, deal_type=string, sort=string`
- **Response**: `{"deals": [{"id": "", "property_address": "", "status": "", "deal_type": "", "arv": 0, ...}], "total": 0}`
- **Common Errors**: 401 Unauthorized, 422 Unprocessable Entity
- **WeWeb Usage**: Deals dashboard, filtering, sorting

#### /api/deals (POST)
- **Method**: POST
- **Purpose**: Create new deal
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"property_address": "", "property_value": 0, "deal_type": "wholesale|brrrr|flip", "estimateed_arv": 0}`
- **Response**: `{"id": "", "status": "draft", "created_at": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized
- **WeWeb Usage**: New deal creation form

#### /api/deals/{deal_id}
- **Method**: GET
- **Purpose**: Get detailed deal information
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"id": "", "property": {}, "status": "", "deal_type": "", "timeline": [], "buyers": [], "offers": [], "contracts": []}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Deal detail page

#### /api/deals/{deal_id}/action
- **Method**: POST
- **Purpose**: Advance deal to next stage
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"action": "advance|close|archive", "notes": ""}`
- **Response**: `{"deal_id": "", "status": "new_status", "timestamp": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 409 Conflict
- **WeWeb Usage**: Deal status workflow buttons

---

### Buyers & Disposition (20 endpoints)

#### /api/buyers
- **Method**: GET
- **Purpose**: List all buyers (paginated)
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `skip=0, limit=50, region=string, deal_type=string`
- **Response**: `{"buyers": [{"id": "", "name": "", "regions": [], "deal_types": [], "contact": ""}], "total": 0}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: Buyer matching, disposition list

#### /api/deals/{deal_id}/buyers
- **Method**: GET
- **Purpose**: Get potential buyers for a deal
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"buyers": [{"id": "", "name": "", "match_score": 0.95, "regions": [], "contact": ""}], "total": 0}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Buyer matching results

#### /api/deals/{deal_id}/send-to-buyer/{buyer_id}
- **Method**: POST
- **Purpose**: Send deal packet to specific buyer
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"include_analysis": true, "deadline_days": 3}`
- **Response**: `{"sent_at": "ISO8601", "buyer_id": "", "deal_id": ""}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Buyer outreach workflow

---

### Messaging & Communication (12 endpoints)

#### /api/messaging/va/draft-seller-message/{lead_id}
- **Method**: POST
- **Purpose**: Draft initial seller message for VA lead
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"tone": "professional|friendly|formal", "urgency": "high|normal|low"}`
- **Response**: `{"message": "string", "suggested_follow_up": "string"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Message composition assistant

#### /api/messaging/va/create-buyer-packet/{deal_id}
- **Method**: POST
- **Purpose**: Create and prepare buyer information packet
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"include_analysis": true, "include_comps": true, "format": "pdf|email"}`
- **Response**: `{"packet_id": "", "url": "string", "created_at": "ISO8601"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Buyer packet generation

#### /api/messaging/{deal_id}/send-message
- **Method**: POST
- **Purpose**: Send communication to buyer or seller
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"recipient_type": "buyer|seller", "recipient_id": "", "message": "", "channel": "email|sms|internal"}`
- **Response**: `{"message_id": "", "sent_at": "ISO8601", "status": "sent"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized
- **WeWeb Usage**: Direct messaging workflow

---

### Reports & Analytics (12 endpoints)

#### /api/reports/summary
- **Method**: GET
- **Purpose**: Executive dashboard summary
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `start_date=ISO8601, end_date=ISO8601, region=string`
- **Response**: `{"total_deals": 0, "active_deals": 0, "pending_approvals": 0, "conversions": 0, "metrics": {}}`
- **Common Errors**: 401 Unauthorized, 422 Unprocessable Entity
- **WeWeb Usage**: Dashboard KPI display

#### /api/reports/eia-monthly-summary
- **Method**: GET
- **Purpose**: Monthly EIA (Engagement, Impact, Analysis) report
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `month=MM, year=YYYY`
- **Response**: `{"period": "", "metrics": {}, "top_performers": [], "issues": []}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: Report dashboard view

#### /api/reports/deal-analysis
- **Method**: GET
- **Purpose**: Detailed analysis for specific deal
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `deal_id=string`
- **Response**: `{"deal_id": "", "analysis": {}, "comparables": [], "market_trend": ""}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Deal analysis view

---

### Audit & Compliance (9 endpoints)

#### /api/audit-log
- **Method**: GET
- **Purpose**: Get audit trail of system activities
- **Auth**: Yes (Admin)
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `skip=0, limit=50, entity_type=string, action=string`
- **Response**: `{"logs": [{"timestamp": "", "user": "", "action": "", "entity": "", "changes": {}}], "total": 0}`
- **Common Errors**: 401 Unauthorized, 403 Forbidden
- **WeWeb Usage**: Compliance audit view (admin only)

#### /api/audit-log/{log_id}
- **Method**: GET
- **Purpose**: Get detailed audit entry
- **Auth**: Yes (Admin)
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"id": "", "timestamp": "", "user": "", "action": "", "before": {}, "after": {}, "reason": ""}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Audit detail modal

---

### FLIP Analysis (2 endpoints)

#### /api/flip/estimate
- **Method**: POST
- **Purpose**: Estimate FLIP deal profitability
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"purchase_price": 0, "arv": 0, "holding_cost_months": 6, "rehab_cost": 0}`
- **Response**: `{"gross_profit": 0, "roi": 0.25, "monthly_carrying": 0, "recommendation": "string"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized
- **WeWeb Usage**: FLIP calculator widget

#### /api/flip/{deal_id}/timeline
- **Method**: GET
- **Purpose**: Get FLIP deal timeline
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"phases": [{"name": "", "start": "", "end": "", "cost": 0, "status": ""}]}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: FLIP project timeline view

---

### BRRRR Analysis (19 endpoints)

#### /api/brrrr/estimate
- **Method**: POST
- **Purpose**: Estimate BRRRR deal performance
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Body**: `{"purchase_price": 0, "arv": 0, "rehab_cost": 0, "desired_ltv": 0.7, "desired_rent": 0}`
- **Response**: `{"after_repair_value": 0, "max_loan_amount": 0, "monthly_rent": 0, "cash_flow": 0, "recommendation": "string"}`
- **Common Errors**: 400 Bad Request, 401 Unauthorized
- **WeWeb Usage**: BRRRR calculator widget

#### /api/brrrr/{deal_id}/financing-options
- **Method**: GET
- **Purpose**: Get financing scenarios for BRRRR deal
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"options": [{"name": "", "loan_amount": 0, "rate": 0.05, "term_months": 360, "monthly_payment": 0}]}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Financing comparison table

---

### Notifications (30 endpoints)

#### /api/notifications
- **Method**: GET
- **Purpose**: Get user notifications (paginated)
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `skip=0, limit=20, read=boolean, type=string`
- **Response**: `{"notifications": [{"id": "", "type": "", "message": "", "timestamp": "", "read": false, "action_url": ""}], "unread_count": 0}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: Notification dropdown, bell badge

#### /api/notifications/{notification_id}/read
- **Method**: POST
- **Purpose**: Mark notification as read
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"id": "", "read": true}`
- **Common Errors**: 401 Unauthorized, 404 Not Found
- **WeWeb Usage**: Notification interaction

#### /api/notifications/read-all
- **Method**: POST
- **Purpose**: Mark all notifications as read
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Response**: `{"updated_count": 0}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: "Mark all as read" button

---

### Jarvis Intelligence (14 endpoints)

#### /api/jarvis/dashboard
- **Method**: GET
- **Purpose**: Heimdall AI-powered dashboard with community contacts and scoring
- **Auth**: Yes (Optional)
- **Headers**: `Session-Token` or JWT Bearer (optional)
- **Response**: `{"contacts": [{"id": "", "name": "", "score": 0.95, "reason": "", "action": ""}], "insights": []}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: AI dashboard widget, intelligence view

#### /api/jarvis/hot-contacts
- **Method**: GET
- **Purpose**: List all contacts ranked by Heimdall scoring with explanations
- **Auth**: Yes
- **Headers**: `Session-Token` or JWT Bearer
- **Query Params**: `limit=20, min_score=0.7`
- **Response**: `{"contacts": [{"id": "", "name": "", "score": 0.95, "explanation": "", "recommended_action": ""}], "total": 0}`
- **Common Errors**: 401 Unauthorized
- **WeWeb Usage**: Hot leads intelligence list

---

## Auth & Security Notes

### Required Headers
- **Session-Token**: Legacy session token (alternative to JWT)
- **Authorization**: JWT Bearer token format: `Authorization: Bearer eyJ...`
- **Content-Type**: application/json (for POST/PUT requests)

### Common Auth Errors
- **401 Unauthorized**: Missing or invalid token
- **403 Forbidden**: Token valid but lacks required permissions
- **405 Method Not Allowed**: Wrong HTTP method
- **422 Unprocessable Entity**: Invalid request body schema

### Session Token Environment
- Dev/Local: Use `SESSION_TOKEN_DEV` or set `VALHALLA_JWT_SECRET`
- Render Production: JWT SECRET injected as environment variable
- WeWeb: Store token in `AUTH_TOKEN` variable, send in all requests

---

## Error Handling Patterns

### Standard Error Response
```json
{
  "detail": "Human readable error message",
  "status": 400,
  "type": "error_type"
}
```

### Common HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request (validation error)
- **401**: Unauthorized (missing auth)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (duplicate, invalid state)
- **422**: Unprocessable Entity (schema validation)
- **500**: Internal Server Error
- **503**: Service Unavailable

---

## Pagination Pattern

Most list endpoints support:
```
skip: 0        # Number of items to skip
limit: 50      # Number of items per page (max varies)
sort: "-created_at"  # Sort field (- = descending)
```

Response includes:
```json
{
  "items": [],
  "total": 0,
  "skip": 0,
  "limit": 50
}
```

---

## Performance Notes

- Most queries support pagination (default limit 50)
- Health checks are lightweight, no auth required
- Large list operations may take 1-2 seconds
- Concurrent requests to same resource may cause 409 Conflict
- File uploads (if present) limited to 10MB

---

## Next Steps

1. **Verify connectivity** from WeWeb to backend health endpoint
2. **Test authentication** with actual session token or JWT
3. **Build lead intake flow** using va-intake endpoints
4. **Implement approval workflow** using approvals endpoints
5. **Wire deal dashboard** using /api/deals endpoints
6. **Add buyer matching** using /api/buyers endpoints
7. **Implement notifications** real-time or polling

---

**Last Updated**: 2026-05-19  
**Backend Version**: Valhalla 1.0.0  
**OpenAPI Documentation**: See attached openapi.json
