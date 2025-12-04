from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.system_check_job import SystemCheckJob
from app.schemas.system_check_job import (
    SystemCheckJobCreate,
    SystemCheckJobUpdate,
    SystemCheckJobOut,
)

router = APIRouter()


@router.post("/", response_model=SystemCheckJobOut)
def create_system_check_job(
    payload: SystemCheckJobCreate,
    db: Session = Depends(get_db),
):
    obj = SystemCheckJob(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[SystemCheckJobOut])
def list_system_check_jobs(
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SystemCheckJob)
    if active is not None:
        query = query.filter(SystemCheckJob.active == active)
    return query.all()


@router.put("/{job_id}", response_model=SystemCheckJobOut)
def update_system_check_job(
    job_id: int,
    payload: SystemCheckJobUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(SystemCheckJob).get(job_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
