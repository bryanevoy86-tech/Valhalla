# Governance Runbook Deployment - Complete

## Summary
The Valhalla governance runbook system has been successfully deployed to production on Render. All endpoints are operational and secured.

## Deployment Timeline
- **Commit 0e02851**: Converge release with governance hardening
- **Commit 239ec30**: Initial debug logging for governance routes
- **Commit 08b1287**: Route list debugging + disabled conflicting router
- **Commit b5b0e9f**: ✅ **FIXED** - Added governance router to correct main.py (services/api/main.py)
- **Commit 0d08af7**: ✅ **SECURITY** - Gated debug endpoint behind env var, documented dual endpoints

## Key Finding
The repository had **two different main.py files**:
- `/services/api/app/main.py` - Complex governance file (NOT used by Render)
- `/services/api/main.py` - **ACTUAL production file** (used by Render)

Render was deploying from `/services/api/main.py` but I was editing `/services/api/app/main.py`. This caused the governance router to never be mounted despite correct code being in the "wrong" file.

## Production Endpoints

### Health Check (Uptime Monitoring)
```
GET https://valhalla-api-ha6a.onrender.com/health
Response: {"status": "ok"}
Status: 200 OK
```

### Governance Runbook (Go-Live Status)
```
GET https://valhalla-api-ha6a.onrender.com/api/governance/runbook/status
Response: {
  "generated_at": "2026-01-17T...",
  "blockers": [...],
  "warnings": [...],
  "info": [...],
  "ok_to_enable_go_live": bool
}
Status: 200 OK
```

### Legacy Runbook (Backward Compatibility)
```
GET https://valhalla-api-ha6a.onrender.com/api/runbook/status
Status: 200 OK (kept for migration period)
```

### Debug Routes (Disabled by Default)
```
GET https://valhalla-api-ha6a.onrender.com/__routes
Status: 404 (unless EXPOSE_DEBUG_ROUTES=1 is set in Render)
Purpose: Lists all registered routes for debugging
```

## Security Configuration

### Debug Endpoint Protection
The `/__routes` endpoint is gated behind an environment variable:
- **Default**: Returns 404 (disabled)
- **To enable temporarily**: Set `EXPOSE_DEBUG_ROUTES=1` in Render environment settings
- **Production**: Always keep `EXPOSE_DEBUG_ROUTES=0` or unset

### CORS
- Enabled for all origins (`*`)
- Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Headers: Authorization, Content-Type, Accept, X-Requested-With

## Files Modified

### services/api/main.py
```python
# Added import:
from app.routers import runbook as governance_runbook_router

# Added router mount:
app.include_router(governance_runbook_router.router, prefix="/api")

# Added secure debug endpoint:
if os.getenv("EXPOSE_DEBUG_ROUTES") == "1":
    @app.get("/__routes", include_in_schema=False)
    def __routes():
        return JSONResponse(sorted({r.path for r in app.router.routes}))
else:
    @app.get("/__routes", include_in_schema=False)
    def __routes_disabled():
        raise HTTPException(status_code=404, detail="Not found")
```

## WeWeb Integration

### Configuration
```
Base URL: https://valhalla-api-ha6a.onrender.com
Health Endpoint: /health
Governance Endpoint: /api/governance/runbook/status
```

### Health Check Setup
- Endpoint: `/health`
- Expected: `200 OK` with `{"status": "ok"}`
- Retry: 3 consecutive failures before marking service as down
- Timeout: 10 seconds

### Smoke Test
Before deploying to production users:
1. Verify `/health` returns 200
2. Verify `/api/governance/runbook/status` returns 200 with governance data
3. Check browser console for CORS errors (should be none)
4. Load test the service for 5+ minutes

## Monitoring & Alerts

### Uptime Alerts
Monitor: `GET /health`
- Alert on: HTTP status != 200
- Alert on: Response time > 5 seconds

### Governance/Go-Live Alerts
Monitor: `GET /api/governance/runbook/status`
- Alert on: HTTP status != 200
- Alert on: `blockers.length > 0`
- Alert on: `ok_to_enable_go_live == false`

## Dual Endpoint Strategy

Two runbook endpoints exist for backward compatibility:

1. **Legacy**: `/api/runbook/status`
   - Purpose: Unified health check
   - Status: Maintained for backward compatibility
   - Recommendation: Deprecate after migration period

2. **Canonical** ⭐: `/api/governance/runbook/status`
   - Purpose: Go-live readiness + policy compliance
   - Status: Recommended for new integrations
   - Features: Blockers, warnings, info, policies

### Recommendation
Use `/api/governance/runbook/status` for all new work. The legacy endpoint can be deprecated once all consumers migrate.

## Commit History

```
0d08af7 - SECURITY: Gate /__routes behind EXPOSE_DEBUG_ROUTES env var; document dual runbook endpoints
b5b0e9f - FIX: Add governance_runbook router to correct main.py (services/api/main.py) with debug route listing
08b1287 - DEBUG: Add route list endpoint, isolate governance_runbook router by disabling runbook_status
239ec30 - DEBUG: Add route registration logging for governance/runbook endpoints
0e02851 - Converge release: dedupe + sanity + stable deploy
```

## Status
✅ **PRODUCTION READY**

All endpoints are operational, secured, and ready for WeWeb integration and production monitoring.
