from typing import List

from backend.db.session import get_session
from backend.schemas.webhooks import EventOut, WebhookIn, WebhookOut
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookOut)
async def create_webhook(body: WebhookIn, session: AsyncSession = Depends(get_session)):
    row = (
        (
            await session.execute(
                text(
                    """
      INSERT INTO export_webhooks (name, url, secret, is_active, events)
      VALUES (:name, :url, :secret, :is_active, :events)
      RETURNING id, name, url, secret, is_active, events
    """
                ),
                body.model_dump(),
            )
        )
        .mappings()
        .first()
    )
    await session.commit()
    return dict(row)


@router.get("", response_model=List[WebhookOut])
async def list_webhooks(session: AsyncSession = Depends(get_session)):
    rows = (
        (
            await session.execute(
                text(
                    """
      SELECT id, name, url, secret, is_active, events
      FROM export_webhooks ORDER BY created_at DESC
    """
                )
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


@router.patch("/{id}", response_model=WebhookOut)
async def update_webhook(id: int, body: WebhookIn, session: AsyncSession = Depends(get_session)):
    row = (
        (
            await session.execute(
                text(
                    """
      UPDATE export_webhooks
      SET name=:name, url=:url, secret=:secret, is_active=:is_active, events=:events, updated_at=NOW()
      WHERE id=:id
      RETURNING id, name, url, secret, is_active, events
    """
                ),
                {**body.model_dump(), "id": id},
            )
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    await session.commit()
    return dict(row)


@router.get("/events", response_model=List[EventOut])
async def list_events(
    limit: int = Query(50, ge=1, le=200), session: AsyncSession = Depends(get_session)
):
    rows = (
        (
            await session.execute(
                text(
                    """
      SELECT id, event_type, job_id, payload, status, attempts, last_error
      FROM export_events ORDER BY created_at DESC LIMIT :limit
    """
                ),
                {"limit": limit},
            )
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]
