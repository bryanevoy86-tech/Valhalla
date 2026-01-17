"""
PACK AP: Decision Governance Engine Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.decision_governance import DecisionPolicy, DecisionRecord
from app.schemas.decision_governance import (
    DecisionPolicyCreate,
    DecisionPolicyUpdate,
    DecisionCreate,
    DecisionUpdate,
)


# Policies

def create_policy(db: Session, payload: DecisionPolicyCreate) -> DecisionPolicy:
    obj = DecisionPolicy(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_policy(
    db: Session,
    policy_id: int,
    payload: DecisionPolicyUpdate,
) -> Optional[DecisionPolicy]:
    obj = db.query(DecisionPolicy).filter(DecisionPolicy.id == policy_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_policy_by_key(db: Session, key: str) -> Optional[DecisionPolicy]:
    return db.query(DecisionPolicy).filter(DecisionPolicy.key == key).first()


def list_policies(db: Session, active_only: bool = True) -> List[DecisionPolicy]:
    q = db.query(DecisionPolicy)
    if active_only:
        q = q.filter(DecisionPolicy.is_active.is_(True))
    return q.order_by(DecisionPolicy.created_at.desc()).all()


# Decisions

def create_decision(db: Session, payload: DecisionCreate) -> DecisionRecord:
    obj = DecisionRecord(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_decision(
    db: Session,
    decision_id: int,
    payload: DecisionUpdate,
) -> Optional[DecisionRecord]:
    obj = db.query(DecisionRecord).filter(DecisionRecord.id == decision_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)

    if "status" in data and data["status"] is not None:
        obj.status = data["status"]
        if data["status"] in ("approved", "rejected"):
            obj.decided_at = datetime.utcnow()

    if "context" in data and data["context"] is not None:
        obj.context = data["context"]

    db.commit()
    db.refresh(obj)
    return obj


def list_decisions_for_entity(
    db: Session,
    entity_type: str,
    entity_id: str,
) -> List[DecisionRecord]:
    return (
        db.query(DecisionRecord)
        .filter(
            DecisionRecord.entity_type == entity_type,
            DecisionRecord.entity_id == entity_id,
        )
        .order_by(DecisionRecord.created_at.desc())
        .all()
    )
