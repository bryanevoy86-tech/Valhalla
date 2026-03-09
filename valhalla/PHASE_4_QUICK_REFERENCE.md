# Phase 4 (PACK UG-UJ) Quick Reference & Examples

## Quick API Examples

### PACK UG: Notification Channel Engine

#### Create a Notification Channel
```bash
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "critical_alerts_email",
    "channel_type": "email",
    "target": "ops-team@example.com",
    "active": true,
    "description": "Email for critical system alerts"
  }'

# Response:
# {
#   "id": 1,
#   "name": "critical_alerts_email",
#   "channel_type": "email",
#   "target": "ops-team@example.com",
#   "active": true,
#   "description": "Email for critical system alerts",
#   "created_at": "2024-01-20T12:00:00",
#   "updated_at": "2024-01-20T12:00:00"
# }
```

#### List All Notification Channels
```bash
curl http://localhost:8000/system/notify/channels

# Response:
# {
#   "total": 2,
#   "items": [
#     {
#       "id": 1,
#       "name": "critical_alerts_email",
#       "channel_type": "email",
#       ...
#     },
#     {
#       "id": 2,
#       "name": "security_webhook",
#       "channel_type": "webhook",
#       ...
#     }
#   ]
# }
```

#### Enqueue a Notification
```bash
curl -X POST http://localhost:8000/system/notify/ \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": 1,
    "subject": "Database Replication Lag Detected",
    "body": "Primary and replica databases are out of sync by 5 seconds",
    "payload": {
      "severity": "warning",
      "component": "database",
      "metric": "replication_lag_ms",
      "value": 5000
    }
  }'

# Response:
# {
#   "id": 1,
#   "created_at": "2024-01-20T12:05:00",
#   "channel_id": 1,
#   "subject": "Database Replication Lag Detected",
#   "body": "Primary and replica databases are out of sync by 5 seconds",
#   "payload": {...},
#   "status": "pending",
#   "last_error": null,
#   "attempts": 0
# }
```

#### List Pending Notifications
```bash
curl "http://localhost:8000/system/notify/?status=pending"

# List failed notifications
curl "http://localhost:8000/system/notify/?status=failed"

# Limit to 50 results
curl "http://localhost:8000/system/notify/?limit=50"
```

---

### PACK UH: Export Job Engine

#### Create an Export Job
```bash
curl -X POST http://localhost:8000/system/exports/ \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "audit_log_export",
    "filter_params": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "severity": "warning"
    },
    "requested_by": "admin@example.com"
  }'

# Response:
# {
#   "id": 1,
#   "created_at": "2024-01-20T12:10:00",
#   "completed_at": null,
#   "job_type": "audit_log_export",
#   "filter_params": {...},
#   "status": "pending",
#   "storage_url": null,
#   "error_message": null,
#   "requested_by": "admin@example.com"
# }
```

#### List All Export Jobs
```bash
curl http://localhost:8000/system/exports/

# Filter by status
curl "http://localhost:8000/system/exports/?status=completed"
curl "http://localhost:8000/system/exports/?status=running"
curl "http://localhost:8000/system/exports/?status=failed"

# Limit results
curl "http://localhost:8000/system/exports/?limit=100"
```

#### Update Export Job Status
```bash
# Mark as running
curl -X POST http://localhost:8000/system/exports/1/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running"
  }'

# Mark as completed with storage URL
curl -X POST http://localhost:8000/system/exports/1/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "storage_url": "s3://data-exports/audit-logs-jan-2024.csv"
  }'

# Mark as failed with error message
curl -X POST http://localhost:8000/system/exports/1/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "failed",
    "error_message": "Database connection timeout after 30 seconds"
  }'
```

---

### PACK UI: Data Retention Policy Registry

#### Set Retention Policy
```bash
# Create new policy
curl -X POST http://localhost:8000/system/retention/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "audit_logs",
    "days_to_keep": 365,
    "enabled": true,
    "description": "Keep audit logs for 1 year (compliance requirement)"
  }'

# Response:
# {
#   "id": 1,
#   "category": "audit_logs",
#   "days_to_keep": 365,
#   "enabled": true,
#   "description": "Keep audit logs for 1 year (compliance requirement)",
#   "created_at": "2024-01-20T12:15:00",
#   "updated_at": "2024-01-20T12:15:00"
# }
```

#### Update Retention Policy
```bash
# Update existing policy (POST is idempotent)
curl -X POST http://localhost:8000/system/retention/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "audit_logs",
    "days_to_keep": 730,
    "enabled": true,
    "description": "Extended to 2 years per new compliance requirement"
  }'

# Disable policy without deleting it
curl -X POST http://localhost:8000/system/retention/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "temp_cache",
    "days_to_keep": 7,
    "enabled": false,
    "description": "Temporarily disabled pending review"
  }'
```

#### List All Retention Policies
```bash
curl http://localhost:8000/system/retention/

# Response:
# {
#   "total": 3,
#   "items": [
#     {
#       "id": 1,
#       "category": "audit_logs",
#       "days_to_keep": 365,
#       "enabled": true,
#       ...
#     },
#     {
#       "id": 2,
#       "category": "error_logs",
#       "days_to_keep": 90,
#       "enabled": true,
#       ...
#     },
#     {
#       "id": 3,
#       "category": "debug_logs",
#       "days_to_keep": 7,
#       "enabled": false,
#       ...
#     }
#   ]
# }
```

#### Get Specific Policy
```bash
curl http://localhost:8000/system/retention/audit_logs

# Response:
# {
#   "id": 1,
#   "category": "audit_logs",
#   "days_to_keep": 365,
#   "enabled": true,
#   "description": "Keep audit logs for 1 year",
#   "created_at": "2024-01-20T12:15:00",
#   "updated_at": "2024-01-20T12:15:00"
# }

# 404 if not found
curl http://localhost:8000/system/retention/nonexistent_category
# Returns 404 Not Found
```

---

### PACK UJ: Read-Only Shield Middleware

#### Test Safe Methods (Always Allowed)
```bash
# GET is always allowed
curl http://localhost:8000/system/notify/channels
# Returns 200

# HEAD is always allowed
curl -I http://localhost:8000/system/notify/channels
# Returns 200

# OPTIONS is always allowed (CORS preflight)
curl -X OPTIONS http://localhost:8000/system/notify/channels
# Returns 200
```

#### Check Maintenance State (Before Toggling)
```bash
# Get current maintenance state via PACK UE
curl http://localhost:8000/system/maintenance/state

# Response (if in normal mode):
# {
#   "mode": "normal",
#   "reason": null,
#   "set_by": null,
#   "set_at": "2024-01-20T10:00:00"
# }
```

#### Test Write Methods in Normal Mode
```bash
# POST works when mode = "normal"
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_channel",
    "channel_type": "email",
    "target": "test@example.com"
  }'
# Returns 200 (success)
```

#### Enter Read-Only Mode (via PACK UE)
```bash
# Set system to read-only mode
curl -X POST http://localhost:8000/system/maintenance/state \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "read_only",
    "reason": "Database maintenance window"
  }'

# Response:
# {
#   "mode": "read_only",
#   "reason": "Database maintenance window",
#   "set_by": "admin@example.com",
#   "set_at": "2024-01-20T12:20:00"
# }
```

#### Test Write Blocking in Read-Only Mode
```bash
# GET still works in read-only mode
curl http://localhost:8000/system/notify/channels
# Returns 200

# But POST is blocked
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "blocked_channel",
    "channel_type": "email",
    "target": "blocked@example.com"
  }'

# Response (503 Service Unavailable):
# {
#   "status_code": 503,
#   "detail": "System is in read-only mode. Write operations are not allowed.",
#   "mode": "read_only"
# }
```

#### Test Other Write Methods Blocking
```bash
# PUT blocked
curl -X PUT http://localhost:8000/system/some/endpoint \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
# Returns 503

# PATCH blocked
curl -X PATCH http://localhost:8000/system/some/endpoint \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
# Returns 503

# DELETE blocked
curl -X DELETE http://localhost:8000/system/some/endpoint
# Returns 503
```

#### Return to Normal Mode
```bash
# Reset to normal mode
curl -X POST http://localhost:8000/system/maintenance/state \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "normal",
    "reason": "Maintenance complete"
  }'

# Now writes work again
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "unblocked_channel",
    "channel_type": "email",
    "target": "unblocked@example.com"
  }'
# Returns 200 (success)
```

---

## Python Client Examples

### Using requests library with PACK UG
```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Create channel
channel_data = {
    "name": "ops_alerts",
    "channel_type": "email",
    "target": "ops@example.com",
}
channel_resp = requests.post(
    f"{BASE_URL}/system/notify/channels",
    json=channel_data
)
channel = channel_resp.json()
print(f"Created channel: {channel['id']}")

# Enqueue notification
notification_data = {
    "channel_id": channel['id'],
    "subject": "System Alert",
    "body": "High CPU usage detected",
    "payload": {"cpu_percent": 95.5}
}
notif_resp = requests.post(
    f"{BASE_URL}/system/notify/",
    json=notification_data
)
print(f"Queued notification: {notif_resp.json()['id']}")

# List pending notifications
list_resp = requests.get(f"{BASE_URL}/system/notify/?status=pending")
pending = list_resp.json()
print(f"Pending notifications: {pending['total']}")
```

### Using requests library with PACK UH
```python
import requests

BASE_URL = "http://localhost:8000"

# Create export job
job_data = {
    "job_type": "audit_export",
    "filter_params": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
    "requested_by": "user@example.com"
}
job_resp = requests.post(f"{BASE_URL}/system/exports/", json=job_data)
job = job_resp.json()
job_id = job['id']
print(f"Created job: {job_id}")

# Poll for completion
import time
while True:
    status_resp = requests.get(f"{BASE_URL}/system/exports/?status=completed")
    completed = status_resp.json()
    
    # Check if our job is there
    for item in completed['items']:
        if item['id'] == job_id:
            print(f"Job completed: {item['storage_url']}")
            exit()
    
    print(f"Job still pending... ({job['status']})")
    time.sleep(5)
```

### Using requests library with PACK UI
```python
import requests

BASE_URL = "http://localhost:8000"

# Set retention policy
policy_data = {
    "category": "event_logs",
    "days_to_keep": 180,
    "enabled": True,
    "description": "Keep event logs for 6 months"
}
policy_resp = requests.post(f"{BASE_URL}/system/retention/", json=policy_data)
policy = policy_resp.json()
print(f"Set policy: {policy['category']} ({policy['days_to_keep']} days)")

# Get policy
get_resp = requests.get(f"{BASE_URL}/system/retention/event_logs")
current_policy = get_resp.json()
print(f"Current policy: {current_policy['days_to_keep']} days")

# Update policy
policy_data['days_to_keep'] = 365  # Extend to 1 year
update_resp = requests.post(f"{BASE_URL}/system/retention/", json=policy_data)
updated = update_resp.json()
print(f"Updated policy: {updated['days_to_keep']} days")
```

### Testing PACK UJ Middleware
```python
import requests

BASE_URL = "http://localhost:8000"

# Check current maintenance state
state_resp = requests.get(f"{BASE_URL}/system/maintenance/state")
state = state_resp.json()
print(f"Current mode: {state['mode']}")

# Set to read-only
maintenance_data = {"mode": "read_only", "reason": "Testing"}
set_resp = requests.post(f"{BASE_URL}/system/maintenance/state", json=maintenance_data)
print(f"Set mode to: {set_resp.json()['mode']}")

# Try read (should work)
read_resp = requests.get(f"{BASE_URL}/system/notify/channels")
print(f"GET allowed: {read_resp.status_code == 200}")

# Try write (should be blocked)
write_data = {"name": "test", "channel_type": "email", "target": "test@test.com"}
write_resp = requests.post(f"{BASE_URL}/system/notify/channels", json=write_data)
print(f"POST blocked: {write_resp.status_code == 503}")

# Reset to normal
normal_data = {"mode": "normal", "reason": "Test complete"}
requests.post(f"{BASE_URL}/system/maintenance/state", json=normal_data)
print("Reset to normal mode")
```

---

## Database Query Examples

### Check Notification Outbox
```sql
-- Count pending notifications
SELECT COUNT(*) as pending_count FROM notification_outbox WHERE status = 'pending';

-- Check failed notifications with error details
SELECT id, created_at, subject, last_error, attempts 
FROM notification_outbox 
WHERE status = 'failed' 
ORDER BY created_at DESC 
LIMIT 10;

-- Get latest notifications for specific channel
SELECT * FROM notification_outbox 
WHERE channel_id = 1 
ORDER BY created_at DESC 
LIMIT 20;
```

### Check Export Jobs
```sql
-- Count jobs by status
SELECT status, COUNT(*) as count 
FROM export_jobs 
GROUP BY status;

-- Find long-running jobs
SELECT id, created_at, job_type, status, DATEDIFF(NOW(), created_at) as hours_elapsed
FROM export_jobs 
WHERE status = 'running' 
AND created_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);

-- Get completed jobs with storage URLs
SELECT id, created_at, completed_at, job_type, storage_url, requested_by
FROM export_jobs 
WHERE status = 'completed' 
ORDER BY completed_at DESC 
LIMIT 20;
```

### Check Retention Policies
```sql
-- List all active policies
SELECT * FROM data_retention_policies 
WHERE enabled = TRUE 
ORDER BY category;

-- Find policies with long retention (> 1 year)
SELECT category, days_to_keep, enabled 
FROM data_retention_policies 
WHERE days_to_keep > 365 
ORDER BY days_to_keep DESC;

-- Get policy change history (via audit trail)
SELECT * FROM system_logs 
WHERE entity = 'data_retention_policies' 
AND action = 'update' 
ORDER BY created_at DESC;
```

---

## Common Workflows

### Workflow 1: System Alert → Notification Delivery
```bash
# 1. Ensure alert channel is configured
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "critical_alerts",
    "channel_type": "email",
    "target": "ops-team@example.com"
  }'

# 2. When alert occurs, enqueue notification
curl -X POST http://localhost:8000/system/notify/ \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": 1,
    "subject": "CRITICAL: CPU at 98%",
    "body": "Server prod-1 CPU usage critical",
    "payload": {"server": "prod-1", "cpu": 98}
  }'

# 3. Background worker processes outbox and sends email
# 4. Notification status updated to "sent" or "failed"
```

### Workflow 2: User Requests Data Export
```bash
# 1. Create export job
curl -X POST http://localhost:8000/system/exports/ \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "user_data_export",
    "filter_params": {"user_id": 12345},
    "requested_by": "user@example.com"
  }'
# Returns job_id = 1

# 2. Background worker processes job
# 3. Worker queries data (respecting retention policy)
# 4. Worker saves to S3 and updates job status
curl -X POST http://localhost:8000/system/exports/1/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "storage_url": "s3://exports/user-12345-2024-01-20.zip"
  }'

# 5. User downloads file from storage_url
```

### Workflow 3: Scheduled Data Purging
```bash
# 1. Admin sets retention policies
curl -X POST http://localhost:8000/system/retention/ \
  -H "Content-Type: application/json" \
  -d '{"category": "temp_logs", "days_to_keep": 7}'

# 2. Cron job runs daily
# SELECT * FROM data_retention_policies WHERE enabled = true

# 3. For each policy, purge old data
# DELETE FROM temp_logs WHERE created_at < (NOW() - INTERVAL 7 DAY)

# 4. Audit log records purge operation
```

### Workflow 4: Maintenance Window
```bash
# 1. Admin enters read-only mode
curl -X POST http://localhost:8000/system/maintenance/state \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "read_only",
    "reason": "Database schema migration"
  }'

# 2. Middleware blocks all writes
# GET requests still work, POST/PUT/PATCH/DELETE return 503

# 3. Database team performs schema migration
# 4. Admin returns to normal mode
curl -X POST http://localhost:8000/system/maintenance/state \
  -H "Content-Type: application/json" \
  -d '{"mode": "normal", "reason": "Migration complete"}'

# 5. System accepts writes again
```

---

## Troubleshooting Common Issues

### Issue: Notifications stuck in "pending"
**Cause:** Background worker not running
**Solution:** 
- Check if worker process is running: `ps aux | grep worker`
- Check logs for worker errors
- Verify database connection string in worker config
- Manually mark as processed for testing: `UPDATE notification_outbox SET status='sent' WHERE id=1`

### Issue: Export job stays "pending"
**Cause:** Worker not processing jobs
**Solution:**
- Verify worker can query database
- Check export_jobs table for disk space issues
- Look at job error_message field for details
- Try creating job with simpler filter_params

### Issue: Retention policy not purging data
**Cause:** Purge job not running
**Solution:**
- Verify cron job is scheduled and running
- Check system_logs for purge operations
- Manually check retention policy: `SELECT * FROM data_retention_policies WHERE category='...`
- Run purge manually in test environment first

### Issue: Write operations blocked unexpectedly
**Cause:** System in maintenance mode
**Solution:**
- Check state: `curl http://localhost:8000/system/maintenance/state`
- If mode != "normal", check reason and expected duration
- Admin can reset: `curl -X POST http://localhost:8000/system/maintenance/state -d '{"mode":"normal"}'`
- For emergencies, update database directly (last resort)

---

## Performance Tips

1. **Batch Notifications**: Queue multiple notifications in one job rather than individual calls
2. **Filter Exports**: Use filter_params to reduce export size and processing time
3. **Archive Old Data**: Use retention policies aggressively (shorter days_to_keep = less data to scan)
4. **Monitor Queue**: Check notification_outbox regularly to catch bottlenecks
5. **Index Optimization**: Ensure status fields are indexed for fast filtering

---

*End of Quick Reference*
