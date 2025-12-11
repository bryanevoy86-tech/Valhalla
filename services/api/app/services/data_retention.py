"""
PACK UI: Data Retention Policy Registry Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.data_retention import DataRetentionPolicy
from app.schemas.data_retention import DataRetentionSet


def set_retention_policy(
    db: Session,
    payload: DataRetentionSet,
) -> DataRetentionPolicy:
    obj = (
        db.query(DataRetentionPolicy)
        .filter(DataRetentionPolicy.category == payload.category)
        .first()
    )
    if not obj:
        obj = DataRetentionPolicy(**payload.model_dump())
        db.add(obj)
    else:
        obj.days_to_keep = payload.days_to_keep
        obj.enabled = payload.enabled
        if payload.description is not None:
            obj.description = payload.description
        obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


def list_retention_policies(db: Session) -> List[DataRetentionPolicy]:
    return (
        db.query(DataRetentionPolicy)
        .order_by(DataRetentionPolicy.category.asc())
        .all()
    )


def get_retention_policy(
    db: Session,
    category: str,
) -> Optional[DataRetentionPolicy]:
    return (
        db.query(DataRetentionPolicy)
        .filter(DataRetentionPolicy.category == category)
        .first()
    )
