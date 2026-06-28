# WeWeb: DO NOT TOUCH

**Critical backend assumptions and production constraints that must be preserved**

---

## Backend Entry Point (SACRED)

**Location**: `d:\dev\services\api`

**Start Command** (LOCAL DEV):
```bash
cd d:\dev\services\api
. .venv/bin/activate
uvicorn app.main:app --reload --port 4000
```

**Start Command** (RENDER PRODUCTION):
```bash
cd d:\dev
python start.py
# Runs: uvicorn app.main:app --host 0.0.0.0 --port PORT --reload=False
```

### Why This Matters:
- Backend MUST start from `services/api` directory
- Using `d:\dev` as working directory will cause namespace collision
- `app` package resolution depends on directory context
- Render deployment uses `start.py` which handles PORT/HOST injection

**DO NOT**:
- Change working directory to d:\dev before running
- Modify entry point in start.py
- Change `app.main:app` import string
- Use different port than 4000 (dev) without updating WeWeb config

---

## Authentication Context

**Session Token Header**:
```
Session-Token: <token_value>
```

**JWT Bearer Token** (alternative):
```
Authorization: Bearer <jwt_token_value>
```

### Do NOT:
- Mix both headers in same request
- Send token in query parameter
- Forget to URL-encode Bearer token if it contains special chars
- Use different token name (WeWeb must use exact header names)
- Assume unauthenticated requests work (most endpoints require auth)

**Token Storage**:
- Store in WeWeb's **secure variable** (not localStorage)
- Must be included in EVERY request (except GET /health)
- Expires after ~24 hours (backend may enforce refresh)

---

## Database Context (MUST NOT MODIFY)

**Database URL** (set via environment variable):
```
DATABASE_URL="postgresql://user:pass@host:5432/valhalla"  # Production
DATABASE_URL="sqlite:///valhalla_test.db"                 # Local fallback
```

**Alembic Migrations**:
- Located in `d:\dev\services\api\alembic/`
- Managed by backend team only
- WeWeb must NEVER create tables, columns, or indexes
- WeWeb must NEVER run migrations (backend handles on startup)

### DO NOT:
- Attempt to modify database schema
- Create new tables for caching (use API endpoints only)
- Run SQL directly against database
- Assume schema is fixed (backend may migrate)
- Store large objects in database cache

**Result**: All data must flow through API endpoints. No direct database access.

---

## Protected Routes (DO NOT USE)

These endpoints exist but are **reserved for backend internal use** and may change:

- `/docs` - Swagger UI (internal documentation only)
- `/redoc` - ReDoc API docs (internal documentation only)
- `/openapi.json` - Schema export (read-only, for reference)
- `/internal/*` - Any path starting with /internal/
- `/admin/system/*` - System management endpoints
- `/debug/*` - Debug/diagnostic endpoints

**Result**: WeWeb must only use endpoints documented in WEWEB_BACKEND_CONTRACT.md

---

## Critical Endpoints (High Availability Required)

These endpoints must NEVER fail or WeWeb experience degrades:

| Endpoint | Criticality | Fallback Strategy |
|----------|-----------|-------------------|
| GET /health | Critical | Retry every 5 seconds, show "offline" banner if fails |
| POST /api/auth/login | Critical | Show login error, suggest "contact support" |
| GET /api/go-live/status | Critical | Assume "inactive" if unavailable |
| GET /api/va-intake/leads | High | Show "leads unavailable" placeholder |
| GET /api/deals | High | Show "deals unavailable" placeholder |
| GET /api/reports/summary | Medium | Show "dashboard updating..." spinner |

**DO NOT**:
- Hard-fail if reporting endpoints are slow
- Assume 100% uptime from backend
- Cache results for >5 minutes
- Retry failed requests without backoff

---

## Namespace Collision Prevention

**Backend uses split packages** (intentional design):
```
d:\dev\app/                    # WeWeb-related routes (heimdall)
d:\dev\services\api\app/       # Core backend (models, services, routers)
```

### DO NOT:
- Import from `d:\dev\app` directly in backend code
- Assume `from app.something` resolves the same everywhere
- Change sys.path configuration in start.py
- Add new modules to `d:\dev\app` without backend team approval
- Move services/api/app to d:\dev\app

**Result**: Canonical backend is services/api/app. Do not create dependencies on wrapper package.

---

## CORS Configuration

**Allowed Origins** (set via environment):
```
CORS_ALLOWED_ORIGINS="http://localhost:3000,https://app.valhalla.com"
```

**Requests from WeWeb must**:
- Include `Origin` header (automatic in browsers)
- Follow same origin policy
- NOT use credentials unless explicitly allowed
- NOT use preflight workarounds (rely on backend CORS)

### DO NOT:
- Hard-code CORS headers in WeWeb
- Attempt to bypass CORS restrictions
- Use fetch with mode='no-cors' (breaks backend integration)
- Assume cookies work (only tokens supported)

---

## Error Response Format

**All errors from backend follow this structure**:
```json
{
  "detail": "Human readable error message",
  "status": 400,
  "type": "error_type_identifier"
}
```

### DO NOT:
- Assume HTTP status code alone indicates error type
- Parse error messages with regex (use `type` field)
- Ignore 400-level errors (they contain useful info)
- Log full error objects to console (may contain sensitive data)

**Result**: Always parse `error.detail` for user-facing messages.

---

## Performance Constraints

**Backend capacity limits**:
```
Max list size:           10,000 items (for GET /api/deals, etc.)
Max bulk create:         100 items (per batch import)
Typical query time:      200-500ms
Health check time:       <50ms
```

### DO NOT:
- Request `limit > 500` on list endpoints (will be capped)
- Attempt to import >100 leads in single batch
- Refresh critical data faster than every 10 seconds
- Poll endpoints continuously (use webhooks if available)

---

## Sensitive Fields (DO NOT EXPOSE)

**Fields that should NEVER appear in logs/console**:
- `password` (backend never returns, don't store)
- `api_key` (use AUTH_TOKEN instead)
- `ssn` (if present in data, never log)
- Full `email` in URLs (only use IDs)
- `phone` numbers without masking in UI (X-XXX-XXXX pattern)

### DO NOT:
- Log entire API responses
- Display sensitive fields in errors
- Store tokens in localStorage (use secure storage)
- Copy/paste token values in Slack/email

---

## Upgrade & Rollback

**Backend is deployed to Render** without WeWeb's input or approval.

### When backend updates:
- API contract may change
- New endpoints may be added
- Deprecated endpoints may be removed
- Response format may vary slightly

### WeWeb must:
- Handle 404 for deprecated endpoints
- Validate response structure before using
- Fall back gracefully if new endpoints don't exist
- Use version headers if available

### DO NOT:
- Assume endpoint stability (backend is under active development)
- Hard-code assumptions about response format
- Fail completely if single endpoint changes
- Require backend coordination for WeWeb deploys

---

## Testing Against Backend

**Safe testing practices**:
- Always test against live backend (d:\dev/services\api or Render prod)
- Use read-only endpoints first (GET /health, GET /api/deals)
- Create test leads/deals before testing workflows
- Clean up test data after testing (if deletable)

### DO NOT:
- Assume mock data is equivalent to real backend
- Test against stale OpenAPI.json
- Create thousands of test records
- Modify production data for testing

---

## Common Mistakes to AVOID

| Mistake | Impact | Fix |
|---------|--------|-----|
| Forget AUTH_TOKEN in request | 401 errors everywhere | Always include token in header |
| Use wrong API_BASE_URL | All requests fail | Check environment config |
| Parse error response as success | Silent failures | Check HTTP status before parsing |
| Cache data too long | Stale information | Refresh every 5-10 minutes |
| Block on slow endpoint | UI freezes | Load in background, show placeholder |
| Assume endpoint exists | 404 errors | Validate endpoint before using |
| Mix Session-Token + Bearer | Conflicts | Use one auth method only |
| Hardcode test token | Auth fails in production | Use environment variable |

---

## Support & Escalation

**If something breaks**:

1. **Check health endpoint first**:
   ```
   GET http://localhost:4000/health
   ```
   If fails → Backend is down, contact backend team

2. **Check your request**:
   - Is AUTH_TOKEN present?
   - Is API_BASE_URL correct?
   - Is JSON body valid?
   - Check Network tab in WeWeb debugger

3. **Check OpenAPI spec**:
   - Does endpoint exist in openapi.json?
   - Are required fields present in body?
   - Is response format as documented?

4. **Contact backend team** (if above passes):
   - Provide error message from `error.detail`
   - Provide endpoint path and HTTP method
   - Provide request body (scrub tokens)
   - Provide backend logs if available

---

## Documentation Sources

| Topic | Source |
|-------|--------|
| Endpoint definitions | WEWEB_BACKEND_CONTRACT.md |
| OpenAPI schema | openapi.json |
| WeWeb variables | WEWEB_VARIABLES.md |
| WeWeb workflows | WEWEB_WORKFLOWS.md |
| Page layouts | WEWEB_PAGE_MAP.md |
| Build sequence | WEWEB_BUILD_ORDER.md |
| Full backend code | d:\dev\services\api\ (for backend team) |

---

## Emergency Contacts

- **Backend is down**: Contact backend team, check Render dashboard
- **Auth not working**: Verify JWT_SECRET is correct in environment
- **Data is stale**: Check if refresh workflows are running
- **Unknown error**: Check WEWEB_BACKEND_CONTRACT.md for endpoint definition

---

**DO NOT BYPASS THESE CONSTRAINTS**  
This document preserves critical backend assumptions.  
Violating these rules may cause:
- Silent data loss
- Security vulnerabilities
- Backend crashes
- Permanent production outages

---

**Last Updated**: 2026-05-19
