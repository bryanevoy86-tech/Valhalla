"""
PACK AS: Empire Journal Engine Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.empire_journal import JournalEntry
from app.schemas.empire_journal import JournalEntryCreate


def create_entry(db: Session, payload: JournalEntryCreate) -> JournalEntry:
    obj = JournalEntry(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_entries(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    category: Optional[str] = None,
    author: Optional[str] = None,
    limit: int = 100,
) -> List[JournalEntry]:
    q = db.query(JournalEntry)

    if entity_type:
        q = q.filter(JournalEntry.entity_type == entity_type)
    if entity_id:
        q = q.filter(JournalEntry.entity_id == entity_id)
    if category:
        q = q.filter(JournalEntry.category == category)
    if author:
        q = q.filter(JournalEntry.author == author)

    return q.order_by(JournalEntry.created_at.desc()).limit(limit).all()
