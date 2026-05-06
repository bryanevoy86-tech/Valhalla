"""
VA (Virtual Assistant) Intake router - database-backed, production version.

Flow:
1. VA submits raw lead info via /lead endpoint
2. Heimdall scores it using distress signals, contact info, source quality
3. If qualified (score >= 75), lead is queued for Bryan approval
4. After approval, lead can convert to deal via existing /deals flow
5. All leads tracked with source metadata and audit logging
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.db import get_db
from app.schemas.va_intake import VALeadIntakeCreate, VALeadIntakeResult
from app.services.heimdall_lead_intake import score_lead
from app.models.va_lead import VALead
from app.models.va_approval_queue import VAApprovalQueue
from app.services.va_audit_service import log_va_event, get_lead_audit_trail, get_approval_audit_trail
from app.services.approval_service import approve_lead, deny_lead, get_pending_approvals
from app.services.lead_conversion_service import convert_lead_to_deal, get_deal_from_va_lead

router = APIRouter(prefix="/api/va-intake", tags=["VA Intake"])


@router.post("/lead", response_model=VALeadIntakeResult)
def submit_va_lead(payload: VALeadIntakeCreate, db: Session = Depends(get_db)):
    """
    Submit a VA intake lead.
    
    - Scores using Heimdall logic (distress signals, contact info, source quality)
    - Saves to database (persistent)
    - If qualified (score >= 75), queues for approval
    - Returns analysis and next steps
    """
    data = payload.model_dump()

    # Score the lead
    analysis = score_lead(data)
    
    # Create lead record in database
    lead = VALead(
        source_platform=data.get("source_platform"),
        source_type=data.get("source_type", "manual_va"),
        source_url=data.get("source_url"),
        address=data.get("address"),
        city=data.get("city", "Winnipeg"),
        province=data.get("province", "MB"),
        seller_name=data.get("seller_name"),
        seller_phone=data.get("seller_phone"),
        seller_email=data.get("seller_email"),
        asking_price=Decimal(str(data.get("asking_price"))) if data.get("asking_price") else None,
        raw_text=data.get("raw_text"),
        va_notes=data.get("va_notes"),
        strategy_fit=data.get("strategy_fit", "wholesale"),
        submitted_by=data.get("submitted_by", "va"),
        heimdall_score=analysis["heimdall_score"],
        risk_level=analysis["risk_level"],
        confidence=analysis["confidence"],
        recommended_action=analysis["recommended_action"],
        status=analysis["lead_status"],
        stage=analysis["next_pipeline_stage"],
    )
    
    db.add(lead)
    db.flush()
    lead_id = lead.id
    
    # Create approval queue entry if needed
    if analysis["approval_required"]:
        approval = VAApprovalQueue(
            entity_type="lead",
            entity_id=lead_id,
            va_lead_id=lead_id,
            status="pending",
            recommended_action=analysis["recommended_action"],
            heimdall_score=analysis["heimdall_score"],
            risk_level=analysis["risk_level"],
            assigned_to="bryan"
        )
        db.add(approval)
        db.flush()
        approval_id = approval.id
    else:
        approval_id = None
    
    db.commit()
    
    # Log the event
    log_va_event(
        actor="va",
        action="lead_submitted",
        entity_type="va_lead",
        entity_id=lead_id,
        details=f"Lead submitted from {data.get('source_platform')}. Address: {data.get('address')}",
        db=db
    )
    
    # Log scoring
    log_va_event(
        actor="system",
        action="lead_scored",
        entity_type="va_lead",
        entity_id=lead_id,
        details=analysis["reasoning_summary"],
        new_value=str(analysis["heimdall_score"]),
        db=db
    )
    
    return {
        "success": True,
        "lead_id": str(lead_id),
        "lead_status": analysis["lead_status"],
        "source_platform": data.get("source_platform"),
        "heimdall_score": analysis["heimdall_score"],
        "risk_level": analysis["risk_level"],
        "confidence": analysis["confidence"],
        "recommended_action": analysis["recommended_action"],
        "approval_required": analysis["approval_required"],
        "next_pipeline_stage": analysis["next_pipeline_stage"],
        "reasoning_summary": analysis["reasoning_summary"],
    }


@router.get("/leads")
def list_va_leads(db: Session = Depends(get_db), status: str = None, limit: int = 50):
    """List all VA intake leads, optionally filtered by status."""
    query = db.query(VALead)
    
    if status:
        query = query.filter(VALead.status == status)
    
    leads = query.order_by(VALead.created_at.desc()).limit(limit).all()
    
    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "address": lead.address,
            "seller_name": lead.seller_name,
            "asking_price": float(lead.asking_price) if lead.asking_price else None,
            "source_platform": lead.source_platform,
            "heimdall_score": lead.heimdall_score,
            "risk_level": lead.risk_level,
            "status": lead.status,
            "stage": lead.stage,
            "deal_id": lead.deal_id,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
        })
    
    return {
        "success": True,
        "count": len(result),
        "items": result,
    }


@router.get("/leads/{lead_id}")
def get_va_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific VA lead with full details."""
    lead = db.query(VALead).filter(VALead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get associated approval if it exists
    approval = db.query(VAApprovalQueue).filter(
        VAApprovalQueue.va_lead_id == lead_id
    ).first()
    
    return {
        "success": True,
        "lead": {
            "id": lead.id,
            "source_platform": lead.source_platform,
            "source_type": lead.source_type,
            "source_url": lead.source_url,
            "address": lead.address,
            "city": lead.city,
            "province": lead.province,
            "seller_name": lead.seller_name,
            "seller_phone": lead.seller_phone,
            "seller_email": lead.seller_email,
            "asking_price": float(lead.asking_price) if lead.asking_price else None,
            "raw_text": lead.raw_text,
            "va_notes": lead.va_notes,
            "strategy_fit": lead.strategy_fit,
            "heimdall_score": lead.heimdall_score,
            "risk_level": lead.risk_level,
            "confidence": lead.confidence,
            "status": lead.status,
            "stage": lead.stage,
            "deal_id": lead.deal_id,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
        },
        "approval": {
            "id": approval.id,
            "status": approval.status,
            "assigned_to": approval.assigned_to,
        } if approval else None,
        "audit_trail": get_lead_audit_trail(lead_id, db)
    }


@router.get("/approvals/pending")
def list_pending_approvals(db: Session = Depends(get_db), limit: int = 50):
    """List all pending approvals."""
    approvals = get_pending_approvals(db, limit)
    
    return {
        "success": True,
        "count": len(approvals),
        "items": approvals,
    }


@router.post("/approvals/{approval_id}/approve")
def approve_va_lead(approval_id: int, approved_by: str = "bryan", db: Session = Depends(get_db)):
    """Approve a lead for the next pipeline step."""
    result = approve_lead(approval_id, approved_by, db)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/approvals/{approval_id}/deny")
def deny_va_lead(approval_id: int, denied_by: str = "bryan", reason: str = "", db: Session = Depends(get_db)):
    """Deny a lead approval."""
    result = deny_lead(approval_id, denied_by, reason, db)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/leads/{lead_id}/convert-to-deal")
def convert_lead_to_real_deal(lead_id: int, converted_by: str = "system", db: Session = Depends(get_db)):
    """Convert an approved VA lead into a real deal."""
    result = convert_lead_to_deal(lead_id, converted_by, db)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/leads/{lead_id}/deal")
def get_deal_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get the deal associated with a VA lead."""
    result = get_deal_from_va_lead(lead_id, db)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    
    return result


@router.get("/leads/{lead_id}/audit")
def get_lead_audit(lead_id: int, db: Session = Depends(get_db)):
    """Get complete audit trail for a lead."""
    lead = db.query(VALead).filter(VALead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    audit_trail = get_lead_audit_trail(lead_id, db)
    
    return {
        "success": True,
        "lead_id": lead_id,
        "audit_trail": audit_trail,
    }
