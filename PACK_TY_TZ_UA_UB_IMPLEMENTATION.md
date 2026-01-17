# PACK TY, TZ, UA, UB Implementation Guide

## Overview

Four powerful system management and visibility packs for Valhalla:

- **PACK TY**: Route Index & Debug Explorer — enumerate all mounted routes
- **PACK TZ**: Config & Environment Registry — safe, non-secret configuration management
- **PACK UA**: Feature Flag Engine — toggle features on/off, run safe experiments
- **PACK UB**: Deployment Profile & Smoke Test Runner — deployment visibility and health validation

---

## PACK TY: Route Index & Debug Explorer

### Purpose
Provides a `/debug/routes/` endpoint that returns a complete inventory of all API routes, methods, tags, and documentation. Allows Heimdall and operators to discover capabilities dynamically.

### Files Created

**1. `app/schemas/route_index.py`** (Routes metadata)
- `RouteInfo`: Single route metadata (path, methods, name, tags, summary, deprecated)
- `RouteIndex`: Complete index (total count + list of routes)

**2. `app/services/route_index.py`** (Index builder)
- `build_route_index(app: FastAPI) → RouteIndex`: Scans app.routes and builds inventory
  - Filters out OPTIONS and HEAD methods (noise)
  - Extracts path, methods, name, tags, summary, deprecation status

**3. `app/routers/route_index.py`** (REST endpoint)
- `GET /debug/routes/` → RouteIndex
  - Returns all mounted routes with metadata
  - Includes route name, HTTP methods, tags for discovery
  - Safe to call (no side effects)

### Use Cases
- **Heimdall Discovery**: Call to see what capabilities are available
- **Deployment Validation**: Confirm expected endpoints are mounted
- **API Documentation**: Generate dynamic documentation from live routes
- **Pack Verification**: Verify all packs are registered correctly

### Example Response
```json
{
  "total": 127,
  "routes": [
    {
      "path": "/debug/routes/",
      "methods": ["GET"],
      "name": "list_routes",
      "tags": ["Debug"],
      "summary": "Returns an index of all API routes.",
      "deprecated": false
    },
    {
      "path": "/system/config/",
      "methods": ["GET", "POST"],
      "name": "list_configs_endpoint",
      "tags": ["System Config"],
      "summary": null,
      "deprecated": false
    }
  ]
}
```

---

## PACK TZ: Config & Environment Registry

### Purpose
Safe, non-secret configuration management. Store and retrieve runtime settings like environment flags, feature toggles, feature URLs, and operational constants without using environment variables.

### Files Created

**1. `app/models/system_config.py`** (Database model)
- `SystemConfig` table: id, key, value, description, mutable, created_at, updated_at
- Unique constraint on key
- Mutable flag prevents accidental overwrites of critical configs

**2. `app/schemas/system_config.py`** (Request/response schemas)
- `SystemConfigSet`: Request payload (key, value, description, mutable)
- `SystemConfigOut`: Full response with id, timestamps
- `SystemConfigList`: Paginated list response

**3. `app/services/system_config.py`** (CRUD operations)
- `set_config(db, payload)`: Create or update config
  - Respects immutability flag (won't update if mutable=False)
- `get_config(db, key)`: Retrieve single config by key
- `list_configs(db)`: List all configs sorted by key

**4. `app/routers/system_config.py`** (REST endpoints)
- `POST /system/config/` → SystemConfigOut: Create/update config
- `GET /system/config/` → SystemConfigList: List all configs
- `GET /system/config/{key}` → SystemConfigOut: Get single config by key

### Use Cases
- **Environment Flags**: Store dev/stage/prod flags without env variables
- **Feature URLs**: Store URLs for external services (WeWeb, dashboards, etc.)
- **Operational Constants**: Store values that need to be changed at runtime
- **Immutable Settings**: Lock critical configs with mutable=False

### Example Usage
```bash
# Set config
POST /system/config/ {
  "key": "weapp_public_url",
  "value": "https://app.example.com",
  "description": "WeWeb frontend URL",
  "mutable": true
}

# Get single config
GET /system/config/weapp_public_url
→ { "key": "weapp_public_url", "value": "https://app.example.com", ... }

# List all
GET /system/config/
→ { "total": 5, "items": [...] }
```

---

## PACK UA: Feature Flag Engine

### Purpose
Toggle features on/off without code deployment. Enables safe experiments, graceful degradation, and emergency lockdown.

### Files Created

**1. `app/models/feature_flags.py`** (Database model)
- `FeatureFlag` table: id, key, enabled, description, group, created_at, updated_at
- Unique constraint on key
- Group field for organizing flags (security, ui, experiments, etc.)

**2. `app/schemas/feature_flags.py`** (Request/response schemas)
- `FeatureFlagSet`: Request payload (key, enabled, description, group)
- `FeatureFlagOut`: Full response with id, timestamps
- `FeatureFlagList`: Paginated list response

**3. `app/services/feature_flags.py`** (Operations)
- `set_feature_flag(db, payload)`: Create or update flag
- `list_feature_flags(db, group)`: List flags, optionally filter by group
- `is_feature_enabled(db, key, default=True)`: Check if flag is enabled
  - Returns default value if flag doesn't exist

**4. `app/routers/feature_flags.py`** (REST endpoints)
- `POST /system/features/` → FeatureFlagOut: Create/update flag
- `GET /system/features/` → FeatureFlagList: List all flags (optional ?group filter)
- `GET /system/features/{key}` → {key, enabled}: Check if flag is enabled

### Use Cases
- **Feature Experiments**: Run A/B tests without deployment
- **Emergency Shutdown**: Disable honeypot, security checks, or expensive operations
- **Graceful Degradation**: Disable non-critical features under load
- **Security Control**: Toggle security features by group
- **Canary Deployments**: Enable new features for subset of users

### Example Usage
```bash
# Create flag
POST /system/features/ {
  "key": "security_honeypot_enabled",
  "enabled": true,
  "description": "Enable honeypot attacks detection",
  "group": "security"
}

# Check if enabled
GET /system/features/security_honeypot_enabled
→ { "key": "security_honeypot_enabled", "enabled": true }

# List by group
GET /system/features/?group=security
→ { "total": 3, "items": [...] }

# Disable during emergency
POST /system/features/ {
  "key": "security_honeypot_enabled",
  "enabled": false
}
```

---

## PACK UB: Deployment Profile & Smoke Test Runner

### Purpose
Provide deployment visibility (environment + version) and quick smoke tests to validate deployment health.

### Files Created

**1. `app/schemas/deployment_profile.py`** (Response schemas)
- `DeploymentProfile`: environment, version, timestamp
- `SmokeTestResult`: Single test result (name, endpoint, ok, status_code, detail)
- `SmokeTestReport`: Full report (timestamp, environment, version, results, all_ok)

**2. `app/services/deployment_profile.py`** (Profile and test operations)
- `get_deployment_profile(db, environment)`: Retrieve deployment info from SystemMetadata
- `run_smoke_tests(base_url, environment, version)`: Async HTTP calls to key endpoints
  - Tests: /system/health/live, /system/health/ready, /system/status/, /security/dashboard/
  - Returns results for each test with status code and error details

**3. `app/routers/deployment_profile.py`** (REST endpoints)
- `GET /system/deploy/profile?environment=dev` → DeploymentProfile: Get deployment info
- `GET /system/deploy/smoke?base_url=...&environment=dev` → SmokeTestReport: Run smoke tests

### Use Cases
- **Deployment Verification**: Confirm backend version and environment after deploy
- **Health Validation**: Quick check that critical endpoints are responding
- **Smoke Testing**: Safe validation without load testing
- **CI/CD Integration**: Automated checks after deployment
- **Monitoring**: Periodic checks to catch availability issues

### Example Usage
```bash
# Get deployment info
GET /system/deploy/profile?environment=prod
→ {
  "environment": "prod",
  "version": "1.2.3",
  "timestamp": "2025-12-06T..."
}

# Run smoke tests
GET /system/deploy/smoke?base_url=https://api.example.com&environment=prod
→ {
  "timestamp": "2025-12-06T...",
  "environment": "prod",
  "version": "1.2.3",
  "results": [
    { "name": "health_live", "endpoint": "/system/health/live", "ok": true, "status_code": 200, "detail": null },
    { "name": "health_ready", "endpoint": "/system/health/ready", "ok": true, "status_code": 200, "detail": null },
    ...
  ],
  "all_ok": true
}
```

---

## Integration with Heimdall

These packs provide Heimdall with critical visibility:

1. **PACK TY**: Heimdall calls `/debug/routes/` to discover capabilities dynamically
2. **PACK TZ**: Heimdall stores non-secret config (WeWeb URL, feature flags state, etc.)
3. **PACK UA**: Heimdall toggles features on/off based on security events or operational needs
4. **PACK UB**: Heimdall verifies deployment health after updates

---

## Database Schema

### system_config (PACK TZ)
```sql
CREATE TABLE system_config (
  id INTEGER PRIMARY KEY,
  key VARCHAR UNIQUE NOT NULL,
  value VARCHAR,
  description TEXT,
  mutable BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_system_config_key ON system_config(key);
```

### feature_flags (PACK UA)
```sql
CREATE TABLE feature_flags (
  id INTEGER PRIMARY KEY,
  key VARCHAR UNIQUE NOT NULL,
  enabled BOOLEAN DEFAULT TRUE,
  description TEXT,
  "group" VARCHAR,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_feature_flags_key ON feature_flags(key);
CREATE INDEX ix_feature_flags_group ON feature_flags("group");
```

---

## Testing

Run all tests:
```bash
pytest app/tests/test_route_index.py
pytest app/tests/test_system_config.py
pytest app/tests/test_feature_flags.py
pytest app/tests/test_deployment_profile.py
```

Or run coverage:
```bash
pytest --cov=app.services.route_index --cov=app.routers.route_index \
       --cov=app.services.system_config --cov=app.routers.system_config \
       --cov=app.services.feature_flags --cov=app.routers.feature_flags \
       --cov=app.services.deployment_profile --cov=app.routers.deployment_profile
```

---

## Deployment Checklist

- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify routes registered: `GET /debug/routes/` (should include new endpoints)
- [ ] Test system config: `POST /system/config/` with test data
- [ ] Test feature flags: `POST /system/features/` with test data
- [ ] Test deployment profile: `GET /system/deploy/profile?environment=prod`
- [ ] Run smoke tests: `GET /system/deploy/smoke?base_url=...&environment=prod`
- [ ] Check all_ok flag in smoke test report
- [ ] Verify Heimdall can call all endpoints
