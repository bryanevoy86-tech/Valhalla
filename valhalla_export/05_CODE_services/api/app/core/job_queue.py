"""
PACK L0-08: Job Queue Adapter
Abstracts away job queue implementation details.
Supports Redis RQ, Celery, or in-memory queue.
Marked as stable API (STABLE CONTRACT).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
import json


class JobQueueAdapter(ABC):
    """
    Abstract base class for job queue implementations.
    
    Allows swapping between Redis RQ, Celery, or other implementations
    without changing application code.
    """
    
    @abstractmethod
    def enqueue(
        self,
        task_path: str,
        args: Optional[Dict[str, Any]] = None,
        priority: int = 10,
        job_id: Optional[str] = None,
    ) -> str:
        """
        Enqueue a task for execution.
        
        Args:
            task_path: Python path to execute (e.g., 'tasks.snapshots.create_weekly')
            args: Arguments for task
            priority: Priority level (1-100, higher = more urgent)
            job_id: Optional custom job ID
        
        Returns:
            Job ID (for status tracking)
        """
        pass
    
    @abstractmethod
    def get_status(self, job_id: str) -> str:
        """Get current status of a job (pending, running, success, failed, etc.)."""
        pass
    
    @abstractmethod
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get result of completed job."""
        pass
    
    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """Cancel a pending job. Returns True if cancelled."""
        pass
    
    @abstractmethod
    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all jobs, optionally filtered by status."""
        pass


class InMemoryJobQueue(JobQueueAdapter):
    """
    Simple in-memory job queue implementation.
    
    Useful for development and testing.
    Jobs are lost when process restarts.
    """
    
    def __init__(self):
        """Initialize in-memory queue."""
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._counter = 0
    
    def enqueue(
        self,
        task_path: str,
        args: Optional[Dict[str, Any]] = None,
        priority: int = 10,
        job_id: Optional[str] = None,
    ) -> str:
        """
        Enqueue a task for execution.
        
        STABLE CONTRACT: Return type will not change.
        """
        if not job_id:
            self._counter += 1
            job_id = f"job-{self._counter}"
        
        self.jobs[job_id] = {
            "id": job_id,
            "task_path": task_path,
            "args": args or {},
            "priority": priority,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }
        
        return job_id
    
    def get_status(self, job_id: str) -> str:
        """Get current status of a job."""
        if job_id not in self.jobs:
            return "not_found"
        return self.jobs[job_id]["status"]
    
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get result of completed job."""
        if job_id not in self.jobs:
            return None
        job = self.jobs[job_id]
        if job["status"] == "success":
            return job.get("result")
        return None
    
    def cancel(self, job_id: str) -> bool:
        """Cancel a pending job."""
        if job_id not in self.jobs:
            return False
        if self.jobs[job_id]["status"] == "pending":
            self.jobs[job_id]["status"] = "cancelled"
            return True
        return False
    
    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        return jobs
    
    def mark_running(self, job_id: str) -> None:
        """Mark job as running (for testing)."""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
    
    def mark_success(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as success (for testing)."""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "success"
            self.jobs[job_id]["finished_at"] = datetime.utcnow().isoformat()
            self.jobs[job_id]["result"] = result or {}
    
    def mark_failed(self, job_id: str, error: str) -> None:
        """Mark job as failed (for testing)."""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["finished_at"] = datetime.utcnow().isoformat()
            self.jobs[job_id]["error"] = error


# Global queue instance (swap with Redis/Celery implementation)
_queue: Optional[JobQueueAdapter] = None


def get_queue() -> JobQueueAdapter:
    """Get job queue instance (lazy initialization)."""
    global _queue
    if _queue is None:
        # For now, use in-memory queue
        # In production, swap with:
        # _queue = RedisJobQueue(redis_url="redis://localhost:6379")
        _queue = InMemoryJobQueue()
    return _queue


def set_queue(queue: JobQueueAdapter) -> None:
    """Set custom queue implementation (for testing)."""
    global _queue
    _queue = queue
