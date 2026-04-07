"""
Offer service layer for persistent offer management.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.offers.models import Offer
from app.offers.schemas import OfferCreate, OfferUpdate


def create_offer(db: Session, offer: OfferCreate) -> Offer:
    """
    Create a new offer on a deal.
    
    Args:
        db: Database session
        offer: Offer creation data
    
    Returns:
        Offer: Created offer entity
    """
    # Verify deal exists
    from app.deals.models import Deal
    deal = db.query(Deal).filter(Deal.id == offer.deal_id).first()
    if not deal:
        raise ValueError(f"Deal {offer.deal_id} not found")
    
    db_offer = Offer(
        deal_id=offer.deal_id,
        offer_price=offer.offer_price,
        emd_amount=offer.emd_amount,
        closing_window_days=offer.closing_window_days,
        conditions_summary=offer.conditions_summary,
        generated_by=offer.generated_by,
        status=offer.status or "draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    return db_offer


def get_all_offers(db: Session, skip: int = 0, limit: int = 100) -> List[Offer]:
    """Get all offers with pagination."""
    return db.query(Offer).offset(skip).limit(limit).all()


def get_offer_by_id(db: Session, offer_id: int) -> Optional[Offer]:
    """Get a specific offer by ID."""
    return db.query(Offer).filter(Offer.id == offer_id).first()


def get_offers_for_deal(db: Session, deal_id: int) -> List[Offer]:
    """Get all offers for a specific deal."""
    return db.query(Offer).filter(Offer.deal_id == deal_id).all()


def update_offer(db: Session, offer_id: int, update: OfferUpdate) -> Optional[Offer]:
    """
    Update an offer.
    
    Args:
        db: Database session
        offer_id: ID of offer to update
        update: Update data
    
    Returns:
        Offer: Updated offer or None if not found
    """
    db_offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not db_offer:
        return None
    
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_offer, key, value)
    
    db_offer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_offer)
    return db_offer


def delete_offer(db: Session, offer_id: int) -> bool:
    """Delete an offer."""
    db_offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not db_offer:
        return False
    db.delete(db_offer)
    db.commit()
    return True
