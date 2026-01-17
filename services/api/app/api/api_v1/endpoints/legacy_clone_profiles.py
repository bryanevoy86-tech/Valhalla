from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.legacy_clone_profile import LegacyCloneProfile
from app.schemas.legacy_clone_profile import (
    LegacyCloneProfileCreate,
    LegacyCloneProfileUpdate,
    LegacyCloneProfileOut,
)

router = APIRouter()


@router.post("/", response_model=LegacyCloneProfileOut)
def create_legacy_clone_profile(payload: LegacyCloneProfileCreate, db: Session = Depends(get_db)):
    obj = LegacyCloneProfile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[LegacyCloneProfileOut])
def list_legacy_clone_profiles(db: Session = Depends(get_db)):
    return db.query(LegacyCloneProfile).all()


@router.put("/{profile_id}", response_model=LegacyCloneProfileOut)
def update_legacy_clone_profile(profile_id: int, payload: LegacyCloneProfileUpdate, db: Session = Depends(get_db)):
    obj = db.query(LegacyCloneProfile).get(profile_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
