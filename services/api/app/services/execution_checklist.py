"""
PACK CL15: Execution Checklist Service
"""

from typing import List
from sqlalchemy.orm import Session
from app.models.execution_checklist import ExecutionChecklistItem
from app.schemas.execution_checklist import ExecutionChecklistItemCreate


def upsert_item(db: Session, payload: ExecutionChecklistItemCreate) -> ExecutionChecklistItem:
    obj = db.query(ExecutionChecklistItem).filter(ExecutionChecklistItem.key == payload.key).first()
    if obj:
        obj.title = payload.title
        obj.description = payload.description
        db.commit()
        db.refresh(obj)
        return obj

    obj = ExecutionChecklistItem(key=payload.key, title=payload.title, description=payload.description)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_items(db: Session, limit: int = 500) -> List[ExecutionChecklistItem]:
    return db.query(ExecutionChecklistItem).order_by(ExecutionChecklistItem.id.asc()).limit(limit).all()
