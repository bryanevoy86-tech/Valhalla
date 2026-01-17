"""
PACK TI: Financial Stress Early Warning Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.pack_st import FinancialIndicator, FinancialStressEvent
from app.schemas.financial_stress import (
    FinancialIndicatorCreate,
    FinancialStressEventCreate,
)


def create_indicator(
    db: Session,
    payload: FinancialIndicatorCreate,
) -> FinancialIndicator:
    obj = FinancialIndicator(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_indicators(db: Session, active_only: bool = False) -> List[FinancialIndicator]:
    q = db.query(FinancialIndicator)
    if active_only:
        q = q.filter(FinancialIndicator.active.is_(True))
    return q.order_by(FinancialIndicator.name.asc()).all()


def record_stress_event(
    db: Session,
    payload: FinancialStressEventCreate,
) -> Optional[FinancialStressEvent]:
    indicator = (
        db.query(FinancialIndicator)
        .filter(FinancialIndicator.id == payload.indicator_id)
        .first()
    )
    if not indicator:
        return None
    obj = FinancialStressEvent(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def resolve_stress_event(db: Session, event_id: int) -> Optional[FinancialStressEvent]:
    obj = db.query(FinancialStressEvent).filter(FinancialStressEvent.id == event_id).first()
    if not obj:
        return None
    obj.resolved = True
    db.commit()
    db.refresh(obj)
    return obj
