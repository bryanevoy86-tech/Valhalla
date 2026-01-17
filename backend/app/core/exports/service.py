from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict
from pathlib import Path

from .schemas import ExportJobOut, ExportJobCreate

# File-based job store for worker process coordination.
# Later: swap to Redis/DB (same interface).
import sys
_backend_dir = Path(__file__).parent.parent.parent.parent  # go from service.py to backend/
JOBS_FILE = _backend_dir / "jobs_store.json"

def _load_jobs() -> Dict[str, dict]:
    """Load jobs from file or return empty dict."""
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_jobs(jobs: Dict[str, dict]) -> None:
    """Save jobs to file."""
    try:
        # Ensure parent directory exists
        JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving jobs to {JOBS_FILE}: {e}", file=sys.stderr)


def create_job(req: ExportJobCreate) -> ExportJobOut:
    jobs = _load_jobs()
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
    # Store as dict with ISO strings for JSON serialization
    job_dict = job.model_dump()
    job_dict['created_at'] = now.isoformat()
    job_dict['updated_at'] = now.isoformat()
    jobs[job_id] = job_dict
    _save_jobs(jobs)
    return job


def get_job(job_id: str) -> ExportJobOut | None:
    jobs = _load_jobs()
    job_data = jobs.get(job_id)
    if not job_data:
        return None
    # Ensure timestamps are properly typed
    if isinstance(job_data.get('created_at'), str):
        job_data['created_at'] = datetime.fromisoformat(job_data['created_at'])
    if isinstance(job_data.get('updated_at'), str):
        job_data['updated_at'] = datetime.fromisoformat(job_data['updated_at'])
    return ExportJobOut(**job_data)


def list_jobs() -> list[ExportJobOut]:
    jobs = _load_jobs()
    job_list = []
    for job_data in jobs.values():
        # Ensure timestamps are properly typed
        if isinstance(job_data.get('created_at'), str):
            job_data['created_at'] = datetime.fromisoformat(job_data['created_at'])
        if isinstance(job_data.get('updated_at'), str):
            job_data['updated_at'] = datetime.fromisoformat(job_data['updated_at'])
        job_list.append(ExportJobOut(**job_data))
    return sorted(job_list, key=lambda j: j.created_at, reverse=True)


def update_job(job_id: str, **kwargs) -> ExportJobOut | None:
    jobs = _load_jobs()
    job_data = jobs.get(job_id)
    if not job_data:
        return None
    job_data.update(kwargs)
    job_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    jobs[job_id] = job_data
    _save_jobs(jobs)
    return ExportJobOut(**job_data)
