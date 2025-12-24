from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict

from .schemas import ExportJobOut, ExportJobCreate

# In-memory store so you can build NOW without DB.
# Swap to DB later (same interface).
_JOBS: Dict[str, ExportJobOut] = {}


def create_job(req: ExportJobCreate) -> ExportJobOut:
    now = datetime.now(timezone.utc)
    job_id = uuid4().hex
    job = ExportJobOut(
        id=job_id,
        status="queued",
        export_type=req.export_type,
        created_at=now,
        updated_at=now,
        result_url=None,
        error=None,
    )
    _JOBS[job_id] = job
    return job


def get_job(job_id: str) -> ExportJobOut | None:
    return _JOBS.get(job_id)


def list_jobs() -> list[ExportJobOut]:
    return sorted(_JOBS.values(), key=lambda j: j.created_at, reverse=True)


def update_job(job_id: str, **kwargs) -> ExportJobOut | None:
    job = _JOBS.get(job_id)
    if not job:
        return None
    data = job.model_dump()
    data.update(kwargs)
    data["updated_at"] = datetime.now(timezone.utc)
    new_job = ExportJobOut(**data)
    _JOBS[job_id] = new_job
    return new_job
