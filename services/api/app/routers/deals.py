"""
Deals router for managing deal briefs (independent of full property records).
Includes input sanitization and validation to prevent malformed data issues.
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
from ..schemas.match import DealBriefIn, DealBriefOut, DealActionIn

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
