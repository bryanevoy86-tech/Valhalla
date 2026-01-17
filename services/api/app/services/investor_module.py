"""
PACK AE: Public Investor Module Service
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.investor_module import InvestorProfile, InvestorProjectSummary
from app.schemas.investor_module import (
    InvestorProfileCreate,
    InvestorProfileUpdate,
    InvestorProjectCreate,
    InvestorProjectUpdate,
)


def create_or_get_profile(db: Session, payload: InvestorProfileCreate) -> InvestorProfile:
    """Create a new profile or return existing one for user_id"""
    existing = db.query(InvestorProfile).filter(InvestorProfile.user_id == payload.user_id).first()
    if existing:
        return existing

    obj = InvestorProfile(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_profile(
    db: Session,
    user_id: int,
    payload: InvestorProfileUpdate,
) -> Optional[InvestorProfile]:
    """Update an investor profile"""
    obj = db.query(InvestorProfile).filter(InvestorProfile.user_id == user_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_profile(db: Session, user_id: int) -> Optional[InvestorProfile]:
    """Get an investor profile by user_id"""
    return db.query(InvestorProfile).filter(InvestorProfile.user_id == user_id).first()


def create_project(db: Session, payload: InvestorProjectCreate) -> InvestorProjectSummary:
    """Create a new project summary"""
    obj = InvestorProjectSummary(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_project(
    db: Session,
    slug: str,
    payload: InvestorProjectUpdate,
) -> Optional[InvestorProjectSummary]:
    """Update a project summary by slug"""
    obj = db.query(InvestorProjectSummary).filter(InvestorProjectSummary.slug == slug).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_projects(db: Session, status: Optional[str] = None) -> List[InvestorProjectSummary]:
    """List projects, optionally filtered by status"""
    q = db.query(InvestorProjectSummary)
    if status:
        q = q.filter(InvestorProjectSummary.status == status)
    return q.order_by(InvestorProjectSummary.created_at.desc()).all()


def get_project_by_slug(db: Session, slug: str) -> Optional[InvestorProjectSummary]:
    """Get a project summary by slug"""
    return db.query(InvestorProjectSummary).filter(InvestorProjectSummary.slug == slug).first()
