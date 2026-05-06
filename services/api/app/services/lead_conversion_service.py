"""
Lead Conversion Service - convert VA leads into real deals.
"""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.va_lead import VALead
from app.models.deal import Deal
from app.services.va_audit_service import log_va_event


def convert_lead_to_deal(lead_id: int, converted_by: str, db: Session) -> dict:
    """
    Convert an approved VA lead into a real deal in the deals pipeline.
    """
    # Get the lead
    lead = db.query(VALead).filter(VALead.id == lead_id).first()
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    # Verify it's approved
    if lead.status != "approved":
        return {"success": False, "error": f"Lead status is {lead.status}, must be 'approved'"}
    
    # Verify it's not already converted
    if lead.deal_id:
        return {"success": False, "error": f"Lead already converted to deal {lead.deal_id}"}
    
    try:
        # Build deal title from lead info
        title = f"VA Lead - {lead.address or 'Unknown'} - {lead.seller_name or 'Seller'}"
        
        # Create deal record
        deal = Deal(
            title=title,
            stage="intake",  # Starting stage
            status="active",
            lead_id=lead_id,
            notes=f"Converted from VA Lead {lead_id}\n\nVA Notes: {lead.va_notes}\n\nStrategy: {lead.strategy_fit}",
            score=Decimal(lead.heimdall_score) if lead.heimdall_score else Decimal(0),
        )
        
        # Add financial data if available
        if lead.asking_price:
            deal.arv = Decimal(str(lead.asking_price))
        
        db.add(deal)
        db.flush()  # Get the deal ID
        deal_id = deal.id
        
        # Link lead to deal
        lead.deal_id = deal_id
        lead.status = "converted"
        lead.stage = "deal_conversion"
        lead.converted_at = datetime.now(timezone.utc)
        db.add(lead)
        
        db.commit()
        
        # Log the event
        log_va_event(
            actor=converted_by,
            action="lead_converted_to_deal",
            entity_type="va_lead",
            entity_id=lead_id,
            details=f"Lead converted to deal {deal_id}. Address: {lead.address}, Asking Price: {lead.asking_price}",
            new_value=str(deal_id),
            db=db
        )
        
        return {
            "success": True,
            "lead_id": lead_id,
            "deal_id": deal_id,
            "deal_title": title,
            "conversion_status": "success"
        }
    
    except Exception as e:
        db.rollback()
        
        # Log error
        log_va_event(
            actor=converted_by,
            action="lead_conversion_failed",
            entity_type="va_lead",
            entity_id=lead_id,
            details=f"Error converting lead to deal: {str(e)}",
            status="error",
            db=db
        )
        
        return {
            "success": False,
            "error": f"Failed to convert lead to deal: {str(e)}"
        }


def get_deal_from_va_lead(lead_id: int, db: Session) -> dict:
    """
    Get the deal associated with a VA lead (if converted).
    """
    lead = db.query(VALead).filter(VALead.id == lead_id).first()
    if not lead:
        return {"success": False, "error": "Lead not found"}
    
    if not lead.deal_id:
        return {"success": False, "error": "Lead has not been converted to deal"}
    
    deal = db.query(Deal).filter(Deal.id == lead.deal_id).first()
    if not deal:
        return {"success": False, "error": "Deal not found"}
    
    return {
        "success": True,
        "lead_id": lead_id,
        "deal_id": deal.id,
        "deal_title": deal.title,
        "deal_stage": deal.stage,
        "deal_status": deal.status
    }
