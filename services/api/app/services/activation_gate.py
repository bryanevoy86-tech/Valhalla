"""
PACK CL17: Activation Gate Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.activation_gate import ActivationGate
from app.schemas.activation_gate import ActivationGateUpsert, ActivationGateLock


def upsert_gate(db: Session, payload: ActivationGateUpsert) -> ActivationGate:
    obj = db.query(ActivationGate).filter(ActivationGate.gate_key == payload.gate_key).first()
    if obj:
        if obj.is_locked:
            return obj
        obj.title = payload.title
        obj.description = payload.description
        obj.requirements = payload.requirements
        obj.is_enabled = payload.is_enabled
        obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(obj)
        return obj

    obj = ActivationGate(
        gate_key=payload.gate_key,
        title=payload.title,
        description=payload.description,
        requirements=payload.requirements,
        is_enabled=payload.is_enabled,
        is_locked=False,
        lock_reason=None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def lock_gate(db: Session, gate_key: str, payload: ActivationGateLock) -> Optional[ActivationGate]:
    obj = db.query(ActivationGate).filter(ActivationGate.gate_key == gate_key).first()
    if not obj:
        return None
    obj.is_locked = payload.is_locked
    obj.lock_reason = payload.lock_reason
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


def list_gates(db: Session, limit: int = 500) -> List[ActivationGate]:
    return db.query(ActivationGate).order_by(ActivationGate.id.asc()).limit(limit).all()
