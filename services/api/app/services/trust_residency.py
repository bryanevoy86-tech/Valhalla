"""
PACK AU: Trust & Residency Profile Service
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.trust_residency import TrustResidencyProfile
from app.schemas.trust_residency import TrustResidencyCreate, TrustResidencyUpdate


def create_or_get_profile(db: Session, payload: TrustResidencyCreate) -> TrustResidencyProfile:
    existing = (
        db.query(TrustResidencyProfile)
        .filter(
            TrustResidencyProfile.subject_type == payload.subject_type,
            TrustResidencyProfile.subject_id == payload.subject_id,
        )
        .first()
    )
    if existing:
        return existing

    obj = TrustResidencyProfile(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_profile(
    db: Session,
    subject_type: str,
    subject_id: str,
    payload: TrustResidencyUpdate,
) -> Optional[TrustResidencyProfile]:
    obj = (
        db.query(TrustResidencyProfile)
        .filter(
            TrustResidencyProfile.subject_type == subject_type,
            TrustResidencyProfile.subject_id == subject_id,
        )
        .first()
    )
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_profile(
    db: Session,
    subject_type: str,
    subject_id: str,
) -> Optional[TrustResidencyProfile]:
    return (
        db.query(TrustResidencyProfile)
        .filter(
            TrustResidencyProfile.subject_type == subject_type,
            TrustResidencyProfile.subject_id == subject_id,
        )
        .first()
    )


def list_profiles(
    db: Session,
    subject_type: Optional[str] = None,
    min_trust: Optional[float] = None,
    limit: int = 100,
) -> List[TrustResidencyProfile]:
    q = db.query(TrustResidencyProfile)
    if subject_type:
        q = q.filter(TrustResidencyProfile.subject_type == subject_type)
    if min_trust is not None:
        q = q.filter(TrustResidencyProfile.trust_score >= min_trust)
    return q.order_by(TrustResidencyProfile.updated_at.desc()).limit(limit).all()
