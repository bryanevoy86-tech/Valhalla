"""
PACK UH: Export & Snapshot Job Engine Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.export_job import ExportJob
from app.schemas.export_job import ExportJobCreate


def create_export_job(
    db: Session,
    payload: ExportJobCreate,
) -> ExportJob:
    obj = ExportJob(
        job_type=payload.job_type,
        filter_params=payload.filter_params,
        requested_by=payload.requested_by,
        status="pending",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_export_jobs(
    db: Session,
    status: Optional[str] = None,
    limit: int = 200,
) -> List[ExportJob]:
    q = db.query(ExportJob)
    if status:
        q = q.filter(ExportJob.status == status)
    return (
        q.order_by(ExportJob.created_at.desc())
        .limit(limit)
        .all()
    )


def update_export_job_status(
    db: Session,
    job_id: int,
    status: str,
    storage_url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Optional[ExportJob]:
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        return None
    job.status = status
    if status == "completed":
        job.completed_at = datetime.utcnow()
        job.error_message = None
    if status == "failed" and error_message:
        job.error_message = error_message
    if storage_url:
        job.storage_url = storage_url
    db.commit()
    db.refresh(job)
    return job
