"""
PACK SJ: Wholesale Deal Machine Router
FastAPI endpoints for wholesale deal pipeline management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.wholesale_deals import (
    WholesaleLeadSchema, WholesaleOfferSchema, BuyerProfileSchema,
    AssignmentRecordSchema, WholesalePipelineSnapshotSchema, DealPipelineResponse
)
from app.services.wholesale_deals import (
    create_wholesale_lead, get_wholesale_lead, list_wholesale_leads, update_lead_stage,
    create_wholesale_offer, list_offers_by_lead, update_offer_status,
    create_buyer_profile, list_buyers,
    create_assignment, get_assignments_by_lead,
    get_pipeline_summary, create_pipeline_snapshot
)

router = APIRouter(prefix="/wholesale", tags=["wholesale"])


@router.post("/leads", response_model=WholesaleLeadSchema)
def create_lead(lead_data: dict, db: Session = Depends(get_db)):
    """Create a new wholesale lead."""
    return create_wholesale_lead(db, **lead_data)


@router.get("/leads/{lead_id}", response_model=WholesaleLeadSchema)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead."""
    lead = get_wholesale_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/leads", response_model=list[WholesaleLeadSchema])
def list_leads(db: Session = Depends(get_db)):
    """List all wholesale leads."""
    return list_wholesale_leads(db)


@router.put("/leads/{lead_id}/stage", response_model=WholesaleLeadSchema)
def update_stage(lead_id: int, stage: str, db: Session = Depends(get_db)):
    """Update lead stage in pipeline."""
    lead = update_lead_stage(db, lead_id, stage)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/offers", response_model=WholesaleOfferSchema)
def create_offer(offer_data: dict, db: Session = Depends(get_db)):
    """Create a wholesale offer."""
    return create_wholesale_offer(db, **offer_data)


@router.get("/offers/lead/{lead_id}", response_model=list[WholesaleOfferSchema])
def list_lead_offers(lead_id: int, db: Session = Depends(get_db)):
    """List offers for a specific lead."""
    return list_offers_by_lead(db, lead_id)


@router.put("/offers/{offer_id}/status", response_model=WholesaleOfferSchema)
def update_offer_status_route(offer_id: int, status: str, db: Session = Depends(get_db)):
    """Update offer status."""
    offer = update_offer_status(db, offer_id, status)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.post("/buyers", response_model=BuyerProfileSchema)
def create_buyer(buyer_data: dict, db: Session = Depends(get_db)):
    """Create a buyer profile."""
    return create_buyer_profile(db, **buyer_data)


@router.get("/buyers", response_model=list[BuyerProfileSchema])
def list_all_buyers(db: Session = Depends(get_db)):
    """List all buyers."""
    return list_buyers(db)


@router.post("/assignments", response_model=AssignmentRecordSchema)
def create_new_assignment(assignment_data: dict, db: Session = Depends(get_db)):
    """Create an assignment record."""
    return create_assignment(db, **assignment_data)


@router.get("/assignments/lead/{lead_id}", response_model=list[AssignmentRecordSchema])
def get_lead_assignments(lead_id: int, db: Session = Depends(get_db)):
    """Get assignments for a lead."""
    return get_assignments_by_lead(db, lead_id)


@router.get("/pipeline", response_model=DealPipelineResponse)
def get_pipeline(db: Session = Depends(get_db)):
    """Get current deal pipeline summary."""
    return get_pipeline_summary(db)


@router.post("/pipeline/snapshot", response_model=WholesalePipelineSnapshotSchema)
def create_snapshot(snapshot_data: dict, db: Session = Depends(get_db)):
    """Create a pipeline snapshot."""
    return create_pipeline_snapshot(db, **snapshot_data)
