"""
Automation service for applying pipeline rules to deals.
"""

import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from ..models.match import DealBrief

logger = logging.getLogger(__name__)


def run_automation_rules(db: Session, deal: DealBrief) -> dict:
    """
    Apply deterministic automation rules to a deal based on its current state.
    
    Rules applied in order:
    - Rule A: Initialize disposition for pipeline deals
    - Rule B: Acknowledge buyer review status
    - Rule C: No-op for dead deals
    - Rule D: Move to pipeline if recommendation suggests it
    - Rule E: Default no-action
    
    Args:
        db: Database session
        deal: DealBrief object to apply rules to
    
    Returns:
        dict with deal_id, headline, status, disposition_status, action_taken, message
    """
    
    action_taken = "no_action"
    message = "No automation action applied"
    status = deal.status
    disposition_status = deal.disposition_status
    
    # Rule A: Initialize disposition for pipeline deals
    if status == "pipeline" and not disposition_status:
        disposition_status = "new"
        action_taken = "initialized_disposition"
        message = "Disposition initialized to 'new' for pipeline deal"
        deal.disposition_status = disposition_status
        db.commit()
    
    # Rule B: Awaiting buyer review
    elif status == "pipeline" and disposition_status == "buyer_review":
        action_taken = "awaiting_buyer_review"
        message = "Deal awaiting buyer review"
    
    # Rule C: Dead deal
    elif status == "dead":
        action_taken = "no_action_dead_deal"
        message = "No automation for dead deals"
    
    # Rule D: Move to pipeline based on recommendation
    elif status == "active":
        try:
            pipeline_ready = False
            
            # Check if analysis_data exists and indicates pipeline readiness
            if hasattr(deal, "analysis_data") and deal.analysis_data:
                try:
                    analysis = (
                        json.loads(deal.analysis_data)
                        if isinstance(deal.analysis_data, str)
                        else deal.analysis_data
                    )
                    # Check various indicators that deal should be in pipeline
                    if (
                        analysis.get("recommendation_status") == "move_to_pipeline"
                        or analysis.get("pipeline_ready") is True
                        or analysis.get("recommendation_score", 0) > 0.7
                    ):
                        pipeline_ready = True
                except Exception as e:
                    logger.debug(f"Error parsing analysis_data: {e}")
            
            # Check if there's a recommendation field indicating pipeline move
            if (
                hasattr(deal, "recommendation")
                and deal.recommendation
                and deal.recommendation.get("action") == "move_to_pipeline"
            ):
                pipeline_ready = True
            
            if pipeline_ready:
                status = "pipeline"
                if not disposition_status:
                    disposition_status = "new"
                action_taken = "moved_to_pipeline"
                message = "Deal moved to pipeline based on analysis/recommendation"
                deal.status = status
                deal.disposition_status = disposition_status
                db.commit()
        except Exception as e:
            logger.error(f"Error in Rule D automation: {e}")
    
    # Rule E: Default no-action (already set above)
    
    return {
        "deal_id": deal.id,
        "headline": deal.headline,
        "status": status,
        "disposition_status": disposition_status,
        "action_taken": action_taken,
        "message": message,
    }
