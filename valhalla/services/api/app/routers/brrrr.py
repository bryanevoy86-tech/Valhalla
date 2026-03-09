"""
Pack 49: Global BRRRR Zone Compliance Profiles
API endpoints for zone compliance evaluation and checklist generation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.brrrr import service
from app.brrrr.schemas import ZoneOut, ChecklistItem, EvaluateIn, EvaluateOut
from typing import List

router = APIRouter(prefix="/brrrr", tags=["brrrr"])


@router.get("/zones", response_model=List[ZoneOut])
def list_zones(db: Session = Depends(get_db)):
    """
    List all registered jurisdictions/zones.
    """
    return service.list_zones(db)


@router.get("/{zone}/checklist", response_model=List[ChecklistItem])
def get_zone_checklist(zone: str, deal_type: str, db: Session = Depends(get_db)):
    """
    Get required document checklist for a zone and deal type.
    """
    docs = service.get_checklist(db, zone, deal_type)
    return [
        ChecklistItem(
            doc_name=doc.doc_name,
            doc_category=doc.doc_category,
            is_mandatory=doc.is_mandatory,
            description=doc.description
        )
        for doc in docs
    ]


@router.post("/evaluate", response_model=EvaluateOut)
def evaluate_compliance(req: EvaluateIn, db: Session = Depends(get_db)):
    """
    Evaluate compliance for a deal in a given zone.
    Returns ok/warnings/risk_score/checklist/taxes.
    """
    return service.evaluate(db, req)
