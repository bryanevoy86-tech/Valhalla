"""
PACK CI2: Opportunity Engine Service
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityIn


def create_or_update_opportunity(
    db: Session,
    payload: OpportunityIn,
) -> Opportunity:
    obj: Optional[Opportunity] = None
    if payload.source_type and payload.source_id:
        obj = (
            db.query(Opportunity)
            .filter(
                Opportunity.source_type == payload.source_type,
                Opportunity.source_id == payload.source_id,
            )
            .first()
        )

    if not obj:
        obj = Opportunity(**payload.model_dump())
        db.add(obj)
    else:
        for field, value in payload.model_dump().items():
            setattr(obj, field, value)
        obj.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(obj)
    return obj


def list_opportunities(
    db: Session,
    source_type: Optional[str] = None,
    active_only: bool = True,
    limit: int = 200,
) -> List[Opportunity]:
    q = db.query(Opportunity)
    if source_type:
        q = q.filter(Opportunity.source_type == source_type)
    if active_only:
        q = q.filter(Opportunity.active.is_(True))

    return (
        q.order_by(Opportunity.value_score.desc(), Opportunity.roi_score.desc())
        .limit(limit)
        .all()
    )
