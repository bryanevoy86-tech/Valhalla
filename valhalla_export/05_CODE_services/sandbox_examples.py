"""
Batch 1 - Sandbox + Stability: Integration Guide & Examples
Demonstrates how to use all 10 activation blocks in practice.
"""

import asyncio
import logging
from services.sandbox import (
    SandboxOrchestrator,
    SandboxDatabaseManager,
    DryRunLock,
    WorkerProcess,
    SchedulerHeartbeat,
    RetryBackoffManager,
    IdempotencyManager,
    GovernorEnforcer,
    AlertSystem,
    StructuredLogger,
    SandboxReadinessChecker,
)

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Complete Sandbox Initialization
# ============================================================================

def example_complete_sandbox_setup():
    """Example: Set up complete sandbox environment."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Complete Sandbox Setup")
    print("="*70)
    
    # Initialize orchestrator
    sandbox = SandboxOrchestrator(use_memory_db=True)
    sandbox.initialize()
    
    # Run readiness checks
    print("\nRunning readiness checks...")
    status = sandbox.readiness_checker.run_all_checks()
    print(f"Sandbox ready: {sandbox.is_ready()}")
    
    # Display status
    print("\nSandbox Status:")
    for component, value in sandbox.get_status().items():
        print(f"  {component}: {value}")
    
    # Cleanup
    sandbox.cleanup()
    print("\nSandbox cleaned up successfully")


# ============================================================================
# EXAMPLE 2: Using Dry-Run Locks
# ============================================================================

def example_dry_run_locks():
    """Example: Preventing irreversible actions in sandbox."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Dry-Run Locks for Irreversible Actions")
    print("="*70)
    
    dry_run = DryRunLock(dry_run=True, strict_mode=False)
    
    def make_payment(amount):
        """Simulate payment processing."""
        print(f"Processing payment of ${amount}")
        return {"status": "completed", "amount": amount}
    
    def send_email(recipient):
        """Simulate sending email."""
        print(f"Sending email to {recipient}")
        return {"status": "sent", "to": recipient}
    
    # Try to execute payment (should be blocked in dry-run)
    print("\nAttempting payment in dry-run mode...")
    result = dry_run.execute('payment', make_payment, 150.00)
    print(f"Result: {result}")
    
    # Safe operation (not in irreversible list)
    print("\nAttempting email (not irreversible)...")
    result = dry_run.execute('send_notification', send_email, 'user@example.com')
    print(f"Result: {result}")
    
    # View execution log
    print("\nExecution Log:")
    for action, logs in dry_run.execution_log.items():
        print(f"\n  {action}:")
        for log in logs:
            print(f"    - {log}")


# ============================================================================
# EXAMPLE 3: Background Worker Processing
# ============================================================================

def example_worker_processing():
    """Example: Using background workers."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Background Worker Processing")
    print("="*70)
    
    worker = WorkerProcess(poll_interval=1.0, max_workers=2)
    worker.start()
    
    def long_running_task(task_id, duration=2):
        """Simulate a long-running task."""
        import time
        print(f"  Processing task {task_id} for {duration}s...")
        time.sleep(duration)
        return f"Task {task_id} completed"
    
    # Submit jobs
    print("\nSubmitting jobs to worker queue...")
    job_ids = []
    for i in range(3):
        job_id = worker.submit_job(f"task_{i}", long_running_task, i, duration=1)
        job_ids.append(job_id)
        print(f"  Submitted: {job_id}")
    
    # Wait for processing
    import time
    time.sleep(4)
    
    # Check results
    print("\nJob Results:")
    for job_id in job_ids:
        status = worker.get_job_status(job_id)
        if status:
            print(f"  {job_id}: {status['status']}")
    
    worker.stop()
    print("\nWorker stopped")


# ============================================================================
# EXAMPLE 4: Scheduler Heartbeat Monitoring
# ============================================================================

def example_heartbeat_monitoring():
    """Example: Monitoring scheduler health."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Scheduler Heartbeat Monitoring")
    print("="*70)
    
    heartbeat = SchedulerHeartbeat(interval=2.0, timeout=5.0)
    heartbeat.start()
    
    print("\nHeartbeat started. Monitoring health...")
    
    import time
    for i in range(4):
        time.sleep(1.5)
        status = heartbeat.get_health_status()
        print(f"\n  Check {i+1}:")
        print(f"    Healthy: {status['is_healthy']}")
        print(f"    Seconds since heartbeat: {status['seconds_since_heartbeat']:.2f}")
    
    # Simulate timeout
    print("\n\nSimulating scheduler timeout...")
    heartbeat.stop()
    time.sleep(6)
    
    # Check if detected unhealthy
    status = heartbeat.get_health_status()
    print(f"\nAfter timeout:")
    print(f"  Healthy: {status['is_healthy']}")


# ============================================================================
# EXAMPLE 5: Retry with Exponential Backoff
# ============================================================================

def example_retry_backoff():
    """Example: Automatic retry with backoff."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Retry with Exponential Backoff")
    print("="*70)
    
    retry_manager = RetryBackoffManager(max_retries=3, base_delay=0.5, max_delay=5.0)
    
    attempt_count = 0
    
    def flaky_operation():
        """Simulate operation that fails then succeeds."""
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError(f"Connection failed (attempt {attempt_count})")
        return "Operation successful!"
    
    print("\nExecuting operation with retry logic...")
    try:
        result = retry_manager.execute_with_retry(
            flaky_operation,
            "flaky_api_call",
            backoff_multiplier=2.0,
            jitter=True
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed after retries: {e}")
    
    # Show retry log
    print("\nRetry Log:")
    for attempt in retry_manager.retry_log['flaky_api_call']:
        print(f"  Attempt {attempt['attempt']}: {attempt['status']}")


# ============================================================================
# EXAMPLE 6: Idempotent Operations
# ============================================================================

def example_idempotency():
    """Example: Idempotent operation deduplication."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Idempotent Operations")
    print("="*70)
    
    idempotency = IdempotencyManager(ttl_seconds=60)
    
    call_count = 0
    
    def expensive_operation(user_id):
        """Simulate expensive operation."""
        nonlocal call_count
        call_count += 1
        print(f"    [ACTUAL CALL #{call_count}] Processing for user {user_id}")
        return {"status": "processed", "user": user_id, "call_number": call_count}
    
    # Same operation called twice with same idempotency key
    print("\nFirst call with idempotency key 'user-123-payment'...")
    result1 = idempotency.process_idempotent(
        'user-123-payment',
        expensive_operation,
        'user-123'
    )
    print(f"  Result: {result1}")
    
    print("\nSecond call with same idempotency key (should use cache)...")
    result2 = idempotency.process_idempotent(
        'user-123-payment',
        expensive_operation,
        'user-123'
    )
    print(f"  Result: {result2}")
    
    print(f"\nTotal actual calls made: {call_count} (should be 1 due to deduplication)")


# ============================================================================
# EXAMPLE 7: Governor Rate Limiting
# ============================================================================

def example_governor_limiting():
    """Example: Rate limiting with governor."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Governor Rate Limiting")
    print("="*70)
    
    governor = GovernorEnforcer()
    
    # Set strict limits for demo
    governor.set_limit('payment', max_actions=3, window_seconds=60)
    
    print("\nPayment limit: 3 payments per minute\n")
    
    for i in range(5):
        allowed, message = governor.check_limit('payment')
        status = "✓ ALLOWED" if allowed else "✗ DENIED"
        print(f"  Payment attempt {i+1}: {status}")
        if not allowed:
            print(f"    Reason: {message}")
    
    # Show governor status
    print("\nGovernor Status:")
    status = governor.get_status('payment')
    print(f"  Current actions: {status['current_actions']}/{status['max_actions']}")
    print(f"  Denied count: {status['denied_count']}")


# ============================================================================
# EXAMPLE 8: Alert System
# ============================================================================

def example_alert_system():
    """Example: Centralized alert system."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Alert System")
    print("="*70)
    
    alert_system = AlertSystem()
    
    # Subscribe to specific task alerts
    def handle_payment_failure(alert):
        print(f"    [SUBSCRIBER] Payment alert received: {alert['reason']}")
    
    alert_system.subscribe('payment_processing', handle_payment_failure)
    
    # Trigger alerts
    print("\nTriggering alerts...\n")
    
    alert_system.alert(
        'payment_processing',
        'Insufficient funds',
        severity='warning',
        context={'amount': 500, 'available': 300}
    )
    
    alert_system.alert(
        'data_sync',
        'Database connection timeout',
        severity='error',
        context={'timeout': 30}
    )
    
    # View all alerts
    print("\nAll Alerts:")
    for alert in alert_system.get_alerts():
        print(f"  [{alert['severity'].upper()}] {alert['task']}: {alert['reason']}")


# ============================================================================
# EXAMPLE 9: Structured Logging
# ============================================================================

def example_structured_logging():
    """Example: Structured logging with correlation IDs."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Structured Logging with Correlation IDs")
    print("="*70)
    
    logger = StructuredLogger()
    
    # Simulate handling a user request
    print("\nSimulating user request flow...\n")
    
    # Start request
    correlation_id = logger.log_request(
        endpoint='/api/payments',
        method='POST',
        user_id='user-456'
    )
    print(f"Generated correlation ID: {correlation_id}")
    
    # Log subsequent actions with same correlation ID
    print("\nLogging related actions...")
    logger.log_action('payment_validation', level='info', amount=250)
    logger.log_action('payment_approved', level='info', transaction_id='txn-789')
    logger.log_action('confirmation_sent', level='info', email='user@example.com')
    
    print(f"All actions logged with correlation ID: {correlation_id}")


# ============================================================================
# EXAMPLE 10: Readiness Checks
# ============================================================================

def example_readiness_checks():
    """Example: Sandbox readiness verification."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Sandbox Readiness Checks")
    print("="*70)
    
    checker = SandboxReadinessChecker()
    
    # Register custom checks
    print("\nRegistering readiness checks...\n")
    
    checker.register_check(
        'database_connected',
        lambda: True
    )
    
    checker.register_check(
        'api_responsive',
        lambda: True
    )
    
    checker.register_check(
        'external_services_available',
        lambda: True
    )
    
    checker.register_check(
        'encryption_enabled',
        lambda: True
    )
    
    # Run checks
    print("Running checks...\n")
    results = checker.run_all_checks()
    
    # Display results
    status = checker.get_status()
    print(f"\nReadiness Summary:")
    print(f"  Total checks: {status['total_checks']}")
    print(f"  Passed: {status['passed_checks']}")
    print(f"  Failed: {status['failed_checks']}")
    print(f"  Sandbox GO: {status['is_ready']}")


# ============================================================================
# INTEGRATED WORKFLOW EXAMPLE
# ============================================================================

def example_integrated_workflow():
    """Example: Complete workflow using all components."""
    print("\n" + "="*70)
    print("INTEGRATED WORKFLOW: E-Commerce Transaction in Sandbox")
    print("="*70)
    
    # Initialize sandbox
    sandbox = SandboxOrchestrator(use_memory_db=True)
    sandbox.initialize()
    
    # Create structured logger with correlation ID
    logger = sandbox.logger
    correlation_id = logger.log_request(
        endpoint='/api/checkout',
        method='POST',
        user_id='user-789'
    )
    print(f"\nCheckout request: {correlation_id}\n")
    
    # Step 1: Check rate limits (governor)
    print("Step 1: Checking rate limits...")
    allowed, msg = sandbox.governor.check_limit('payment')
    if not allowed:
        sandbox.alert_system.alert('checkout', msg, severity='warning')
        print(f"  ✗ {msg}")
        return
    print("  ✓ Rate limit OK")
    
    # Step 2: Verify idempotency
    print("\nStep 2: Checking for duplicate orders...")
    idempotency_key = f"order-user-789-{123}"
    if sandbox.idempotency_manager.is_duplicate(idempotency_key):
        cached = sandbox.idempotency_manager.get_cached_result(idempotency_key)
        print(f"  ✓ Duplicate detected, returning cached order")
        return
    print("  ✓ New order")
    
    # Step 3: Process payment (with dry-run lock)
    print("\nStep 3: Processing payment...")
    
    def process_payment():
        return {"transaction_id": "txn-abc-123", "amount": 99.99}
    
    result = sandbox.dry_run_lock.execute('payment', process_payment)
    print(f"  ✓ {result}")
    
    # Step 4: Submit background tasks
    print("\nStep 4: Submitting background jobs...")
    
    def send_confirmation_email():
        print("    Sending confirmation email...")
        return "email_sent"
    
    job_id = sandbox.worker.submit_job(
        'send_email',
        send_confirmation_email
    )
    print(f"  ✓ Email job submitted: {job_id}")
    
    # Step 5: Store result with idempotency
    print("\nStep 5: Recording transaction...")
    sandbox.idempotency_manager.process_idempotent(
        idempotency_key,
        lambda: {"order_id": "ord-456", "status": "confirmed"}
    )
    print("  ✓ Transaction recorded")
    
    # Final status
    print("\n" + "-"*70)
    print("Sandbox Status After Transaction:")
    status = sandbox.get_status()
    print(f"  Worker queue: {status['worker_queue_length']} pending")
    print(f"  Completed jobs: {status['completed_jobs']}")
    print(f"  Total alerts: {status['alerts']}")
    
    sandbox.cleanup()
    print("\nWorkflow complete!")


# ============================================================================
# Run all examples
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "█" * 70)
    print("█ BATCH 1: SANDBOX + STABILITY EXAMPLES")
    print("█ 10 Activation Blocks Implementation & Usage")
    print("█" * 70)
    
    # Run examples
    try:
        example_complete_sandbox_setup()
        example_dry_run_locks()
        example_worker_processing()
        example_heartbeat_monitoring()
        example_retry_backoff()
        example_idempotency()
        example_governor_limiting()
        example_alert_system()
        example_structured_logging()
        example_readiness_checks()
        example_integrated_workflow()
        
        print("\n" + "█" * 70)
        print("█ All examples completed successfully!")
        print("█" * 70 + "\n")
    
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
