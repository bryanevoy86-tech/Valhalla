"""
Deal service layer for persistent deal management.

Business logic for CRUD operations, stage transitions, and scoring.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from app.deals.models import Deal, DealStage, DealStatus
from app.deals.schemas import DealCreate, DealScoreUpdate, DealStageUpdate, DealUpdate


# Valid stage transitions with restrictions
ALLOWED_STAGE_TRANSITIONS = {
    "lead_received": ["intake_review", "dead"],
    "intake_review": ["underwrite_ready", "dead"],
    "underwrite_ready": ["offer_ready", "dead"],
    "offer_ready": ["offer_sent", "dead"],
    "offer_sent": ["contract_pending", "dead"],
    "contract_pending": ["contract_signed", "dead"],
    "contract_signed": ["buyer_matching", "dead"],
    "buyer_matching": ["dispo_ready", "dead"],
    "dispo_ready": ["closed", "dead"],
    "closed": ["dead"],  # Can only go to dead once closed
    "dead": [],  # Terminal state - no transitions
}


def create_deal(db: Session, lead_id: int, deal: DealCreate) -> Deal:
    """
    Create a new deal from a lead.
    
    Args:
        db: Database session
        lead_id: ID of the lead
        deal: Deal creation data
    
    Returns:
        Deal: Created deal entity
    """
    # Verify lead exists
    from app.leads.models import Lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    db_deal = Deal(
        lead_id=lead_id,
        title=deal.title,
        stage=deal.stage or "lead_received",
        status=deal.status or "active",
        arv=deal.arv,
        estimated_repair_cost=deal.estimated_repair_cost,
        max_allowable_offer=deal.max_allowable_offer,
        target_assignment_fee=deal.target_assignment_fee,
        score=deal.score or Decimal(0),
        notes=deal.notes,
        disposition_status=deal.disposition_status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal


def create_deal_direct(db: Session, deal_data) -> Deal:
    """
    Create a standalone deal with optional lead_id.
    
    If lead_id is not provided, creates a placeholder/system lead automatically.
    
    Args:
        db: Database session
        deal_data: Deal creation data (DealCreateDirect schema)
    
    Returns:
        Deal: Created deal entity
    """
    from app.leads.models import Lead
    
    lead_id = deal_data.lead_id
    
    if lead_id:
        # Verify lead exists
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
    else:
        # Create a placeholder lead for standalone deal
        placeholder_lead = Lead(
            lead_name=f"Deal: {deal_data.title}",
            lead_email="system@internal.local",
            lead_phone="000-000-0000",
            lead_status="converted",
            source="api_direct",
            notes=f"Placeholder lead for direct deal creation: {deal_data.notes}" if deal_data.notes else "Placeholder lead for direct deal creation",
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow(),
        )
        db.add(placeholder_lead)
        db.flush()
        lead_id = placeholder_lead.id
    
    # Create the deal
    db_deal = Deal(
        lead_id=lead_id,
        title=deal_data.title,
        stage=deal_data.stage or "lead_received",
        status=deal_data.status or "active",
        arv=deal_data.arv,
        estimated_repair_cost=deal_data.estimated_repair_cost,
        max_allowable_offer=deal_data.max_allowable_offer,
        target_assignment_fee=deal_data.target_assignment_fee,
        score=deal_data.score or Decimal(0),
        notes=deal_data.notes,
        disposition_status=deal_data.disposition_status,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal


def get_all_deals(db: Session, skip: int = 0, limit: int = 100) -> List[Deal]:
    """Get all deals with pagination."""
    return db.query(Deal).offset(skip).limit(limit).all()


def get_deal_by_id(db: Session, deal_id: int) -> Optional[Deal]:
    """Get a specific deal by ID."""
    return db.query(Deal).filter(Deal.id == deal_id).first()


def get_deals_by_lead(db: Session, lead_id: int) -> List[Deal]:
    """Get all deals for a specific lead."""
    return db.query(Deal).filter(Deal.lead_id == lead_id).all()


def get_deals_by_stage(db: Session, stage: str) -> List[Deal]:
    """Get all deals in a specific stage."""
    return db.query(Deal).filter(Deal.stage == stage).all()


def update_deal(db: Session, deal_id: int, update: DealUpdate) -> Optional[Deal]:
    """
    Update deal fields.
    
    Args:
        db: Database session
        deal_id: ID of deal to update
        update: Update data
    
    Returns:
        Deal: Updated deal or None if not found
    """
    db_deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not db_deal:
        return None
    
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_deal, key, value)
    
    db_deal.updated_ts = datetime.utcnow()
    db.commit()
    db.refresh(db_deal)
    return db_deal


def update_deal_score(db: Session, deal_id: int, score_update: DealScoreUpdate) -> Optional[Deal]:
    """
    Update deal score with optional notes.
    
    Args:
        db: Database session
        deal_id: ID of deal to update
        score_update: Score and notes
    
    Returns:
        Deal: Updated deal or None if not found
    """
    db_deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not db_deal:
        return None
    
    db_deal.score = score_update.score
    if score_update.notes:
        db_deal.notes = score_update.notes
    
    db_deal.updated_ts = datetime.utcnow()
    db.commit()
    db.refresh(db_deal)
    return db_deal


def update_deal_stage(
    db: Session,
    deal_id: int,
    stage_update: DealStageUpdate,
    override_reason: Optional[str] = None
) -> Optional[Deal]:
    """
    Update deal stage with validation of allowed transitions.
    
    Args:
        db: Database session
        deal_id: ID of deal to update
        stage_update: New stage and optional override
        override_reason: Optional reason for override
    
    Returns:
        Deal: Updated deal or None if not found
        
    Raises:
        ValueError: If stage transition is not allowed
    """
    db_deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not db_deal:
        return None
    
    old_stage = db_deal.stage
    new_stage = stage_update.new_stage
    
    # Check if transition is allowed
    allowed = ALLOWED_STAGE_TRANSITIONS.get(old_stage, [])
    if new_stage not in allowed:
        msg = f"Cannot transition from {old_stage} to {new_stage}"
        if not stage_update.override_reason:
            raise ValueError(msg)
        # If override_reason provided, log it but allow transition
        print(f"WARNING: {msg} (override: {stage_update.override_reason})")
    
    # Log to deal_stage_history
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO deal_stage_history (deal_id, old_stage, new_stage, override_reason, created_at)
            VALUES (:deal_id, :old_stage, :new_stage, :override_reason, :created_at)
        """), {
            "deal_id": deal_id,
            "old_stage": old_stage,
            "new_stage": new_stage,
            "override_reason": stage_update.override_reason,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Failed to log stage transition: {e}")
    
    # Update deal
    db_deal.stage = new_stage
    db_deal.updated_ts = datetime.utcnow()
    db.commit()
    db.refresh(db_deal)
    return db_deal


def delete_deal(db: Session, deal_id: int) -> bool:
    """Delete a deal."""
    db_deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not db_deal:
        return False
    db.delete(db_deal)
    db.commit()
    return True
