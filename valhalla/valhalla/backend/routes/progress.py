import asyncio
import json

from backend.db.session import get_session
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/exports", tags=["exports"])


async def _fetch_job(session: AsyncSession, job_id: int):
    row = (
        (
            await session.execute(
                text(
                    """
      SELECT id, status, progress, progress_msg, attempts, max_attempts, last_error
      FROM export_jobs WHERE id=:id
    """
                ),
                {"id": job_id},
            )
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


@router.get("/{job_id}/progress/stream")
async def stream_progress(job_id: int, session: AsyncSession = Depends(get_session)):
    job = await _fetch_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_gen():
        # Send initial snapshot immediately
        payload = {"type": "snapshot", "data": job}
        yield f"event: snapshot\ndata: {json.dumps(payload)}\n\n"

        # Poll every 1s until terminal
        while True:
            await asyncio.sleep(1)
            j = await _fetch_job(session, job_id)
            if not j:
                yield f"event: error\ndata: {json.dumps({'error':'missing'})}\n\n"
                break

            yield f"event: tick\ndata: {json.dumps({'type':'tick','data': j})}\n\n"

            if j["status"] in ("completed", "failed"):
                yield f"event: done\ndata: {json.dumps({'type':'done','data': j})}\n\n"
                break

    return StreamingResponse(event_gen(), media_type="text/event-stream")
