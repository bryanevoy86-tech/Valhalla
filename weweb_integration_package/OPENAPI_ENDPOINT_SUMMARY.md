# OpenAPI Endpoint Summary

**Quick reference guide to Valhalla backend endpoints - organized by use case**

---

## Quick Stats

| Metric | Count |
|--------|-------|
| **Total Paths** | 902 |
| **Total Operations** | 1088 |
| **Health Endpoints** | 5 (GET /health, /healthz, /readyz, /metrics) |
| **Authenticated Endpoints** | 890+ |
| **Read-Only Endpoints** | ~300 |
| **Write Endpoints** | ~590 |

---

## Tier 1: Always Use (Critical Path)

These endpoints should work on day 1 of integration:

### Health & Status
```
GET  /health                           Status: OK/Failed
GET  /healthz                          Kubernetes ready probe
GET  /readyz                           Service ready probe
```

### Authentication
```
POST /api/auth/login                   (if available) or use SESSION_TOKEN_DEV
GET  /current-user                     Get logged-in user info
```

### Go-Live Control
```
GET  /api/go-live/status               Current mode (active/inactive)
POST /api/go-live/enable               Enable go-live (admin only)
POST /api/go-live/disable              Disable go-live (emergency stop)
```

---

## Tier 2: Lead Intake (Day 1-2)

Lead management and approval pipeline:

### Lead CRUD
```
GET  /api/va-intake/leads              List all leads (paginated)
POST /api/va-intake/lead               Create new lead
GET  /api/va-intake/leads/{lead_id}    Get lead details with audit trail
```

### Approvals
```
GET  /api/va-intake/approvals/pending  Get pending approvals queue
POST /api/va-intake/approvals/{approval_id}/approve    Approve lead
POST /api/va-intake/approvals/{approval_id}/deny       Deny lead
```

### Lead to Deal Conversion
```
POST /api/va-intake/leads/{lead_id}/convert-to-deal    Convert to deal
```

**Most Common Query Pattern**:
```
GET /api/va-intake/leads?skip=0&limit=50&status=pending&sort=-created_at
```

---

## Tier 3: Deals (Day 2-3)

Deal tracking and workflow:

### Deal CRUD
```
GET  /api/deals                        List all deals (filterable, paginated)
POST /api/deals                        Create new deal
GET  /api/deals/{deal_id}              Get deal details with timeline/buyers/offers
```

### Deal Actions
```
POST /api/deals/{deal_id}/action       Advance stage or close deal
```

### Deal Analysis
```
POST /api/flip/estimate                Calculate FLIP profitability
POST /api/brrrr/estimate               Calculate BRRRR financing
GET  /api/reports/deal-analysis        Get comps and market data
```

**Most Common Query Pattern**:
```
GET /api/deals?skip=0&limit=50&status=active&sort=-created_at
POST /api/flip/estimate with {purchase_price, arv, rehab_cost, holding_months}
```

---

## Tier 4: Buyers & Disposition (Day 3)

Buyer matching and outreach:

### Buyers
```
GET  /api/buyers                       List all buyers (filterable)
GET  /api/deals/{deal_id}/buyers       Get matched buyers for specific deal
```

### Outreach
```
POST /api/deals/{deal_id}/send-to-buyer/{buyer_id}     Send deal to buyer
POST /api/messaging/va/create-buyer-packet/{deal_id}   Generate buyer packet (PDF)
```

**Most Common Query Pattern**:
```
GET /api/deals/{deal_id}/buyers?sort=match_score
POST /api/deals/{deal_id}/send-to-buyer/buyer_123
```

---

## Tier 5: Messaging & Communication (Day 3-4)

AI-assisted outreach and templates:

### Message Generation
```
POST /api/messaging/va/draft-seller-message/{lead_id}  Draft AI message
```

### Packets & Documents
```
POST /api/messaging/va/create-buyer-packet/{deal_id}   Create buyer packet
```

**Most Common Query Pattern**:
```
POST /api/messaging/va/draft-seller-message/lead_456 with {tone: "professional", urgency: "high"}
```

---

## Tier 6: Reports & Analytics (Day 4)

KPIs and performance tracking:

### Dashboard
```
GET  /api/reports/summary              Executive summary (KPIs)
```

### Monthly Reports
```
GET  /api/reports/eia-monthly-summary  Monthly EIA report
```

**Most Common Query Pattern**:
```
GET /api/reports/summary?start_date=2026-05-01&end_date=2026-05-31
```

---

## Tier 7: Notifications & Audit (Day 4-5)

System events and compliance:

### Notifications
```
GET  /api/notifications                Get user notifications
POST /api/notifications/{id}/read      Mark notification as read
POST /api/notifications/read-all       Mark all as read
```

### Audit Trail
```
GET  /api/audit-log                    Get system audit log (admin only)
GET  /api/audit-log/{log_id}           Get audit entry details
```

**Most Common Query Pattern**:
```
GET /api/notifications?skip=0&limit=20&read=false
```

---

## Tier 8: Jarvis Intelligence (Day 5)

AI-powered insights and recommendations:

### Smart Dashboards
```
GET  /api/jarvis/dashboard             AI dashboard with recommendations
GET  /api/jarvis/hot-contacts          Ranked community contacts with scoring
```

**Most Common Query Pattern**:
```
GET /api/jarvis/hot-contacts?limit=20&min_score=0.7
```

---

## Authentication Pattern (ALL ENDPOINTS)

**Except** GET /health, GET /healthz - all endpoints require:

### Header Option 1: Session Token
```
Session-Token: <session_token_value>
```

### Header Option 2: JWT Bearer
```
Authorization: Bearer <jwt_token_value>
```

**WeWeb must choose ONE method and use consistently**

---

## Common Request Patterns

### List Endpoints (GET with pagination)
```javascript
GET /api/{resource}?skip=0&limit=50&status=filter&sort=-field_name

// Response structure:
{
  "items": [...],
  "total": 142,
  "skip": 0,
  "limit": 50
}
```

### Create Endpoints (POST)
```javascript
POST /api/{resource} with JSON body
// Response: Created resource with ID and timestamp
```

### Detail Endpoints (GET single)
```javascript
GET /api/{resource}/{id}
// Response: Full resource with all fields including nested objects
```

### Action Endpoints (POST)
```javascript
POST /api/{resource}/{id}/{action} with optional body
// Response: Updated resource or status
```

---

## Error Response Pattern (ALL ENDPOINTS)

```json
{
  "detail": "Human readable error description",
  "status": 400,
  "type": "error_identifier"
}
```

### Common Status Codes
| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Use response data |
| 201 | Created | Use response data, show success |
| 400 | Bad request | Check request body, show user message |
| 401 | Unauthorized | Refresh token, re-authenticate |
| 403 | Forbidden | Check permissions, show "not authorized" |
| 404 | Not found | Refresh data, show "not found" message |
| 409 | Conflict | Handle duplicate/state conflict, show message |
| 422 | Validation error | Check required fields, highlight in form |
| 500 | Server error | Show "try again later", log to backend team |
| 503 | Unavailable | Show "service maintenance", retry later |

---

## Performance Expectations

| Endpoint Type | Response Time | Notes |
|---------------|---------------|-------|
| Health checks | <50ms | Lightweight, frequent polling OK |
| List endpoints | 200-500ms | Pagination helps (limit 50) |
| Detail endpoints | 200-400ms | Usually cached |
| Create endpoints | 300-800ms | Database insert + audit |
| Analysis endpoints | 500ms-2s | Calculation heavy |
| Dashboard KPIs | 1-3s | Multiple aggregations |

**Recommendations**:
- Cache list data for 5-10 minutes
- Show loading spinners for requests >500ms
- Use background refresh (don't block UI)
- Implement error retry with exponential backoff

---

## Recommended Request Order (First Time)

1. **Verify connectivity**: GET /health
2. **Check authentication**: GET /current-user (will fail with 401 if no token)
3. **Test read-only**: GET /api/va-intake/leads (small limit=5)
4. **Test write**: POST /api/va-intake/lead (create test lead)
5. **Test detail**: GET /api/va-intake/leads/{test_lead_id}
6. **Test workflow**: POST /api/va-intake/approvals/{approval_id}/approve

If all above succeed, full integration is likely viable.

---

## Endpoints to Test Early (Day 1 Validation)

```
✓ GET  /health                          (no auth)
✓ GET  /api/go-live/status             (verify go-live mode)
✓ GET  /api/va-intake/leads            (verify data access)
✓ POST /api/va-intake/lead             (verify create permission)
✓ GET  /api/deals                      (verify deals exist or empty list)
```

If all 5 pass, backend is ready for WeWeb integration.

---

## Full Endpoint List Reference

| Category | Count | Key Endpoints |
|----------|-------|---------------|
| Health | 5 | /health, /healthz, /readyz, /metrics |
| Go-Live | 3 | /api/go-live/status, /enable, /disable |
| VA Intake | 9 | leads (CRUD), approvals (queue, approve, deny) |
| Deals | 63 | deals (CRUD), actions, analysis |
| Buyers | 20 | /api/buyers, /api/deals/{id}/buyers, send-to-buyer |
| Messaging | 12 | draft-seller-message, create-buyer-packet, send |
| Reports | 12 | summary, eia, deal-analysis |
| Notifications | 30 | notifications (list, read, read-all) |
| Audit | 9 | audit-log (list, detail) |
| Jarvis | 14 | dashboard, hot-contacts |
| FLIP | 2 | estimate, timeline |
| BRRRR | 19 | estimate, financing-options |
| **Total** | **902 paths, 1088 operations** | See openapi.json for exhaustive list |

---

## Documentation Files

| File | Purpose |
|------|---------|
| **openapi.json** | Full OpenAPI 3.1 schema (machine-readable) |
| **WEWEB_BACKEND_CONTRACT.md** | Human-readable endpoint definitions (50+ pages) |
| **WEWEB_VARIABLES.md** | Variable setup and lifecycle |
| **WEWEB_WORKFLOWS.md** | Step-by-step workflow implementations |
| **WEWEB_PAGE_MAP.md** | UI pages and endpoint mappings |
| **WEWEB_BUILD_ORDER.md** | Safe build sequence (5 phases) |
| **WEWEB_DO_NOT_TOUCH.md** | Critical constraints (MUST READ) |

---

## Next Steps

1. **Download openapi.json** → Import to Postman/Insomnia for testing
2. **Test health endpoint** → Confirm backend is running
3. **Review WEWEB_DO_NOT_TOUCH.md** → Understand critical constraints
4. **Follow WEWEB_BUILD_ORDER.md** → Build in phases, test each phase
5. **Use WEWEB_BACKEND_CONTRACT.md** → Reference while building
6. **Refer to WEWEB_WORKFLOWS.md** → Implement workflows correctly

---

**Last Updated**: 2026-05-19  
**OpenAPI Version**: 3.1.0  
**Backend Ready**: ✅ YES - 902 endpoints, all operational
