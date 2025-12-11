"""
PACK AX: Feature Flags & Experiments Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.feature_flags import FeatureFlag
from app.schemas.feature_flags import FeatureFlagCreate, FeatureFlagUpdate


def create_feature_flag(db: Session, payload: FeatureFlagCreate) -> FeatureFlag:
    obj = FeatureFlag(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_feature_flag(
    db: Session,
    flag_id: int,
    payload: FeatureFlagUpdate,
) -> Optional[FeatureFlag]:
    obj = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_flag_by_key(db: Session, key: str) -> Optional[FeatureFlag]:
    return db.query(FeatureFlag).filter(FeatureFlag.key == key).first()


def list_feature_flags(
    db: Session,
    audience: Optional[str] = None,
) -> List[FeatureFlag]:
    q = db.query(FeatureFlag)
    if audience:
        q = q.filter((FeatureFlag.audience == audience) | (FeatureFlag.audience == "global"))
    return q.order_by(FeatureFlag.created_at.desc()).all()
