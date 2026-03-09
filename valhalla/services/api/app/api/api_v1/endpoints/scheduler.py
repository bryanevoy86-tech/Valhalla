from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scheduled_job import ScheduledJob
from app.schemas.scheduler import (
    ScheduledJobCreate,
    ScheduledJobUpdate,
    ScheduledJobOut,
)

router = APIRouter()


@router.post("/", response_model=ScheduledJobOut)
def create_scheduled_job(
    payload: ScheduledJobCreate,
    db: Session = Depends(get_db),
):
    obj = ScheduledJob(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ScheduledJobOut])
def list_scheduled_jobs(
    active: bool | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ScheduledJob)
    if active is not None:
        query = query.filter(ScheduledJob.active == active)
    if category:
        query = query.filter(ScheduledJob.category == category)
    return query.all()


@router.put("/{job_id}", response_model=ScheduledJobOut)
def update_scheduled_job(
    job_id: int,
    payload: ScheduledJobUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(ScheduledJob).get(job_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
