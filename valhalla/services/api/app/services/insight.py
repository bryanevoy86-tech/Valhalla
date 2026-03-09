"""
PACK CI4: Insight Synthesizer Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.insight import Insight
from app.schemas.insight import InsightIn


def create_insight(
    db: Session,
    payload: InsightIn,
) -> Insight:
    obj = Insight(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_insights(
    db: Session,
    category: Optional[str] = None,
    min_importance: int = 1,
    limit: int = 200,
) -> List[Insight]:
    q = db.query(Insight)
    if category:
        q = q.filter(Insight.category == category)
    q = q.filter(Insight.importance >= min_importance)

    return (
        q.order_by(Insight.importance.desc(), Insight.created_at.desc())
        .limit(limit)
        .all()
    )
