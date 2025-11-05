from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_export_jobs(
    session: AsyncSession,
    page: int,
    page_size: int,
    status: Optional[str],
    q: Optional[str],
) -> Tuple[int, List[dict]]:
    where = []
    params = {}
    if status:
        where.append("status = :status")
        params["status"] = status
    if q:
        where.append("(job_type ILIKE :q OR COALESCE(file_path,'') ILIKE :q)")
        params["q"] = f"%{q}%"
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    count_sql = text(f"SELECT COUNT(*) FROM export_jobs {where_sql}")
    total = (await session.execute(count_sql, params)).scalar()

    offset = (page - 1) * page_size
    rows_sql = text(
        f"""
      SELECT id, job_type, params, file_path, file_type, status, attempts, max_attempts,
             last_error, next_run_at, created_at, updated_at
      FROM export_jobs
      {where_sql}
      ORDER BY created_at DESC
      LIMIT :limit OFFSET :offset
    """
    )
    params.update({"limit": page_size, "offset": offset})
    rows = (await session.execute(rows_sql, params)).mappings().all()
    return total, [dict(r) for r in rows]


async def schedule_retry(session: AsyncSession, job_id: int) -> Optional[dict]:
    row = (
        (await session.execute(text("SELECT * FROM export_jobs WHERE id = :id"), {"id": job_id}))
        .mappings()
        .first()
    )
    if not row:
        return None
    if row["attempts"] >= row["max_attempts"]:
        return dict(row)
    upd = text(
        """
      UPDATE export_jobs
      SET status='queued', next_run_at=NOW(), updated_at=NOW()
      WHERE id=:id
      RETURNING id, job_type, params, file_path, file_type, status, attempts, max_attempts,
                last_error, next_run_at, created_at, updated_at
    """
    )
    newrow = (await session.execute(upd, {"id": job_id})).mappings().first()
    await session.commit()
    return dict(newrow)
