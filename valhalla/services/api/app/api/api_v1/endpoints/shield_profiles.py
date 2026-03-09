from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.shield_profile import ShieldProfile
from app.schemas.shield_profile import (
    ShieldProfileCreate,
    ShieldProfileUpdate,
    ShieldProfileOut,
)

router = APIRouter()


@router.post("/", response_model=ShieldProfileOut)
def create_shield_profile(payload: ShieldProfileCreate, db: Session = Depends(get_db)):
    obj = ShieldProfile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ShieldProfileOut])
def list_shield_profiles(db: Session = Depends(get_db)):
    return db.query(ShieldProfile).all()


@router.put("/{profile_id}", response_model=ShieldProfileOut)
def update_shield_profile(profile_id: int, payload: ShieldProfileUpdate, db: Session = Depends(get_db)):
    obj = db.query(ShieldProfile).get(profile_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
