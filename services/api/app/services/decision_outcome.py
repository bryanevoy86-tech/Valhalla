"""
PACK CL9-10: Decision Outcome Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.decision_outcome import DecisionOutcome
from app.schemas.decision_outcome import DecisionOutcomeCreate


def create_decision_outcome(
    db: Session,
    payload: DecisionOutcomeCreate,
) -> DecisionOutcome:
    obj = DecisionOutcome(
        **payload.model_dump(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_decision_outcomes(
    db: Session,
    domain: Optional[str] = None,
    decision_id: Optional[str] = None,
    limit: int = 200,
) -> List[DecisionOutcome]:
    q = db.query(DecisionOutcome)
    if domain:
        q = q.filter(DecisionOutcome.domain == domain)
    if decision_id:
        q = q.filter(DecisionOutcome.decision_id == decision_id)
    return q.order_by(DecisionOutcome.created_at.desc()).limit(limit).all()
