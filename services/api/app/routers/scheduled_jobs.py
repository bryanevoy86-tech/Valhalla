from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.scheduler.schemas import JobCreate, JobResponse
from app.scheduler.service import register_job, list_jobs, mark_job_run


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    return register_job(db=db, job=job)


@router.get("/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return list_jobs(db)


@router.post("/{job_id}/run", response_model=JobResponse)
def run_job(job_id: int, db: Session = Depends(get_db)):
    return mark_job_run(db, job_id)
