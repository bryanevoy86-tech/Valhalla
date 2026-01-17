from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.legal_profile import LegalProfile
from app.schemas.legal_profile import (
    LegalProfileCreate,
    LegalProfileUpdate,
    LegalProfileOut,
)

router = APIRouter()


@router.post("/", response_model=LegalProfileOut)
def create_legal_profile(payload: LegalProfileCreate, db: Session = Depends(get_db)):
    obj = LegalProfile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[LegalProfileOut])
def list_legal_profiles(country: str | None = None, db: Session = Depends(get_db)):
    query = db.query(LegalProfile)
    if country:
        query = query.filter(LegalProfile.country == country)
    return query.all()


@router.put("/{profile_id}", response_model=LegalProfileOut)
def update_legal_profile(profile_id: int, payload: LegalProfileUpdate, db: Session = Depends(get_db)):
    obj = db.query(LegalProfile).get(profile_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
