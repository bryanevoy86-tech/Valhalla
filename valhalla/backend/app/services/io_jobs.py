import os
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.io_job import ExportJob, ImportJob, ImportRowError
from ..schemas.io_job import (
    ExportJobCreate,
    ExportJobUpdate,
    ImportJobCreate,
    ImportJobUpdate,
    ImportRowErrorCreate,
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../data/uploads")
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "../../data/exports")


# --- ImportJob helpers ---
def create_import_job(db: Session, job_in: ImportJobCreate) -> ImportJob:
    job = ImportJob(**job_in.dict())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_import_job(db: Session, job: ImportJob, job_in: ImportJobUpdate) -> ImportJob:
    for field, value in job_in.dict(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


def log_import_row_error(db: Session, error_in: ImportRowErrorCreate) -> ImportRowError:
    error = ImportRowError(**error_in.dict())
    db.add(error)
    db.commit()
    db.refresh(error)
    return error


def get_import_job(db: Session, job_id: int) -> Optional[ImportJob]:
    return db.query(ImportJob).filter(ImportJob.id == job_id).first()


def get_import_row_errors(db: Session, job_id: int) -> List[ImportRowError]:
    return db.query(ImportRowError).filter(ImportRowError.job_id == job_id).all()


# --- ExportJob helpers ---
def create_export_job(db: Session, job_in: ExportJobCreate) -> ExportJob:
    job = ExportJob(**job_in.dict())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_export_job(db: Session, job: ExportJob, job_in: ExportJobUpdate) -> ExportJob:
    for field, value in job_in.dict(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


def get_export_job(db: Session, job_id: int) -> Optional[ExportJob]:
    return db.query(ExportJob).filter(ExportJob.id == job_id).first()


# --- File helpers ---
def get_upload_path(filename: str) -> str:
    return os.path.join(UPLOAD_DIR, filename)


def get_export_path(filename: str) -> str:
    return os.path.join(EXPORT_DIR, filename)
