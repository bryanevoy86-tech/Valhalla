from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tax_risk_profile import TaxRiskProfile
from app.schemas.tax_risk import (
    TaxRiskProfileCreate,
    TaxRiskProfileUpdate,
    TaxRiskProfileOut,
)

router = APIRouter()


@router.post("/", response_model=TaxRiskProfileOut)
def create_tax_risk_profile(payload: TaxRiskProfileCreate, db: Session = Depends(get_db)):
    obj = TaxRiskProfile(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[TaxRiskProfileOut])
def list_tax_risk_profiles(jurisdiction: str | None = None, db: Session = Depends(get_db)):
    query = db.query(TaxRiskProfile)
    if jurisdiction:
        query = query.filter(TaxRiskProfile.jurisdiction == jurisdiction)
    return query.all()


@router.put("/{profile_id}", response_model=TaxRiskProfileOut)
def update_tax_risk_profile(profile_id: int, payload: TaxRiskProfileUpdate, db: Session = Depends(get_db)):
    obj = db.query(TaxRiskProfile).get(profile_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
