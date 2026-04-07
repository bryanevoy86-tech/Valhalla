"""
Heimdall v0.1 Router - API endpoints for deal analysis and stage management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_builder_key
from app.services.heimdall_service import analyze_deal, advance_stage_with_approval

router = APIRouter(prefix="/heimdall", tags=["heimdall"])


# ===== REQUEST/RESPONSE SCHEMAS =====

class AnalyzeDealResponse(BaseModel):
    """Response from analyze endpoint."""
    deal_id: int
    analysis_timestamp: str
    current_stage: str
    deal_data: dict
    offer_data: Optional[dict]
    contract_data: Optional[dict]
    buyer_match_data: Optional[dict]
    missing_fields: list
    blocker_flags: list
    risk_flags: list
    recommendations: dict

    class Config:
        from_attributes = True


class AdvanceStagRequest(BaseModel):
    """Request to advance deal stage."""
    requested_stage: str
    approved_by: str
    reason: str
    override_reason: Optional[str] = None


class AdvanceStagResponse(BaseModel):
    """Response from advance stage endpoint."""
    deal_id: int
    action: str
    previous_stage: Optional[str]
    new_stage: Optional[str]
    approved_by: Optional[str]
    timestamp: str
    result: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    blocker_overrides: list = []

    class Config:
        from_attributes = True


# ===== ENDPOINTS =====

@router.post("/deals/{deal_id}/analyze", response_model=AnalyzeDealResponse)
def heimdall_analyze_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Analyze a deal and return recommendations.

    Returns:
    - current_stage: Deal's current stage
    - deal_data: Relevant deal metrics
    - missing_fields: Fields required for next stage
    - blocker_flags: Blockers preventing progress
    - risk_flags: Warnings and risks
    - recommendations: Recommended next steps

    No side effects - read-only analysis.
    """
    try:
        analysis = analyze_deal(deal_id, db)
        return analysis.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/deals/{deal_id}/advance-stage", response_model=AdvanceStagResponse)
def heimdall_advance_stage(
    deal_id: int,
    request: AdvanceStagRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key),
):
    """
    Advance a deal to a new stage with explicit approval.

    Request body:
    - requested_stage: Target stage (must be valid transition)
    - approved_by: Who is approving this advancement
    - reason: Why is this advancement being made
    - override_reason: (optional) If advancing despite blockers, why

    Returns:
    - previous_stage: Stage before advancement
    - new_stage: Stage after advancement
    - result: "success" or "rejected"
    - reason: Explanation if rejected

    Creates audit entries for all actions.
    """
    try:
        result = advance_stage_with_approval(
            deal_id=deal_id,
            requested_stage=request.requested_stage,
            approved_by=request.approved_by,
            reason=request.reason,
            override_reason=request.override_reason,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stage advancement failed: {str(e)}")
