from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.scheduler.models import ScheduledJob
from app.scheduler.schemas import JobCreate


def register_job(db: Session, job: JobCreate) -> ScheduledJob:
    new_job = ScheduledJob(**job.dict())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


def list_jobs(db: Session) -> list[ScheduledJob]:
    return db.query(ScheduledJob).all()


def mark_job_run(db: Session, job_id: int) -> ScheduledJob | None:
    job = db.get(ScheduledJob, job_id)
    if job:
        job.last_run = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
    return job
