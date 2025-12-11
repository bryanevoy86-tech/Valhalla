"""
PACK L0-08: Job Service
Manages job lifecycle, enqueuing, status tracking, and result retrieval.
Marked as stable API (STABLE CONTRACT).
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.scheduled_job import ScheduledJob
from app.models.system_check_job import SystemCheckJob
from app.models.training_job import TrainingJob
from app.schemas.job import (
    ScheduledJobCreate,
    ScheduledJobOut,
    SystemCheckJobCreate,
    SystemCheckJobOut,
    TrainingJobCreate,
    TrainingJobOut,
    JobStatus,
)
from app.core.job_queue import get_queue


class JobService:
    """
    Service for managing jobs.
    
    Handles job creation, queuing, status tracking, and integration with telemetry.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.queue = get_queue()
    
    # Scheduled Jobs
    
    def create_scheduled_job(
        self,
        payload: ScheduledJobCreate,
    ) -> ScheduledJobOut:
        """
        Create a new scheduled job.
        
        STABLE CONTRACT: Return type will not change.
        
        Args:
            payload: ScheduledJobCreate with job details
        
        Returns:
            ScheduledJobOut: The created job
        """
        obj = ScheduledJob(
            name=payload.name,
            category=payload.category,
            schedule=payload.schedule,
            task_path=payload.task_path,
            args=str(payload.args or {}),
            active=payload.active,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return ScheduledJobOut.from_orm(obj)
    
    def list_scheduled_jobs(self, active_only: bool = False) -> List[ScheduledJobOut]:
        """List scheduled jobs, optionally filtered to active only."""
        q = self.db.query(ScheduledJob)
        if active_only:
            q = q.filter(ScheduledJob.active == True)
        items = q.all()
        return [ScheduledJobOut.from_orm(item) for item in items]
    
    # System Check Jobs
    
    def create_system_check_job(
        self,
        payload: SystemCheckJobCreate,
    ) -> SystemCheckJobOut:
        """
        Create a new system check job.
        
        Args:
            payload: SystemCheckJobCreate with check details
        
        Returns:
            SystemCheckJobOut: The created job
        """
        obj = SystemCheckJob(
            name=payload.name,
            scope=payload.scope,
            scope_code=payload.scope_code,
            schedule=payload.schedule,
            active=payload.active,
            notes=payload.notes,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return SystemCheckJobOut.from_orm(obj)
    
    def list_system_check_jobs(
        self,
        active_only: bool = False,
    ) -> List[SystemCheckJobOut]:
        """List system check jobs."""
        q = self.db.query(SystemCheckJob)
        if active_only:
            q = q.filter(SystemCheckJob.active == True)
        items = q.all()
        return [SystemCheckJobOut.from_orm(item) for item in items]
    
    # Training Jobs
    
    def create_training_job(
        self,
        payload: TrainingJobCreate,
    ) -> Tuple[TrainingJobOut, str]:
        """
        Create and enqueue a training job.
        
        Args:
            payload: TrainingJobCreate with job details
        
        Returns:
            Tuple of (job_out, queue_job_id)
                - job_out: Created training job
                - queue_job_id: ID in job queue for status tracking
        """
        # Create in database
        obj = TrainingJob(
            job_type=payload.job_type,
            target_module=payload.target_module,
            priority=payload.priority,
            payload=str(payload.payload or {}),
            status="pending",
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        
        # Enqueue in job queue
        queue_job_id = self.queue.enqueue(
            task_path=f"tasks.training.{payload.job_type}",
            args={
                "job_id": obj.id,
                "target_module": payload.target_module,
                "payload": payload.payload or {},
            },
            priority=payload.priority,
        )
        
        return TrainingJobOut.from_orm(obj), queue_job_id
    
    def get_training_job_status(self, job_id: int) -> str:
        """Get status of a training job."""
        job = self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            return "not_found"
        return job.status
    
    def update_training_job_status(
        self,
        job_id: int,
        status: JobStatus,
        progress: float = 0.0,
        error_message: Optional[str] = None,
    ) -> Optional[TrainingJobOut]:
        """
        Update training job status (called by worker).
        
        Args:
            job_id: Training job ID
            status: New status
            progress: Progress percentage (0-1)
            error_message: Error message if failed
        
        Returns:
            Updated job or None if not found
        """
        job = self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            return None
        
        job.status = status.value if isinstance(status, JobStatus) else status
        job.progress = min(1.0, max(0.0, progress))
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        
        if status in (JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED):
            job.finished_at = datetime.utcnow()
        
        if error_message:
            job.error_message = error_message
        
        self.db.commit()
        self.db.refresh(job)
        return TrainingJobOut.from_orm(job)
    
    def list_training_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[TrainingJobOut]:
        """List training jobs, optionally filtered by status."""
        q = self.db.query(TrainingJob)
        if status:
            status_str = status.value if isinstance(status, JobStatus) else status
            q = q.filter(TrainingJob.status == status_str)
        items = q.order_by(TrainingJob.created_at.desc()).limit(limit).all()
        return [TrainingJobOut.from_orm(item) for item in items]


def get_job_service(db: Session) -> JobService:
    """Factory function to create JobService instance."""
    return JobService(db)
