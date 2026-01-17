"""
Test suite for Batch 1 - Sandbox + Stability Components
Verifies all 10 activation blocks are working correctly.
"""

import unittest
import time
import threading
from datetime import datetime, timedelta
from services.sandbox import (
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
    SandboxOrchestrator,
)


class TestSandboxDatabase(unittest.TestCase):
    """Tests for SandboxDatabaseManager."""
    
    def test_memory_db_creation(self):
        """Test creation of in-memory database."""
        db = SandboxDatabaseManager(use_memory=True)
        self.assertIsNotNone(db.engine)
        self.assertEqual(db.database_url, "sqlite:///:memory:")
    
    def test_session_creation(self):
        """Test session management."""
        db = SandboxDatabaseManager(use_memory=True)
        session = db.get_session()
        self.assertIsNotNone(session)
        session.close()
    
    def test_cleanup(self):
        """Test database cleanup."""
        db = SandboxDatabaseManager(use_memory=True)
        db.cleanup()
        # Should not raise exception


class TestDryRunLock(unittest.TestCase):
    """Tests for DryRunLock."""
    
    def test_dry_run_blocks_payment(self):
        """Test dry-run mode blocks payment."""
        lock = DryRunLock(dry_run=True, strict_mode=False)
        
        def payment():
            return "paid"
        
        result = lock.execute('payment', payment)
        self.assertFalse(result['result'])
        self.assertTrue(result['dry_run'])
    
    def test_non_dry_run_allows_payment(self):
        """Test non-dry-run mode allows payment."""
        lock = DryRunLock(dry_run=False)
        
        def payment():
            return "paid"
        
        result = lock.execute('payment', payment)
        self.assertEqual(result, "paid")
    
    def test_safe_action_in_dry_run(self):
        """Test safe actions allowed in dry-run mode."""
        lock = DryRunLock(dry_run=True)
        
        def safe_action():
            return "result"
        
        result = lock.execute('read_data', safe_action)
        self.assertEqual(result, "result")
    
    def test_strict_mode_raises_exception(self):
        """Test strict mode raises on irreversible action."""
        lock = DryRunLock(dry_run=True, strict_mode=True)
        
        def payment():
            return "paid"
        
        with self.assertRaises(PermissionError):
            lock.execute('payment', payment)
    
    def test_execution_log(self):
        """Test execution logging."""
        lock = DryRunLock(dry_run=True)
        
        def payment():
            return "paid"
        
        lock.execute('payment', payment)
        log = lock.get_execution_log('payment')
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]['status'], 'dry_run_blocked')


class TestWorkerProcess(unittest.TestCase):
    """Tests for WorkerProcess."""
    
    def setUp(self):
        """Set up worker for tests."""
        self.worker = WorkerProcess(poll_interval=0.1, max_workers=1)
    
    def tearDown(self):
        """Clean up worker."""
        if self.worker.is_running:
            self.worker.stop()
    
    def test_worker_start_stop(self):
        """Test worker start and stop."""
        self.worker.start()
        self.assertTrue(self.worker.is_running)
        self.worker.stop()
        self.assertFalse(self.worker.is_running)
    
    def test_submit_job(self):
        """Test job submission."""
        self.worker.start()
        
        def test_task():
            return "completed"
        
        job_id = self.worker.submit_job('test', test_task)
        self.assertIsNotNone(job_id)
        
        self.worker.stop()
    
    def test_job_completion(self):
        """Test job completion tracking."""
        self.worker.start()
        
        def test_task():
            return "result"
        
        job_id = self.worker.submit_job('test', test_task)
        time.sleep(0.5)  # Wait for processing
        
        status = self.worker.get_job_status(job_id)
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'completed')
        
        self.worker.stop()


class TestSchedulerHeartbeat(unittest.TestCase):
    """Tests for SchedulerHeartbeat."""
    
    def setUp(self):
        """Set up heartbeat for tests."""
        self.heartbeat = SchedulerHeartbeat(interval=0.1, timeout=0.5)
    
    def tearDown(self):
        """Clean up heartbeat."""
        if self.heartbeat.is_running:
            self.heartbeat.stop()
    
    def test_heartbeat_start_stop(self):
        """Test heartbeat start and stop."""
        self.heartbeat.start()
        self.assertTrue(self.heartbeat.is_running)
        self.heartbeat.stop()
        self.assertFalse(self.heartbeat.is_running)
    
    def test_heartbeat_health_check(self):
        """Test heartbeat health check."""
        self.heartbeat.start()
        time.sleep(0.2)
        self.assertTrue(self.heartbeat.is_healthy())
        self.heartbeat.stop()
    
    def test_heartbeat_timeout(self):
        """Test heartbeat timeout detection."""
        self.heartbeat.start()
        self.heartbeat.stop()
        time.sleep(1)  # Wait for timeout
        self.assertFalse(self.heartbeat.is_healthy())


class TestRetryBackoff(unittest.TestCase):
    """Tests for RetryBackoffManager."""
    
    def test_successful_execution(self):
        """Test successful execution on first try."""
        retry = RetryBackoffManager(max_retries=3)
        
        def successful_task():
            return "success"
        
        result = retry.execute_with_retry(successful_task, 'task')
        self.assertEqual(result, "success")
    
    def test_retry_on_failure(self):
        """Test retry on failure."""
        retry = RetryBackoffManager(max_retries=2, base_delay=0.01)
        
        attempt_count = [0]
        
        def flaky_task():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise Exception("fail")
            return "success"
        
        result = retry.execute_with_retry(flaky_task, 'task')
        self.assertEqual(result, "success")
        self.assertEqual(attempt_count[0], 2)
    
    def test_exhausted_retries(self):
        """Test exception when retries exhausted."""
        retry = RetryBackoffManager(max_retries=2, base_delay=0.01)
        
        def failing_task():
            raise Exception("always fails")
        
        with self.assertRaises(Exception):
            retry.execute_with_retry(failing_task, 'task')
    
    def test_retry_log(self):
        """Test retry logging."""
        retry = RetryBackoffManager(max_retries=1, base_delay=0.01)
        
        def failing_task():
            raise Exception("fail")
        
        try:
            retry.execute_with_retry(failing_task, 'task')
        except:
            pass
        
        log = retry.get_retry_log('task')
        self.assertGreater(len(log), 0)


class TestIdempotency(unittest.TestCase):
    """Tests for IdempotencyManager."""
    
    def test_first_call_executes(self):
        """Test first call executes."""
        idempotency = IdempotencyManager(ttl_seconds=60)
        
        call_count = [0]
        
        def task():
            call_count[0] += 1
            return "result"
        
        result = idempotency.process_idempotent('key1', task)
        self.assertEqual(result, "result")
        self.assertEqual(call_count[0], 1)
    
    def test_duplicate_call_cached(self):
        """Test duplicate call uses cache."""
        idempotency = IdempotencyManager(ttl_seconds=60)
        
        call_count = [0]
        
        def task():
            call_count[0] += 1
            return "result"
        
        idempotency.process_idempotent('key1', task)
        idempotency.process_idempotent('key1', task)
        
        self.assertEqual(call_count[0], 1)
    
    def test_duplicate_detection(self):
        """Test duplicate detection."""
        idempotency = IdempotencyManager(ttl_seconds=60)
        
        def task():
            return "result"
        
        idempotency.process_idempotent('key1', task)
        self.assertTrue(idempotency.is_duplicate('key1'))
        self.assertFalse(idempotency.is_duplicate('key2'))
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        idempotency = IdempotencyManager(ttl_seconds=0.1)
        
        def task():
            return "result"
        
        idempotency.process_idempotent('key1', task)
        time.sleep(0.2)
        
        self.assertFalse(idempotency.is_duplicate('key1'))


class TestGovernorEnforcer(unittest.TestCase):
    """Tests for GovernorEnforcer."""
    
    def test_set_limit(self):
        """Test setting rate limit."""
        governor = GovernorEnforcer()
        governor.set_limit('payment', 5, 60)
        
        status = governor.get_status('payment')
        self.assertEqual(status['max_actions'], 5)
    
    def test_allow_action_within_limit(self):
        """Test action allowed within limit."""
        governor = GovernorEnforcer()
        governor.set_limit('payment', 5, 60)
        
        allowed, _ = governor.check_limit('payment')
        self.assertTrue(allowed)
    
    def test_deny_action_over_limit(self):
        """Test action denied over limit."""
        governor = GovernorEnforcer()
        governor.set_limit('payment', 2, 60)
        
        governor.check_limit('payment')
        governor.check_limit('payment')
        allowed, message = governor.check_limit('payment')
        
        self.assertFalse(allowed)
        self.assertIn('Rate limit exceeded', message)
    
    def test_governor_status(self):
        """Test governor status reporting."""
        governor = GovernorEnforcer()
        governor.set_limit('payment', 5, 60)
        
        governor.check_limit('payment')
        status = governor.get_status('payment')
        
        self.assertEqual(status['current_actions'], 1)
        self.assertEqual(status['max_actions'], 5)


class TestAlertSystem(unittest.TestCase):
    """Tests for AlertSystem."""
    
    def test_alert_creation(self):
        """Test alert creation."""
        alerts = AlertSystem()
        alerts.alert('task', 'reason', severity='warning')
        
        alert_list = alerts.get_alerts()
        self.assertEqual(len(alert_list), 1)
    
    def test_alert_severity(self):
        """Test alert severity levels."""
        alerts = AlertSystem()
        
        alerts.alert('task1', 'info message', severity='info')
        alerts.alert('task2', 'error message', severity='error')
        
        errors = alerts.get_alerts(severity='error')
        self.assertEqual(len(errors), 1)
    
    def test_alert_subscription(self):
        """Test alert subscription."""
        alerts = AlertSystem()
        
        received = []
        
        def callback(alert):
            received.append(alert)
        
        alerts.subscribe('task', callback)
        alerts.alert('task', 'reason')
        
        self.assertEqual(len(received), 1)
    
    def test_alert_context(self):
        """Test alert with context."""
        alerts = AlertSystem()
        
        alerts.alert(
            'task',
            'reason',
            context={'amount': 100, 'user': 'test'}
        )
        
        alert_list = alerts.get_alerts()
        self.assertEqual(alert_list[0]['context']['amount'], 100)


class TestStructuredLogger(unittest.TestCase):
    """Tests for StructuredLogger."""
    
    def test_correlation_id_generation(self):
        """Test correlation ID generation."""
        logger = StructuredLogger()
        cid = logger.set_correlation_id()
        
        self.assertIsNotNone(cid)
        self.assertEqual(logger.get_correlation_id(), cid)
    
    def test_explicit_correlation_id(self):
        """Test explicit correlation ID."""
        logger = StructuredLogger()
        logger.set_correlation_id('test-id-123')
        
        self.assertEqual(logger.get_correlation_id(), 'test-id-123')
    
    def test_log_action(self):
        """Test logging action."""
        logger = StructuredLogger()
        logger.set_correlation_id('test-id')
        
        log_data = logger.log_action('test_action', amount=100)
        
        self.assertEqual(log_data['action'], 'test_action')
        self.assertEqual(log_data['amount'], 100)
    
    def test_log_request(self):
        """Test logging request."""
        logger = StructuredLogger()
        cid = logger.log_request('/api/test', 'POST', 'user-123')
        
        self.assertIsNotNone(cid)
        self.assertEqual(logger.get_correlation_id(), cid)


class TestReadinessChecker(unittest.TestCase):
    """Tests for SandboxReadinessChecker."""
    
    def test_register_check(self):
        """Test registering checks."""
        checker = SandboxReadinessChecker()
        checker.register_check('test_check', lambda: True)
        
        self.assertIn('test_check', checker.checks)
    
    def test_run_checks_all_pass(self):
        """Test running checks that all pass."""
        checker = SandboxReadinessChecker()
        checker.register_check('check1', lambda: True)
        checker.register_check('check2', lambda: True)
        
        results = checker.run_all_checks()
        
        self.assertTrue(all(results.values()))
        self.assertTrue(checker.is_ready())
    
    def test_run_checks_some_fail(self):
        """Test running checks with failures."""
        checker = SandboxReadinessChecker()
        checker.register_check('check1', lambda: True)
        checker.register_check('check2', lambda: False)
        
        results = checker.run_all_checks()
        
        self.assertFalse(checker.is_ready())
    
    def test_readiness_status(self):
        """Test readiness status reporting."""
        checker = SandboxReadinessChecker()
        checker.register_check('check1', lambda: True)
        
        checker.run_all_checks()
        status = checker.get_status()
        
        self.assertEqual(status['total_checks'], 1)
        self.assertEqual(status['passed_checks'], 1)
        self.assertTrue(status['is_ready'])


class TestSandboxOrchestrator(unittest.TestCase):
    """Tests for SandboxOrchestrator integration."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        sandbox = SandboxOrchestrator(use_memory_db=True)
        sandbox.initialize()
        
        self.assertTrue(sandbox.worker.is_running)
        self.assertTrue(sandbox.heartbeat.is_running)
        
        sandbox.cleanup()
    
    def test_orchestrator_readiness(self):
        """Test orchestrator readiness checks."""
        sandbox = SandboxOrchestrator(use_memory_db=True)
        sandbox.initialize()
        
        self.assertTrue(sandbox.is_ready())
        
        sandbox.cleanup()
    
    def test_orchestrator_status(self):
        """Test orchestrator status reporting."""
        sandbox = SandboxOrchestrator(use_memory_db=True)
        sandbox.initialize()
        
        status = sandbox.get_status()
        
        self.assertIn('readiness', status)
        self.assertIn('heartbeat', status)
        self.assertIn('governor', status)
        
        sandbox.cleanup()
    
    def test_orchestrator_cleanup(self):
        """Test orchestrator cleanup."""
        sandbox = SandboxOrchestrator(use_memory_db=True)
        sandbox.initialize()
        sandbox.cleanup()
        
        self.assertFalse(sandbox.worker.is_running)
        self.assertFalse(sandbox.heartbeat.is_running)


class TestIntegration(unittest.TestCase):
    """Integration tests for multiple components."""
    
    def test_complete_workflow(self):
        """Test complete workflow with all components."""
        sandbox = SandboxOrchestrator(use_memory_db=True)
        sandbox.initialize()
        
        # Use dry-run lock
        result = sandbox.dry_run_lock.execute(
            'payment',
            lambda: {"status": "completed"}
        )
        self.assertTrue(result['dry_run'])
        
        # Use governor
        allowed, _ = sandbox.governor.check_limit('payment')
        self.assertTrue(allowed)
        
        # Use idempotency
        result = sandbox.idempotency_manager.process_idempotent(
            'test-key',
            lambda: "result"
        )
        self.assertEqual(result, "result")
        
        # Check readiness
        self.assertTrue(sandbox.is_ready())
        
        sandbox.cleanup()


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
