"""
Buyers router for managing buyer profiles and preferences.
PERSISTENT: All buyers are stored in DB, not in-memory.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.match import Buyer, DealBrief
from ..models.buyer_candidate import BuyerCandidate
from ..models.deal_buyer_match import DealBuyerMatch
from ..models.deal_notification import DealNotification
from ..schemas.match import BuyerIn, BuyerOut, MatchComputeOut, MatchHit
from ..schemas.buyer import BuyerCandidateIn, BuyerCandidateOut, DealBuyerMatchIn, DealBuyerMatchOut
from ..core.matcher import score_buyer_vs_deal
from ..audit.service import log_event
from ..audit.schemas import AuditEventCreate
from ..services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buyers", tags=["buyers"])


@router.post("", response_model=BuyerOut)
def add_buyer(
    payload: BuyerIn, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key),
    request: Request = None
):
    """Create a new buyer and log audit event."""
    row = Buyer(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    
    # Log audit event
    try:
        log_event(db, AuditEventCreate(
            actor="system",
            action="buyer_created",
            target=f"buyer_{row.id}",
            result="success",
            meta={"buyer_id": row.id, "buyer_name": row.name}
        ))
    except Exception as e:
        print(f"Warning: Could not log audit event: {e}")
    
    return row


@router.get("", response_model=List[BuyerOut])
def list_buyers(
    active: bool | None = None, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """List all buyers, optionally filtered by active status."""
    q = db.query(Buyer)
    if active is not None:
        q = q.filter(Buyer.active.is_(active))
    return q.order_by(Buyer.id.desc()).limit(500).all()


@router.get("/{buyer_id}", response_model=BuyerOut)
def get_buyer(
    buyer_id: int, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Get a specific buyer by ID."""
    buyer = db.get(Buyer, buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail=f"buyer {buyer_id} not found")
    return buyer


@router.post("/{buyer_id}/toggle")
def toggle_buyer(
    buyer_id: int, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Toggle buyer active status."""
    r = db.get(Buyer, buyer_id)
    if not r:
        raise HTTPException(status_code=404, detail="buyer not found")
    r.active = not r.active
    db.commit()
    db.refresh(r)
    return {"ok": True, "active": r.active}


@router.post("/match/{deal_id}", response_model=MatchComputeOut)
def match_buyer_to_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """
    Match a deal to all active buyers and return ranked matches.
    
    Returns:
    - mode: "deal->buyers"
    - total: number of matching buyers
    - hits: List[MatchHit] with buyer_id, buyer_name, score, reasons
    """
    # Get the deal
    deal = db.get(DealBrief, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail=f"deal {deal_id} not found")
    
    # Get all active buyers
    buyers = db.query(Buyer).filter(Buyer.active.is_(True)).all()
    
    # Score each buyer against the deal
    hits: List[MatchHit] = []
    for buyer in buyers:
        score, reasons = score_buyer_vs_deal(buyer, deal)
        if score >= 0.25:  # minimum threshold
            hits.append(MatchHit(
                buyer_id=buyer.id,
                buyer_name=buyer.name,
                score=round(score, 4),
                reasons=reasons
            ))
    
    # Sort by score descending
    hits.sort(key=lambda x: x.score, reverse=True)
    
    # Log the matching action
    try:
        log_event(db, AuditEventCreate(
            actor="system",
            action="deal_buyer_match",
            target=f"deal_{deal_id}",
            result="success",
            meta={
                "deal_id": deal_id,
                "total_matches": len(hits),
                "top_buyer_id": hits[0]["buyer_id"] if hits else None
            }
        ))
    except Exception as e:
        print(f"Warning: Could not log audit event: {e}")
    
    return MatchComputeOut(
        mode="deal->buyers",
        total=len(hits),
        hits=hits[:20]  # Return top 20
    )


# ============================================================================
# NEW LIGHTWEIGHT BUYER MATCHING LAYER
# ============================================================================

@router.get("/candidates/list", response_model=List[BuyerCandidateOut])
def list_buyer_candidates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all buyer candidates (no auth required).
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of BuyerCandidateOut objects
    """
    try:
        candidates = db.query(BuyerCandidate).offset(skip).limit(limit).all()
        logger.info(f"Listed {len(candidates)} buyer candidates")
        return candidates
    except Exception as err:
        logger.error(f"Failed to list buyer candidates: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to list candidates", "message": str(err)}
        )


@router.post("/candidates/seed", response_model=List[BuyerCandidateOut])
def seed_test_candidates(db: Session = Depends(get_db)):
    """
    Create 5 test buyer candidates if none exist (no auth required).
    
    Useful for development and testing the buyer matching system.
    
    Args:
        db: Database session
    
    Returns:
        List of created candidates or existing if already seeded
    """
    try:
        # Check if candidates already exist
        existing_count = db.query(BuyerCandidate).count()
        if existing_count > 0:
            logger.info(f"Candidates already exist ({existing_count} total), skipping seed")
            return db.query(BuyerCandidate).limit(5).all()
        
        # Create test candidates
        test_candidates = [
            BuyerCandidate(
                name="John Smith - Flip Specialist",
                email="john@flipinvestments.com",
                phone="555-0101",
                buy_box="Single family homes, 3-4 beds, $200k-$400k, good bones, need cosmetics",
                notes="Prefers properties that need cosmetic work. Experienced flipper."
            ),
            BuyerCandidate(
                name="Real Estate Capital Partners",
                email="deals@recappartners.com",
                phone="555-0102",
                buy_box="Multi-unit properties, 2-10 units, $500k-$2M, established tenants preferred",
                notes="Looking for BRRRR opportunities. Needs minimum 6% cap rate."
            ),
            BuyerCandidate(
                name="Sarah Williams - Wholesaler",
                email="sarah.wholesale@email.com",
                phone="555-0103",
                buy_box="Off-market deals, any property type, below market value required",
                notes="Focuses on wholesale strategy. High volume buyer."
            ),
            BuyerCandidate(
                name="Strategic Acquisitions LLC",
                email="acquisitions@strat-acq.com",
                phone="555-0104",
                buy_box="Commercial properties, retail/office, $1M+, stabilized preferred",
                notes="Institutional buyer. Requires professional underwriting."
            ),
            BuyerCandidate(
                name="Local Investor Group",
                email="info@localinvestors.net",
                phone="555-0105",
                buy_box="Properties in metro area, any type, $100k-$500k range",
                notes="Active local buyer. Quick closing capability."
            ),
        ]
        
        for candidate in test_candidates:
            db.add(candidate)
        
        db.commit()
        
        logger.info(f"Seeded {len(test_candidates)} test buyer candidates")
        return test_candidates
        
    except Exception as err:
        logger.error(f"Failed to seed test candidates: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to seed candidates", "message": str(err)}
        )


@router.get("/{deal_id}/matches", response_model=List[DealBuyerMatchOut])
def list_deal_matches(
    deal_id: int,
    db: Session = Depends(get_db)
):
    """
    List all buyer matches for a deal (no auth required).
    
    Args:
        deal_id: ID of the deal
        db: Database session
    
    Returns:
        List of DealBuyerMatchOut objects
    
    Raises:
        HTTPException: If deal not found
    """
    try:
        # Validate deal exists
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for matches: {deal_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        matches = db.query(DealBuyerMatch).filter(DealBuyerMatch.deal_id == deal_id).all()
        logger.info(f"Listed {len(matches)} buyer matches for deal {deal_id}")
        return matches
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to list deal matches: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to list matches", "message": str(err)}
        )


@router.post("/{deal_id}/matches", response_model=DealBuyerMatchOut)
def create_or_update_deal_match(
    deal_id: int,
    payload: DealBuyerMatchIn,
    db: Session = Depends(get_db)
):
    """
    Create or update a buyer match for a deal (no auth required).
    
    If a match already exists, update it. Otherwise create new.
    
    Match statuses:
    - candidate: Initial match
    - contacted: Buyer has been contacted
    - interested: Buyer expressed interest
    - passed: Buyer passed on the deal
    - assigned: Deal assigned to this buyer
    
    Args:
        deal_id: ID of the deal
        payload: Match data (buyer_id, match_status, notes)
        db: Database session
    
    Returns:
        Created or updated DealBuyerMatchOut
    
    Raises:
        HTTPException: If deal or buyer not found
    """
    try:
        # Validate deal exists
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for match: {deal_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # Validate buyer exists
        buyer = db.query(BuyerCandidate).filter(BuyerCandidate.id == payload.buyer_id).first()
        if not buyer:
            logger.warning(f"Buyer not found for match: {payload.buyer_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "Buyer not found", "buyer_id": payload.buyer_id}
            )
        
        # Validate match status
        valid_statuses = ["candidate", "contacted", "interested", "passed", "assigned"]
        if payload.match_status not in valid_statuses:
            logger.warning(f"Invalid match status: {payload.match_status}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid match status",
                    "message": f"Status must be one of: {valid_statuses}",
                    "provided": payload.match_status
                }
            )
        
        # Check if match already exists
        existing_match = db.query(DealBuyerMatch).filter(
            DealBuyerMatch.deal_id == deal_id,
            DealBuyerMatch.buyer_id == payload.buyer_id
        ).first()
        
        if existing_match:
            # Update existing match
            old_status = existing_match.match_status
            existing_match.match_status = payload.match_status
            existing_match.notes = payload.notes
            db.commit()
            db.refresh(existing_match)
            
            # Log audit event
            log_audit_event(
                db=db,
                deal_id=deal_id,
                event_type="buyer_match_updated",
                message=f"Buyer match updated: {buyer.name} ({old_status} -> {payload.match_status})",
                metadata={
                    "buyer_id": payload.buyer_id,
                    "buyer_name": buyer.name,
                    "old_status": old_status,
                    "new_status": payload.match_status
                }
            )
            
            logger.info(
                f"Deal {deal_id} buyer match updated: buyer {payload.buyer_id} "
                f"({old_status} -> {payload.match_status})"
            )
            
            match = existing_match
        else:
            # Create new match
            match = DealBuyerMatch(
                deal_id=deal_id,
                buyer_id=payload.buyer_id,
                match_status=payload.match_status,
                notes=payload.notes
            )
            db.add(match)
            db.commit()
            db.refresh(match)
            
            # Log audit event
            log_audit_event(
                db=db,
                deal_id=deal_id,
                event_type="buyer_match_created",
                message=f"Buyer match created: {buyer.name} ({payload.match_status})",
                metadata={
                    "buyer_id": payload.buyer_id,
                    "buyer_name": buyer.name,
                    "match_status": payload.match_status
                }
            )
            
            logger.info(
                f"Deal {deal_id} buyer match created: buyer {payload.buyer_id} "
                f"(status={payload.match_status})"
            )
        
        # Create notification if assigned
        if payload.match_status == "assigned":
            notification = DealNotification(
                deal_id=deal_id,
                type="buyer_assigned",
                title=f"Deal Assigned to {buyer.name}",
                message=f"This deal has been assigned to buyer: {buyer.name}. Contact: {buyer.email or buyer.phone or 'N/A'}",
                is_read=False
            )
            db.add(notification)
            db.commit()
            
            logger.info(f"Assigned notification created for deal {deal_id}, buyer {payload.buyer_id}")
        
        return match
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to create/update buyer match: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to create/update match", "message": str(err)}
        )
