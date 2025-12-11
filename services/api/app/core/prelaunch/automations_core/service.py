"""PACK-CORE-PRELAUNCH-01: Automations Core - Service"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from . import models


def list_jobs(db: Session) -> List[models.AutomationJob]:
    return db.query(models.AutomationJob).order_by(models.AutomationJob.code).all()


def get_job_by_code(db: Session, code: str) -> Optional[models.AutomationJob]:
    return db.query(models.AutomationJob).filter(models.AutomationJob.code == code).first()


def mark_run_result(
    db: Session,
    job: models.AutomationJob,
    status: str,
    result: dict | None = None,
) -> models.AutomationJob:
    job.last_run_at = datetime.utcnow()
    job.last_status = status
    job.last_result = result or {}
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_job(db: Session, code: str) -> models.AutomationJob:
    job = get_job_by_code(db, code)
    if not job:
        raise ValueError(f"Job {code} not found")

    # TODO: call actual implementations based on job.code
    # Example:
    # if code == "RENT_ROLL_CHECK":
    #     result = run_rent_roll(...)
    # else:
    #     result = {"status": "NOT_IMPLEMENTED"}

    result = {"status": "NOT_IMPLEMENTED"}
    mark_run_result(db, job, status="SUCCESS", result=result)
    return job
