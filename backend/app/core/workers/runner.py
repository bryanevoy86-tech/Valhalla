from __future__ import annotations

import time
from typing import Callable

from app.core.exports.service import list_jobs, update_job

# Minimal worker loop.
# Later: swap to Celery/RQ/Arq, but this keeps you moving NOW.

SLEEP_SECONDS = 2.0


def process_export_job(job_id: str):
    # TODO: replace with real export logic.
    # For now, mark done with a placeholder URL.
    update_job(job_id, status="running")
    time.sleep(1.0)
    update_job(job_id, status="done", result_url=f"/downloads/{job_id}.csv")


def run_once():
    for job in list_jobs():
        if job.status == "queued":
            try:
                process_export_job(job.id)
            except Exception as e:
                update_job(job.id, status="failed", error=str(e))


def run_forever():
    while True:
        run_once()
        time.sleep(SLEEP_SECONDS)
