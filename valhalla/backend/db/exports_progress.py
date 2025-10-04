from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def mark_started(session: AsyncSession, job_id: int):
    await session.execute(
        text(
            """
      UPDATE export_jobs
      SET started_at = COALESCE(started_at, NOW()), status='processing', updated_at=NOW()
      WHERE id=:id
    """
        ),
        {"id": job_id},
    )
    await session.commit()


async def set_progress(
    session: AsyncSession, job_id: int, percent: int, message: str | None = None
):
    percent = max(0, min(100, int(percent)))
    await session.execute(
        text(
            """
      UPDATE export_jobs
      SET progress=:p, progress_msg=:m, updated_at=NOW()
      WHERE id=:id
    """
        ),
        {"id": job_id, "p": percent, "m": message},
    )
    await session.commit()


async def mark_finished(session: AsyncSession, job_id: int, status: str):
    # status should be 'completed' or 'failed'
    await session.execute(
        text(
            """
      UPDATE export_jobs
      SET finished_at = NOW(), status=:s, updated_at=NOW(), progress=CASE WHEN :s='completed' THEN 100 ELSE progress END
      WHERE id=:id
    """
        ),
        {"id": job_id, "s": status},
    )
    await session.commit()
