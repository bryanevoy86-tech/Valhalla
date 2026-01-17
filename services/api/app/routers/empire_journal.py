"""
PACK AS: Empire Journal Engine Router
Prefix: /journal
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.empire_journal import JournalEntryCreate, JournalEntryOut
from app.services.empire_journal import create_entry, list_entries

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("/", response_model=JournalEntryOut)
def create_journal_entry_endpoint(
    payload: JournalEntryCreate,
    db: Session = Depends(get_db),
):
    """Create a new journal entry."""
    return create_entry(db, payload)


@router.get("/", response_model=List[JournalEntryOut])
def list_journal_entries_endpoint(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List journal entries with optional filters."""
    return list_entries(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        category=category,
        author=author,
        limit=limit,
    )
