"""
PACK Y: Dispo Engine Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.dispo import DispoBuyerProfile, DispoAssignment
from app.schemas.dispo import (
    DispoBuyerCreate,
    DispoBuyerUpdate,
    DispoAssignmentCreate,
    DispoAssignmentUpdate,
)


# Buyers

def create_buyer(db: Session, payload: DispoBuyerCreate) -> DispoBuyerProfile:
    obj = DispoBuyerProfile(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_buyer(
    db: Session,
    buyer_id: int,
    payload: DispoBuyerUpdate,
) -> Optional[DispoBuyerProfile]:
    obj = db.query(DispoBuyerProfile).filter(DispoBuyerProfile.id == buyer_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_buyers(db: Session, active_only: bool = True) -> List[DispoBuyerProfile]:
    q = db.query(DispoBuyerProfile)
    if active_only:
        q = q.filter(DispoBuyerProfile.is_active.is_(True))
    return q.order_by(DispoBuyerProfile.created_at.desc()).all()


def get_buyer(db: Session, buyer_id: int) -> Optional[DispoBuyerProfile]:
    return db.query(DispoBuyerProfile).filter(DispoBuyerProfile.id == buyer_id).first()


# Assignments

def create_assignment(
    db: Session,
    payload: DispoAssignmentCreate,
) -> DispoAssignment:
    obj = DispoAssignment(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_assignment(
    db: Session,
    assignment_id: int,
    payload: DispoAssignmentUpdate,
) -> Optional[DispoAssignment]:
    obj = db.query(DispoAssignment).filter(DispoAssignment.id == assignment_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_assignments_for_pipeline(
    db: Session,
    pipeline_id: int,
) -> List[DispoAssignment]:
    return (
        db.query(DispoAssignment)
        .filter(DispoAssignment.pipeline_id == pipeline_id)
        .order_by(DispoAssignment.created_at.desc())
        .all()
    )
