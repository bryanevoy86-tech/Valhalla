"""
PACK TJ: Kids Education & Development Service Layer
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.kids_education_tj import ChildProfile, LearningPlan, EducationLog
from app.schemas.kids_education_tj import (
    ChildProfileCreate,
    LearningPlanCreate,
    EducationLogCreate,
    ChildWeeklySummary,
)


def create_child(db: Session, payload: ChildProfileCreate) -> ChildProfile:
    obj = ChildProfile(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_children(db: Session) -> List[ChildProfile]:
    return db.query(ChildProfile).order_by(ChildProfile.name.asc()).all()


def create_learning_plan(db: Session, payload: LearningPlanCreate) -> Optional[LearningPlan]:
    child = db.query(ChildProfile).filter(ChildProfile.id == payload.child_id).first()
    if not child:
        return None
    obj = LearningPlan(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_education_log(db: Session, payload: EducationLogCreate) -> Optional[EducationLog]:
    child = db.query(ChildProfile).filter(ChildProfile.id == payload.child_id).first()
    if not child:
        return None
    obj = EducationLog(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_child_weekly_summary(
    db: Session,
    child_id: int,
    week_of: datetime,
) -> Optional[ChildWeeklySummary]:
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        return None

    start = week_of
    end = week_of + timedelta(days=7)

    logs = (
        db.query(EducationLog)
        .filter(
            EducationLog.child_id == child_id,
            EducationLog.date >= start,
            EducationLog.date < end,
        )
        .all()
    )

    completed_goals: List[str] = []
    fun_moments: List[str] = []
    growth_notes_parts: List[str] = []

    for log in logs:
        if log.completed_activities:
            completed_goals.append(log.completed_activities)
        if log.highlights:
            fun_moments.append(log.highlights)
        if log.parent_notes:
            growth_notes_parts.append(log.parent_notes)

    return ChildWeeklySummary(
        child_id=child.id,
        child_name=child.name,
        week_of=start,
        completed_goals=completed_goals,
        fun_moments=fun_moments,
        growth_notes="\n".join(growth_notes_parts),
    )
