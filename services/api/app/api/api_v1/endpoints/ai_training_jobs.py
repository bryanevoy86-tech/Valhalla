from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.ai_training_job import AITrainingJob
from app.schemas.ai_training_job import (
    AITrainingJobCreate,
    AITrainingJobUpdate,
    AITrainingJobOut,
)

router = APIRouter()


@router.post("/", response_model=AITrainingJobOut)
def create_ai_training_job(payload: AITrainingJobCreate, db: Session = Depends(get_db)):
    obj = AITrainingJob(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[AITrainingJobOut])
def list_ai_training_jobs(
    engine_name: str | None = None,
    job_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AITrainingJob)
    if engine_name:
        query = query.filter(AITrainingJob.engine_name == engine_name)
    if job_type:
        query = query.filter(AITrainingJob.job_type == job_type)
    if status:
        query = query.filter(AITrainingJob.status == status)
    return query.order_by(AITrainingJob.created_at.desc()).all()


@router.put("/{job_id}", response_model=AITrainingJobOut)
def update_ai_training_job(job_id: int, payload: AITrainingJobUpdate, db: Session = Depends(get_db)):
    obj = db.query(AITrainingJob).get(job_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
