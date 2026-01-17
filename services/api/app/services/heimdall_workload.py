"""
PACK AR: Heimdall Workload Balancer Service
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.heimdall_workload import HeimdallJob, HeimdallWorkloadConfig
from app.schemas.heimdall_workload import (
    HeimdallJobCreate,
    HeimdallJobUpdate,
)


def create_job(db: Session, payload: HeimdallJobCreate) -> HeimdallJob:
    obj = HeimdallJob(
        job_type=payload.job_type,
        source=payload.source,
        priority=payload.priority,
        payload=payload.payload,
        status="queued",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_job(
    db: Session,
    job_id: int,
    payload: HeimdallJobUpdate,
) -> Optional[HeimdallJob]:
    obj = db.query(HeimdallJob).filter(HeimdallJob.id == job_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        obj.status = data["status"]
        if data["status"] == "in_progress" and not obj.started_at:
            obj.started_at = datetime.utcnow()
        if data["status"] in ("completed", "failed", "cancelled") and not obj.completed_at:
            obj.completed_at = datetime.utcnow()

    if "payload" in data and data["payload"] is not None:
        obj.payload = data["payload"]

    db.commit()
    db.refresh(obj)
    return obj


def list_jobs(
    db: Session,
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 100,
) -> List[HeimdallJob]:
    q = db.query(HeimdallJob)
    if status:
        q = q.filter(HeimdallJob.status == status)
    if job_type:
        q = q.filter(HeimdallJob.job_type == job_type)
    return q.order_by(HeimdallJob.created_at.desc()).limit(limit).all()


def queue_stats(db: Session):
    total = db.query(HeimdallJob).count()
    queued = db.query(HeimdallJob).filter(HeimdallJob.status == "queued").count()
    in_progress = db.query(HeimdallJob).filter(HeimdallJob.status == "in_progress").count()
    completed = db.query(HeimdallJob).filter(HeimdallJob.status == "completed").count()
    failed = db.query(HeimdallJob).filter(HeimdallJob.status == "failed").count()

    return {
        "total_jobs": total,
        "queued": queued,
        "in_progress": in_progress,
        "completed": completed,
        "failed": failed,
    }


def set_workload_config(
    db: Session,
    job_type: str,
    enabled: Optional[bool] = None,
    max_concurrent: Optional[int] = None,
    notes: Optional[str] = None,
) -> HeimdallWorkloadConfig:
    obj = db.query(HeimdallWorkloadConfig).filter(HeimdallWorkloadConfig.job_type == job_type).first()
    if not obj:
        obj = HeimdallWorkloadConfig(job_type=job_type)
        db.add(obj)

    if enabled is not None:
        obj.enabled = enabled
    if max_concurrent is not None:
        obj.max_concurrent = max_concurrent
    if notes is not None:
        obj.notes = notes

    obj.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(obj)
    return obj


def get_workload_config(db: Session, job_type: str) -> Optional[HeimdallWorkloadConfig]:
    return db.query(HeimdallWorkloadConfig).filter(HeimdallWorkloadConfig.job_type == job_type).first()
