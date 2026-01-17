from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.arbitrage_profile import ArbitrageProfile
from app.schemas.arbitrage_profile import (
    ArbitrageProfileCreate,
    ArbitrageProfileUpdate,
    ArbitrageProfileOut,
)

router = APIRouter()


@router.post("/", response_model=ArbitrageProfileOut)
def create_arbitrage_profile(
    payload: ArbitrageProfileCreate,
    db: Session = Depends(get_db),
):
    obj = ArbitrageProfile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ArbitrageProfileOut])
def list_arbitrage_profiles(
    pool_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ArbitrageProfile)
    if pool_type:
        query = query.filter(ArbitrageProfile.pool_type == pool_type)
    return query.all()


@router.put("/{profile_id}", response_model=ArbitrageProfileOut)
def update_arbitrage_profile(
    profile_id: int,
    payload: ArbitrageProfileUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(ArbitrageProfile).get(profile_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
