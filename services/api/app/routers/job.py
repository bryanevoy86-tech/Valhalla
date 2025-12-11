"""
PACK L0-08: Jobs Router
Provides endpoints for managing scheduled jobs, system checks, and training jobs.
Marked as stable API (STABLE CONTRACT).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.db import get_db
from app.schemas.job import (
    ScheduledJobCreate,
    ScheduledJobOut,
    SystemCheckJobCreate,
    SystemCheckJobOut,
    TrainingJobCreate,
    TrainingJobOut,
)
from app.services.job import get_job_service
from app.middleware.correlation_id import get_correlation_id


router = APIRouter(prefix="/jobs", tags=["Jobs"])


# Scheduled Jobs

@router.post("/scheduled", response_model=ScheduledJobOut)
def create_scheduled_job(
    payload: ScheduledJobCreate,
    db: Session = Depends(get_db),
) -> ScheduledJobOut:
    """
    Create a new scheduled job.
    
    Scheduled jobs are executed periodically according to a cron schedule.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    Args:
        payload: ScheduledJobCreate with job details
        db: Database session (injected)
    
    Returns:
        ScheduledJobOut: The created scheduled job
    
    Example:
        ```json
        POST /jobs/scheduled
        {
          "name": "weekly_empire_snapshot",
          "category": "snapshot",
          "schedule": "0 3 * * MON",
          "task_path": "tasks.snapshots.create_weekly",
          "args": {"scope": "empire"}
        }
        ```
    """
    service = get_job_service(db)
    return service.create_scheduled_job(payload)


@router.get("/scheduled", response_model=List[ScheduledJobOut])
def list_scheduled_jobs(
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> List[ScheduledJobOut]:
    """
    List all scheduled jobs.
    
    **STABLE CONTRACT:** This endpoint will remain backwards compatible.
    
    Args:
        active_only: Filter to active jobs only
        db: Database session (injected)
    
    Returns:
        List of scheduled jobs
    """
    service = get_job_service(db)
    return service.list_scheduled_jobs(active_only=active_only)


# System Check Jobs

@router.post("/system-checks", response_model=SystemCheckJobOut)
def create_system_check_job(
    payload: SystemCheckJobCreate,
    db: Session = Depends(get_db),
) -> SystemCheckJobOut:
    """
    Create a new system check job.
    
    System checks are health/status checks run periodically to validate
    system components are working correctly.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    Args:
        payload: SystemCheckJobCreate with check details
        db: Database session (injected)
    
    Returns:
        SystemCheckJobOut: The created system check job
    """
    service = get_job_service(db)
    return service.create_system_check_job(payload)


@router.get("/system-checks", response_model=List[SystemCheckJobOut])
def list_system_check_jobs(
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> List[SystemCheckJobOut]:
    """
    List all system check jobs.
    
    Args:
        active_only: Filter to active checks only
        db: Database session (injected)
    
    Returns:
        List of system check jobs
    """
    service = get_job_service(db)
    return service.list_system_check_jobs(active_only=active_only)


# Training Jobs

@router.post("/training", response_model=Dict[str, Any])
def create_training_job(
    payload: TrainingJobCreate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Create and enqueue a training job.
    
    Training jobs are long-running jobs that execute asynchronously.
    Returns immediately with job ID for status tracking.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    Args:
        payload: TrainingJobCreate with job details
        db: Database session (injected)
    
    Returns:
        Dict with job details and queue ID for status tracking
    
    Example:
        ```json
        POST /jobs/training
        {
          "job_type": "embedding",
          "target_module": "heimdall_core",
          "priority": 50,
          "payload": {"model": "bge-large-en-v1.5"}
        }
        ```
    """
    service = get_job_service(db)
    job, queue_job_id = service.create_training_job(payload)
    return {
        "id": job.id,
        "queue_id": queue_job_id,
        "status": job.status,
        "created_at": job.created_at,
    }


@router.get("/training/{job_id}", response_model=Dict[str, Any])
def get_training_job_status(
    job_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get status of a training job.
    
    **STABLE CONTRACT:** Response format will not change.
    
    Args:
        job_id: Training job ID
        db: Database session (injected)
    
    Returns:
        Dict with current job status, progress, and result if available
    """
    service = get_job_service(db)
    status = service.get_training_job_status(job_id)
    
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job_id,
        "status": status,
        "correlation_id": get_correlation_id(),
    }


@router.get("/training", response_model=List[TrainingJobOut])
def list_training_jobs(
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[TrainingJobOut]:
    """
    List training jobs, optionally filtered by status.
    
    Args:
        status: Filter by status (pending, running, success, failed)
        limit: Max results (default 100)
        db: Database session (injected)
    
    Returns:
        List of training jobs
    """
    service = get_job_service(db)
    return service.list_training_jobs(status=status, limit=limit)
