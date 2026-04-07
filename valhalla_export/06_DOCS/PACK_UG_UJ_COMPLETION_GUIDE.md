# PACK UG-UJ: Data Operations & Infrastructure Completion Guide

## Overview

This document covers the final 4 infrastructure packs completing the Valhalla ecosystem:

- **PACK UG**: Notification & Alert Channel Engine
- **PACK UH**: Export & Snapshot Job Engine  
- **PACK UI**: Data Retention Policy Registry
- **PACK UJ**: Read-Only Shield Middleware

Together, these packs provide notification delivery, async job management, retention policy configuration, and maintenance-aware write protection.

---

## PACK UG: Notification & Alert Channel Engine

### Purpose
Reliable notification delivery through pluggable channels (email, webhook, SMS) with outbox pattern for guaranteed delivery.

### Architecture

**Models:**
- `notification_channels`: Registry of configured notification channels
  - `id`, `name` (unique), `channel_type` (email/webhook/sms), `target`, `active`, `description`, `created_at`, `updated_at`
- `notification_outbox`: Queue of pending notifications with status tracking
  - `id`, `created_at`, `channel_id`, `subject`, `body`, `payload` (JSON), `status` (pending/sent/failed), `last_error`, `attempts`

**API Endpoints:**
- `POST /system/notify/channels` - Create notification channel
- `GET /system/notify/channels` - List all channels (paginated)
- `POST /system/notify/` - Enqueue notification to outbox
- `GET /system/notify/` - List notifications (filterable by status)

### Key Patterns

**Outbox Pattern:**
- All notifications are written to outbox table with status=pending
- A background worker processes the outbox table and sends actual notifications
- Worker marks entries as sent/failed, retries on failure
- Ensures no notification is lost even if worker crashes mid-delivery

**Payload Flexibility:**
- JSON payload column allows flexible structured data for each notification
- Useful for including context (user_id, resource_id, metadata)

### Example Usage

```bash
# Create a channel
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "owner_email",
    "channel_type": "email",
    "target": "owner@example.com",
    "description": "Email for owner alerts"
  }'

# Enqueue a notification
curl -X POST http://localhost:8000/system/notify/ \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": 1,
    "subject": "Alert",
    "body": "System updated",
    "payload": {"resource": "config", "action": "update"}
  }'

# List pending notifications
curl http://localhost:8000/system/notify/?status=pending
```

### Testing
Run: `pytest services/api/app/tests/test_notification_channel.py -v`

Test coverage:
- Channel creation and listing
- Notification enqueueing with status tracking
- Notification filtering by status
- Payload handling for structured data

---

## PACK UH: Export & Snapshot Job Engine

### Purpose
Async job management for long-running export operations (audit logs, data snapshots, reports).

### Architecture

**Models:**
- `export_jobs`: Job registry with tracking
  - `id`, `created_at`, `completed_at`, `job_type`, `filter_params` (JSON), `status` (pending/running/completed/failed), `storage_url`, `error_message`, `requested_by`

**API Endpoints:**
- `POST /system/exports/` - Create export job
- `GET /system/exports/` - List jobs (filterable by status)
- `POST /system/exports/{id}/status` - Update job status and completion info

### Key Patterns

**Async Job Pattern:**
- Job created with status=pending (returns immediately)
- Client polls GET endpoint to check status
- Worker processes pending jobs, sets status to running, then completed/failed
- Completed jobs have storage_url pointing to result location (S3, etc.)

**Filter Parameters:**
- JSON column stores flexible filter params for each job type
- Example: audit log export with start_date, end_date filters
- Allows different job types to carry different parameters

### Example Usage

```bash
# Create an export job
curl -X POST http://localhost:8000/system/exports/ \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "audit_log_export",
    "filter_params": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
    "requested_by": "admin@example.com"
  }'

# Check job status
curl http://localhost:8000/system/exports/?status=running

# Mark job as completed
curl -X POST http://localhost:8000/system/exports/1/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "storage_url": "s3://bucket/exports/job-123.csv"
  }'
```

### Testing
Run: `pytest services/api/app/tests/test_export_job.py -v`

Test coverage:
- Job creation with and without filter parameters
- Job listing and status filtering
- Job status updates with completion info
- Error handling

---

## PACK UI: Data Retention Policy Registry

### Purpose
Configuration-driven data retention rules for automated purging of old records.

### Architecture

**Models:**
- `data_retention_policies`: Retention rules per data category
  - `id`, `category` (unique), `days_to_keep`, `enabled`, `description`, `created_at`, `updated_at`

**API Endpoints:**
- `POST /system/retention/` - Create/update retention policy
- `GET /system/retention/` - List all policies (paginated)
- `GET /system/retention/{category}` - Get specific policy by category

### Key Patterns

**Configuration Registry:**
- Single row per category (audit_logs, events, temp_data, etc.)
- Enabled flag allows policies to be toggled without deletion
- Updated via POST (idempotent, create-or-update)

**Worker Integration:**
- Policies are read by background worker/cron job
- Worker purges records older than days_to_keep
- Allows easy policy management without code changes

### Example Usage

```bash
# Set retention policy
curl -X POST http://localhost:8000/system/retention/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "audit_logs",
    "days_to_keep": 365,
    "description": "Keep audit logs for 1 year"
  }'

# List all policies
curl http://localhost:8000/system/retention/

# Get specific policy
curl http://localhost:8000/system/retention/audit_logs

# Update policy
curl -X POST http://localhost:8000/system/retention/ \
  -H "Content-Type: application/json" \
  -d '{
    "category": "audit_logs",
    "days_to_keep": 730,
    "description": "Extended to 2 years"
  }'
```

### Testing
Run: `pytest services/api/app/tests/test_data_retention.py -v`

Test coverage:
- Policy creation and updates (idempotent)
- Listing and retrieval by category
- Enabled/disabled flag handling
- Unique category constraint

---

## PACK UJ: Read-Only Shield Middleware

### Purpose
Blocks write operations (POST/PUT/PATCH/DELETE) when system is in read-only or maintenance mode.

### Architecture

**Middleware Logic:**
- Checks `MaintenanceState.mode` in database
- Allows safe methods (GET, HEAD, OPTIONS) always
- Blocks write methods (POST, PUT, PATCH, DELETE) if mode != "normal"
- Returns 503 Service Unavailable with JSON response
- Fails open (returns error) if database unreachable

**Middleware Stack Position:**
- Must be added EARLY in FastAPI middleware stack
- Added after CorrelationId and Error handlers
- This ensures read-only check happens before request processing

### Key Patterns

**Safe Methods Always Allowed:**
- GET: Safe to execute in read-only
- HEAD: Safe to execute
- OPTIONS: Safe (CORS preflight)

**Write Methods Blocked:**
- POST: Blocked in non-normal mode
- PUT: Blocked in non-normal mode
- PATCH: Blocked in non-normal mode
- DELETE: Blocked in non-normal mode

**Maintenance States:**
- `normal`: All operations allowed
- `read_only`: Write operations blocked, but reads allowed
- `maintenance`: All write operations blocked (stronger message)

### Example Response

When write is blocked:
```json
{
  "status_code": 503,
  "detail": "System is in read-only mode. Write operations are not allowed.",
  "mode": "read_only"
}
```

### Configuration

The middleware checks `MaintenanceState` table (PACK UE). Update mode via:

```bash
# Via PACK UE Maintenance Router
curl -X POST http://localhost:8000/system/maintenance/state \
  -H "Content-Type: application/json" \
  -d '{"mode": "read_only", "reason": "Scheduled maintenance"}'
```

### Testing
Run: `pytest services/api/app/tests/test_read_only_middleware.py -v`

Test coverage:
- Safe methods (GET, HEAD, OPTIONS) always allowed
- Write methods (POST, PUT, PATCH, DELETE) blocked in non-normal mode
- Mode checking and state transitions
- Error handling for database unavailability

---

## Integration: How These Packs Work Together

### Notification + Export
```
User requests data export (PACK UH)
  → Creates export_job with status=pending
  → System sends notification via PACK UG
  → Worker processes job, updates status
  → Sends completion notification
```

### Export + Retention
```
Export job (PACK UH) includes retention policy (PACK UI)
  → Job has filter_params: {"before_date": "2024-01-01"}
  → Worker exports data matching retention rules
  → After export, retention policy purges old records
```

### Read-Only Mode + All Packs
```
Admin enters maintenance mode (PACK UE + UJ)
  → PACK UJ middleware blocks all writes
  → Reads still work (monitoring dashboards stay live)
  → Notifications still queue (PACK UG)
  → Export jobs can still be read (PACK UH)
  → Only writes blocked
```

---

## Database Schema Summary

### notification_channels
```sql
id INT PRIMARY KEY
created_at DATETIME (indexed)
updated_at DATETIME
name VARCHAR(256) UNIQUE
channel_type VARCHAR(64)
target VARCHAR(512)
active BOOLEAN
description TEXT
```

### notification_outbox
```sql
id INT PRIMARY KEY
created_at DATETIME (indexed)
channel_id INT FK
subject VARCHAR(512)
body TEXT
payload JSON
status VARCHAR(32) (indexed)
last_error TEXT
attempts INT
```

### export_jobs
```sql
id INT PRIMARY KEY
created_at DATETIME (indexed)
completed_at DATETIME
job_type VARCHAR(128)
filter_params JSON
status VARCHAR(32) (indexed)
storage_url VARCHAR(512)
error_message TEXT
requested_by VARCHAR(256)
```

### data_retention_policies
```sql
id INT PRIMARY KEY
created_at DATETIME
updated_at DATETIME
category VARCHAR(128) UNIQUE (indexed)
days_to_keep INT
enabled BOOLEAN
description TEXT
```

---

## Deployment & Testing Checklist

### Pre-Deployment
- [ ] Run all migration scripts (0075-0077)
- [ ] Run test suites for UG-UJ (27 total tests)
- [ ] Verify database schema changes
- [ ] Test middleware with maintenance mode toggle
- [ ] Verify router registration in main.py

### Post-Deployment
- [ ] Create at least one notification channel
- [ ] Test notification enqueueing
- [ ] Create and process an export job
- [ ] Configure retention policies
- [ ] Toggle maintenance mode and verify write blocking
- [ ] Monitor logs for middleware registration

### Health Checks
```bash
# Verify routers are registered
curl http://localhost:8000/system/notify/channels
curl http://localhost:8000/system/exports/
curl http://localhost:8000/system/retention/

# Verify middleware is active
# Toggle maintenance mode and try a POST request
curl -X POST http://localhost:8000/system/notify/channels \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "channel_type": "email", "target": "test@test.com"}'
# Should succeed in normal mode, fail (503) in read_only/maintenance mode
```

---

## Troubleshooting

### Middleware not blocking writes
- Verify `ReadOnlyShieldMiddleware` is imported and added in main.py
- Check that MaintenanceState table exists and has a row
- Verify middleware stack order (should be early)

### Notifications not delivering
- Check notification_outbox table for pending notifications
- Verify a background worker is running to process outbox
- Check notification_channels table for active channels
- Look at last_error field for details

### Export jobs stuck in pending
- Verify export_jobs table and status is actually "pending"
- Check for background worker processing jobs
- Look at error_message field if job failed
- Verify storage_url is accessible before marking completed

### Retention policies not purging
- Verify data_retention_policies has correct days_to_keep
- Check that enabled=true for the category
- Verify background cron job is running
- Confirm old records are actually older than days_to_keep

---

## Phase 4 Completion Summary

**Files Created:**
- 4 core files (UG, UH, UI models)
- 4 schema files (UG, UH, UI schemas)
- 4 service files (UG, UH, UI services)
- 4 router files (UG, UH, UI routers)
- 1 middleware file (UJ middleware)
- 4 test files (UG-UJ test suites)
- 3 migration files (0075-0077)
- 1 documentation file (this file)

**Total Lines of Code:**
- Production code: ~552 lines
- Test code: ~200 lines
- Migrations: ~100 lines

**Database Tables:**
- notification_channels
- notification_outbox
- export_jobs
- data_retention_policies

**Test Coverage:**
- 27 total test cases across 4 packs
- All CRUD operations tested
- Integration patterns tested

**Endpoints:**
- 4 notification endpoints (channels, outbox)
- 3 export endpoints (jobs, status)
- 3 retention endpoints (policy management)
- All routers registered in main.py

---

## Next Steps (Phase 5 - Future)

If continuing beyond Phase 4, consider:

1. **Worker Framework** - Background job processors for notifications and exports
2. **Event Bus** - Pub/sub system for triggering notifications from domain events
3. **Audit Logging** - Capture who requested exports, who changed retention policies
4. **Rate Limiting Integration** - Apply rate limits to notification and export endpoints
5. **Analytics** - Track notification delivery success rates, export job performance

For now, Phase 4 completes the infrastructure layers. All 12 packs (TQ-UJ) are implemented.

---

## Questions?

For technical details on implementation:
- See docstrings in routers (app/routers/*.py)
- Check service implementations for business logic
- Review test files for usage examples
- Consult alembic migrations for schema details

All packs follow consistent patterns for easy maintenance and extension.
