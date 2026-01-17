"""
PACK TO: Daily Rhythm & Tempo Router
Prefix: /rhythm
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.daily_rhythm import (
    DailyRhythmProfileCreate,
    DailyRhythmProfileOut,
    TempoRuleCreate,
    TempoRuleOut,
    DailyRhythmSnapshot,
)
from app.services.daily_rhythm import (
    create_daily_rhythm_profile,
    list_daily_rhythm_profiles,
    create_tempo_rule,
    list_tempo_rules,
    get_daily_rhythm_snapshot,
)

router = APIRouter(prefix="/rhythm", tags=["Daily Rhythm"])


@router.post("/profiles", response_model=DailyRhythmProfileOut)
def create_profile_endpoint(
    payload: DailyRhythmProfileCreate,
    db: Session = Depends(get_db),
):
    return create_daily_rhythm_profile(db, payload)


@router.get("/profiles", response_model=List[DailyRhythmProfileOut])
def list_profiles_endpoint(db: Session = Depends(get_db)):
    return list_daily_rhythm_profiles(db)


@router.post("/tempo-rules", response_model=TempoRuleOut)
def create_tempo_rule_endpoint(
    payload: TempoRuleCreate,
    db: Session = Depends(get_db),
):
    return create_tempo_rule(db, payload)


@router.get("/tempo-rules", response_model=List[TempoRuleOut])
def list_tempo_rules_endpoint(
    profile_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return list_tempo_rules(db, profile_name=profile_name)


@router.get("/snapshot", response_model=DailyRhythmSnapshot)
def snapshot_endpoint(
    profile_name: str = Query("default"),
    db: Session = Depends(get_db),
):
    snapshot = get_daily_rhythm_snapshot(db, profile_name=profile_name)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Profile not found")
    return snapshot
