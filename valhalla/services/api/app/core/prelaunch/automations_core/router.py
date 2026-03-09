"""PACK-CORE-PRELAUNCH-01: Automations Core - Router"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/automations", tags=["automations"])


@router.get("/", response_model=List[schemas.AutomationJobRead])
def get_jobs(db: Session = Depends(get_db)):
    return service.list_jobs(db)


@router.post("/{job_code}/run", response_model=schemas.AutomationJobRead)
def run_job(job_code: str, db: Session = Depends(get_db)):
    try:
        job = service.run_job(db, job_code)
        return job
    except ValueError:
        raise HTTPException(status_code=404, detail="Automation job not found")
