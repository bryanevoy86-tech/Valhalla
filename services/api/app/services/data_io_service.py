"""PACK 74: Data IO Service
Service layer for import/export operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.data_io import ImportJob, ExportJob


def queue_import_job(db: Session, target_model: str, file_path: str) -> ImportJob:
    """Queue a new import job."""
    job = ImportJob(
        target_model=target_model,
        file_path=file_path,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_import_status(
    db: Session,
    job_id: int,
    status: str,
    error_report: Optional[str] = None,
) -> ImportJob:
    """Update import job status."""
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if job:
        job.status = status
        if error_report is not None:
            job.error_report = error_report
        db.commit()
        db.refresh(job)
    return job


def list_import_jobs(db: Session) -> list:
    """List all import jobs."""
    return db.query(ImportJob).order_by(ImportJob.id.desc()).all()


def queue_export_job(db: Session, source_model: str, filter_payload: Optional[str]) -> ExportJob:
    """Queue a new export job."""
    job = ExportJob(
        source_model=source_model,
        filter_payload=filter_payload,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_export_status(
    db: Session,
    job_id: int,
    status: str,
    download_path: Optional[str] = None,
) -> ExportJob:
    """Update export job status."""
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if job:
        job.status = status
        if download_path is not None:
            job.download_path = download_path
        db.commit()
        db.refresh(job)
    return job


def list_export_jobs(db: Session) -> list:
    """List all export jobs."""
    return db.query(ExportJob).order_by(ExportJob.id.desc()).all()
