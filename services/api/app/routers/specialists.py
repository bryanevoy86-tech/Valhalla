from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.db import get_db
from app.specialists.models import HumanSpecialist, SpecialistCaseComment
from app.specialists.schemas import (
    HumanSpecialistCreate,
    HumanSpecialistRead,
    SpecialistCommentCreate,
    SpecialistCaseCommentRead,
)


router = APIRouter(prefix="/specialists", tags=["Human Specialist Bridge"])


@router.post("", response_model=HumanSpecialistRead)
def create_specialist(
    payload: HumanSpecialistCreate,
    db: Session = Depends(get_db)
):
    specialist = HumanSpecialist(
        name=payload.name,
        role=payload.role,
        email=payload.email,
        phone=payload.phone,
        notes=payload.notes,
        expertise=payload.expertise,
    )
    db.add(specialist)
    db.commit()
    db.refresh(specialist)
    return specialist


@router.get("/{specialist_id}", response_model=HumanSpecialistRead)
def get_specialist(
    specialist_id: UUID,
    db: Session = Depends(get_db)
):
    result = db.execute(
        select(HumanSpecialist).where(HumanSpecialist.id == specialist_id)
    )
    specialist = result.scalar_one_or_none()
    if not specialist:
        raise HTTPException(404, "Specialist not found")
    return specialist


@router.post("/{specialist_id}/comment/{case_id}", response_model=SpecialistCaseCommentRead)
def specialist_comment(
    specialist_id: UUID,
    case_id: UUID,
    payload: SpecialistCommentCreate,
    db: Session = Depends(get_db)
):
    # Verify specialist exists
    specialist_result = db.execute(
        select(HumanSpecialist).where(HumanSpecialist.id == specialist_id)
    )
    if not specialist_result.scalar_one_or_none():
        raise HTTPException(404, "Specialist not found")

    # Verify case exists
    from app.god.models import GodReviewCase, GodReviewEvent
    case_result = db.execute(
        select(GodReviewCase).where(GodReviewCase.id == case_id)
    )
    if not case_result.scalar_one_or_none():
        raise HTTPException(404, "Case not found")

    # Create comment
    comment = SpecialistCaseComment(
        specialist_id=specialist_id,
        case_id=case_id,
        comment=payload.comment,
        payload=payload.payload
    )
    db.add(comment)
    db.flush()

    # Also forward into GodCase event stream
    event = GodReviewEvent(
        case_id=case_id,
        actor="human",
        event_type="comment",
        message=payload.comment or "Specialist added comment",
        payload=payload.payload,
    )
    db.add(event)

    db.commit()
    db.refresh(comment)
    return comment
