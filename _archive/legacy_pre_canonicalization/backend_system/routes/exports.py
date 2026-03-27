from backend.db.exports_dao import list_export_jobs, schedule_retry
from backend.db.session import get_session
from backend.schemas.exports import ExportJobList, ExportJobOut
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("", response_model=ExportJobList)
async def list_exports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    q: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    total, rows = await list_export_jobs(session, page, page_size, status, q)
    return {"total": total, "page": page, "page_size": page_size, "items": rows}


@router.post("/{job_id}/retry", response_model=ExportJobOut)
async def retry_export(
    job_id: int,
    session: AsyncSession = Depends(get_session),
):
    row = await schedule_retry(session, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Export job not found")
    if row["attempts"] >= row["max_attempts"]:
        raise HTTPException(status_code=409, detail="Max attempts reached; cannot retry")
    return row
