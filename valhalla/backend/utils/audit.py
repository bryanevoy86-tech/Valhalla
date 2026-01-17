from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def log_event(
    session: AsyncSession,
    *,
    org_id: int,
    action: str,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> int:
    row = (
        await session.execute(
            text(
                """
          INSERT INTO audit_events (org_id, user_id, action, resource, metadata)
          VALUES (:org_id, :user_id, :action, :resource, CAST(:metadata AS JSONB))
          RETURNING id
        """
            ),
            {
                "org_id": org_id,
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "metadata": metadata or {},
            },
        )
    ).first()
    await session.commit()
    return row[0]
