"""
Lead intake router - create leads, normalize to deals.
"""

from typing import List
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..core.normalizer import normalize_lead_fields
from ..models.intake import LeadIntake
from ..models.match import DealBrief
from ..schemas.intake import LeadIn, LeadOut, NormalizeOut

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("/leads", response_model=LeadOut)
def add_lead(
    payload: LeadIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """Create a new lead intake record from raw data."""
    lead = LeadIntake(
        source=payload.source,
        name=payload.name,
        email=str(payload.email or ""),
        phone=payload.phone,
        address=payload.address,
        region=payload.region,
        property_type=payload.property_type,
        price=payload.price,
        beds=payload.beds,
        baths=payload.baths,
        notes=payload.notes,
        raw_json=json.dumps(payload.raw or {})
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads", response_model=List[LeadOut])
def list_leads(
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """List all lead intake records (most recent first)."""
    return db.query(LeadIntake).order_by(LeadIntake.id.desc()).limit(500).all()


def _to_deal(lead: LeadIntake) -> DealBrief:
    """Convert a lead to a DealBrief."""
    return DealBrief(
        headline=(lead.address or lead.region or "New lead"),
        region=lead.region,
        property_type=lead.property_type,
        price=lead.price,
        beds=lead.beds,
        baths=lead.baths,
        notes=lead.notes,
        status="active"
    )


@router.post("/leads/{lead_id}/normalize", response_model=NormalizeOut)
def normalize_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """
    Normalize lead fields using heuristics and create a DealBrief if not already created.
    Updates lead status to 'normalized'.
    """
    lead = db.get(LeadIntake, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="lead not found")
    
    # merge normalized fields from raw_json if present
    try:
        raw = json.loads(lead.raw_json or "{}")
    except Exception:
        raw = {}
    
    fields = normalize_lead_fields({
        **raw,
        **{
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "address": lead.address,
            "region": lead.region,
            "property_type": lead.property_type,
            "price": lead.price,
            "beds": lead.beds,
            "baths": lead.baths,
            "notes": lead.notes
        }
    })
    
    for k, v in fields.items():
        setattr(lead, k, v)
    
    # create deal if not already created
    deal_id = lead.deal_id
    if not deal_id:
        deal = _to_deal(lead)
        db.add(deal)
        db.commit()
        db.refresh(deal)
        lead.deal_id = deal.id
    
    lead.status = "normalized"
    db.commit()
    db.refresh(lead)
    
    return NormalizeOut(ok=True, lead_id=lead.id, deal_id=lead.deal_id)
