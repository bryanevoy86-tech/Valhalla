"""
PACK TO: Daily Rhythm & Tempo Service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.daily_rhythm import DailyRhythmProfile, TempoRule
from app.schemas.daily_rhythm import (
    DailyRhythmProfileCreate,
    TempoRuleCreate,
    DailyRhythmSnapshot,
)


def create_daily_rhythm_profile(
    db: Session,
    payload: DailyRhythmProfileCreate,
) -> DailyRhythmProfile:
    data = payload.model_dump()
    obj = DailyRhythmProfile(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_daily_rhythm_profiles(db: Session) -> List[DailyRhythmProfile]:
    return db.query(DailyRhythmProfile).order_by(DailyRhythmProfile.name.asc()).all()


def create_tempo_rule(db: Session, payload: TempoRuleCreate) -> TempoRule:
    obj = TempoRule(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_tempo_rules(db: Session, profile_name: Optional[str] = None) -> List[TempoRule]:
    q = db.query(TempoRule)
    if profile_name:
        q = q.filter(TempoRule.profile_name == profile_name)
    return q.order_by(TempoRule.time_block.asc()).all()


def get_daily_rhythm_snapshot(
    db: Session,
    profile_name: str = "default",
) -> Optional[DailyRhythmSnapshot]:
    profile = (
        db.query(DailyRhythmProfile)
        .filter(DailyRhythmProfile.name == profile_name, DailyRhythmProfile.active.is_(True))
        .first()
    )
    if not profile:
        return None
    rules = list_tempo_rules(db, profile_name=profile_name)
    return DailyRhythmSnapshot(
        profile=profile,
        rules=rules,
        meta={"profile_name": profile_name},
    )
