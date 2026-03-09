# PACK TQ, TR, TS, TT Quick Reference

## Overview

Four integrated security orchestration packs providing policy management, action workflows, honeypot telemetry, and unified dashboarding.

## PACK TQ: Security Policy & Blocklist

**Purpose**: Central security policy and entity blocking

**Core Functions**:
```python
# Get/update policy
policy = await get_policy(db)
policy = await update_policy(db, default_mode="elevated", auto_elevate=True)

# Block entities
block = await create_block(db, "ip", "192.168.1.100", "suspicious activity")
blocks = await list_blocks(db, active_only=True)
await deactivate_block(db, block_id)
```

**Endpoints**:
```
GET  /security/policy/              → Current policy
POST /security/policy/              → Update policy
POST /security/policy/blocks        → Create block
GET  /security/policy/blocks        → List blocks
POST /security/policy/blocks/{id}/deactivate → Deactivate block
```

**Model**:
- `SecurityPolicy`: One per deployment (mode, escalation, limits)
- `BlockedEntity`: Many (type, value, expiration, active status)

---

## PACK TR: Security Action Workflow

**Purpose**: Request/approval/execution workflow for security actions

**Core Functions**:
```python
# Create and manage actions
request = await create_action_request(db, "Heimdall", "block_entity", {"entity": "..."})
requests = await list_action_requests(db, status="pending")
approved = await approve_action(db, request_id, "Tyr")
rejected = await reject_action(db, request_id, "Tyr", "Insufficient evidence")
```

**Endpoints**:
```
POST /security/actions/           → Create request
GET  /security/actions/           → List requests (filterable by status)
GET  /security/actions/{id}       → Get specific request
POST /security/actions/{id}       → Update status (approve/reject/execute)
```

**Model**:
- `SecurityActionRequest`: Tracks requested_by, approved_by, status, action_type, payload

**Workflow**:
```
pending → approved → executed
      ↘    rejected
```

---

## PACK TS: Honeypot Registry & Telemetry Bridge

**Purpose**: Honeypot instance management and attack telemetry collection

**Core Functions**:
```python
# Manage honeypot instances
instance = await create_instance(db, "SSH Trap", "ssh", "us-east-1")
# instance.api_key auto-generated (32-char URL-safe token)

honeypot = await get_instance_by_api_key(db, api_key)
instances = await list_instances(db, active_only=True)

# Record events
event = await record_event(db, honeypot_id, "203.0.113.45", "auth_attempt", payload={...})
events = await list_events(db, unprocessed_only=True)
await mark_event_processed(db, event_id)
```

**Endpoints**:
```
POST /security/honeypot/instances                     → Create instance (returns api_key)
GET  /security/honeypot/instances                     → List instances
POST /security/honeypot/events                        → Record event (X-HONEYPOT-KEY header auth)
GET  /security/honeypot/events                        → List events
POST /security/honeypot/instances/{id}/deactivate    → Deactivate instance
```

**Models**:
- `HoneypotInstance`: name, api_key (unique), honeypot_type, location, metadata
- `HoneypotEvent`: source_ip, event_type, payload, detected_threat, processed status

**Authentication**:
- X-HONEYPOT-KEY header required for event submission
- Validates API key against active honeypot instances

**Event Types**: connection, auth_attempt, exploitation, scan

---

## PACK TT: Security Dashboard Aggregator

**Purpose**: Unified security view combining all security subsystems

**Core Function**:
```python
dashboard = await get_security_dashboard(db)
# Returns snapshot with security_mode, incidents, blocklist, honeypot, action_requests
```

**Endpoint**:
```
GET /security/dashboard  → Complete security state (JSON)
```

**Response Structure**:
```json
{
  "timestamp": "2024-01-01T00:00:00",
  "security_mode": {
    "mode": "normal|elevated|lockdown",
    "updated_at": "timestamp"
  },
  "incidents": {
    "total_open": int,
    "critical": int,
    "high": int,
    "medium": int,
    "low": int
  },
  "blocklist": {
    "total_blocked": int,
    "ips": int,
    "users": int,
    "api_keys": int
  },
  "honeypot": {
    "total_instances": int,
    "active_instances": int,
    "recent_events": int,
    "threats_detected": int
  },
  "action_requests": {
    "total_pending": int,
    "pending_by_type": { "action_type": count, ... }
  },
  "last_update": "timestamp"
}
```

---

## Database Tables

| Table | Purpose | Key Columns |
|-------|---------|------------|
| `security_policies` | Policy config | default_mode, auto_elevate, auto_lockdown |
| `blocked_entities` | Entity blocklist | entity_type, value, active, expires_at |
| `security_action_requests` | Action workflow | requested_by, approved_by, action_type, status |
| `honeypot_instances` | Honeypot registry | name, api_key, honeypot_type, active |
| `honeypot_events` | Attack telemetry | honeypot_id, source_ip, event_type, detected_threat |

---

## Usage Examples

### Block a malicious IP
```bash
curl -X POST http://api/security/policy/blocks \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "ip",
    "value": "203.0.113.45",
    "reason": "Brute force attack detected",
    "expires_at": "2024-02-01T00:00:00"
  }'
```

### Create security action request
```bash
curl -X POST http://api/security/actions \
  -H "Content-Type: application/json" \
  -d '{
    "requested_by": "Heimdall",
    "action_type": "set_mode",
    "payload": {"mode": "elevated"}
  }'
```

### Create honeypot instance
```bash
curl -X POST http://api/security/honeypot/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SSH Trap Alpha",
    "honeypot_type": "ssh",
    "location": "us-east-1",
    "metadata": {"version": "1.0", "credentials": "honeypot"}
  }'

# Response includes auto-generated api_key
```

### Submit honeypot event
```bash
curl -X POST http://api/security/honeypot/events \
  -H "Content-Type: application/json" \
  -H "X-HONEYPOT-KEY: <api_key>" \
  -d '{
    "source_ip": "203.0.113.45",
    "event_type": "auth_attempt",
    "payload": {"username": "admin", "password": "test"},
    "detected_threat": "credential_stuffing"
  }'
```

### Check security dashboard
```bash
curl http://api/security/dashboard | jq .
```

---

## Configuration

### Default Security Policy
```python
{
  "default_mode": "normal",
  "auto_elevate": false,
  "auto_lockdown": false,
  "max_failed_auth": 5,
  "max_scan_events": 10,
  "notes": "Default policy"
}
```

Update via:
```bash
curl -X POST http://api/security/policy \
  -H "Content-Type: application/json" \
  -d '{
    "default_mode": "elevated",
    "auto_elevate": true,
    "max_failed_auth": 3
  }'
```

---

## Integration Points

- **PACK TP (Security Monitor)**: Dashboard pulls security_mode and incidents
- **PACK TQ (Policy)**: Dashboard includes blocklist summary
- **PACK TR (Actions)**: Dashboard includes pending action requests
- **PACK TS (Honeypot)**: Dashboard includes honeypot statistics

---

## Testing

Run comprehensive test suite:
```bash
pytest app/tests/test_security_policy.py -v
pytest app/tests/test_security_actions.py -v
pytest app/tests/test_honeypot_bridge.py -v
pytest app/tests/test_security_dashboard.py -v
```

Run all security tests:
```bash
pytest app/tests/test_security_*.py -v
```

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid API key for honeypot)
- `404` - Not found (resource doesn't exist)
- `500` - Server error

---

## Performance Notes

- Blocked entities indexed by type/value/active for fast queries
- Action requests indexed by status/created_at for sorting
- Honeypot events indexed by instance/IP/processed for filtering
- Dashboard aggregation runs in parallel where possible
- All queries support limit/offset for pagination

---

## Key Design Decisions

1. **Tyr Ownership**: PACK TQ policy is Tyr's operational domain
2. **Action Workflow**: All security changes tracked and require approvals
3. **Honeypot Authentication**: X-HONEYPOT-KEY prevents spoofing of decoy data
4. **Cascade Delete**: Honeypot events deleted when instance is removed
5. **JSON Flexibility**: Payload columns support arbitrary action/event details
6. **No Automatic Actions**: Dashboard only shows state; actions manual or via workflow

---

**Status**: Ready for Production
**Last Updated**: 2024
