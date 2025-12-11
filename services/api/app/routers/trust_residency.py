"""
PACK AU: Trust & Residency Profile Router
Prefix: /trust-residency
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.trust_residency import (
    TrustResidencyCreate,
    TrustResidencyUpdate,
    TrustResidencyOut,
)
from app.services.trust_residency import (
    create_or_get_profile,
    update_profile,
    get_profile,
    list_profiles,
)

router = APIRouter(prefix="/trust-residency", tags=["TrustResidency"])


@router.post("/", response_model=TrustResidencyOut)
def create_or_get_profile_endpoint(
    payload: TrustResidencyCreate,
    db: Session = Depends(get_db),
):
    """Create or get trust & residency profile."""
    obj = create_or_get_profile(db, payload)
    return obj


@router.patch("/", response_model=TrustResidencyOut)
def update_profile_endpoint(
    subject_type: str,
    subject_id: str,
    payload: TrustResidencyUpdate,
    db: Session = Depends(get_db),
):
    """Update trust & residency profile."""
    obj = update_profile(db, subject_type, subject_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj


@router.get("/", response_model=TrustResidencyOut)
def get_profile_endpoint(
    subject_type: str,
    subject_id: str,
    db: Session = Depends(get_db),
):
    """Get trust & residency profile."""
    obj = get_profile(db, subject_type, subject_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj


@router.get("/list", response_model=List[TrustResidencyOut])
def list_profiles_endpoint(
    subject_type: Optional[str] = Query(None),
    min_trust: Optional[float] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List profiles with optional filters."""
    return list_profiles(db, subject_type=subject_type, min_trust=min_trust, limit=limit)
