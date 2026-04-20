"""
Deals router for managing deal briefs (independent of full property records).
Includes input sanitization and validation to prevent malformed data issues.
UPDATE TRIGGER: 2026-04-19T02:40:00Z - Ensure endpoint registration
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..core.sanitization import (
    sanitize_input,
    sanitize_deal_data,
    validate_deal_fields,
    log_sanitization_details,
)
from ..models.match import DealBrief
from ..schemas.match import DealBriefIn, DealBriefOut, DealActionIn, DealAnalysis, DealAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("", response_model=DealBriefOut)
def add_deal(
    payload: DealBriefIn, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """
    Create a new deal brief with input sanitization and validation.
    
    Args:
        payload: Deal data from request body
        db: Database session
        _: Builder key authentication
    
    Returns:
        Created deal brief with sanitized data
    
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Convert Pydantic model to dictionary
        deal_dict = payload.model_dump()
        
        logger.info(f"Creating deal with data: {deal_dict}")
        
        # Log original data before sanitization
        original_data = deal_dict.copy()
        
        # Sanitize all fields
        sanitized_data = sanitize_deal_data(deal_dict)
        
        # Log sanitization changes
        log_sanitization_details(original_data, sanitized_data)
        
        # Validate sanitized data
        is_valid, error_message = validate_deal_fields(sanitized_data)
        if not is_valid:
            logger.warning(f"Deal validation failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid data", "message": error_message}
            )
        
        # Create deal with sanitized data
        row = DealBrief(**sanitized_data)
        db.add(row)
        db.commit()
        db.refresh(row)
        
        logger.info(f"Deal created successfully with id: {row.id}")
        return row
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to create deal: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create deal", "message": str(err)}
        )


@router.get("", response_model=List[DealBriefOut])
def list_deals(
    status: str | None = None, 
    db: Session = Depends(get_db)
):
    """
    List all deals with optional status filtering.
    
    Args:
        status: Optional status filter (e.g., 'active')
        db: Database session
    
    Returns:
        List of deal briefs, limited to 500 most recent
    """
    try:
        q = db.query(DealBrief)
        
        if status:
            # Sanitize status parameter
            sanitized_status = sanitize_input(status)
            logger.info(f"Filtering deals by status: {sanitized_status}")
            q = q.filter(DealBrief.status == sanitized_status)
        
        deals = q.order_by(DealBrief.id.desc()).limit(500).all()
        logger.info(f"Retrieved {len(deals)} deals from database")
        return deals
        
    except Exception as err:
        logger.error(f"Failed to list deals: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve deals", "message": str(err)}
        )


@router.post("/{deal_id}/action", response_model=DealBriefOut)
def update_deal_action(
    deal_id: int,
    payload: DealActionIn,
    db: Session = Depends(get_db)
):
    """
    Update a deal's status based on an action.
    
    Maps actions to status values:
    - analyze -> status = "analyzing"
    - hot -> status = "hot"
    - dead -> status = "dead"
    - pipeline -> status = "pipeline"
    
    Args:
        deal_id: ID of the deal to update
        payload: Action to perform
        db: Database session
    
    Returns:
        Updated deal brief
    
    Raises:
        HTTPException: If deal not found or invalid action
    """
    # Action to status mapping
    action_status_map = {
        "analyze": "analyzing",
        "hot": "hot",
        "dead": "dead",
        "pipeline": "pipeline"
    }
    
    try:
        # Validate action
        action = payload.action.lower() if payload.action else None
        if action not in action_status_map:
            logger.warning(f"Invalid action: {action}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid action",
                    "message": f"Action must be one of: {list(action_status_map.keys())}",
                    "provided": action
                }
            )
        
        # Find the deal
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found: {deal_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # Update status based on action
        new_status = action_status_map[action]
        old_status = deal.status
        deal.status = new_status
        
        db.commit()
        db.refresh(deal)
        
        logger.info(f"Deal {deal_id} updated: {old_status} -> {new_status} (action: {action})")
        return deal
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to update deal action: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to update deal", "message": str(err)}
        )


@router.post("/{deal_id}/analyze", response_model=DealAnalysisResponse)
def score_deal(
    deal_id: int,
    db: Session = Depends(get_db)
):
    """
    Perform a first-pass analysis of a deal based on available fields.
    
    Analysis includes:
    - score: 0-100 based on property characteristics
    - risk: low, medium, high
    - strategy: flip, brrrr, wholesale, hold, unknown
    - recommendation: actionable text
    
    Args:
        deal_id: ID of the deal to analyze
        db: Database session
    
    Returns:
        DealAnalysisResponse with deal info and analysis
    
    Raises:
        HTTPException: If deal not found
    """
    try:
        # Find the deal
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for analysis: {deal_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # Initialize analysis
        score = 50
        risk = "low"
        strategy = "unknown"
        recommendation = "Additional analysis needed"
        
        # Price-based scoring
        if deal.price is None:
            score = 40
            risk = "high"
            recommendation = "Need more data - price missing"
        else:
            price = float(deal.price)
            
            # Risk assessment by price
            if price >= 1000000:
                risk = "medium"
            elif price < 500000:
                score = min(100, score + 10)
        
        # Property type strategy mapping
        prop_type = (deal.property_type or "").lower()
        
        if "multi" in prop_type or "duplex" in prop_type:
            strategy = "brrrr"
        elif any(t in prop_type for t in ["condo", "townhouse", "sfh", "semi"]):
            strategy = "flip"
        else:
            strategy = "wholesale"
        
        # Notes analysis
        notes_text = (deal.notes or "").lower()
        cash_flow_keywords = ["cash flow", "rental", "tenant", "lease", "income"]
        
        if any(kw in notes_text for kw in cash_flow_keywords):
            strategy = "brrrr" if strategy in ["brrrr", "unknown"] else "hold"
            score = min(100, score + 15)
        
        # Beds/baths completeness bonus
        if deal.beds is not None and deal.baths is not None:
            score = min(100, score + 5)
        else:
            score = max(0, score - 10)
        
        # Generate recommendation based on score
        if score >= 80:
            recommendation = "Strong candidate, proceed to underwriting"
        elif score >= 60:
            recommendation = "Acceptable deal, perform detailed analysis"
        elif score >= 40:
            recommendation = "Marginal opportunity, needs careful review"
        else:
            recommendation = "High risk profile - caution advised"
        
        # Build analysis response
        analysis = DealAnalysis(
            score=score,
            risk=risk,
            strategy=strategy,
            recommendation=recommendation
        )
        
        logger.info(f"Analysis complete for deal {deal_id}: score={score}, strategy={strategy}, risk={risk}")
        
        return DealAnalysisResponse(
            deal_id=deal.id,
            headline=deal.headline,
            analysis=analysis
        )
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to analyze deal: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to analyze deal", "message": str(err)}
        )
