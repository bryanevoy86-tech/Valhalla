"""
PACK TK: Life Timeline & Milestones Service
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.life_timeline import LifeEvent, LifeMilestone
from app.schemas.life_timeline import LifeEventCreate, LifeMilestoneCreate, LifeTimelineSnapshot


def create_life_event(db: Session, payload: LifeEventCreate) -> LifeEvent:
    data = payload.model_dump()
    if data.get("date") is None:
        data["date"] = datetime.utcnow()
    obj = LifeEvent(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_life_events(db: Session) -> List[LifeEvent]:
    return db.query(LifeEvent).order_by(LifeEvent.date.asc()).all()


def create_life_milestone(db: Session, payload: LifeMilestoneCreate) -> LifeMilestone:
    obj = LifeMilestone(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_life_milestones(db: Session) -> List[LifeMilestone]:
    return db.query(LifeMilestone).order_by(LifeMilestone.id.asc()).all()


def get_timeline_snapshot(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> LifeTimelineSnapshot:
    events = (
        db.query(LifeEvent)
        .filter(LifeEvent.date >= from_date, LifeEvent.date <= to_date)
        .order_by(LifeEvent.date.asc())
        .all()
    )
    milestones = list_life_milestones(db)
    return LifeTimelineSnapshot(
        from_date=from_date,
        to_date=to_date,
        events=events,
        milestones=milestones,
    )
