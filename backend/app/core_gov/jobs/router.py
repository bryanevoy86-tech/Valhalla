import logging
import uuid
import datetime as dt
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..security.rbac import require_active_subscription, require_scopes
from ..security.devkey.deps import require_dev_key
from ..rate_limit.deps import rate_limit

logger = logging.getLogger("valhalla.jobs")

router = APIRouter(prefix="/jobs", tags=["Core: Jobs"])

class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"

class JobRecord(BaseModel):
    id: str
    name: str
    status: str = Field(default=JobStatus.PENDING)
    attempts: int = 0
    last_error: Optional[str] = None
    created_at_utc: str = Field(default_factory=lambda: dt.datetime.utcnow().isoformat() + "Z")
    updated_at_utc: str = Field(default_factory=lambda: dt.datetime.utcnow().isoformat() + "Z")
    payload: Dict[str, Any] = Field(default_factory=dict)

_JOBS: Dict[str, JobRecord] = {}

@router.post("/create", response_model=JobRecord)
def create(name: str, user=Depends(require_active_subscription)):
    jid = str(uuid.uuid4())
    job = JobRecord(id=jid, name=name)
    _JOBS[jid] = job
    logger.info("JOB_CREATED id=%s name=%s", jid, name)
    return job

@router.get("/{job_id}", response_model=JobRecord)
def read(job_id: str, user=Depends(require_active_subscription)):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/run", response_model=JobRecord)
def run(
    job_id: str,
    _key=Depends(require_dev_key),
    _sub=Depends(require_active_subscription),
    user=require_scopes("owner"),
    _rl=rate_limit("job_run", max_requests=30, window_seconds=60),
):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.RUNNING
    job.updated_at_utc = dt.datetime.utcnow().isoformat() + "Z"

    try:
        job.attempts += 1
        # placeholder work
        _ = True
        job.status = JobStatus.SUCCEEDED
        job.last_error = None
        logger.info("JOB_SUCCEEDED id=%s attempts=%s", job.id, job.attempts)
    except Exception as e:
        job.last_error = f"{type(e).__name__}: {e}"
        job.status = JobStatus.FAILED
        logger.exception("JOB_FAILED id=%s attempts=%s", job.id, job.attempts)
    finally:
        job.updated_at_utc = dt.datetime.utcnow().isoformat() + "Z"
        _JOBS[job.id] = job

    return job
