# PACK TY, TZ, UA, UB Deployment Package

## Deployment Steps

### 1. Pre-Deployment Verification
```bash
cd c:\dev\valhalla\services\api

# Verify all files are present
ls -la app/schemas/route_index.py
ls -la app/services/route_index.py
ls -la app/routers/route_index.py
ls -la app/models/system_config.py
ls -la app/schemas/system_config.py
ls -la app/services/system_config.py
ls -la app/routers/system_config.py
ls -la app/schemas/feature_flags.py
ls -la app/services/feature_flags.py
ls -la app/routers/feature_flags.py
ls -la app/schemas/deployment_profile.py
ls -la app/services/deployment_profile.py
ls -la app/routers/deployment_profile.py
ls -la app/tests/test_route_index.py
ls -la app/tests/test_system_config.py
ls -la app/tests/test_feature_flags.py
ls -la app/tests/test_deployment_profile.py
ls -la alembic/versions/0070_pack_tz_system_config.py
ls -la alembic/versions/0071_pack_ua_feature_flags.py
```

### 2. Run Migrations
```bash
# From valhalla root
cd c:\dev\valhalla

# Apply migrations
alembic upgrade head

# Verify migrations
alembic current
```

### 3. Verify Route Registration
```bash
# Start application
cd services/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# In another terminal, verify endpoints exist
curl http://localhost:8000/debug/routes/ | jq '.total'
curl http://localhost:8000/system/config/ | jq '.total'
curl http://localhost:8000/system/features/ | jq '.total'
curl http://localhost:8000/system/deploy/profile | jq '.environment'
```

### 4. Run Test Suite
```bash
cd services/api

# Run all tests for these packs
pytest app/tests/test_route_index.py -v
pytest app/tests/test_system_config.py -v
pytest app/tests/test_feature_flags.py -v
pytest app/tests/test_deployment_profile.py -v

# Or run all at once
pytest app/tests/test_route_index.py app/tests/test_system_config.py \
        app/tests/test_feature_flags.py app/tests/test_deployment_profile.py -v
```

### 5. Integration Testing
```bash
# Test PACK TY: Route Index
curl -X GET http://localhost:8000/debug/routes/ | jq '.total'
# Should return number > 0

# Test PACK TZ: System Config
curl -X POST http://localhost:8000/system/config/ \
  -H "Content-Type: application/json" \
  -d '{"key": "test_key", "value": "test_value"}'
# Should return 200 with full config object

curl -X GET http://localhost:8000/system/config/test_key
# Should return 200 with the config we just created

# Test PACK UA: Feature Flags
curl -X POST http://localhost:8000/system/features/ \
  -H "Content-Type: application/json" \
  -d '{"key": "test_flag", "enabled": true, "group": "test"}'
# Should return 200 with flag object

curl -X GET http://localhost:8000/system/features/test_flag
# Should return { "key": "test_flag", "enabled": true }

# Test PACK UB: Deployment Profile
curl -X GET "http://localhost:8000/system/deploy/profile?environment=dev"
# Should return { "environment": "dev", "version": "...", "timestamp": "..." }

curl -X GET "http://localhost:8000/system/deploy/smoke?base_url=http://localhost:8000&environment=dev"
# Should return report with results[] and all_ok field
```

### 6. Production Deployment Checklist
- [ ] All migrations run successfully
- [ ] All tests pass (pytest)
- [ ] Route index endpoint returns all routes including new ones
- [ ] System config endpoints CRUD operations work
- [ ] Feature flags can be created, read, listed, filtered
- [ ] Deployment profile returns correct environment and version
- [ ] Smoke tests pass (all_ok=true)
- [ ] Load testing shows no performance degradation
- [ ] Heimdall can call all new endpoints
- [ ] Documentation updated for operations team

---

## File Inventory

### Models (2 files)
- `app/models/system_config.py` — SystemConfig ORM (15 lines)
- `app/models/feature_flags.py` — Already exists, no changes needed

### Schemas (5 files)
- `app/schemas/route_index.py` — RouteInfo, RouteIndex (17 lines)
- `app/schemas/system_config.py` — SystemConfigSet, SystemConfigOut, SystemConfigList (28 lines)
- `app/schemas/feature_flags.py` — Already exists, no changes needed
- `app/schemas/deployment_profile.py` — DeploymentProfile, SmokeTestResult, SmokeTestReport (28 lines)

### Services (4 files)
- `app/services/route_index.py` — build_route_index (35 lines)
- `app/services/system_config.py` — set_config, get_config, list_configs (55 lines)
- `app/services/feature_flags.py` — Already exists, no changes needed
- `app/services/deployment_profile.py` — get_deployment_profile, run_smoke_tests (71 lines)

### Routers (4 files)
- `app/routers/route_index.py` — GET /debug/routes/ (32 lines)
- `app/routers/system_config.py` — POST/GET /system/config/ endpoints (42 lines)
- `app/routers/feature_flags.py` — Already exists, no changes needed
- `app/routers/deployment_profile.py` — GET /system/deploy/profile, /smoke (41 lines)

### Tests (4 files)
- `app/tests/test_route_index.py` — 3 test cases (42 lines)
- `app/tests/test_system_config.py` — 6 test cases (78 lines)
- `app/tests/test_feature_flags.py` — Already exists, no changes needed
- `app/tests/test_deployment_profile.py` — 3 test cases (37 lines)

### Migrations (2 files)
- `alembic/versions/0070_pack_tz_system_config.py` — system_config table (25 lines)
- `alembic/versions/0071_pack_ua_feature_flags.py` — feature_flags table (28 lines)

### Configuration
- `app/main.py` — Added 4 router imports and includes (updated, +30 lines)

### Documentation (3 files)
- `PACK_TY_TZ_UA_UB_IMPLEMENTATION.md` — Full implementation guide (~450 lines)
- `PACK_TY_TZ_UA_UB_QUICK_REFERENCE.md` — API reference and examples (~300 lines)
- `PACK_TY_TZ_UA_UB_DEPLOYMENT_PACKAGE.md` — This file

---

## Database Changes Summary

### New Tables
1. **system_config** (PACK TZ)
   - 7 columns: id, key, value, description, mutable, created_at, updated_at
   - 1 index: key (unique)
   - Purpose: Store non-secret configuration

2. **feature_flags** (PACK UA)
   - 7 columns: id, key, enabled, description, group, created_at, updated_at
   - 2 indexes: key (unique), group
   - Purpose: Store feature toggles

### Rollback Plan
If deployment fails:
```bash
# Rollback to previous migration
alembic downgrade -1

# Or to specific revision
alembic downgrade 0069_pack_tv_system_logs

# Verify
alembic current
```

---

## Performance Considerations

### PACK TY: Route Index
- **Latency**: < 5ms (scans app.routes in memory)
- **Caching**: Not cached (routes are static)
- **Load**: Very low, safe to call frequently
- **Recommendation**: Call once at startup, cache in Heimdall

### PACK TZ: System Config
- **Latency**: 1-5ms per operation (single DB lookup)
- **Caching**: Could cache in-memory if needed
- **Load**: Low, typical CRUD operations
- **Recommendation**: Cache in application if values rarely change

### PACK UA: Feature Flags
- **Latency**: 1-3ms per is_feature_enabled call
- **Caching**: Highly recommended (flags change rarely)
- **Load**: Low, but called frequently from routes
- **Recommendation**: Use in-memory cache with TTL (5-10 minutes)

### PACK UB: Deployment Profile & Smoke Tests
- **Profile Latency**: < 1ms (single DB lookup + memory read)
- **Smoke Test Latency**: 5-30s depending on endpoint responsiveness
- **Recommendation**: Profile call is fast, smoke tests should be run only after deployment
- **Warning**: Don't call smoke tests frequently, they're for validation only

---

## Monitoring & Alerting

### Key Metrics to Track
1. **Route Index Response Time**: Should be < 10ms
2. **Config Get Response Time**: Should be < 5ms
3. **Feature Flag Check Response Time**: Should be < 5ms
4. **Smoke Test Success Rate**: Should be 100% in healthy deployment

### Alerts to Set Up
1. Alert if `/debug/routes/` returns 5xx error
2. Alert if system_config table is unreachable
3. Alert if feature_flags table is unreachable
4. Alert if smoke tests return all_ok=false

---

## Security Considerations

### PACK TY: Route Index
- **Risk**: Exposes API surface to attackers
- **Mitigation**: Could be restricted to admin-only in future
- **Status**: Debug endpoint, assume internal network

### PACK TZ: System Config
- **Risk**: Non-secret config exposed in responses
- **Mitigation**: Never store secrets, use environment variables for those
- **Validation**: Schema enforces non-sensitive values only
- **Status**: Safe for deployment-related, UI URLs, feature constants

### PACK UA: Feature Flags
- **Risk**: Feature toggles exposed could be disabled maliciously
- **Mitigation**: Use immutable=true for critical flags in future
- **Status**: Should probably add RBAC in future (disable only for admins)

### PACK UB: Deployment Profile & Smoke Tests
- **Risk**: Exposes version info and endpoint availability
- **Mitigation**: Version info is already in /docs, this is just convenient
- **Status**: Smoke tests should be run only internally, not exposed publicly

---

## Rollforward Plan

If migration succeeds but there are issues:

1. **Issue**: Endpoints not loading
   - **Fix**: Restart application, verify imports in main.py
   - **Verify**: Check app startup logs for import errors

2. **Issue**: Migrations show as complete but tables don't exist
   - **Fix**: Check Postgres/SQLite for migration history
   - **Verify**: Run `alembic current` to see actual state

3. **Issue**: Feature flags/config endpoints 404
   - **Fix**: Verify routers are imported in main.py
   - **Verify**: Call /debug/routes/ to see if endpoints are registered

4. **Issue**: Smoke tests failing
   - **Fix**: Verify required endpoints exist (/system/health/live, /system/health/ready)
   - **Verify**: Call endpoints manually to confirm they work

---

## Support & Documentation

### For Questions
- Review `PACK_TY_TZ_UA_UB_IMPLEMENTATION.md` for detailed design
- Review `PACK_TY_TZ_UA_UB_QUICK_REFERENCE.md` for API examples
- Check test files for usage patterns

### For Issues
1. Check application logs for errors
2. Verify database migrations: `alembic current`
3. Test endpoints manually with curl
4. Review test files for expected behavior
5. Check GitHub issues or contact team

---

## Version History

- **v1.0.0** (2025-12-06)
  - Initial implementation of PACK TY, TZ, UA, UB
  - Full CRUD for system config
  - Feature flag engine with grouping
  - Route index for endpoint discovery
  - Deployment profile and smoke test runner
