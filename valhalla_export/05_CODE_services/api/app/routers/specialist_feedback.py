from __future__ import annotations

from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.god_case import GodCase
from app.models.specialist_feedback import SpecialistFeedback
from app.schemas.specialist_feedback import (
    SpecialistFeedbackCreate,
    SpecialistFeedbackRead,
)

router = APIRouter(prefix="/god-cases", tags=["Specialist Feedback"])


@router.post("/{case_id}/feedback", response_model=SpecialistFeedbackRead, status_code=status.HTTP_201_CREATED)
def add_feedback(
    case_id: UUID,
    payload: SpecialistFeedbackCreate,
    db: Session = Depends(get_db),
) -> SpecialistFeedbackRead:
    result = db.execute(select(GodCase).where(GodCase.id == case_id))
    god_case = result.scalar_one_or_none()
    if not god_case:
        raise HTTPException(status_code=404, detail="GodCase not found")

    fb = SpecialistFeedback(
        god_case_id=case_id,
        specialist_role=payload.specialist_role,
        specialist_name=payload.specialist_name,
        notes=payload.notes,
        suggested_changes=payload.suggested_changes,
    )
    god_case.needs_rescan = True
    god_case.last_specialist_feedback_at = datetime.utcnow()
    db.add(fb)
    db.add(god_case)
    db.commit()
    db.refresh(fb)
    return fb


@router.get("/{case_id}/feedback", response_model=List[SpecialistFeedbackRead])
def list_feedback(
    case_id: UUID,
    db: Session = Depends(get_db),
) -> List[SpecialistFeedbackRead]:
    result_case = db.execute(select(GodCase).where(GodCase.id == case_id))
    god_case = result_case.scalar_one_or_none()
    if not god_case:
        raise HTTPException(status_code=404, detail="GodCase not found")
    result = db.execute(
        select(SpecialistFeedback)
        .where(SpecialistFeedback.god_case_id == case_id)
        .order_by(SpecialistFeedback.created_at.desc())
    )
    return result.scalars().all()
