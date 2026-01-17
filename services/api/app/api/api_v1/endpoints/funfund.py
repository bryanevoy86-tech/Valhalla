from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.funfund_routing import FunFundRouting
from app.schemas.funfund import (
    FunFundRoutingCreate,
    FunFundRoutingUpdate,
    FunFundRoutingOut,
)

router = APIRouter()


@router.post("/", response_model=FunFundRoutingOut)
def create_funfund_profile(
    payload: FunFundRoutingCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(FunFundRouting).filter(
        FunFundRouting.profile_name == payload.profile_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile name already exists")
    obj = FunFundRouting(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[FunFundRoutingOut])
def list_funfund_profiles(
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(FunFundRouting)
    if active is not None:
        query = query.filter(FunFundRouting.active == active)
    return query.all()


@router.get("/active", response_model=FunFundRoutingOut)
def get_active_funfund_profile(
    db: Session = Depends(get_db),
):
    obj = db.query(FunFundRouting).filter(FunFundRouting.active.is_(True)).first()
    if not obj:
        raise HTTPException(status_code=404, detail="No active Fun Fund profile")
    return obj


@router.put("/{profile_id}", response_model=FunFundRoutingOut)
def update_funfund_profile(
    profile_id: int,
    payload: FunFundRoutingUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(FunFundRouting).get(profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
