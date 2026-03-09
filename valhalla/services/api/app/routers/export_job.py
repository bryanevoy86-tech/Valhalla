"""
PACK UH: Export & Snapshot Job Engine Router
Prefix: /system/exports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.export_job import ExportJobCreate, ExportJobOut, ExportJobList
from app.services.export_job import (
    create_export_job,
    list_export_jobs,
    update_export_job_status,
)

router = APIRouter(prefix="/system/exports", tags=["Exports"])


@router.post("/", response_model=ExportJobOut)
def create_job_endpoint(
    payload: ExportJobCreate,
    db: Session = Depends(get_db),
):
    return create_export_job(db, payload)


@router.get("/", response_model=ExportJobList)
def list_jobs_endpoint(
    status: str | None = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    items = list_export_jobs(db, status=status, limit=limit)
    return ExportJobList(total=len(items), items=items)


@router.post("/{job_id}/status", response_model=ExportJobOut)
def update_job_status_endpoint(
    job_id: int,
    status: str = Query(...),
    storage_url: str | None = Query(None),
    error_message: str | None = Query(None),
    db: Session = Depends(get_db),
):
    job = update_export_job_status(
        db,
        job_id=job_id,
        status=status,
        storage_url=storage_url,
        error_message=error_message,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job
