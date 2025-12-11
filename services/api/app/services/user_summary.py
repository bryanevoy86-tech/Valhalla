"""
PACK AT: User-Facing Summary Snapshot Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user_summary import UserSummarySnapshot
from app.schemas.user_summary import UserSummaryCreate


def create_summary(db: Session, payload: UserSummaryCreate) -> UserSummarySnapshot:
    obj = UserSummarySnapshot(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_summaries(
    db: Session,
    summary_type: Optional[str] = None,
    audience: Optional[str] = None,
    limit: int = 50,
) -> List[UserSummarySnapshot]:
    q = db.query(UserSummarySnapshot)
    if summary_type:
        q = q.filter(UserSummarySnapshot.summary_type == summary_type)
    if audience:
        q = q.filter(UserSummarySnapshot.audience == audience)
    return q.order_by(UserSummarySnapshot.created_at.desc()).limit(limit).all()
