from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_limits_row(session: AsyncSession, org_id: int):
    await session.execute(
        text(
            """
      INSERT INTO export_limits (org_id) VALUES (:org_id)
      ON CONFLICT (org_id) DO NOTHING
    """
        ),
        {"org_id": org_id},
    )
    await session.commit()


async def check_daily_quota(
    session: AsyncSession, org_id: int, count_needed: int
) -> Tuple[bool, int, int]:
    row = (
        (
            await session.execute(
                text(
                    """
      WITH q AS (
        SELECT COALESCE((SELECT daily_quota FROM export_limits WHERE org_id=:org_id), 2000) AS quota
      )
      SELECT quota,
             (SELECT COUNT(*) FROM export_jobs WHERE org_id=:org_id AND created_at::date = NOW()::date) AS used
      FROM q
    """
                ),
                {"org_id": org_id},
            )
        )
        .mappings()
        .first()
    )
    quota, used = row["quota"], row["used"]
    return (used + count_needed) <= quota, used, quota


async def create_batch(
    session: AsyncSession,
    org_id: int,
    name: str | None,
    job_type: str,
    params_template: dict | None,
    total: int,
) -> int:
    row = (
        await session.execute(
            text(
                """
      INSERT INTO export_batches (org_id, name, job_type, params_template, total_jobs, enqueued_jobs)
      VALUES (:org_id, :name, :job_type, CAST(:tmpl AS JSONB), :total, 0)
      RETURNING id
    """
            ),
            {
                "org_id": org_id,
                "name": name,
                "job_type": job_type,
                "tmpl": params_template or {},
                "total": total,
            },
        )
    ).first()
    await session.commit()
    return row[0]


async def bulk_enqueue(
    session: AsyncSession,
    org_id: int,
    batch_id: int,
    job_type: str,
    items: List[dict],
    priority: int = 100,
) -> List[int]:
    ids: List[int] = []
    for p in items:
        r = (
            await session.execute(
                text(
                    """
          INSERT INTO export_jobs (org_id, batch_id, job_type, params, status, attempts, max_attempts, next_run_at, priority)
          VALUES (:org_id, :batch_id, :job_type, CAST(:params AS JSONB), 'queued', 0, 3, NOW(), :priority)
          RETURNING id
        """
                ),
                {
                    "org_id": org_id,
                    "batch_id": batch_id,
                    "job_type": job_type,
                    "params": p,
                    "priority": priority,
                },
            )
        ).first()
        ids.append(r[0])
    await session.execute(
        text(
            "UPDATE export_batches SET enqueued_jobs = enqueued_jobs + :n, updated_at=NOW() WHERE id=:id"
        ),
        {"n": len(ids), "id": batch_id},
    )
    await session.commit()
    return ids


async def get_batch_summary(session: AsyncSession, batch_id: int) -> dict | None:
    row = (
        (
            await session.execute(
                text(
                    """
      SELECT b.id, b.org_id, b.name, b.job_type, b.total_jobs, b.enqueued_jobs, b.created_at, b.updated_at,
             COALESCE(j.total,0) AS jobs_total,
             COALESCE(j.c_completed,0) AS completed,
             COALESCE(j.c_failed,0) AS failed,
             COALESCE(j.c_processing,0) AS processing,
             COALESCE(j.c_retrying,0) AS retrying,
             COALESCE(j.c_queued,0) AS queued
      FROM export_batches b
      LEFT JOIN (
        SELECT batch_id,
               COUNT(*) total,
               COUNT(*) FILTER (WHERE status='completed') c_completed,
               COUNT(*) FILTER (WHERE status='failed')    c_failed,
               COUNT(*) FILTER (WHERE status='processing') c_processing,
               COUNT(*) FILTER (WHERE status='retrying')   c_retrying,
               COUNT(*) FILTER (WHERE status='queued')     c_queued
        FROM export_jobs
        WHERE batch_id=:id
        GROUP BY batch_id
      ) j ON j.batch_id = b.id
      WHERE b.id=:id
    """
                ),
                {"id": batch_id},
            )
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None
