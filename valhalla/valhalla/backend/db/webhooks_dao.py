from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_active_webhooks(session: AsyncSession, event_type: str) -> List[dict]:
    rows = (
        (
            await session.execute(
                text(
                    """
      SELECT id, name, url, secret, events
      FROM export_webhooks
      WHERE is_active = TRUE AND (events @> ARRAY[:event_type]::TEXT[])
    """
                ),
                {"event_type": event_type},
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


async def enqueue_event(
    session: AsyncSession, event_type: str, job_id: int, payload: Dict[str, Any]
) -> int:
    row = (
        await session.execute(
            text(
                """
      INSERT INTO export_events (event_type, job_id, payload, status)
      VALUES (:type, :job_id, :payload::jsonb, 'queued')
      RETURNING id
    """
            ),
            {"type": event_type, "job_id": job_id, "payload": payload},
        )
    ).first()
    await session.commit()
    return row[0]
