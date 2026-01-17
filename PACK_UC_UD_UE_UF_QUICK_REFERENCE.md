# PACK UC, UD, UE, UF Quick Reference

## Endpoints Summary

### PACK UC: Rate Limiting & Quota Engine
```
POST /system/ratelimits/rules
  Body: { scope, key, window_seconds?, max_requests?, enabled?, description? }
  Purpose: Create/update rate limit rule

GET /system/ratelimits/rules
  Query: ?scope=optional-scope-name
  Purpose: List rate limit rules

GET /system/ratelimits/rules/{rule_id}
  Purpose: Get single rate limit rule

DELETE /system/ratelimits/rules/{rule_id}
  Purpose: Delete rate limit rule

GET /system/ratelimits/snapshots
  Query: ?scope=ip&limit=200
  Purpose: Get rate limit snapshots (audit log)
```

### PACK UD: API Key & Client Registry
```
POST /system/clients/
  Body: { name, client_type, api_key, description? }
  Purpose: Register new API client

GET /system/clients/
  Purpose: List all registered clients

POST /system/clients/{client_id}/activate
  Purpose: Re-enable a client

POST /system/clients/{client_id}/deactivate
  Purpose: Disable a client (no new requests)
```

### PACK UE: Maintenance Window & Freeze Switch
```
POST /system/maintenance/windows
  Body: { starts_at, ends_at, description?, active? }
  Purpose: Schedule maintenance window

GET /system/maintenance/windows
  Purpose: List all maintenance windows

GET /system/maintenance/state
  Purpose: Get current maintenance mode (normal, maintenance, read_only)

POST /system/maintenance/state/{mode}
  Query: ?reason=optional-reason
  Purpose: Set maintenance mode (normal, maintenance, read_only)
```

### PACK UF: Admin Ops Console
```
POST /admin/ops/
  Body: { action, payload? }
  Purpose: Execute high-level admin action

Supported Actions:
  - get_maintenance_state
  - set_maintenance_mode (payload: { mode, reason? })
  - set_feature_flag (payload: { key, enabled?, description?, group? })
  - deployment_profile (payload: { environment? })
  - security_snapshot (no payload)
```

---

## cURL Examples

### PACK UC: Rate Limits
```bash
# Create rate limit for IP
curl -X POST http://localhost:8000/system/ratelimits/rules \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "ip",
    "key": "192.168.1.100",
    "window_seconds": 60,
    "max_requests": 100,
    "description": "Restrict suspicious IP"
  }'

# List rate limits by scope
curl -X GET "http://localhost:8000/system/ratelimits/rules?scope=user"

# Get snapshots
curl -X GET "http://localhost:8000/system/ratelimits/snapshots?limit=50"

# Delete rate limit
curl -X DELETE http://localhost:8000/system/ratelimits/rules/1
```

### PACK UD: API Clients
```bash
# Register WeWeb client
curl -X POST http://localhost:8000/system/clients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WeWeb Frontend",
    "client_type": "weweb",
    "api_key": "sk_weweb_prod_abc123",
    "description": "Production WeWeb instance"
  }'

# List all clients
curl -X GET http://localhost:8000/system/clients/

# Deactivate client
curl -X POST http://localhost:8000/system/clients/1/deactivate

# Reactivate client
curl -X POST http://localhost:8000/system/clients/1/activate
```

### PACK UE: Maintenance
```bash
# Schedule maintenance window
curl -X POST http://localhost:8000/system/maintenance/windows \
  -H "Content-Type: application/json" \
  -d '{
    "starts_at": "2025-12-07T02:00:00Z",
    "ends_at": "2025-12-07T04:00:00Z",
    "description": "Database migration and backup"
  }'

# Get maintenance state
curl -X GET http://localhost:8000/system/maintenance/state

# Set to maintenance mode
curl -X POST "http://localhost:8000/system/maintenance/state/maintenance?reason=Emergency+patch"

# Return to normal
curl -X POST http://localhost:8000/system/maintenance/state/normal
```

### PACK UF: Admin Ops
```bash
# Get maintenance state via admin console
curl -X POST http://localhost:8000/admin/ops/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_maintenance_state"
  }'

# Set feature flag via admin console
curl -X POST http://localhost:8000/admin/ops/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "set_feature_flag",
    "payload": {
      "key": "new_ui_enabled",
      "enabled": true,
      "group": "ui"
    }
  }'

# Get security snapshot via admin console
curl -X POST http://localhost:8000/admin/ops/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "security_snapshot"
  }'

# Set read-only mode via admin console
curl -X POST http://localhost:8000/admin/ops/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "set_maintenance_mode",
    "payload": {
      "mode": "read_only",
      "reason": "Database under recovery"
    }
  }'
```

---

## Python Examples

### PACK UC: Rate Limits
```python
import requests

# Create rate limit
resp = requests.post("http://localhost:8000/system/ratelimits/rules", json={
    "scope": "api_key",
    "key": "sk_external_partner",
    "window_seconds": 3600,
    "max_requests": 10000,
})
print(resp.json()["id"])

# List rules for specific scope
resp = requests.get("http://localhost:8000/system/ratelimits/rules?scope=ip")
for rule in resp.json()["items"]:
    print(f"{rule['scope']}: {rule['key']} = {rule['max_requests']}/window")
```

### PACK UD: API Clients
```python
import requests

# Register new client
resp = requests.post("http://localhost:8000/system/clients/", json={
    "name": "Heimdall",
    "client_type": "heimdall",
    "api_key": "sk_heimdall_prod_xyz",
})
client_id = resp.json()["id"]

# List clients
resp = requests.get("http://localhost:8000/system/clients/")
for client in resp.json()["items"]:
    status = "active" if client["active"] else "inactive"
    print(f"{client['name']} ({client['client_type']}): {status}")

# Disable a client
requests.post(f"http://localhost:8000/system/clients/{client_id}/deactivate")
```

### PACK UE: Maintenance
```python
import requests
from datetime import datetime, timedelta

# Schedule window
start = datetime.utcnow() + timedelta(days=1)
end = start + timedelta(hours=2)

resp = requests.post("http://localhost:8000/system/maintenance/windows", json={
    "starts_at": start.isoformat() + "Z",
    "ends_at": end.isoformat() + "Z",
    "description": "System upgrade",
})
print(f"Maintenance window scheduled: {resp.json()['id']}")

# Check current state
resp = requests.get("http://localhost:8000/system/maintenance/state")
print(f"Current mode: {resp.json()['mode']}")

# Switch to read-only
resp = requests.post(
    "http://localhost:8000/system/maintenance/state/read_only",
    params={"reason": "Data consistency check"}
)
print(f"Mode: {resp.json()['mode']}")
```

### PACK UF: Admin Ops
```python
import requests

# Admin action: get maintenance state
resp = requests.post("http://localhost:8000/admin/ops/", json={
    "action": "get_maintenance_state"
})
if resp.json()["ok"]:
    print(f"Maintenance mode: {resp.json()['data']['mode']}")

# Admin action: toggle feature flag
resp = requests.post("http://localhost:8000/admin/ops/", json={
    "action": "set_feature_flag",
    "payload": {
        "key": "new_search_enabled",
        "enabled": False,  # Turn off new search
        "group": "ui"
    }
})
print(f"Flag updated: {resp.json()['ok']}")

# Admin action: set read-only during crisis
resp = requests.post("http://localhost:8000/admin/ops/", json={
    "action": "set_maintenance_mode",
    "payload": {
        "mode": "read_only",
        "reason": "Data corruption detected in sector 7"
    }
})
if resp.json()["ok"]:
    print("System switched to read-only mode")
```

---

## Common Patterns

### Crisis Lockdown (All in One)
```bash
# Via Admin Ops Console
curl -X POST http://localhost:8000/admin/ops/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "set_maintenance_mode",
    "payload": {
      "mode": "read_only",
      "reason": "EMERGENCY: Security incident detected"
    }
  }'
```

### Client Rotation
```python
import requests

# Create new client
new_client = requests.post("http://localhost:8000/system/clients/", json={
    "name": "Heimdall v2",
    "client_type": "heimdall",
    "api_key": "sk_heimdall_v2_newkey",
}).json()

# Old clients still work while new one activates
# When ready, deactivate old
old_clients = requests.get("http://localhost:8000/system/clients/").json()["items"]
for client in old_clients:
    if "v1" in client["name"]:
        requests.post(f"http://localhost:8000/system/clients/{client['id']}/deactivate")
```

### Rate Limit Escalation
```python
import requests

# Start conservative, escalate based on abuse
base_limits = [
    {"scope": "ip", "key": "10.0.0.1", "window_seconds": 60, "max_requests": 100},
    {"scope": "ip", "key": "10.0.0.2", "window_seconds": 60, "max_requests": 50},  # Known bad IP
]

for limit in base_limits:
    requests.post("http://localhost:8000/system/ratelimits/rules", json=limit)
```

---

## Troubleshooting

### Rate limit not applied
- Rule might be disabled: check `enabled` field
- Scope/key might not match actual client: verify format
- Rules are for tracking/alerting, actual enforcement needs middleware

### Client deactivated but still connects
- Check if active=false in database
- Verify client code actually validates get_api_client_by_key
- May need restart of auth middleware

### Maintenance mode not blocking requests
- Middleware needs to check maintenance_state and return 503
- Current implementation stores mode, enforcement is external
- Add check in auth or global middleware

### Admin action failed
- Check database is accessible
- Verify all dependent services (dashboard, maintenance) are working
- Review error detail in response

---

## Best Practices

1. **Rate Limiting**
   - Always set scope and key together
   - Use "ip" for external IPs, "user" for authenticated users
   - Set reasonable windows (60-3600 seconds)

2. **API Clients**
   - Rotate keys regularly
   - Deactivate before deleting (gives time to migrate)
   - Use descriptive names and types

3. **Maintenance**
   - Schedule windows in advance, don't surprise users
   - Use read_only for data consistency issues
   - Always provide reason for state changes

4. **Admin Console**
   - Protect with RBAC/MFA in production
   - Log all admin actions via system_log
   - Use for emergency situations only
