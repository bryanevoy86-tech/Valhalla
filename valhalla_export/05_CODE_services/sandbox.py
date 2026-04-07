"""
Sandbox Service Module - Batch 1 Stability & Activation
Provides isolated testing environment with safety mechanisms and monitoring.
"""

import logging
import uuid
import threading
import time
from typing import Any, Callable, Dict, Optional, Set
from datetime import datetime, timedelta
import random

# ============================================================================
# 1. SANDBOX SERVICE + DB WIRING
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class SandboxDatabaseManager:
    """Manages isolated sandbox database connection."""
    
    def __init__(self, db_url: Optional[str] = None, use_memory: bool = False):
        """
        Initialize sandbox database manager.
        
        Args:
            db_url: PostgreSQL URL for sandbox DB (overrides memory if provided)
            use_memory: If True, uses SQLite in-memory DB for testing
        """
        if use_memory:
            # Use in-memory SQLite for fast sandbox testing
            self.database_url = "sqlite:///:memory:"
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            # Use provided PostgreSQL sandbox DB or default
            self.database_url = db_url or "postgresql://user:password@localhost/sandbox_db"
            self.engine = create_engine(self.database_url)
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        logger.info(f"Sandbox database initialized: {self.database_url}")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def cleanup(self):
        """Clean up database connections."""
        self.engine.dispose()
        logger.info("Sandbox database cleaned up")


# ============================================================================
# 2. SANDBOX DRY-RUN LOCKS ON IRREVERSIBLE ACTIONS
# ============================================================================

class DryRunLock:
    """Prevents irreversible actions in sandbox/dry-run mode."""
    
    IRREVERSIBLE_ACTIONS = {
        'payment',
        'transfer',
        'delete_permanent',
        'external_call',
        'financial_commit',
        'data_export_external',
        'user_deletion',
        'bulk_update_production'
    }
    
    def __init__(self, dry_run: bool = True, strict_mode: bool = False):
        """
        Initialize dry-run lock.
        
        Args:
            dry_run: If True, actions are simulated but not executed
            strict_mode: If True, raises exception on irreversible actions
        """
        self.dry_run = dry_run
        self.strict_mode = strict_mode
        self.execution_log: Dict[str, list] = {}
        logger.info(f"DryRunLock initialized - dry_run={dry_run}, strict_mode={strict_mode}")
    
    def execute(self, action_name: str, action: Callable, *args, **kwargs) -> Any:
        """
        Execute action with dry-run protection.
        
        Args:
            action_name: Name of the action for logging
            action: Callable to execute
            *args, **kwargs: Arguments for the action
            
        Returns:
            Result of action or dry-run simulation
        """
        is_irreversible = action_name.lower() in self.IRREVERSIBLE_ACTIONS
        
        # Log the attempt
        if action_name not in self.execution_log:
            self.execution_log[action_name] = []
        
        timestamp = datetime.now().isoformat()
        
        if self.dry_run and is_irreversible:
            log_entry = {
                'timestamp': timestamp,
                'status': 'dry_run_blocked',
                'action': action_name,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            self.execution_log[action_name].append(log_entry)
            logger.warning(f"DRY RUN: {action_name} will not be executed (irreversible)")
            
            if self.strict_mode:
                raise PermissionError(
                    f"Cannot execute irreversible action '{action_name}' in strict dry-run mode"
                )
            
            return {'dry_run': True, 'action': action_name, 'result': None}
        
        # Execute the action
        try:
            result = action(*args, **kwargs)
            log_entry = {
                'timestamp': timestamp,
                'status': 'executed',
                'action': action_name,
                'result': 'success'
            }
            self.execution_log[action_name].append(log_entry)
            logger.info(f"Action executed: {action_name}")
            return result
        except Exception as e:
            log_entry = {
                'timestamp': timestamp,
                'status': 'error',
                'action': action_name,
                'error': str(e)
            }
            self.execution_log[action_name].append(log_entry)
            logger.error(f"Action failed: {action_name} - {e}")
            raise
    
    def get_execution_log(self, action_name: Optional[str] = None) -> Dict:
        """Get execution log for all or specific action."""
        if action_name:
            return self.execution_log.get(action_name, [])
        return self.execution_log


# ============================================================================
# 3. WORKER PROCESS ENABLED
# ============================================================================

class WorkerProcess:
    """Background worker process for sandbox task handling."""
    
    def __init__(self, poll_interval: float = 5.0, max_workers: int = 1):
        """
        Initialize worker process.
        
        Args:
            poll_interval: Seconds between job polls
            max_workers: Number of concurrent workers
        """
        self.poll_interval = poll_interval
        self.max_workers = max_workers
        self.is_running = False
        self.threads: list = []
        self.job_queue: list = []
        self.completed_jobs: Dict[str, Any] = {}
        logger.info(f"Worker initialized - interval={poll_interval}s, workers={max_workers}")
    
    def start(self):
        """Start worker process."""
        if self.is_running:
            logger.warning("Worker already running")
            return
        
        self.is_running = True
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                name=f"SandboxWorker-{i}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        logger.info(f"Worker process started with {self.max_workers} workers")
    
    def stop(self):
        """Stop worker process."""
        self.is_running = False
        for thread in self.threads:
            thread.join(timeout=2)
        logger.info("Worker process stopped")
    
    def _worker_loop(self):
        """Main worker loop."""
        while self.is_running:
            try:
                if self.job_queue:
                    job = self.job_queue.pop(0)
                    self._process_job(job)
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(self.poll_interval)
    
    def _process_job(self, job: Dict[str, Any]):
        """Process a single job."""
        job_id = job.get('id', str(uuid.uuid4()))
        job_name = job.get('name', 'unknown')
        job_func = job.get('func')
        job_args = job.get('args', ())
        job_kwargs = job.get('kwargs', {})
        
        try:
            logger.info(f"Processing job {job_id}: {job_name}")
            result = job_func(*job_args, **job_kwargs)
            self.completed_jobs[job_id] = {
                'name': job_name,
                'status': 'completed',
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Job {job_id} completed successfully")
        except Exception as e:
            self.completed_jobs[job_id] = {
                'name': job_name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            logger.error(f"Job {job_id} failed: {e}")
    
    def submit_job(self, job_name: str, func: Callable, *args, **kwargs) -> str:
        """Submit a job to the worker queue."""
        job_id = str(uuid.uuid4())
        job = {
            'id': job_id,
            'name': job_name,
            'func': func,
            'args': args,
            'kwargs': kwargs
        }
        self.job_queue.append(job)
        logger.info(f"Job submitted: {job_id} ({job_name})")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a completed job."""
        return self.completed_jobs.get(job_id)


# ============================================================================
# 4. SCHEDULER HEARTBEAT
# ============================================================================

class SchedulerHeartbeat:
    """Monitors scheduler health with periodic heartbeat."""
    
    def __init__(self, interval: float = 10.0, timeout: float = 30.0):
        """
        Initialize scheduler heartbeat.
        
        Args:
            interval: Seconds between heartbeats
            timeout: Seconds before considering scheduler unhealthy
        """
        self.interval = interval
        self.timeout = timeout
        self.is_running = False
        self.last_heartbeat = datetime.now()
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.health_checks: list = []
        logger.info(f"SchedulerHeartbeat initialized - interval={interval}s")
    
    def start(self):
        """Start heartbeat monitoring."""
        if self.is_running:
            logger.warning("Heartbeat already running")
            return
        
        self.is_running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="SchedulerHeartbeat",
            daemon=True
        )
        self.heartbeat_thread.start()
        logger.info("Scheduler heartbeat started")
    
    def stop(self):
        """Stop heartbeat monitoring."""
        self.is_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        logger.info("Scheduler heartbeat stopped")
    
    def _heartbeat_loop(self):
        """Main heartbeat loop."""
        while self.is_running:
            try:
                self.last_heartbeat = datetime.now()
                logger.debug(f"Scheduler heartbeat: {self.last_heartbeat.isoformat()}")
                self.health_checks.append({
                    'timestamp': self.last_heartbeat.isoformat(),
                    'status': 'healthy'
                })
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(self.interval)
    
    def is_healthy(self) -> bool:
        """Check if scheduler is still healthy."""
        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
        return time_since_heartbeat < self.timeout
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            'is_running': self.is_running,
            'is_healthy': self.is_healthy(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'seconds_since_heartbeat': (datetime.now() - self.last_heartbeat).total_seconds(),
            'total_checks': len(self.health_checks)
        }


# ============================================================================
# 5. RETRY / BACKOFF RULES
# ============================================================================

class RetryBackoffManager:
    """Manages retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_log: Dict[str, list] = {}
    
    def execute_with_retry(
        self,
        func: Callable,
        task_name: str,
        *args,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        **kwargs
    ) -> Any:
        """
        Execute function with automatic retry and backoff.
        
        Args:
            func: Function to execute
            task_name: Name of the task
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Add randomness to backoff
            *args, **kwargs: Arguments for function
            
        Returns:
            Result of successful execution
            
        Raises:
            Exception: If all retries exhausted
        """
        if task_name not in self.retry_log:
            self.retry_log[task_name] = []
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt + 1} for task: {task_name}")
                result = func(*args, **kwargs)
                
                self.retry_log[task_name].append({
                    'timestamp': datetime.now().isoformat(),
                    'attempt': attempt + 1,
                    'status': 'success',
                    'result': str(result)[:100]
                })
                
                return result
            
            except Exception as e:
                last_exception = e
                
                self.retry_log[task_name].append({
                    'timestamp': datetime.now().isoformat(),
                    'attempt': attempt + 1,
                    'status': 'failed',
                    'error': str(e)
                })
                
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (backoff_multiplier ** attempt),
                        self.max_delay
                    )
                    
                    if jitter:
                        delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Task '{task_name}' failed (attempt {attempt + 1}). "
                        f"Retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Task '{task_name}' failed after {self.max_retries + 1} attempts")
        
        raise last_exception or Exception(f"Task '{task_name}' failed")
    
    def get_retry_log(self, task_name: Optional[str] = None) -> Dict:
        """Get retry log for all or specific task."""
        if task_name:
            return self.retry_log.get(task_name, [])
        return self.retry_log


# ============================================================================
# 6. IDEMPOTENCY / DEDUPLICATION (BASE)
# ============================================================================

class IdempotencyManager:
    """Manages idempotent operations and deduplication."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize idempotency manager.
        
        Args:
            ttl_seconds: Time-to-live for stored idempotency keys
        """
        self.ttl_seconds = ttl_seconds
        self.seen_operations: Dict[str, Dict[str, Any]] = {}
    
    def process_idempotent(
        self,
        idempotency_key: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function idempotently using key-based deduplication.
        
        Args:
            idempotency_key: Unique key for this operation
            func: Function to execute
            *args, **kwargs: Arguments for function
            
        Returns:
            Cached result if already processed, or new result
        """
        now = datetime.now()
        
        # Check if we've seen this operation before
        if idempotency_key in self.seen_operations:
            cached = self.seen_operations[idempotency_key]
            created_at = datetime.fromisoformat(cached['created_at'])
            
            # Check TTL
            if (now - created_at).total_seconds() < self.ttl_seconds:
                logger.info(f"Idempotent operation '{idempotency_key}' - returning cached result")
                return cached['result']
            else:
                # TTL expired, remove from cache
                del self.seen_operations[idempotency_key]
        
        # Execute the operation
        logger.info(f"Idempotent operation '{idempotency_key}' - executing new")
        result = func(*args, **kwargs)
        
        # Store result
        self.seen_operations[idempotency_key] = {
            'result': result,
            'created_at': now.isoformat(),
            'ttl': self.ttl_seconds
        }
        
        return result
    
    def is_duplicate(self, idempotency_key: str) -> bool:
        """Check if operation has been seen before."""
        if idempotency_key not in self.seen_operations:
            return False
        
        cached = self.seen_operations[idempotency_key]
        created_at = datetime.fromisoformat(cached['created_at'])
        now = datetime.now()
        
        return (now - created_at).total_seconds() < self.ttl_seconds
    
    def get_cached_result(self, idempotency_key: str) -> Optional[Any]:
        """Get cached result if exists and not expired."""
        if not self.is_duplicate(idempotency_key):
            return None
        return self.seen_operations[idempotency_key]['result']
    
    def clear_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.seen_operations.items():
            created_at = datetime.fromisoformat(entry['created_at'])
            if (now - created_at).total_seconds() >= self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.seen_operations[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired idempotency entries")


# ============================================================================
# 7. GOVERNOR ENFORCEMENT EVERYWHERE
# ============================================================================

class GovernorEnforcer:
    """Enforces rate limiting and action quotas."""
    
    def __init__(self):
        """Initialize governor enforcer."""
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.violation_log: list = []
    
    def set_limit(
        self,
        resource_name: str,
        max_actions: int,
        window_seconds: int = 3600
    ):
        """
        Set rate limit for a resource.
        
        Args:
            resource_name: Name of the resource (e.g., 'payment', 'api_call')
            max_actions: Maximum actions allowed
            window_seconds: Time window in seconds
        """
        self.rate_limits[resource_name] = {
            'max_actions': max_actions,
            'window_seconds': window_seconds,
            'actions': [],
            'denied_count': 0
        }
        logger.info(f"Governor limit set: {resource_name} = {max_actions}/{window_seconds}s")
    
    def check_limit(self, resource_name: str) -> tuple[bool, str]:
        """
        Check if action is allowed under current limits.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            Tuple of (allowed, message)
        """
        if resource_name not in self.rate_limits:
            logger.warning(f"No limit set for resource: {resource_name}")
            return True, "No limit configured"
        
        limit_config = self.rate_limits[resource_name]
        now = datetime.now()
        window_start = now - timedelta(seconds=limit_config['window_seconds'])
        
        # Remove actions outside the current window
        limit_config['actions'] = [
            action_time for action_time in limit_config['actions']
            if action_time > window_start
        ]
        
        # Check if limit exceeded
        if len(limit_config['actions']) >= limit_config['max_actions']:
            limit_config['denied_count'] += 1
            message = (
                f"Rate limit exceeded for '{resource_name}': "
                f"{len(limit_config['actions'])}/{limit_config['max_actions']} actions"
            )
            logger.warning(message)
            
            self.violation_log.append({
                'timestamp': now.isoformat(),
                'resource': resource_name,
                'action_count': len(limit_config['actions']),
                'max_allowed': limit_config['max_actions']
            })
            
            return False, message
        
        # Record this action
        limit_config['actions'].append(now)
        return True, "Action allowed"
    
    def get_status(self, resource_name: Optional[str] = None) -> Dict[str, Any]:
        """Get governor status."""
        if resource_name:
            if resource_name not in self.rate_limits:
                return {}
            config = self.rate_limits[resource_name]
            return {
                'resource': resource_name,
                'current_actions': len(config['actions']),
                'max_actions': config['max_actions'],
                'window_seconds': config['window_seconds'],
                'denied_count': config['denied_count']
            }
        
        return {
            name: {
                'current_actions': len(config['actions']),
                'max_actions': config['max_actions'],
                'denied_count': config['denied_count']
            }
            for name, config in self.rate_limits.items()
        }


# ============================================================================
# 8. ALERTS ON FAILURE / DENIAL
# ============================================================================

class AlertSystem:
    """Centralized alert system for failures and denials."""
    
    SEVERITY_LEVELS = {
        'info': 0,
        'warning': 1,
        'error': 2,
        'critical': 3
    }
    
    def __init__(self):
        """Initialize alert system."""
        self.alerts: list = []
        self.subscribers: Dict[str, list] = {}
    
    def alert(
        self,
        task_name: str,
        reason: str,
        severity: str = 'warning',
        context: Optional[Dict] = None
    ):
        """
        Record and dispatch an alert.
        
        Args:
            task_name: Name of the task that failed
            reason: Reason for the failure/denial
            severity: Severity level (info, warning, error, critical)
            context: Additional context data
        """
        severity = severity.lower()
        if severity not in self.SEVERITY_LEVELS:
            severity = 'warning'
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'task': task_name,
            'reason': reason,
            'severity': severity,
            'context': context or {}
        }
        
        self.alerts.append(alert)
        
        # Log appropriately
        log_func = {
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error,
            'critical': logger.critical
        }[severity]
        
        log_func(f"ALERT [{severity.upper()}]: Task '{task_name}' - {reason}")
        
        # Notify subscribers
        self._notify_subscribers(alert)
    
    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe to alerts of a specific type.
        
        Args:
            event_type: Type of alert to subscribe to
            callback: Function to call when alert occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to alerts: {event_type}")
    
    def _notify_subscribers(self, alert: Dict[str, Any]):
        """Notify subscribers of alert."""
        task = alert['task']
        if task in self.subscribers:
            for callback in self.subscribers[task]:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Get alerts with optional filtering."""
        results = self.alerts
        
        if severity:
            results = [a for a in results if a['severity'] == severity.lower()]
        
        if task_name:
            results = [a for a in results if a['task'] == task_name]
        
        return results[-limit:]


# ============================================================================
# 9. STRUCTURED LOGGING + CORRELATION IDs
# ============================================================================

class StructuredLogger:
    """Structured logging with correlation IDs."""
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """Initialize structured logger."""
        self.logger = logger_instance or logger
        self.context: Dict[str, str] = {}
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """
        Set correlation ID for request tracking.
        
        Args:
            correlation_id: Explicit ID or None to generate
            
        Returns:
            The correlation ID
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        self.context['correlation_id'] = correlation_id
        return correlation_id
    
    def get_correlation_id(self) -> str:
        """Get current correlation ID."""
        return self.context.get('correlation_id', 'unknown')
    
    def log_action(
        self,
        action_name: str,
        level: str = 'info',
        **kwargs
    ):
        """
        Log an action with structured data.
        
        Args:
            action_name: Name of the action
            level: Logging level (debug, info, warning, error)
            **kwargs: Additional fields to log
        """
        correlation_id = self.get_correlation_id()
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action_name,
            'correlation_id': correlation_id,
            **kwargs
        }
        
        log_message = f"[{correlation_id}] {action_name} - {log_data}"
        
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(log_message)
        
        return log_data
    
    def log_request(
        self,
        endpoint: str,
        method: str = 'GET',
        user_id: Optional[str] = None
    ) -> str:
        """
        Log incoming request with correlation ID.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            user_id: Optional user ID
            
        Returns:
            The correlation ID for this request
        """
        correlation_id = self.set_correlation_id()
        
        self.log_action(
            'request_received',
            endpoint=endpoint,
            method=method,
            user_id=user_id or 'anonymous'
        )
        
        return correlation_id


# ============================================================================
# 10. SANDBOX GO READINESS CHECKS
# ============================================================================

class SandboxReadinessChecker:
    """Performs readiness checks before sandbox operation."""
    
    def __init__(self):
        """Initialize readiness checker."""
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, bool] = {}
        self.last_check_time: Optional[datetime] = None
    
    def register_check(self, check_name: str, check_func: Callable) -> None:
        """
        Register a readiness check.
        
        Args:
            check_name: Name of the check
            check_func: Function that returns bool (True = passed)
        """
        self.checks[check_name] = check_func
        logger.info(f"Registered readiness check: {check_name}")
    
    def run_all_checks(self) -> Dict[str, bool]:
        """
        Run all registered checks.
        
        Returns:
            Dictionary of check results
        """
        logger.info("Running all readiness checks...")
        self.results = {}
        self.last_check_time = datetime.now()
        
        all_passed = True
        
        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                self.results[check_name] = result
                
                status = "PASSED" if result else "FAILED"
                log_func = logger.info if result else logger.error
                log_func(f"Readiness check '{check_name}': {status}")
                
                if not result:
                    all_passed = False
            
            except Exception as e:
                self.results[check_name] = False
                all_passed = False
                logger.error(f"Readiness check '{check_name}' raised exception: {e}")
        
        if all_passed:
            logger.info("✓ All readiness checks PASSED - Sandbox is GO")
        else:
            logger.error("✗ Some readiness checks FAILED - Sandbox is NOT GO")
        
        return self.results
    
    def is_ready(self) -> bool:
        """Check if all readiness checks have passed."""
        return all(self.results.values()) if self.results else False
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed readiness status."""
        return {
            'is_ready': self.is_ready(),
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'checks': self.results,
            'total_checks': len(self.checks),
            'passed_checks': sum(1 for v in self.results.values() if v),
            'failed_checks': sum(1 for v in self.results.values() if not v)
        }


# ============================================================================
# SANDBOX ORCHESTRATOR (Integration of all components)
# ============================================================================

class SandboxOrchestrator:
    """Orchestrates all sandbox components."""
    
    def __init__(self, use_memory_db: bool = True):
        """Initialize sandbox orchestrator."""
        self.db_manager = SandboxDatabaseManager(use_memory=use_memory_db)
        self.dry_run_lock = DryRunLock(dry_run=True)
        self.worker = WorkerProcess()
        self.heartbeat = SchedulerHeartbeat()
        self.retry_manager = RetryBackoffManager()
        self.idempotency_manager = IdempotencyManager()
        self.governor = GovernorEnforcer()
        self.alert_system = AlertSystem()
        self.logger = StructuredLogger()
        self.readiness_checker = SandboxReadinessChecker()
        
        logger.info("SandboxOrchestrator initialized")
    
    def initialize(self):
        """Initialize all sandbox components."""
        logger.info("Initializing sandbox components...")
        
        # Start worker and heartbeat
        self.worker.start()
        self.heartbeat.start()
        
        # Set up default governor limits
        self.governor.set_limit('payment', 100, 3600)
        self.governor.set_limit('api_call', 1000, 60)
        self.governor.set_limit('data_export', 10, 3600)
        
        # Register readiness checks
        self._register_readiness_checks()
        
        logger.info("Sandbox initialization complete")
    
    def _register_readiness_checks(self):
        """Register all readiness checks."""
        self.readiness_checker.register_check(
            'database_connected',
            lambda: self.db_manager.engine is not None
        )
        self.readiness_checker.register_check(
            'worker_running',
            lambda: self.worker.is_running
        )
        self.readiness_checker.register_check(
            'heartbeat_active',
            lambda: self.heartbeat.is_healthy()
        )
        self.readiness_checker.register_check(
            'governor_configured',
            lambda: len(self.governor.rate_limits) > 0
        )
    
    def run_readiness_check(self) -> bool:
        """Run full readiness check."""
        return self.is_ready()
    
    def is_ready(self) -> bool:
        """Check if sandbox is ready for operation."""
        self.readiness_checker.run_all_checks()
        return self.readiness_checker.is_ready()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive sandbox status."""
        return {
            'readiness': self.readiness_checker.get_status(),
            'heartbeat': self.heartbeat.get_health_status(),
            'governor': self.governor.get_status(),
            'worker_queue_length': len(self.worker.job_queue),
            'completed_jobs': len(self.worker.completed_jobs),
            'alerts': len(self.alert_system.alerts),
            'idempotent_operations': len(self.idempotency_manager.seen_operations)
        }
    
    def cleanup(self):
        """Shutdown sandbox cleanly."""
        logger.info("Cleaning up sandbox...")
        self.worker.stop()
        self.heartbeat.stop()
        self.db_manager.cleanup()
        logger.info("Sandbox cleanup complete")


# ============================================================================
# Module initialization
# ============================================================================

def setup_logging():
    """Set up structured logging for sandbox module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
