from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.underwriter_assessment import UnderwriterAssessment
from app.schemas.underwriter import (
    UnderwriterAssessmentCreate,
    UnderwriterAssessmentUpdate,
    UnderwriterAssessmentOut,
)

router = APIRouter()

@router.post("/", response_model=UnderwriterAssessmentOut)
def create_assessment(
    payload: UnderwriterAssessmentCreate,
    db: Session = Depends(get_db),
):
    obj = UnderwriterAssessment(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[UnderwriterAssessmentOut])
def list_assessments(
    deal_id: int | None = None,
    decision: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(UnderwriterAssessment)
    if deal_id is not None:
        query = query.filter(UnderwriterAssessment.deal_id == deal_id)
    if decision is not None:
        query = query.filter(UnderwriterAssessment.decision == decision)
    return query.all()

@router.put("/{assessment_id}", response_model=UnderwriterAssessmentOut)
def update_assessment(
    assessment_id: int,
    payload: UnderwriterAssessmentUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(UnderwriterAssessment).get(assessment_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
