import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..schemas.io_job import ExportJob, ExportJobCreate, ImportJob, ImportJobCreate, ImportRowError
from ..services.io_jobs import (
    create_export_job,
    create_import_job,
    get_export_job,
    get_export_path,
    get_import_job,
    get_import_row_errors,
    get_upload_path,
)

router = APIRouter(prefix="/io", tags=["io"])


@router.post("/import", response_model=ImportJob)
def start_import_job(
    job_in: ImportJobCreate, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # Save file
    upload_path = get_upload_path(file.filename)
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    job = create_import_job(db, job_in)
    # TODO: Trigger background import processing
    return job


@router.get("/import/{job_id}", response_model=ImportJob)
def get_import_job_status(job_id: int, db: Session = Depends(get_db)):
    job = get_import_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


@router.get("/import/{job_id}/errors", response_model=List[ImportRowError])
def get_import_errors(job_id: int, db: Session = Depends(get_db)):
    return get_import_row_errors(db, job_id)


@router.post("/export", response_model=ExportJob)
def start_export_job(job_in: ExportJobCreate, db: Session = Depends(get_db)):
    job = create_export_job(db, job_in)
    # TODO: Trigger background export processing
    return job


@router.get("/export/{job_id}", response_model=ExportJob)
def get_export_job_status(job_id: int, db: Session = Depends(get_db)):
    job = get_export_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job


@router.get("/export/{job_id}/download")
def download_export_file(job_id: int, db: Session = Depends(get_db)):
    job = get_export_job(db, job_id)
    if not job or not job.out_filename:
        raise HTTPException(status_code=404, detail="Export file not found")
    export_path = get_export_path(job.out_filename)
    if not os.path.exists(export_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    return FileResponse(export_path, filename=job.out_filename)
