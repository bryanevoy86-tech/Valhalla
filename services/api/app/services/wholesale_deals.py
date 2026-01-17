"""
PACK SJ: Wholesale Deal Machine
Service functions for wholesale lead tracking, offers, assignments, and buyers
"""
from sqlalchemy.orm import Session
from app.models.wholesale_deals import (
    WholesaleLead, WholesaleOffer, AssignmentRecord, BuyerProfile, WholesalePipelineSnapshot
)
from datetime import datetime
from typing import List, Optional, Dict, Any


def create_wholesale_lead(
    db: Session,
    lead_id: str,
    source: str,
    property_address: str,
    seller_name: Optional[str] = None,
    seller_contact: Optional[str] = None,
    motivation_level: Optional[str] = None,
    situation_notes: Optional[str] = None
) -> WholesaleLead:
    """Create a new wholesale lead."""
    lead = WholesaleLead(
        lead_id=lead_id,
        source=source,
        seller_name=seller_name,
        seller_contact=seller_contact,
        property_address=property_address,
        motivation_level=motivation_level,
        situation_notes=situation_notes,
        stage="new"
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def get_wholesale_lead(db: Session, lead_id: int) -> Optional[WholesaleLead]:
    """Get a wholesale lead by ID."""
    return db.query(WholesaleLead).filter(WholesaleLead.id == lead_id).first()


def list_wholesale_leads(db: Session, stage: Optional[str] = None) -> List[WholesaleLead]:
    """List all wholesale leads, optionally filtered by stage."""
    query = db.query(WholesaleLead)
    if stage:
        query = query.filter(WholesaleLead.stage == stage)
    return query.all()


def update_lead_stage(db: Session, lead_id: int, new_stage: str) -> WholesaleLead:
    """Update lead stage."""
    lead = get_wholesale_lead(db, lead_id)
    if lead:
        lead.stage = new_stage
        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
    return lead


def create_wholesale_offer(
    db: Session,
    offer_id: str,
    lead_id: int,
    offer_price: int,
    arv: Optional[int] = None,
    repair_estimate: Optional[int] = None,
    notes: Optional[str] = None
) -> WholesaleOffer:
    """Create a wholesale offer for a lead."""
    offer = WholesaleOffer(
        offer_id=offer_id,
        lead_id=lead_id,
        offer_price=offer_price,
        arv=arv,
        repair_estimate=repair_estimate,
        notes=notes,
        status="draft"
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def list_offers_by_lead(db: Session, lead_id: int) -> List[WholesaleOffer]:
    """Get all offers for a lead."""
    return db.query(WholesaleOffer).filter(WholesaleOffer.lead_id == lead_id).all()


def update_offer_status(db: Session, offer_id: int, status: str) -> WholesaleOffer:
    """Update offer status."""
    offer = db.query(WholesaleOffer).filter(WholesaleOffer.id == offer_id).first()
    if offer:
        offer.status = status
        offer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(offer)
    return offer


def create_buyer_profile(
    db: Session,
    buyer_id: str,
    name: str,
    contact: Optional[str] = None,
    criteria: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None
) -> BuyerProfile:
    """Create a buyer profile."""
    buyer = BuyerProfile(
        buyer_id=buyer_id,
        name=name,
        contact=contact,
        criteria=criteria,
        notes=notes,
        status="active"
    )
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


def list_buyers(db: Session, status: str = "active") -> List[BuyerProfile]:
    """List all buyers."""
    return db.query(BuyerProfile).filter(BuyerProfile.status == status).all()


def create_assignment(
    db: Session,
    assignment_id: str,
    lead_id: int,
    assignment_fee: int,
    buyer_id: Optional[int] = None,
    buyer_name: Optional[str] = None,
    buyer_contact: Optional[str] = None,
    notes: Optional[str] = None
) -> AssignmentRecord:
    """Create an assignment record."""
    assignment = AssignmentRecord(
        assignment_id=assignment_id,
        lead_id=lead_id,
        buyer_id=buyer_id,
        buyer_name=buyer_name,
        buyer_contact=buyer_contact,
        assignment_fee=assignment_fee,
        notes=notes,
        status="draft"
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def get_assignments_by_lead(db: Session, lead_id: int) -> List[AssignmentRecord]:
    """Get all assignments for a lead."""
    return db.query(AssignmentRecord).filter(AssignmentRecord.lead_id == lead_id).all()


def get_pipeline_summary(db: Session) -> Dict[str, int]:
    """Get summary of leads by stage."""
    leads = db.query(WholesaleLead).all()
    summary = {stage: 0 for stage in ["new", "contacted", "inspection", "offer_sent", "negotiating", "contract_signed", "assigned", "closed"]}
    for lead in leads:
        if lead.stage in summary:
            summary[lead.stage] += 1
    return summary


def create_pipeline_snapshot(
    db: Session,
    snapshot_id: str,
    by_stage: Dict[str, int],
    hot_leads: int = 0,
    active_offers: int = 0,
    ready_for_assignment: int = 0,
    notes: Optional[str] = None
) -> WholesalePipelineSnapshot:
    """Create a pipeline snapshot."""
    total = sum(by_stage.values())
    snapshot = WholesalePipelineSnapshot(
        snapshot_id=snapshot_id,
        date=datetime.utcnow(),
        total_leads=total,
        by_stage=by_stage,
        hot_leads=hot_leads,
        active_offers=active_offers,
        ready_for_assignment=ready_for_assignment,
        notes=notes
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
