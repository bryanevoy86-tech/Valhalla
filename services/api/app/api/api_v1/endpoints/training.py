from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.training_job import TrainingJob
from app.schemas.training import (
    TrainingJobCreate,
    TrainingJobUpdate,
    TrainingJobOut,
)

router = APIRouter()


@router.post("/", response_model=TrainingJobOut)
def create_training_job(payload: TrainingJobCreate, db: Session = Depends(get_db)):
    obj = TrainingJob(
        job_type=payload.job_type,
        target_module=payload.target_module,
        priority=payload.priority,
        payload=payload.payload,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[TrainingJobOut])
def list_training_jobs(status: str | None = None, job_type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(TrainingJob)
    if status:
        query = query.filter(TrainingJob.status == status)
    if job_type:
        query = query.filter(TrainingJob.job_type == job_type)
    return query.all()


@router.put("/{job_id}", response_model=TrainingJobOut)
def update_training_job(job_id: int, payload: TrainingJobUpdate, db: Session = Depends(get_db)):
    obj = db.query(TrainingJob).get(job_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
