"""PACK 81: Industry Engine - Registry Router"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.industry_registry import IndustryProfileOut, IndustryProfileCreate
from app.services.industry_registry_service import (
    create_industry_profile, list_industry_profiles, get_industry_profile, update_industry_profile, delete_industry_profile
)

router = APIRouter(prefix="/industry", tags=["industry_registry"])


@router.post("/profile", response_model=IndustryProfileOut)
def post_industry_profile(profile: IndustryProfileCreate, db: Session = Depends(get_db)):
    return create_industry_profile(db, profile)


@router.get("/profiles", response_model=list[IndustryProfileOut])
def get_industry_profiles(db: Session = Depends(get_db)):
    return list_industry_profiles(db)


@router.get("/profile/{profile_id}", response_model=IndustryProfileOut)
def get_industry_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    return get_industry_profile(db, profile_id)


@router.put("/profile/{profile_id}", response_model=IndustryProfileOut)
def put_industry_profile(profile_id: int, profile: IndustryProfileCreate, db: Session = Depends(get_db)):
    return update_industry_profile(db, profile_id, profile)


@router.delete("/profile/{profile_id}")
def delete_industry_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    return delete_industry_profile(db, profile_id)
