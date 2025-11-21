from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.god.models import (
    GodReviewCase,
    GodReviewEvent,
    GodCaseStatus,
    GodCaseOutcome,
)
from app.models.god_case import GodCase
from app.schemas.god_case import (
    GodCaseCreate,
    GodCaseRead,
    GodCaseUpdate,
)
from app.god.schemas import (
    GodReviewCaseCreate,
    GodReviewCaseRead,
    GodReviewCaseListItem,
    GodReviewCaseUpdate,
    GodReviewEventCreate,
    GodReviewEventRead,
    DualGodSnapshot,
)

router = APIRouter(prefix="/god-cases", tags=["Dual-God Review Cases"])


# --- helpers -----------------------------------------------------------------


def _get_case_or_404(
    case_id: UUID,
    db: Session,
) -> GodReviewCase:
    result = db.execute(
        select(GodReviewCase).where(GodReviewCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="God review case not found")
    return case


# --- endpoints ---------------------------------------------------------------


@router.post(
    "",
    response_model=GodReviewCaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_god_case(
    payload: GodReviewCaseCreate,
    db: Session = Depends(get_db),
) -> GodReviewCaseRead:
    # this is usually Heimdall creating the case with his first suggestion
    case = GodReviewCase(
        subject_type=payload.subject_type,
        subject_reference=payload.subject_reference,
        title=payload.title,
        description=payload.description,
        status=GodCaseStatus.OPEN,
        heimdall_summary=payload.heimdall_summary,
        heimdall_payload=payload.heimdall_payload,
        final_outcome=GodCaseOutcome.UNKNOWN,
    )
    db.add(case)
    db.flush()
    db.refresh(case)

    # log initial event
    initial_event = GodReviewEvent(
        case_id=case.id,
        actor="heimdall",
        event_type="suggestion",
        message=payload.heimdall_summary or "Heimdall created case.",
        payload=payload.heimdall_payload,
    )
    db.add(initial_event)

    db.commit()
    db.refresh(case)
    return case


@router.get(
    "",
    response_model=List[GodReviewCaseListItem],
)
def list_god_cases(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    subject_type: Optional[str] = None,
    final_outcome: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> List[GodReviewCaseListItem]:
    stmt = select(GodReviewCase).order_by(GodReviewCase.created_at.desc())

    if status_filter:
        stmt = stmt.where(GodReviewCase.status == status_filter)
    if subject_type:
        stmt = stmt.where(GodReviewCase.subject_type == subject_type)
    if final_outcome:
        stmt = stmt.where(GodReviewCase.final_outcome == final_outcome)

    stmt = stmt.limit(limit).offset(offset)

    result = db.execute(stmt)
    cases = result.scalars().all()

    return [
        GodReviewCaseListItem(
            id=c.id,
            created_at=c.created_at,
            subject_type=c.subject_type,
            subject_reference=c.subject_reference,
            title=c.title,
            status=c.status,
            final_outcome=c.final_outcome,
        )
        for c in cases
    ]


@router.get(
    "/{case_id}",
    response_model=GodReviewCaseRead,
)
def get_god_case(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> GodReviewCaseRead:
    case = _get_case_or_404(case_id, db)
    return case


@router.patch(
    "/{case_id}",
    response_model=GodReviewCaseRead,
)
def update_god_case(
    case_id: UUID,
    payload: GodReviewCaseUpdate,
    db: Session = Depends(get_db),
) -> GodReviewCaseRead:
    case = _get_case_or_404(case_id, db)

    if payload.status is not None:
        case.status = payload.status
    if payload.final_outcome is not None:
        case.final_outcome = payload.final_outcome
    if payload.final_notes is not None:
        case.final_notes = payload.final_notes
    if payload.loki_summary is not None:
        case.loki_summary = payload.loki_summary
    if payload.loki_payload is not None:
        case.loki_payload = payload.loki_payload
    if payload.human_summary is not None:
        case.human_summary = payload.human_summary
    if payload.human_payload is not None:
        case.human_payload = payload.human_payload

    db.commit()
    db.refresh(case)
    return case


@router.post(
    "/{case_id}/events",
    response_model=GodReviewEventRead,
    status_code=status.HTTP_201_CREATED,
)
def add_event_to_case(
    case_id: UUID,
    payload: GodReviewEventCreate,
    db: Session = Depends(get_db),
) -> GodReviewEventRead:
    _ = _get_case_or_404(case_id, db)

    event = GodReviewEvent(
        case_id=case_id,
        actor=payload.actor,
        event_type=payload.event_type,
        message=payload.message,
        payload=payload.payload,
    )
    db.add(event)
    db.flush()
    db.refresh(event)
    db.commit()
    db.refresh(event)
    return event


@router.get(
    "/{case_id}/events",
    response_model=List[GodReviewEventRead],
)
def list_case_events(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> List[GodReviewEventRead]:
    _ = _get_case_or_404(case_id, db)

    result = db.execute(
        select(GodReviewEvent)
        .where(GodReviewEvent.case_id == case_id)
        .order_by(GodReviewEvent.created_at.asc())
    )
    events = result.scalars().all()
    return events


@router.get(
    "/{case_id}/snapshot",
    response_model=DualGodSnapshot,
)
def get_dual_god_snapshot(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> DualGodSnapshot:
    case = _get_case_or_404(case_id, db)

    return DualGodSnapshot(
        case_id=case.id,
        subject_type=case.subject_type,
        subject_reference=case.subject_reference,
        title=case.title,
        heimdall_summary=case.heimdall_summary,
        loki_summary=case.loki_summary,
        human_summary=case.human_summary,
        final_outcome=case.final_outcome,
        status=case.status,
    )


# ---------------------------------------------------------------------------
# Pack 83: GodCase Registry CRUD (prefixed under /registry to avoid collisions)
# ---------------------------------------------------------------------------


@router.post("/registry", response_model=GodCaseRead, status_code=status.HTTP_201_CREATED)
def create_god_case_registry(
    payload: GodCaseCreate,
    db: Session = Depends(get_db),
) -> GodCaseRead:
    obj = GodCase(
        title=payload.title,
        source_type=payload.source_type,
        status=payload.status,
        payload=payload.payload,
        heimdall_output=payload.heimdall_output,
        loki_output=payload.loki_output,
        arbitration_output=payload.arbitration_output,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/registry/{case_id}", response_model=GodCaseRead)
def get_god_case_registry(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> GodCaseRead:
    result = db.execute(select(GodCase).where(GodCase.id == case_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="GodCase not found")
    return obj


@router.get("/registry", response_model=List[GodCaseRead])
def list_god_case_registry(
    status: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[GodCaseRead]:
    stmt = select(GodCase)
    if status:
        stmt = stmt.where(GodCase.status == status)
    if source_type:
        stmt = stmt.where(GodCase.source_type == source_type)
    stmt = stmt.order_by(GodCase.created_at.desc())
    result = db.execute(stmt)
    return result.scalars().all()


@router.patch("/registry/{case_id}", response_model=GodCaseRead)
def update_god_case_registry(
    case_id: UUID,
    payload: GodCaseUpdate,
    db: Session = Depends(get_db),
) -> GodCaseRead:
    result = db.execute(select(GodCase).where(GodCase.id == case_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="GodCase not found")
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)
    obj.updated_at = datetime.utcnow()
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
