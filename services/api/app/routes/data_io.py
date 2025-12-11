"""PACK 74: Data IO Router
API endpoints for data import/export operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.data_io_service import (
    queue_import_job,
    update_import_status,
    list_import_jobs,
    queue_export_job,
    update_export_status,
    list_export_jobs,
)
from app.schemas.data_io import ImportJobOut, ExportJobOut

router = APIRouter(prefix="/data-io", tags=["Data Import/Export"])


@router.post("/import", response_model=ImportJobOut)
def new_import_job(
    target_model: str,
    file_path: str,
    db: Session = Depends(get_db),
):
    """Queue a new import job."""
    return queue_import_job(db, target_model, file_path)


@router.post("/import/{job_id}/status", response_model=ImportJobOut)
def set_import_status(
    job_id: int,
    status: str,
    error_report: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update import job status."""
    return update_import_status(db, job_id, status, error_report)


@router.get("/import", response_model=list[ImportJobOut])
def get_import_jobs(db: Session = Depends(get_db)):
    """Get all import jobs."""
    return list_import_jobs(db)


@router.post("/export", response_model=ExportJobOut)
def new_export_job(
    source_model: str,
    filter_payload: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Queue a new export job."""
    return queue_export_job(db, source_model, filter_payload)


@router.post("/export/{job_id}/status", response_model=ExportJobOut)
def set_export_status(
    job_id: int,
    status: str,
    download_path: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update export job status."""
    return update_export_status(db, job_id, status, download_path)


@router.get("/export", response_model=list[ExportJobOut])
def get_export_jobs(db: Session = Depends(get_db)):
    """Get all export jobs."""
    return list_export_jobs(db)
