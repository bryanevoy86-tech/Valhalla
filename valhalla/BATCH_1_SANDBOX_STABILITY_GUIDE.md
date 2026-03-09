# Batch 1: Sandbox + Stability Implementation Guide

## Overview
Batch 1 implements 10 activation blocks for sandbox environment setup and stability mechanisms. These components work together to provide a safe, isolated testing environment with comprehensive monitoring and safety features.

---

## Quick Start

### Basic Initialization
```python
from services.sandbox import SandboxOrchestrator

# Create sandbox
sandbox = SandboxOrchestrator(use_memory_db=True)
sandbox.initialize()

# Run readiness checks
if sandbox.is_ready():
    print("Sandbox is GO!")

# Get status
status = sandbox.get_status()

# Cleanup
sandbox.cleanup()
```

---

## Component Breakdown

### 1. Sandbox Service + DB Wiring

**Purpose:** Provide isolated database for testing without affecting production data.

**Key Features:**
- Configurable database URL (PostgreSQL or SQLite)
- In-memory mode for fast testing
- Session management
- Automatic cleanup

**Usage:**
```python
from services.sandbox import SandboxDatabaseManager

# Use PostgreSQL sandbox
db = SandboxDatabaseManager(
    db_url="postgresql://user:password@localhost/sandbox_db"
)

# Or use in-memory for tests
db = SandboxDatabaseManager(use_memory=True)

# Get session
session = db.get_session()
# ... perform operations ...

# Cleanup
db.cleanup()
```

**Configuration:**
- PostgreSQL URL: `postgresql://user:password@host/sandbox_db`
- SQLite in-memory: Automatic when `use_memory=True`

**Integration Points:**
- Used by `SandboxOrchestrator.db_manager`
- Provides isolated testing without production impact

---

### 2. Sandbox Dry-Run Locks on Irreversible Actions

**Purpose:** Prevent accidental execution of non-recoverable operations in sandbox.

**Key Features:**
- Automatic detection of irreversible actions
- Dry-run mode simulation
- Strict mode option (raises exceptions)
- Execution logging

**Irreversible Actions Tracked:**
- `payment`, `transfer`, `delete_permanent`
- `external_call`, `financial_commit`
- `data_export_external`, `user_deletion`
- `bulk_update_production`

**Usage:**
```python
from services.sandbox import DryRunLock

dry_run = DryRunLock(dry_run=True, strict_mode=False)

def make_payment(amount):
    return {"status": "paid", "amount": amount}

# In dry-run mode, this is blocked:
result = dry_run.execute('payment', make_payment, 150.00)
# Output: {'dry_run': True, 'action': 'payment', 'result': None}

# View log
log = dry_run.get_execution_log()
```

**Configuration:**
- `dry_run=True`: Blocks irreversible actions
- `dry_run=False`: Allows execution (production mode)
- `strict_mode=True`: Raises exceptions instead of silently blocking

---

### 3. Worker Process Enabled

**Purpose:** Handle background tasks without blocking main application.

**Key Features:**
- Configurable worker threads
- Job queue management
- Completion tracking
- Error handling per job

**Usage:**
```python
from services.sandbox import WorkerProcess

worker = WorkerProcess(poll_interval=5.0, max_workers=2)
worker.start()

def long_task():
    return "task result"

# Submit job
job_id = worker.submit_job('my_task', long_task)

# Check status
status = worker.get_job_status(job_id)

worker.stop()
```

**Features:**
- **Job Queue:** Automatic FIFO processing
- **Multiple Workers:** Process jobs concurrently
- **Polling Interval:** Adjustable check frequency
- **Completion Log:** Track all job results

---

### 4. Scheduler Heartbeat

**Purpose:** Monitor system health and detect failures.

**Key Features:**
- Periodic health pulses
- Configurable timeout detection
- Health status tracking
- Unhealthy state detection

**Usage:**
```python
from services.sandbox import SchedulerHeartbeat

heartbeat = SchedulerHeartbeat(interval=10.0, timeout=30.0)
heartbeat.start()

# Check if healthy
if heartbeat.is_healthy():
    print("System is healthy")

# Get status
status = heartbeat.get_health_status()
# {
#   'is_running': True,
#   'is_healthy': True,
#   'last_heartbeat': '2026-01-07T...',
#   'seconds_since_heartbeat': 2.3,
#   'total_checks': 42
# }

heartbeat.stop()
```

**Configuration:**
- `interval`: Seconds between heartbeats (default: 10)
- `timeout`: Seconds before marking unhealthy (default: 30)

---

### 5. Retry / Backoff Rules

**Purpose:** Automatically retry failed operations with exponential backoff.

**Key Features:**
- Exponential backoff strategy
- Configurable retry limits
- Optional jitter to prevent thundering herd
- Retry logging

**Usage:**
```python
from services.sandbox import RetryBackoffManager

retry = RetryBackoffManager(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0
)

def unstable_api_call():
    if random.random() < 0.7:
        raise ConnectionError("Network error")
    return "success"

result = retry.execute_with_retry(
    unstable_api_call,
    'api_call',
    backoff_multiplier=2.0,
    jitter=True
)

# View retry log
log = retry.get_retry_log('api_call')
```

**Backoff Formula:**
```
delay = min(
    base_delay * (multiplier ^ attempt),
    max_delay
)
if jitter:
    delay *= (0.5 + random.random())
```

---

### 6. Idempotency / Deduplication (Base)

**Purpose:** Ensure operations are not duplicated if retried.

**Key Features:**
- Key-based deduplication
- TTL-based cache expiration
- Duplicate detection
- Automatic cache cleanup

**Usage:**
```python
from services.sandbox import IdempotencyManager

idempotency = IdempotencyManager(ttl_seconds=3600)

def expensive_operation(user_id):
    return {"processed": True, "user": user_id}

# First call: executes
result1 = idempotency.process_idempotent(
    'payment-user-123',
    expensive_operation,
    'user-123'
)

# Second call with same key: returns cached result
result2 = idempotency.process_idempotent(
    'payment-user-123',
    expensive_operation,
    'user-123'
)

# Check if duplicate
if idempotency.is_duplicate('payment-user-123'):
    cached = idempotency.get_cached_result('payment-user-123')
    print(f"Using cached result: {cached}")

# Clear expired entries
idempotency.clear_expired()
```

**TTL Management:**
- Default TTL: 3600 seconds (1 hour)
- Expired entries automatically ignored
- Manual cleanup via `clear_expired()`

---

### 7. Governor Enforcement Everywhere

**Purpose:** Enforce rate limits and prevent resource exhaustion.

**Key Features:**
- Per-resource rate limiting
- Time-window based quotas
- Violation tracking
- Status reporting

**Usage:**
```python
from services.sandbox import GovernorEnforcer

governor = GovernorEnforcer()

# Set limits
governor.set_limit('payment', max_actions=100, window_seconds=3600)
governor.set_limit('api_call', max_actions=1000, window_seconds=60)

# Check before action
allowed, message = governor.check_limit('payment')
if allowed:
    # Process payment
    pass
else:
    # Rate limit exceeded
    print(f"Error: {message}")

# Get status
status = governor.get_status('payment')
# {
#   'resource': 'payment',
#   'current_actions': 45,
#   'max_actions': 100,
#   'window_seconds': 3600,
#   'denied_count': 2
# }
```

**Features:**
- **Automatic Window Reset:** Old actions removed from count
- **Per-Resource Tracking:** Independent quotas
- **Denial Logging:** Track rejected attempts

---

### 8. Alerts on Failure / Denial

**Purpose:** Centralized notification system for failures and policy violations.

**Key Features:**
- Severity levels (info, warning, error, critical)
- Subscriber pattern for notifications
- Context data capture
- Structured alert format

**Usage:**
```python
from services.sandbox import AlertSystem

alerts = AlertSystem()

# Subscribe to alerts
def handle_payment_alerts(alert):
    print(f"Payment alert: {alert['reason']}")

alerts.subscribe('payment', handle_payment_alerts)

# Trigger alerts
alerts.alert(
    'payment',
    'Insufficient funds',
    severity='warning',
    context={'amount': 500, 'available': 300}
)

# Query alerts
recent_errors = alerts.get_alerts(severity='error', limit=10)
payment_alerts = alerts.get_alerts(task_name='payment')
```

**Severity Levels:**
- `info` (0): Informational messages
- `warning` (1): Warning conditions
- `error` (2): Error conditions
- `critical` (3): Critical failures

**Subscribers:**
- Task-specific: Triggered for specific task failures
- Allow custom handling via callbacks

---

### 9. Structured Logging + Correlation IDs

**Purpose:** Track requests across distributed components for debugging.

**Key Features:**
- Automatic correlation ID generation
- Structured log format
- Context tracking
- Request-level logging

**Usage:**
```python
from services.sandbox import StructuredLogger

logger = StructuredLogger()

# Start request
correlation_id = logger.log_request(
    endpoint='/api/checkout',
    method='POST',
    user_id='user-123'
)

# Log related actions
logger.log_action(
    'payment_validation',
    level='info',
    amount=250,
    method='credit_card'
)

logger.log_action(
    'payment_approved',
    level='info',
    transaction_id='txn-789'
)

# Manually set correlation ID
logger.set_correlation_id('custom-id-456')

# Get current ID
current_id = logger.get_correlation_id()
```

**Format:**
```
[correlation-id] action_name - {timestamp, action, correlation_id, ...fields}
```

**Benefits:**
- Trace requests through entire system
- Identify related log entries
- Debug distributed issues

---

### 10. Sandbox GO Readiness Checks

**Purpose:** Verify sandbox is ready for operations before startup.

**Key Features:**
- Pluggable readiness checks
- Health status reporting
- Pass/fail validation
- GO/NO-GO determination

**Usage:**
```python
from services.sandbox import SandboxReadinessChecker

checker = SandboxReadinessChecker()

# Register checks
checker.register_check(
    'database_connected',
    lambda: db.engine is not None
)

checker.register_check(
    'worker_running',
    lambda: worker.is_running
)

checker.register_check(
    'external_api_responsive',
    lambda: external_api.ping()
)

# Run checks
results = checker.run_all_checks()
# {'database_connected': True, 'worker_running': True, ...}

# Check readiness
if checker.is_ready():
    print("GO: All systems ready")
else:
    print("NO-GO: Some systems failed")

# Get detailed status
status = checker.get_status()
# {
#   'is_ready': True,
#   'total_checks': 4,
#   'passed_checks': 4,
#   'failed_checks': 0,
#   'checks': {...}
# }
```

**Built-in Checks:**
- Database connectivity
- Worker process running
- Scheduler heartbeat active
- Governor configured

---

## Integration Patterns

### Pattern 1: Safe Payment Processing
```python
# Get permission from governor
allowed, _ = sandbox.governor.check_limit('payment')
if not allowed:
    sandbox.alert_system.alert('payment', 'Rate limit exceeded')
    return

# Ensure idempotency
result = sandbox.idempotency_manager.process_idempotent(
    f"payment-{user_id}",
    process_payment,
    user_id,
    amount
)

# Execute with dry-run protection
result = sandbox.dry_run_lock.execute(
    'payment',
    lambda: record_payment(result)
)
```

### Pattern 2: Background Job Processing
```python
# Submit job to worker
job_id = sandbox.worker.submit_job(
    'email_notification',
    send_email,
    user_email
)

# Monitor completion
import time
while True:
    status = sandbox.worker.get_job_status(job_id)
    if status and status['status'] != 'pending':
        break
    time.sleep(1)
```

### Pattern 3: Resilient API Calls
```python
try:
    result = sandbox.retry_manager.execute_with_retry(
        external_api_call,
        'external_api',
        max_retries=3,
        backoff_multiplier=2.0,
        jitter=True
    )
except Exception as e:
    sandbox.alert_system.alert(
        'external_api',
        f'Failed after retries: {e}',
        severity='error'
    )
```

---

## Configuration Reference

### Environment Variables
```bash
# Database
SANDBOX_DB_URL=postgresql://user:password@localhost/sandbox_db
SANDBOX_USE_MEMORY_DB=false

# Worker
SANDBOX_WORKER_INTERVAL=5.0
SANDBOX_MAX_WORKERS=2

# Heartbeat
SANDBOX_HEARTBEAT_INTERVAL=10.0
SANDBOX_HEARTBEAT_TIMEOUT=30.0

# Governor defaults
SANDBOX_PAYMENT_LIMIT=100
SANDBOX_PAYMENT_WINDOW=3600
SANDBOX_API_LIMIT=1000
SANDBOX_API_WINDOW=60
```

### Rate Limits (Defaults)
| Resource | Limit | Window |
|----------|-------|--------|
| payment | 100 | 3600s (1h) |
| api_call | 1000 | 60s (1m) |
| data_export | 10 | 3600s (1h) |

---

## Monitoring & Debugging

### Get Full Status
```python
status = sandbox.get_status()
print(f"Readiness: {status['readiness']}")
print(f"Heartbeat: {status['heartbeat']}")
print(f"Governor: {status['governor']}")
print(f"Worker queue: {status['worker_queue_length']}")
print(f"Alerts: {status['alerts']}")
```

### View Execution Logs
```python
# Dry-run log
log = dry_run.get_execution_log()

# Retry log
retry_log = retry_manager.get_retry_log('task_name')

# Alert history
alerts = alert_system.get_alerts(severity='error')
```

### Health Diagnostics
```python
# Scheduler health
health = heartbeat.get_health_status()

# Governor utilization
governor_status = governor.get_status()

# Readiness details
readiness = checker.get_status()
```

---

## Testing Checklist

- [ ] Database connectivity verified
- [ ] Dry-run locks blocking irreversible actions
- [ ] Worker processing jobs correctly
- [ ] Heartbeat detecting failures
- [ ] Retry mechanism with backoff working
- [ ] Idempotency preventing duplicates
- [ ] Governor enforcing rate limits
- [ ] Alerts triggering on failures
- [ ] Correlation IDs tracked through requests
- [ ] Readiness checks all passing
- [ ] Full status dashboard accessible
- [ ] Cleanup removes resources properly

---

## Troubleshooting

### Issue: Sandbox not ready
**Solution:** Check readiness details
```python
status = sandbox.readiness_checker.get_status()
for check, passed in status['checks'].items():
    if not passed:
        print(f"Failed: {check}")
```

### Issue: Rate limits too strict
**Solution:** Adjust limits
```python
sandbox.governor.set_limit('payment', max_actions=1000, window_seconds=3600)
```

### Issue: Workers backing up
**Solution:** Add more workers and adjust poll interval
```python
worker = WorkerProcess(poll_interval=1.0, max_workers=4)
```

### Issue: Retries exhausted
**Solution:** Increase retry count or backoff multiplier
```python
result = retry.execute_with_retry(
    func,
    'task',
    backoff_multiplier=3.0  # Increase backoff
)
```

---

## Next Steps

1. **Deploy to test environment** - Verify all components work
2. **Configure rate limits** - Adjust based on expected load
3. **Set up monitoring** - Wire alerts to notification system
4. **Load test** - Verify governor and retry logic under load
5. **Production hardening** - Add persistent logging/metrics
6. **Document custom checks** - Add site-specific readiness criteria

---

## Files Modified/Created

- `services/sandbox.py` - Core implementation (1000+ lines)
- `services/sandbox_examples.py` - Usage examples and demonstrations
- `BATCH_1_SANDBOX_STABILITY_GUIDE.md` - This guide

---

## Summary

Batch 1 provides comprehensive sandbox and stability infrastructure:

✓ **Isolation:** Separate database for testing  
✓ **Safety:** Dry-run locks prevent accidents  
✓ **Concurrency:** Background workers handle tasks  
✓ **Reliability:** Retry logic with exponential backoff  
✓ **Consistency:** Idempotent operations prevent duplicates  
✓ **Control:** Governor enforces rate limits  
✓ **Visibility:** Structured logging with correlation IDs  
✓ **Monitoring:** Heartbeat detects failures  
✓ **Alerting:** Centralized notification system  
✓ **Validation:** Readiness checks before GO  

Ready for Batch 2: Advanced Features & Integrations
