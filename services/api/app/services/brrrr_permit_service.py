"""PACK 72: BRRRR & Permit Service
Service layer for BRRRR analysis and permit operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.brrrr_permit import BrrrrAnalysis, PermitPackage


def create_brrrr_analysis(
    db: Session,
    property_address: str,
    blueprint_id: Optional[int],
    purchase_price: float,
    rehab_cost: float,
    arv_estimate: float,
    rent_estimate: float,
    refinance_ltv: float,
    notes: Optional[str],
) -> BrrrrAnalysis:
    """Create a new BRRRR analysis."""
    item = BrrrrAnalysis(
        property_address=property_address,
        blueprint_id=blueprint_id,
        purchase_price=purchase_price,
        rehab_cost=rehab_cost,
        arv_estimate=arv_estimate,
        rent_estimate=rent_estimate,
        refinance_ltv=refinance_ltv,
        notes=notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_brrrr_analyses(db: Session) -> list:
    """List all BRRRR analyses."""
    return db.query(BrrrrAnalysis).order_by(BrrrrAnalysis.id.desc()).all()


def create_permit_package(
    db: Session,
    brrrr_id: int,
    jurisdiction: str,
    package_payload: str,
    status: str = "draft",
) -> PermitPackage:
    """Create a new permit package."""
    pkg = PermitPackage(
        brrrr_id=brrrr_id,
        jurisdiction=jurisdiction,
        package_payload=package_payload,
        status=status,
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def list_permit_packages(db: Session, brrrr_id: Optional[int] = None) -> list:
    """List permit packages, optionally filtered by BRRRR ID."""
    q = db.query(PermitPackage)
    if brrrr_id is not None:
        q = q.filter(PermitPackage.brrrr_id == brrrr_id)
    return q.order_by(PermitPackage.id.desc()).all()


def update_permit_status(db: Session, package_id: int, status: str) -> PermitPackage:
    """Update permit package status."""
    pkg = db.query(PermitPackage).filter(PermitPackage.id == package_id).first()
    if pkg:
        pkg.status = status
        db.commit()
        db.refresh(pkg)
    return pkg
