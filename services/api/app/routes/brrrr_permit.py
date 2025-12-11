"""PACK 72: BRRRR & Permit Router
API endpoints for BRRRR analysis and permit operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.services.brrrr_permit_service import (
    create_brrrr_analysis,
    list_brrrr_analyses,
    create_permit_package,
    list_permit_packages,
    update_permit_status,
)
from app.schemas.brrrr_permit import (
    BrrrrAnalysisOut,
    PermitPackageOut,
)

router = APIRouter(prefix="/brrrr", tags=["BRRRR & Permits"])


@router.post("/", response_model=BrrrrAnalysisOut)
def new_brrrr_analysis(
    property_address: str,
    purchase_price: float,
    rehab_cost: float,
    arv_estimate: float,
    rent_estimate: float,
    refinance_ltv: float,
    blueprint_id: Optional[int] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a new BRRRR analysis."""
    return create_brrrr_analysis(
        db=db,
        property_address=property_address,
        blueprint_id=blueprint_id,
        purchase_price=purchase_price,
        rehab_cost=rehab_cost,
        arv_estimate=arv_estimate,
        rent_estimate=rent_estimate,
        refinance_ltv=refinance_ltv,
        notes=notes,
    )


@router.get("/", response_model=list[BrrrrAnalysisOut])
def get_brrrr_analyses(db: Session = Depends(get_db)):
    """Get all BRRRR analyses."""
    return list_brrrr_analyses(db)


@router.post("/permit", response_model=PermitPackageOut)
def new_permit_package(
    brrrr_id: int,
    jurisdiction: str,
    package_payload: str,
    status: str = "draft",
    db: Session = Depends(get_db),
):
    """Create a new permit package."""
    return create_permit_package(db, brrrr_id, jurisdiction, package_payload, status)


@router.get("/permit", response_model=list[PermitPackageOut])
def get_permit_packages(brrrr_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get permit packages, optionally filtered by BRRRR ID."""
    return list_permit_packages(db, brrrr_id)


@router.post("/permit/{package_id}/status", response_model=PermitPackageOut)
def set_permit_status(package_id: int, status: str, db: Session = Depends(get_db)):
    """Update permit package status."""
    return update_permit_status(db, package_id, status)
