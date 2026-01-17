from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.legacy_performance import LegacyPerformance
from app.schemas.legacy_performance import LegacyPerformanceCreate, LegacyPerformanceOut

router = APIRouter()


@router.post("/", response_model=LegacyPerformanceOut)
def create_legacy_performance(payload: LegacyPerformanceCreate, db: Session = Depends(get_db)):
    obj = LegacyPerformance(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[LegacyPerformanceOut])
def list_legacy_performance(
    legacy_code: str | None = None,
    period: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(LegacyPerformance)
    if legacy_code:
        query = query.filter(LegacyPerformance.legacy_code == legacy_code)
    if period:
        query = query.filter(LegacyPerformance.period == period)
    return query.order_by(LegacyPerformance.created_at.desc()).all()
