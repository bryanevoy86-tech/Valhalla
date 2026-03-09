"""PACK-CORE-PRELAUNCH-01: Daily Ops - Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

from . import schemas, service

router = APIRouter(prefix="/daily_ops", tags=["daily_ops"])


@router.post("/morning", response_model=schemas.DailySnapshotRead)
def run_morning(db: Session = Depends(get_db)):
    snapshot = service.run_morning_briefing(db)
    return snapshot


@router.post("/night", response_model=schemas.NightlySnapshotRead)
def run_night(db: Session = Depends(get_db)):
    snapshot = service.run_night_shutdown(db)
    return snapshot


@router.get("/today")
def get_today(db: Session = Depends(get_db)):
    data = service.get_today_snapshots(db)
    return {
        "daily": schemas.DailySnapshotRead.model_validate(data["daily"])
        if data["daily"]
        else None,
        "nightly": schemas.NightlySnapshotRead.model_validate(data["nightly"])
        if data["nightly"]
        else None,
    }
