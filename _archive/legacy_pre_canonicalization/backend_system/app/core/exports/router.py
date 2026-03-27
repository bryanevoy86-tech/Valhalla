from __future__ import annotations

from fastapi import APIRouter, HTTPException
from .schemas import ExportJobCreate
from .service import create_job, get_job, list_jobs

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("")
def create(req: ExportJobCreate):
    return create_job(req).model_dump()


@router.get("/{job_id}")
def get(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job.model_dump()


@router.get("")
def list_all():
    return [j.model_dump() for j in list_jobs()]


@router.get("/poll/since")
def poll_since(_: str = ""):
    # Placeholder signature that works with WeWeb polling patterns.
    # Replace with "since" time filtering when DB-backed.
    return [j.model_dump() for j in list_jobs()]
