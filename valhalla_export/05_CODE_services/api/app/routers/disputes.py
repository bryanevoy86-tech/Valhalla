from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.disputes import Dispute
from app.schemas.disputes import DisputeCreate, DisputeUpdate, DisputeRead

router = APIRouter(prefix="/disputes", tags=["Disputes & Resolutions"])


@router.post("/", response_model=DisputeRead)
def create_dispute(
    payload: DisputeCreate,
    db: Session = Depends(get_db),
):
    dispute = Dispute(
        case_id=payload.case_id,
        human_role=payload.human_role,
        human_specialist_id=payload.human_specialist_id,
        topic=payload.topic,
        description=payload.description,
        human_position=payload.human_position,
        heimdall_position=payload.heimdall_position,
        loki_position=payload.loki_position,
        status="open",
    )

    db.add(dispute)
    db.flush()

    from app.god.models import GodReviewEvent
    event = GodReviewEvent(
        case_id=payload.case_id,
        actor="system",
        event_type="dispute_opened",
        message=payload.topic or "Dispute opened",
        payload={
            "dispute_id": str(dispute.id),
            "human_role": payload.human_role,
        },
    )
    db.add(event)

    db.commit()
    db.refresh(dispute)
    return dispute


@router.patch("/{dispute_id}", response_model=DisputeRead)
def update_dispute(
    dispute_id: UUID,
    payload: DisputeUpdate,
    db: Session = Depends(get_db),
):
    result = db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if payload.status is not None:
        dispute.status = payload.status
    if payload.human_position is not None:
        dispute.human_position = payload.human_position
    if payload.heimdall_position is not None:
        dispute.heimdall_position = payload.heimdall_position
    if payload.loki_position is not None:
        dispute.loki_position = payload.loki_position
    if payload.resolution_summary is not None:
        dispute.resolution_summary = payload.resolution_summary
    if payload.resolution_metadata is not None:
        dispute.resolution_metadata = payload.resolution_metadata

    from datetime import datetime as _dt
    dispute.updated_at = _dt.utcnow()

    db.flush()

    if payload.status in {"resolved", "user_override"}:
        event_type = (
            "dispute_resolved" if payload.status == "resolved" else "dispute_user_override"
        )
        from app.god.models import GodReviewEvent
        event = GodReviewEvent(
            case_id=dispute.case_id,
            actor="system",
            event_type=event_type,
            message=payload.resolution_summary or "Dispute updated",
            payload={
                "dispute_id": str(dispute.id),
                "status": dispute.status,
            },
        )
        db.add(event)

    db.commit()
    db.refresh(dispute)
    return dispute


@router.get("/by-case/{case_id}", response_model=List[DisputeRead])
def list_disputes_for_case(
    case_id: UUID,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Dispute).where(Dispute.case_id == case_id)
    if status:
        stmt = stmt.where(Dispute.status == status)
    stmt = stmt.order_by(Dispute.created_at.desc())

    result = db.execute(stmt)
    disputes = result.scalars().all()
    return list(disputes)


@router.get("/{dispute_id}", response_model=DisputeRead)
def get_dispute(
    dispute_id: UUID,
    db: Session = Depends(get_db),
):
    result = db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute
