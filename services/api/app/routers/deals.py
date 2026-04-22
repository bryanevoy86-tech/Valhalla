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
from ..core.dependencies import require_builder_key, require_auth
from ..core.sanitization import (
    sanitize_input,
    sanitize_deal_data,
    validate_deal_fields,
    log_sanitization_details,
)
from ..models.match import DealBrief
from ..models.deal_notification import DealNotification
from ..schemas.match import DealBriefIn, DealBriefOut, DealActionIn, DealAnalysis, DealAnalysisResponse, ApplyRecommendationResponse, DealDispositionIn, AutomationRuleResponse
from ..schemas.deal_notifications import DealNotificationOut, DealNotificationIn
from ..services.audit_service import log_audit_event
from ..services.automation_service import run_automation_rules

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
        
        # Log audit event
        log_audit_event(
            db=db,
            deal_id=row.id,
            event_type="deal_created",
            message=f"Deal created: {row.headline}",
            metadata={"headline": row.headline, "status": row.status}
        )
        
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


@router.post("/ui-create", response_model=DealBriefOut)
def create_deal_from_ui(
    payload: DealBriefIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Create a deal from WeWeb frontend without requiring BUILDER_KEY.
    
    Frontend-safe endpoint for creating deals. Uses same validation and 
    sanitization as authenticated endpoint but without key requirement.
    
    Args:
        payload: Deal data from WeWeb form
        db: Database session
    
    Returns:
        Created deal brief
    
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate headline is present
        if not payload.headline or not payload.headline.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "headline is required"}
            )
        
        # Convert to dictionary
        deal_dict = payload.model_dump()
        
        # Default status to "active" if missing or empty
        if not deal_dict.get("status") or deal_dict.get("status") == "":
            deal_dict["status"] = "active"
        
        logger.info(f"Creating deal from UI: {payload.headline}")
        
        # Log original data
        original_data = deal_dict.copy()
        
        # Sanitize all fields
        sanitized_data = sanitize_deal_data(deal_dict)
        
        # Log sanitization changes
        log_sanitization_details(original_data, sanitized_data)
        
        # Validate sanitized data
        is_valid, error_message = validate_deal_fields(sanitized_data)
        if not is_valid:
            logger.warning(f"UI deal validation failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid data", "message": error_message}
            )
        
        # Create deal with sanitized data
        row = DealBrief(**sanitized_data)
        db.add(row)
        db.commit()
        db.refresh(row)
        
        logger.info(f"UI deal created successfully with id: {row.id}")
        return row
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to create UI deal: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create deal", "message": str(err)}
        )


@router.post("/{deal_id}/action", response_model=DealBriefOut)
def update_deal_action(
    deal_id: int,
    payload: DealActionIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
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
        
        # Log audit event
        log_audit_event(
            db=db,
            deal_id=deal_id,
            event_type="deal_action",
            message=f"Deal action performed: {action}",
            metadata={"action": action, "old_status": old_status, "new_status": new_status}
        )
        
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
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
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
        
        # Log audit event
        log_audit_event(
            db=db,
            deal_id=deal.id,
            event_type="deal_analyzed",
            message=f"Deal analyzed: score={score}, risk={risk}",
            metadata={"score": score, "risk": risk, "strategy": strategy}
        )
        
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


@router.post("/{deal_id}/apply-recommendation", response_model=ApplyRecommendationResponse)
def apply_recommendation(
    deal_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Apply a recommendation to a deal (automation execution layer).
    
    Re-runs first-pass analysis logic server-side and applies status changes
    for pipeline and dead recommendations. Safe to call repeatedly.
    
    Recommendation logic:
    - if score >= 80 and risk == "low" -> next_step = "pipeline" (UPDATE status)
    - if score >= 60 and risk == "medium" -> next_step = "review" (NO status change)
    - if score < 60 or risk == "high" -> next_step = "dead" (UPDATE status)
    - otherwise -> next_step = "needs_more_data" (NO status change)
    
    Args:
        deal_id: ID of the deal
        db: Database session
    
    Returns:
        ApplyRecommendationResponse with recommendation and applied status
    
    Raises:
        HTTPException: If deal not found
    """
    try:
        # Find the deal
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for recommendation: {deal_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # ===== SCORE DEAL (Same logic as /analyze endpoint) =====
        score = 50
        risk = "low"
        strategy = "unknown"
        
        # Price-based scoring
        if deal.price is None:
            score = 40
            risk = "high"
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
        
        # ===== DETERMINE NEXT STEP (Deterministic automation logic) =====
        next_step = None
        status_applied = None
        message = ""
        
        if score >= 80 and risk == "low":
            next_step = "pipeline"
            status_applied = "pipeline"
            message = f"Strong candidate: score={score}, risk={risk}. Status updated to pipeline."
        elif score >= 60 and risk == "medium":
            next_step = "review"
            message = f"Acceptable deal: score={score}, risk={risk}. Requires detailed review."
        elif score < 60 or risk == "high":
            next_step = "dead"
            status_applied = "dead"
            message = f"High risk profile: score={score}, risk={risk}. Status updated to dead."
        else:
            next_step = "needs_more_data"
            message = f"Insufficient data: score={score}, risk={risk}. More information needed."
        
        # ===== APPLY STATUS UPDATE IF NEEDED =====
        if status_applied:
            old_status = deal.status
            deal.status = status_applied
            db.commit()
            db.refresh(deal)
            
            # Log audit event
            log_audit_event(
                db=db,
                deal_id=deal_id,
                event_type="recommendation_applied",
                message=f"Recommendation applied: {next_step}",
                metadata={"next_step": next_step, "score": score, "risk": risk, "old_status": old_status, "new_status": status_applied}
            )
            
            logger.info(f"Deal {deal_id} recommendation applied: {old_status} -> {status_applied} (score={score}, risk={risk})")
        else:
            # Log audit event (no status change)
            log_audit_event(
                db=db,
                deal_id=deal_id,
                event_type="recommendation_computed",
                message=f"Recommendation computed: {next_step} (no status change)",
                metadata={"next_step": next_step, "score": score, "risk": risk}
            )
            
            logger.info(f"Deal {deal_id} recommendation computed (no status change): {next_step} (score={score}, risk={risk})")
        
        # ===== RETURN RESULT =====
        return ApplyRecommendationResponse(
            deal_id=deal.id,
            headline=deal.headline,
            next_step=next_step,
            status_applied=status_applied,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to apply recommendation: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to apply recommendation", "message": str(err)}
        )


@router.patch("/{deal_id}/disposition", response_model=DealBriefOut)
def update_deal_disposition(
    deal_id: int,
    payload: DealDispositionIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Update deal disposition status and notes (lightweight buyer routing layer).
    
    Allows pipeline-ready deals to be routed into disposition states with notes.
    Safe for frontend to call without requiring authentication.
    
    Disposition statuses:
    - new: Initial pipeline entry
    - buyer_review: Under buyer review
    - offer_out: Offer sent to buyer
    - assigned: Assigned to specific buyer/agent
    - closed: Deal completed
    - dead: Deal abandoned
    
    Args:
        deal_id: ID of the deal
        payload: Disposition status and optional notes
        db: Database session
    
    Returns:
        Updated deal brief with disposition info
    
    Raises:
        HTTPException: If deal not found
    """
    try:
        # Validate disposition_status
        valid_statuses = ["new", "buyer_review", "offer_out", "assigned", "closed", "dead"]
        status_to_update = payload.disposition_status.lower() if payload.disposition_status else None
        
        if status_to_update not in valid_statuses:
            logger.warning(f"Invalid disposition status: {status_to_update}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid disposition status",
                    "message": f"Status must be one of: {valid_statuses}",
                    "provided": payload.disposition_status
                }
            )
        
        # Find the deal
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for disposition update: {deal_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # Update disposition fields
        old_disposition = deal.disposition_status
        deal.disposition_status = status_to_update
        deal.disposition_notes = payload.disposition_notes
        
        db.commit()
        db.refresh(deal)
        
        # Log audit event
        log_audit_event(
            db=db,
            deal_id=deal_id,
            event_type="disposition_updated",
            message=f"Disposition updated: {status_to_update}",
            metadata={"disposition_status": status_to_update, "notes": payload.disposition_notes}
        )
        
        logger.info(
            f"Deal {deal_id} disposition updated: {old_disposition} -> {status_to_update}. "
            f"Notes: {payload.disposition_notes[:50] if payload.disposition_notes else 'None'}"
        )
        
        return deal
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to update deal disposition: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to update disposition", "message": str(err)}
        )


@router.post("/{deal_id}/notify-event", response_model=DealNotificationOut)
def notify_deal_event(
    deal_id: int,
    payload: DealNotificationIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Create a notification for a deal event.
    
    Records important deal events like analysis completion, status changes, etc.
    Generates default message if not provided.
    
    Valid event types:
    - analysis_complete: Deal analysis has been completed
    - moved_to_pipeline: Deal has been moved to pipeline
    - marked_dead: Deal has been marked as dead
    - disposition_updated: Deal disposition status has been updated
    
    Args:
        deal_id: ID of the deal
        payload: Event type and optional custom message
        db: Database session
    
    Returns:
        Created DealNotificationOut
    
    Raises:
        HTTPException: If deal not found or invalid event type
    """
    try:
        # Validate event type
        valid_types = ["analysis_complete", "moved_to_pipeline", "marked_dead", "disposition_updated"]
        event_type = payload.type.lower() if payload.type else None
        
        if event_type not in valid_types:
            logger.warning(f"Invalid event type: {event_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid event type",
                    "message": f"Type must be one of: {valid_types}",
                    "provided": payload.type
                }
            )
        
        # Find the deal
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for notification: {deal_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # Generate title based on event type
        type_titles = {
            "analysis_complete": "Analysis Complete",
            "moved_to_pipeline": "Moved to Pipeline",
            "marked_dead": "Marked as Dead",
            "disposition_updated": "Disposition Updated"
        }
        
        title = f"{deal.headline} - {type_titles.get(event_type, event_type)}"
        
        # Generate default message if not provided
        if payload.message:
            message = payload.message
        else:
            default_messages = {
                "analysis_complete": f"Deal analysis completed with score and risk assessment.",
                "moved_to_pipeline": f"Deal moved to pipeline and is ready for buyer review.",
                "marked_dead": f"Deal has been marked as dead and removed from active pipeline.",
                "disposition_updated": f"Deal disposition status has been updated."
            }
            message = default_messages.get(event_type)
        
        # Create notification
        notification = DealNotification(
            deal_id=deal_id,
            type=event_type,
            title=title,
            message=message,
            is_read=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Log audit event
        log_audit_event(
            db=db,
            deal_id=deal_id,
            event_type="notification_created",
            message=f"Notification created: {event_type}",
            metadata={"notification_type": event_type, "message": message, "notification_id": notification.id}
        )
        
        logger.info(
            f"Deal notification created: deal_id={deal_id}, type={event_type}, "
            f"notification_id={notification.id}"
        )
        
        return notification
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to create deal notification: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create notification", "message": str(err)}
        )


@router.post("/{deal_id}/run-automation", response_model=AutomationRuleResponse)
def run_automation(
    deal_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Run deterministic pipeline automation rules on a deal.
    
    Applies a series of rules based on deal status and disposition to
    automatically initialize, advance, or hold deals in the pipeline.
    
    Rules applied in order:
    - Rule A: Initialize disposition for pipeline deals (set to "new" if null)
    - Rule B: Acknowledge buyer review status (deal in buyer_review returns early)
    - Rule C: No-op for dead deals (no automation)
    - Rule D: Move to pipeline if recommendation logic suggests it (status active -> pipeline)
    - Rule E: Default no-action (no applicable rule)
    
    Args:
        deal_id: ID of the deal
        db: Database session
    
    Returns:
        AutomationRuleResponse with deal info and action taken
    
    Raises:
        HTTPException: If deal not found
    """
    try:
        # Validate deal exists
        deal = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
        if not deal:
            logger.warning(f"Deal not found for automation: {deal_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Deal not found", "deal_id": deal_id}
            )
        
        # Run automation rules
        result = run_automation_rules(db, deal)
        
        # Log to audit trail
        log_audit_event(
            db=db,
            deal_id=deal_id,
            event_type="automation_rules_applied",
            message=f"Pipeline automation applied: {result['action_taken']}",
            metadata={
                "action_taken": result["action_taken"],
                "new_status": result["status"],
                "new_disposition": result["disposition_status"]
            },
            event_source="system"
        )
        
        # Create notification if action was taken
        if result["action_taken"] in ["moved_to_pipeline", "initialized_disposition"]:
            notification = DealNotification(
                deal_id=deal_id,
                type=result["action_taken"],
                title=f"Deal {result['action_taken'].replace('_', ' ').title()}",
                message=result["message"],
                is_read=False
            )
            db.add(notification)
            db.commit()
            
            logger.info(
                f"Automation notification created: deal_id={deal_id}, "
                f"type={result['action_taken']}"
            )
        
        logger.info(
            f"Deal {deal_id} automation rules applied: {result['action_taken']} "
            f"(status={result['status']}, disposition={result['disposition_status']})"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Failed to run automation rules: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to run automation", "message": str(err)}
        )
