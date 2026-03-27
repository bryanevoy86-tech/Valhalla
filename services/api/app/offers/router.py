"""
Offer router for HTTP API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.db import get_db
from app.offers.models import Offer
from app.offers.schemas import OfferCreate, OfferOut, OfferUpdate
from app.offers import service as offer_service

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
async def create_offer(offer: OfferCreate, db: Session = Depends(get_db)):
    """Create a new offer on a deal."""
    try:
        db_offer = offer_service.create_offer(db, offer)
        
        # Log creation
        try:
            from sqlalchemy import text
            db.execute(text("""
                INSERT INTO audit_logs (entity_type, entity_id, action, new_value, notes, created_at)
                VALUES (:entity_type, :entity_id, :action, :new_value, :notes, :created_at)
            """), {
                "entity_type": "offer",
                "entity_id": db_offer.id,
                "action": "created",
                "new_value": f'{{"offer_price": {db_offer.offer_price}, "deal_id": {db_offer.deal_id}}}',
                "notes": f"Offer created for deal {db_offer.deal_id}",
                "created_at": datetime.utcnow()
            })
            db.commit()
        except Exception as e:
            print(f"Audit log failed: {e}")
        
        return db_offer
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{offer_id}", response_model=OfferOut)
async def get_offer(offer_id: int, db: Session = Depends(get_db)):
    """Get a specific offer by ID."""
    db_offer = offer_service.get_offer_by_id(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return db_offer


@router.get("/deals/{deal_id}", response_model=List[OfferOut])
async def get_offers_for_deal(deal_id: int, db: Session = Depends(get_db)):
    """Get all offers for a specific deal."""
    return offer_service.get_offers_for_deal(db, deal_id)


@router.patch("/{offer_id}", response_model=OfferOut)
async def update_offer(offer_id: int, update: OfferUpdate, db: Session = Depends(get_db)):
    """Update an offer."""
    db_offer = offer_service.update_offer(db, offer_id, update)
    if not db_offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    
    # Log update
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO audit_logs (entity_type, entity_id, action, notes, created_at)
            VALUES (:entity_type, :entity_id, :action, :notes, :created_at)
        """), {
            "entity_type": "offer",
            "entity_id": offer_id,
            "action": "updated",
            "notes": f"Offer updated",
            "created_at": datetime.utcnow()
        })
        db.commit()
    except Exception as e:
        print(f"Audit log failed: {e}")
    
    return db_offer
