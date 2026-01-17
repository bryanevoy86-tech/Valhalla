"""
PACK TG: Mental Load Offloading Router
Prefix: /mental-load
"""

from datetime import date as date_type
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.mental_load_tg import (
    MentalLoadEntryCreate,
    MentalLoadEntryOut,
    MentalLoadSummaryCreate,
    MentalLoadSummaryOut,
    MentalLoadDailyView,
)
from app.services.mental_load_tg import (
    create_entry,
    list_entries,
    archive_entry,
    create_daily_summary,
    get_daily_view,
)

router = APIRouter(prefix="/mental-load", tags=["Mental Load"])


@router.post("/entries", response_model=MentalLoadEntryOut)
def create_entry_endpoint(
    payload: MentalLoadEntryCreate,
    db: Session = Depends(get_db),
):
    """Create a new mental load entry (brain-dump)."""
    return create_entry(db, payload)


@router.get("/entries", response_model=List[MentalLoadEntryOut])
def list_entries_endpoint(
    archived: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List all mental load entries (filter by archived status)."""
    return list_entries(db, archived=archived)


@router.post("/entries/{entry_id}/archive", response_model=MentalLoadEntryOut)
def archive_entry_endpoint(
    entry_id: int,
    db: Session = Depends(get_db),
):
    """Archive a mental load entry."""
    obj = archive_entry(db, entry_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Entry not found")
    return obj


@router.post("/summary", response_model=MentalLoadSummaryOut)
def create_summary_endpoint(
    payload: MentalLoadSummaryCreate,
    db: Session = Depends(get_db),
):
    """Create a daily summary of mental load."""
    return create_daily_summary(db, payload)


@router.get("/daily-view", response_model=MentalLoadDailyView)
def get_daily_view_endpoint(
    day: date_type,
    db: Session = Depends(get_db),
):
    """Get all entries and summary for a specific day."""
    entries, summary = get_daily_view(db, day)
    return MentalLoadDailyView(
        date=day,
        entries=entries,
        summary=summary,
    )
