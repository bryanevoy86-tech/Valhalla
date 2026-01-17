# services/api/app/services/pro_task_service.py

from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.pro_task_link import ProfessionalTaskLink
from app.schemas.pro_task_link import ProfessionalTaskLinkIn


def create_link(db: Session, payload: ProfessionalTaskLinkIn) -> ProfessionalTaskLink:
    """Create a new task link to a professional."""
    obj = ProfessionalTaskLink(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_status(db: Session, link_id: int, status: str) -> Optional[ProfessionalTaskLink]:
    """Update the status of a task link."""
    obj = db.query(ProfessionalTaskLink).filter(ProfessionalTaskLink.id == link_id).first()
    if not obj:
        return None
    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


def list_for_professional(db: Session, professional_id: int) -> List[ProfessionalTaskLink]:
    """Get all task links for a specific professional."""
    return (
        db.query(ProfessionalTaskLink)
        .filter(ProfessionalTaskLink.professional_id == professional_id)
        .all()
    )


def list_for_deal(db: Session, deal_id: int) -> List[ProfessionalTaskLink]:
    """Get all task links for a specific deal."""
    return (
        db.query(ProfessionalTaskLink)
        .filter(ProfessionalTaskLink.deal_id == deal_id)
        .all()
    )


def get_link(db: Session, link_id: int) -> Optional[ProfessionalTaskLink]:
    """Get a specific task link by ID."""
    return db.query(ProfessionalTaskLink).filter(ProfessionalTaskLink.id == link_id).first()
