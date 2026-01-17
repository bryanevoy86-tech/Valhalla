"""
PACK AR: Heimdall Workload Balancer Router
Prefix: /heimdall/workload
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.heimdall_workload import (
    HeimdallJobCreate,
    HeimdallJobUpdate,
    HeimdallJobOut,
    HeimdallWorkloadConfigOut,
    HeimdallQueueStats,
)
from app.services.heimdall_workload import (
    create_job,
    update_job,
    list_jobs,
    queue_stats,
    set_workload_config,
    get_workload_config,
)

router = APIRouter(prefix="/heimdall/workload", tags=["HeimdallWorkload"])


@router.post("/jobs", response_model=HeimdallJobOut)
def create_job_endpoint(
    payload: HeimdallJobCreate,
    db: Session = Depends(get_db),
):
    """Create a Heimdall job."""
    return create_job(db, payload)


@router.patch("/jobs/{job_id}", response_model=HeimdallJobOut)
def update_job_endpoint(
    job_id: int,
    payload: HeimdallJobUpdate,
    db: Session = Depends(get_db),
):
    """Update a Heimdall job."""
    obj = update_job(db, job_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Job not found")
    return obj


@router.get("/jobs", response_model=List[HeimdallJobOut])
def list_jobs_endpoint(
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List Heimdall jobs."""
    return list_jobs(db, status=status, job_type=job_type, limit=limit)


@router.get("/stats", response_model=HeimdallQueueStats)
def queue_stats_endpoint(
    db: Session = Depends(get_db),
):
    """Get queue statistics."""
    stats = queue_stats(db)
    return HeimdallQueueStats(**stats)


@router.post("/config/{job_type}", response_model=HeimdallWorkloadConfigOut)
def set_workload_config_endpoint(
    job_type: str,
    enabled: Optional[bool] = Query(None),
    max_concurrent: Optional[int] = Query(None),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Set or update workload configuration."""
    obj = set_workload_config(
        db,
        job_type=job_type,
        enabled=enabled,
        max_concurrent=max_concurrent,
        notes=notes,
    )
    return obj


@router.get("/config/{job_type}", response_model=Optional[HeimdallWorkloadConfigOut])
def get_workload_config_endpoint(
    job_type: str,
    db: Session = Depends(get_db),
):
    """Get workload configuration for a job type."""
    return get_workload_config(db, job_type)
