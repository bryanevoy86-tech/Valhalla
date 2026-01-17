"""
PACK TG: Mental Load Offloading Service Layer
"""

from datetime import datetime, date as date_type
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.mental_load import MentalLoadEntry, DailyLoadSummary
from app.schemas.mental_load_tg import (
    MentalLoadEntryCreate,
    MentalLoadSummaryCreate,
)


def create_entry(db: Session, payload: MentalLoadEntryCreate) -> MentalLoadEntry:
    obj = MentalLoadEntry(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_entries(
    db: Session,
    archived: Optional[bool] = None,
) -> List[MentalLoadEntry]:
    q = db.query(MentalLoadEntry)
    if archived is not None:
        q = q.filter(MentalLoadEntry.archived == archived)
    return q.order_by(MentalLoadEntry.created_at.desc()).all()


def archive_entry(db: Session, entry_id: int) -> Optional[MentalLoadEntry]:
    obj = db.query(MentalLoadEntry).filter(MentalLoadEntry.id == entry_id).first()
    if not obj:
        return None
    obj.archived = True
    db.commit()
    db.refresh(obj)
    return obj


def create_daily_summary(
    db: Session,
    payload: MentalLoadSummaryCreate,
) -> DailyLoadSummary:
    # Count items for that date
    target_date = payload.date.date()
    start = datetime(target_date.year, target_date.month, target_date.day)
    end = start.replace(hour=23, minute=59, second=59)

    total_items = (
        db.query(func.count(MentalLoadEntry.id))
        .filter(
            and_(
                MentalLoadEntry.created_at >= start,
                MentalLoadEntry.created_at <= end,
            )
        )
        .scalar()
    )

    urgent_items = (
        db.query(func.count(MentalLoadEntry.id))
        .filter(
            and_(
                MentalLoadEntry.created_at >= start,
                MentalLoadEntry.created_at <= end,
                MentalLoadEntry.urgency_level != None,  # noqa
                MentalLoadEntry.urgency_level >= 4,
            )
        )
        .scalar()
    )

    action_items = (
        db.query(func.count(MentalLoadEntry.id))
        .filter(
            and_(
                MentalLoadEntry.created_at >= start,
                MentalLoadEntry.created_at <= end,
                MentalLoadEntry.action_required.is_(True),
            )
        )
        .scalar()
    )

    obj = DailyLoadSummary(
        date=payload.date,
        total_items=total_items or 0,
        urgent_items=urgent_items or 0,
        action_items=action_items or 0,
        notes=payload.notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_daily_view(
    db: Session,
    day: date_type,
):
    start = datetime(day.year, day.month, day.day)
    end = start.replace(hour=23, minute=59, second=59)

    entries = (
        db.query(MentalLoadEntry)
        .filter(
            and_(
                MentalLoadEntry.created_at >= start,
                MentalLoadEntry.created_at <= end,
            )
        )
        .order_by(MentalLoadEntry.created_at.asc())
        .all()
    )

    summary = (
        db.query(DailyLoadSummary)
        .filter(func.date(DailyLoadSummary.date) == day)
        .first()
    )

    return entries, summary
