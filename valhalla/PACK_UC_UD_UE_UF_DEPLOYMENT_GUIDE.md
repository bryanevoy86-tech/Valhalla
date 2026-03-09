# PACK UC, UD, UE, UF Deployment & Operations Guide

## Deployment Steps

### 1. Pre-Deployment Verification
```bash
cd c:\dev\valhalla\services\api

# Verify all files are present
ls -la app/models/rate_limit.py
ls -la app/models/api_clients.py
ls -la app/models/maintenance.py
ls -la app/schemas/rate_limit.py
ls -la app/schemas/api_clients.py
ls -la app/schemas/maintenance.py
ls -la app/schemas/admin_ops.py
ls -la app/services/rate_limit.py
ls -la app/services/api_clients.py
ls -la app/services/maintenance.py
ls -la app/services/admin_ops.py
ls -la app/routers/rate_limit.py
ls -la app/routers/api_clients.py
ls -la app/routers/maintenance.py
ls -la app/routers/admin_ops.py
ls -la app/tests/test_rate_limit.py
ls -la app/tests/test_api_clients.py
ls -la app/tests/test_maintenance.py
ls -la app/tests/test_admin_ops.py
ls -la alembic/versions/0072_pack_uc_rate_limits.py
ls -la alembic/versions/0073_pack_ud_api_clients.py
ls -la alembic/versions/0074_pack_ue_maintenance.py
```

### 2. Run Migrations
```bash
# From valhalla root
cd c:\dev\valhalla

# Apply migrations
alembic upgrade head

# Verify migrations (should show 0074_pack_ue_maintenance)
alembic current
```

### 3. Verify Route Registration
```bash
# Start application
cd services/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# In another terminal, verify endpoints exist
curl http://localhost:8000/system/ratelimits/rules
curl http://localhost:8000/system/clients/
curl http://localhost:8000/system/maintenance/state
curl http://localhost:8000/admin/ops/ -X POST -H "Content-Type: application/json" \
  -d '{"action": "get_maintenance_state"}'
```

### 4. Run Test Suite
```bash
cd services/api

# Run all tests for these packs
pytest app/tests/test_rate_limit.py -v
pytest app/tests/test_api_clients.py -v
pytest app/tests/test_maintenance.py -v
pytest app/tests/test_admin_ops.py -v

# Or all at once
pytest app/tests/test_rate_limit.py app/tests/test_api_clients.py \
        app/tests/test_maintenance.py app/tests/test_admin_ops.py -v
```

### 5. Integration Testing
```bash
# Test PACK UC: Rate Limits
curl -X POST http://localhost:8000/system/ratelimits/rules \
  -H "Content-Type: application/json" \
  -d '{"scope": "ip", "key": "192.168.1.1", "max_requests": 100}'
# Should return 200 with rule object

# Test PACK UD: API Clients
curl -X POST http://localhost:8000/system/clients/ \
  -H "Content-Type: application/json" \
  -d '{"name": "TestClient", "client_type": "test", "api_key": "sk_test_123"}'
# Should return 200 with client object

# Test PACK UE: Maintenance
curl -X GET http://localhost:8000/system/maintenance/state
# Should return 200 with mode, reason, updated_at

# Test PACK UF: Admin Ops
curl -X POST http://localhost:8000/admin/ops/ \
  -H "Content-Type: application/json" \
  -d '{"action": "get_maintenance_state"}'
# Should return 200 with ok=true and data containing mode
```

### 6. Production Deployment Checklist
- [ ] All migrations run successfully
- [ ] All tests pass (pytest)
- [ ] Rate limit endpoints return proper CRUD responses
- [ ] API client endpoints allow register/list/activate/deactivate
- [ ] Maintenance state can be read and set
- [ ] Admin ops console executes actions correctly
- [ ] Load testing shows no performance degradation
- [ ] Tyr can manage rate limits and clients
- [ ] Heimdall can check maintenance state and trigger actions
- [ ] Documentation updated for operations team

---

## File Inventory

### Models (3 files)
- `app/models/rate_limit.py` — RateLimitRule, RateLimitSnapshot (40 lines)
- `app/models/api_clients.py` — ApiClient (20 lines)
- `app/models/maintenance.py` — MaintenanceWindow, MaintenanceState (32 lines)

### Schemas (4 files)
- `app/schemas/rate_limit.py` — RateLimitRuleSet, RateLimitRuleOut, RateLimitSnapshotOut (46 lines)
- `app/schemas/api_clients.py` — ApiClientCreate, ApiClientOut, ApiClientList (31 lines)
- `app/schemas/maintenance.py` — MaintenanceWindowCreate/Out, MaintenanceStateOut (33 lines)
- `app/schemas/admin_ops.py` — AdminActionRequest/Response (16 lines)

### Services (4 files)
- `app/services/rate_limit.py` — CRUD and snapshot queries (78 lines)
- `app/services/api_clients.py` — Client registration and activation (44 lines)
- `app/services/maintenance.py` — Window management and state control (67 lines)
- `app/services/admin_ops.py` — High-level action orchestration (112 lines)

### Routers (4 files)
- `app/routers/rate_limit.py` — 5 endpoints for rules and snapshots (72 lines)
- `app/routers/api_clients.py` — 4 endpoints for client management (47 lines)
- `app/routers/maintenance.py` — 4 endpoints for windows and state (64 lines)
- `app/routers/admin_ops.py` — 1 high-level admin endpoint (17 lines)

### Tests (4 files)
- `app/tests/test_rate_limit.py` — 6 test cases (96 lines)
- `app/tests/test_api_clients.py` — 5 test cases (91 lines)
- `app/tests/test_maintenance.py` — 7 test cases (106 lines)
- `app/tests/test_admin_ops.py` — 5 test cases (75 lines)

### Migrations (3 files)
- `alembic/versions/0072_pack_uc_rate_limits.py` — rate_limit_rules and snapshots tables (40 lines)
- `alembic/versions/0073_pack_ud_api_clients.py` — api_clients table (30 lines)
- `alembic/versions/0074_pack_ue_maintenance.py` — maintenance_windows and maintenance_state tables (36 lines)

### Configuration
- `app/main.py` — Added 5 router imports and includes (updated, +35 lines)

---

## Database Changes Summary

### New Tables

1. **rate_limit_rules** (PACK UC)
   - 9 columns: id, scope, key, window_seconds, max_requests, enabled, description, created_at, updated_at
   - 1 composite index: (scope, key)
   - Purpose: Store rate limit rules

2. **rate_limit_snapshots** (PACK UC)
   - 8 columns: id, scope, key, window_seconds, max_requests, current_count, window_started_at, updated_at
   - 1 composite index: (scope, key)
   - Purpose: Audit log of rate limit states

3. **api_clients** (PACK UD)
   - 8 columns: id, name, client_type, api_key, active, description, created_at, updated_at
   - 2 indexes: api_key (unique), active
   - Purpose: Register external clients

4. **maintenance_windows** (PACK UE)
   - 5 columns: id, starts_at, ends_at, description, active
   - 1 index: starts_at
   - Purpose: Schedule maintenance periods

5. **maintenance_state** (PACK UE)
   - 4 columns: id (always=1), mode, reason, updated_at
   - Single-row lookup table
   - Purpose: Current system maintenance mode

### Rollback Plan
```bash
# Rollback to previous migration
alembic downgrade -1

# Or specific revision
alembic downgrade 0071_pack_ua_feature_flags

# Verify
alembic current
```

---

## Performance Considerations

### PACK UC: Rate Limiting
- **Rule Query**: O(1) with indexed (scope, key)
- **Snapshot Query**: O(n) where n=limit (default 200)
- **Recommendation**: Snapshot queries used for audit/monitoring, not real-time enforcement
- **Note**: Actual rate limiting enforcement should use Redis/in-memory store, this is audit layer

### PACK UD: API Clients
- **Lookup by Key**: O(1) with unique index
- **List All**: O(n) where n=num clients (typically <100)
- **Recommendation**: Cache active clients in memory if > 1000 clients

### PACK UE: Maintenance
- **State Get**: O(1) single-row table
- **State Set**: O(1) single-row update
- **Window List**: O(n) where n=num windows
- **Recommendation**: Cache maintenance state in request context

### PACK UF: Admin Ops
- **Action Execute**: Depends on action, typically <100ms
- **Security Snapshot**: Slowest action, ~50-200ms
- **Recommendation**: Admin console is low-traffic, no caching needed

---

## Security Considerations

### PACK UC: Rate Limiting
- **Risk**: Rules exposed to authenticated users
- **Mitigation**: Should require admin privilege
- **Status**: Add RBAC in future versions
- **Note**: This endpoint is for audit/configuration, actual enforcement is external

### PACK UD: API Clients
- **Risk**: API keys visible if database compromised
- **Mitigation**: Never log full keys, hash before storage (future)
- **Status**: Currently stores keys in plaintext
- **Recommendation**: Implement key hashing in next iteration

### PACK UE: Maintenance
- **Risk**: Anyone can toggle maintenance mode
- **Mitigation**: Should require admin privilege
- **Status**: Add RBAC in future versions
- **Note**: Mode changes should trigger alerts

### PACK UF: Admin Ops
- **Risk**: High-level power with no auth currently
- **Mitigation**: **MUST** be protected by auth + RBAC
- **Status**: Currently unprotected, unsafe for production
- **Action Required**: Implement RBAC before deploying to production

---

## Monitoring & Alerting

### Key Metrics to Track
1. **Rate Limit Rule Count**: Should remain stable
2. **Active API Clients**: Should match expected integrations
3. **Maintenance State Changes**: Should be rare, each one is critical
4. **Admin Ops Executions**: Should be logged and audited

### Alerts to Set Up
1. Alert if `GET /system/ratelimits/rules` returns 5xx error
2. Alert if maintenance_state.mode != "normal" for > 30 minutes
3. Alert for any POST to `/admin/ops/` (every action should trigger alert)
4. Alert if api_clients.active count drops unexpectedly

### Logging
```python
# All PACK UC/UD/UE actions should log to system_log
from app.services.system_log import write_log
from app.schemas.system_log import SystemLogCreate

log = SystemLogCreate(
    level="info",
    category="admin_ops",
    message="Maintenance mode set to read_only",
    context={"mode": "read_only", "reason": "..."}
)
write_log(db, log)
```

---

## Operational Procedures

### Emergency Lockdown
1. Set system to read_only: `POST /system/maintenance/state/read_only?reason=EMERGENCY`
2. Check security dashboard: `POST /admin/ops/` with `security_snapshot`
3. Investigate root cause
4. Resume normal: `POST /system/maintenance/state/normal`

### Client Rotation (Planned)
1. Create new client: `POST /system/clients/`
2. Let new client coexist with old
3. Monitor logs for full migration
4. Deactivate old: `POST /system/clients/{id}/deactivate`
5. Delete old after retention period

### Rate Limit Escalation (Abuse Response)
1. Identify abuser IP/user/key
2. Create restrictive rule: `POST /system/ratelimits/rules`
3. Monitor snapshot: `GET /system/ratelimits/snapshots?scope=ip`
4. Adjust limits as abuse stops/continues

### Scheduled Maintenance
1. Create window: `POST /system/maintenance/windows` (24hrs in advance)
2. 1 hour before: Set to maintenance mode with window ID in reason
3. During window: Set to read_only if data consistency critical
4. After window: Return to normal
5. Update window active=false when complete

---

## Troubleshooting

### Issue: Rate limit rule not taking effect
- **Cause**: Rules are stored but not enforced by middleware
- **Fix**: Implement middleware to check rules and return 429
- **Verify**: Check rule is created and enabled=true

### Issue: API client still active after deactivate
- **Cause**: Client code might not validate on every request
- **Fix**: Ensure code calls get_api_client_by_key which filters active=true
- **Verify**: Check active=false in database

### Issue: Maintenance mode not blocking requests
- **Cause**: Enforcement middleware not implemented
- **Fix**: Add middleware to check maintenance_state and return 503 if not normal
- **Verify**: Manual test by setting mode and making request

### Issue: Admin ops console error
- **Cause**: Dependent service (dashboard, maintenance, feature_flags) is down
- **Fix**: Check all dependent service health
- **Verify**: Call individual endpoints directly

### Issue: Maintenance state always shows "normal"
- **Cause**: Initialization row might not be created
- **Fix**: Call set_maintenance_mode to trigger _ensure_state_row
- **Verify**: Check maintenance_state table has row with id=1

---

## Support & Documentation

### For Questions
- Review operational guide for maintenance procedures
- Review quick reference for endpoint examples
- Check test files for usage patterns

### For Issues
1. Check application logs for errors
2. Verify database migrations: `alembic current`
3. Test endpoints manually with curl
4. Check if dependent services are operational
5. Review this guide's troubleshooting section

---

## Version History

- **v1.0.0** (2025-12-06)
  - Initial implementation of PACK UC, UD, UE, UF
  - Rate limiting rule CRUD + snapshots
  - API client registration and lifecycle
  - Maintenance window scheduling + state management
  - Admin ops console for high-level actions
