# PACK TY, TZ, UA, UB Quick Reference

## Endpoints Summary

### PACK TY: Route Index & Debug Explorer
```
GET /debug/routes/
  Returns: RouteIndex with all mounted routes
  Purpose: Discover capabilities, verify pack registration
  No auth required (debug endpoint)
```

### PACK TZ: Config & Environment Registry
```
POST /system/config/
  Body: { key, value, description?, mutable? }
  Returns: SystemConfigOut
  Purpose: Create/update configuration

GET /system/config/
  Returns: SystemConfigList
  Purpose: List all configurations

GET /system/config/{key}
  Returns: SystemConfigOut
  Purpose: Get single configuration by key
  Error: 404 if key not found
```

### PACK UA: Feature Flag Engine
```
POST /system/features/
  Body: { key, enabled?, description?, group? }
  Returns: FeatureFlagOut
  Purpose: Create/update feature flag

GET /system/features/
  Query: ?group=optional-group-name
  Returns: FeatureFlagList
  Purpose: List all feature flags, optionally by group

GET /system/features/{key}
  Returns: { key, enabled }
  Purpose: Check if flag is enabled
  Default: Returns enabled=true if flag doesn't exist
```

### PACK UB: Deployment Profile & Smoke Test Runner
```
GET /system/deploy/profile
  Query: ?environment=dev|stage|prod
  Returns: DeploymentProfile { environment, version, timestamp }
  Purpose: Get current deployment info

GET /system/deploy/smoke
  Query: ?base_url=https://api.example.com&environment=dev
  Returns: SmokeTestReport { timestamp, environment, version, results[], all_ok }
  Purpose: Run smoke tests against key endpoints
```

---

## cURL Examples

### PACK TY: Route Index
```bash
# Get all routes
curl -X GET http://localhost:8000/debug/routes/

# Pretty print
curl -X GET http://localhost:8000/debug/routes/ | jq .
```

### PACK TZ: System Config
```bash
# Create config
curl -X POST http://localhost:8000/system/config/ \
  -H "Content-Type: application/json" \
  -d '{
    "key": "app_name",
    "value": "MyApp",
    "description": "Application name",
    "mutable": true
  }'

# Get single config
curl -X GET http://localhost:8000/system/config/app_name

# List all configs
curl -X GET http://localhost:8000/system/config/

# Create immutable config
curl -X POST http://localhost:8000/system/config/ \
  -H "Content-Type: application/json" \
  -d '{
    "key": "db_version",
    "value": "1.0.0",
    "mutable": false
  }'
```

### PACK UA: Feature Flags
```bash
# Create flag
curl -X POST http://localhost:8000/system/features/ \
  -H "Content-Type: application/json" \
  -d '{
    "key": "honeypot_enabled",
    "enabled": true,
    "description": "Enable honeypot detection",
    "group": "security"
  }'

# Check if enabled
curl -X GET http://localhost:8000/system/features/honeypot_enabled

# List all flags
curl -X GET http://localhost:8000/system/features/

# List by group
curl -X GET http://localhost:8000/system/features/?group=security

# Toggle flag
curl -X POST http://localhost:8000/system/features/ \
  -H "Content-Type: application/json" \
  -d '{
    "key": "honeypot_enabled",
    "enabled": false
  }'
```

### PACK UB: Deployment Profile & Smoke Tests
```bash
# Get deployment info
curl -X GET http://localhost:8000/system/deploy/profile?environment=dev

# Get prod deployment info
curl -X GET http://localhost:8000/system/deploy/profile?environment=prod

# Run smoke tests locally
curl -X GET "http://localhost:8000/system/deploy/smoke?base_url=http://localhost:8000&environment=dev"

# Run smoke tests against remote deployment
curl -X GET "http://localhost:8000/system/deploy/smoke?base_url=https://api.example.com&environment=prod"
```

---

## Python Examples

### PACK TY: Route Index
```python
import requests

resp = requests.get("http://localhost:8000/debug/routes/")
routes = resp.json()
print(f"Total routes: {routes['total']}")
for route in routes['routes']:
    print(f"  {route['path']} {route['methods']}")
```

### PACK TZ: System Config
```python
import requests

# Set config
resp = requests.post("http://localhost:8000/system/config/", json={
    "key": "max_retries",
    "value": "3",
    "description": "Max retries for API calls"
})
print(resp.json())

# Get config
resp = requests.get("http://localhost:8000/system/config/max_retries")
print(resp.json()["value"])

# List all
resp = requests.get("http://localhost:8000/system/config/")
for config in resp.json()["items"]:
    print(f"{config['key']} = {config['value']}")
```

### PACK UA: Feature Flags
```python
import requests

# Create flag
resp = requests.post("http://localhost:8000/system/features/", json={
    "key": "beta_features",
    "enabled": True,
    "group": "experiments"
})

# Check flag
resp = requests.get("http://localhost:8000/system/features/beta_features")
enabled = resp.json()["enabled"]
if enabled:
    print("Beta features are ON")
else:
    print("Beta features are OFF")

# List security flags
resp = requests.get("http://localhost:8000/system/features/?group=security")
for flag in resp.json()["items"]:
    status = "ON" if flag["enabled"] else "OFF"
    print(f"{flag['key']}: {status}")
```

### PACK UB: Deployment Profile & Smoke Tests
```python
import requests
import asyncio

# Get deployment info
resp = requests.get("http://localhost:8000/system/deploy/profile?environment=prod")
profile = resp.json()
print(f"Deployment: {profile['environment']}")
print(f"Version: {profile['version']}")
print(f"Timestamp: {profile['timestamp']}")

# Run smoke tests
resp = requests.get(
    "http://localhost:8000/system/deploy/smoke",
    params={
        "base_url": "https://api.example.com",
        "environment": "prod"
    }
)
report = resp.json()
if report["all_ok"]:
    print("✓ All smoke tests passed!")
else:
    print("✗ Some smoke tests failed:")
    for result in report["results"]:
        if not result["ok"]:
            print(f"  {result['name']}: {result['detail']}")
```

---

## Common Patterns

### Using Feature Flags in Routes
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.feature_flags import is_feature_enabled

router = APIRouter()

@router.get("/api/expensive-operation/")
def expensive_operation(db: Session = Depends(get_db)):
    if not is_feature_enabled(db, "expensive_feature"):
        return {"error": "Feature disabled"}
    # ... expensive operation
    return {"result": "..."}
```

### Using Config in Initialization
```python
from sqlalchemy.orm import Session
from app.services.system_config import get_config

def setup_service(db: Session):
    api_url = get_config(db, "external_api_url")
    if not api_url:
        raise ValueError("external_api_url not configured")
    return ApiClient(api_url.value)
```

### Smoke Test Integration in CI/CD
```bash
#!/bin/bash
set -e

# Deploy to staging
./deploy.sh staging

# Wait for service to be ready
sleep 10

# Run smoke tests
REPORT=$(curl -s "http://staging.example.com/system/deploy/smoke?base_url=http://staging.example.com&environment=stage")

if echo "$REPORT" | jq -e '.all_ok' > /dev/null; then
    echo "✓ Smoke tests passed"
    exit 0
else
    echo "✗ Smoke tests failed"
    echo "$REPORT" | jq .
    exit 1
fi
```

---

## Troubleshooting

### 404 on route endpoints
- Check that migrations have run: `alembic upgrade head`
- Verify routers are imported in main.py
- Restart the FastAPI application

### Config key not found
- GET /system/config/ to verify key exists
- Check for typos in key name (case-sensitive)

### Feature flag not working
- Check that feature_flags table was created: `alembic upgrade head`
- Verify flag was set: GET /system/features/{key}
- Default behavior: if flag doesn't exist, is_feature_enabled returns default=True

### Smoke test failures
- Verify base_url is correct and accessible
- Check that required endpoints exist: /system/health/live, /system/health/ready
- Review detail field for specific error messages
