from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from rq.job import Job

from ...core.config import get_settings
from ...core.rq import get_queue
from ...schemas.jobs import EnqueueOut, JobStatusOut
from ..deps import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/email", response_model=EnqueueOut)
def queue_email(
    to: list[str],
    subject: str,
    body: str,
    user=Depends(get_current_user),
):
    _ = user
    q = get_queue()
    job = q.enqueue("app.tasks.email_tasks.send_email_task", to, subject, body, None)
    return EnqueueOut(job_id=job.get_id())


@router.post("/lead/{lead_id}/enrich", response_model=EnqueueOut)
def queue_enrich_lead(lead_id: int, user=Depends(get_current_user)):
    _ = user
    q = get_queue()
    job = q.enqueue("app.tasks.lead_tasks.enrich_lead_task", lead_id)
    return EnqueueOut(job_id=job.get_id())


@router.get("/{job_id}", response_model=JobStatusOut)
def job_status(job_id: str, user=Depends(get_current_user)):
    _ = user
    s = get_settings()
    conn = Redis.from_url(s.RQ_REDIS_URL or s.REDIS_URL)
    job = Job.fetch(job_id, connection=conn)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    status = job.get_status()
    res = job.result if status == "finished" else None
    return JobStatusOut(id=job_id, status=status, result=res if isinstance(res, dict) else None)
