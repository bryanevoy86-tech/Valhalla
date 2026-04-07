"""
Deal router for HTTP API endpoints.

Exposes CRUD operations for deal management with stage transitions and scoring.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.db import get_db
from app.deals.models import Deal
from app.deals.schemas import DealCreate, DealOut, DealScoreUpdate, DealStageUpdate, DealUpdate, DealCreateDirect
from app.deals import service as deal_service
from app.deals.validation import validate_deal_data

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/from-lead/{lead_id}", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal_from_lead(lead_id: int, deal: DealCreate, db: Session = Depends(get_db)):
    """
    Create a new deal from a lead.
    
    Transitions the lead into the deal intake pipeline.
    """
    try:
        deal.lead_id = lead_id  # Ensure lead_id matches URL
        db_deal = deal_service.create_deal(db, lead_id, deal)
        
        # Log creation
        try:
            from sqlalchemy import text
            db.execute(text("""
                INSERT INTO audit_logs (entity_type, entity_id, action, new_value, notes, created_at)
                VALUES (:entity_type, :entity_id, :action, :new_value, :notes, :created_at)
            """), {
                "entity_type": "deal",
                "entity_id": db_deal.id,
                "action": "created",
                "new_value": f'{{"title": "{db_deal.title}", "stage": "{db_deal.stage}"}}',
                "notes": f"Deal created from lead {lead_id}",
                "created_at": datetime.utcnow()
            })
            db.commit()
        except Exception as e:
            print(f"Audit log failed: {e}")
        
        return db_deal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal_direct(deal: DealCreateDirect, db: Session = Depends(get_db)):
    """
    Create a new deal directly (standalone) with input validation and sanitization.
    
    If lead_id is not provided, automatically creates a placeholder lead.
    This endpoint allows creating deals without first creating a lead.
    
    Security:
    - Removes HTML tags and script injections from string fields
    - Validates numeric fields (non-negative, within reasonable bounds)
    - Validates choice fields against allowed values
    - Scores capped at 0-100 range
    """
    try:
        # Convert Pydantic model to dict for sanitization
        deal_dict = deal.dict(exclude_unset=False)
        
        # Validate and sanitize input
        sanitized_data = validate_deal_data(deal_dict)
        
        # Reconstruct the model with sanitized data
        sanitized_deal = DealCreateDirect(**sanitized_data)
        
        # Create the deal with sanitized data
        db_deal = deal_service.create_deal_direct(db, sanitized_deal)
        
        # Log creation with security context
        try:
            from sqlalchemy import text
            db.execute(text("""
                INSERT INTO audit_logs (entity_type, entity_id, action, new_value, notes, created_at)
                VALUES (:entity_type, :entity_id, :action, :new_value, :notes, :created_at)
            """), {
                "entity_type": "deal",
                "entity_id": db_deal.id,
                "action": "created",
                "new_value": f'{{"title": "{db_deal.title}", "stage": "{db_deal.stage}"}}',
                "notes": f"Deal created directly via API (input sanitized)",
                "created_at": datetime.utcnow()
            })
            db.commit()
        except Exception as e:
            print(f"Audit log failed: {e}")
        
        return db_deal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process deal data: {str(e)}"
        )


@router.get("", response_model=List[DealOut])
async def list_deals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all deals with pagination."""
    try:
        deals = deal_service.get_all_deals(db, skip=skip, limit=limit)
        return deals
    except Exception as e:
        import traceback
        print("\n" + "="*70)
        print("🔴 === DEALS ENDPOINT ERROR (GET /api/deals) ===")
        print("="*70)
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {str(e)}")
        print("\nFull Traceback:")
        traceback.print_exc()
        print("="*70 + "\n")
        raise


@router.get("/{deal_id}", response_model=DealOut)
async def get_deal(deal_id: int, db: Session = Depends(get_db)):
    """Get a specific deal by ID."""
    db_deal = deal_service.get_deal_by_id(db, deal_id)
    if not db_deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return db_deal


@router.patch("/{deal_id}", response_model=DealOut)
async def update_deal(deal_id: int, update: DealUpdate, db: Session = Depends(get_db)):
    """Update deal fields."""
    db_deal = deal_service.update_deal(db, deal_id, update)
    if not db_deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    
    # Log update
    try:
        from sqlalchemy import text
        update_dict = update.dict(exclude_unset=True)
        db.execute(text("""
            INSERT INTO audit_logs (entity_type, entity_id, action, new_value, notes, created_at)
            VALUES (:entity_type, :entity_id, :action, :new_value, :notes, :created_at)
        """), {
            "entity_type": "deal",
            "entity_id": deal_id,
            "action": "updated",
            "new_value": str(update_dict),
            "notes": f"Deal fields updated",
            "created_at": datetime.utcnow()
        })
        db.commit()
    except Exception as e:
        print(f"Audit log failed: {e}")
    
    return db_deal


@router.patch("/{deal_id}/score", response_model=DealOut)
async def update_deal_score(deal_id: int, score_update: DealScoreUpdate, db: Session = Depends(get_db)):
    """Update deal score."""
    db_deal = deal_service.update_deal_score(db, deal_id, score_update)
    if not db_deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    
    # Log score change
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (entity_type, entity_id, action, new_value, notes, created_at)
            VALUES (:entity_type, :entity_id, :action, :new_value, :notes, :created_at)
        """), {
            "entity_type": "deal",
            "entity_id": deal_id,
            "action": "score_updated",
            "new_value": f'{{"score": {score_update.score}}}',
            "notes": f"Deal score updated to {score_update.score}",
            "created_at": datetime.utcnow()
        })
        db.commit()
    except Exception as e:
        print(f"Audit log failed: {e}")
    
    return db_deal


@router.patch("/{deal_id}/stage", response_model=DealOut)
async def update_deal_stage(deal_id: int, stage_update: DealStageUpdate, db: Session = Depends(get_db)):
    """
    Update deal stage with validation of allowed transitions.
    
    Only allows transitions defined in the stage rules. Provide override_reason
    to force a transition that violates stage rules (for emergency/manual override).
    """
    try:
        db_deal = deal_service.update_deal_stage(db, deal_id, stage_update)
        if not db_deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        return db_deal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
