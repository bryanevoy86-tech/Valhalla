from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.god_verdicts import GodVerdict
from app.schemas.god_verdicts import GodVerdictCreate, GodVerdictRead

router = APIRouter(prefix="/god-verdicts", tags=["Dual-God Verdicts"])


@router.post("/", response_model=GodVerdictRead)
def create_god_verdict(
    payload: GodVerdictCreate,
    db: Session = Depends(get_db),
):
    verdict = GodVerdict(
        case_id=payload.case_id,
        trigger=payload.trigger,
        heimdall_summary=payload.heimdall_summary,
        heimdall_recommendation=payload.heimdall_recommendation,
        heimdall_confidence=payload.heimdall_confidence,
        loki_summary=payload.loki_summary,
        loki_recommendation=payload.loki_recommendation,
        loki_confidence=payload.loki_confidence,
        consensus=payload.consensus,
        risk_level=payload.risk_level,
        notes=payload.notes,
        metadata_json=payload.metadata,
    )

    db.add(verdict)
    db.flush()

    # Log into the God Case event stream as well
    from app.god.models import GodReviewEvent

    event = GodReviewEvent(
        case_id=payload.case_id,
        actor="system",
        event_type="dual_god_verdict",
        message=payload.notes or "Dual-god verdict snapshot created",
        payload={
            "verdict_id": str(verdict.id),
            "trigger": payload.trigger,
            "consensus": payload.consensus,
            "risk_level": payload.risk_level,
        },
    )
    db.add(event)

    db.commit()
    db.refresh(verdict)
    return verdict


@router.get("/by-case/{case_id}", response_model=List[GodVerdictRead])
def list_verdicts_for_case(
    case_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(GodVerdict)
        .where(GodVerdict.case_id == case_id)
        .order_by(GodVerdict.created_at.desc())
        .limit(limit)
    )
    verdicts = result.scalars().all()
    return list(verdicts)


@router.get("/{verdict_id}", response_model=GodVerdictRead)
def get_verdict(
    verdict_id: UUID,
    db: Session = Depends(get_db),
):
    result = db.execute(
        select(GodVerdict).where(GodVerdict.id == verdict_id)
    )
    verdict = result.scalar_one_or_none()
    if not verdict:
        raise HTTPException(status_code=404, detail="Verdict not found")
    return verdict
