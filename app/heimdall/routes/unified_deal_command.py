from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.unified_deal_command_engine import unified_deal_command

router = APIRouter(prefix="/heimdall/command", tags=["Heimdall Deal Command"])


class UnifiedDealCommandRequest(BaseModel):
    lead: Dict[str, Any]
    underwriting: Dict[str, Any]
    buyer_demand: Dict[str, Any]
    market: Dict[str, Any]
    deal: Dict[str, Any]
    buyers: List[Dict[str, Any]] = []


@router.post("/deal")
def command_deal(payload: UnifiedDealCommandRequest):
    """
    Unified deal command engine: orchestrates all scoring engines into one recommendation.
    
    Possible commands:
    - PASS_OR_HOLD: Critical red flag detected
    - HOLD_MISSING_INFORMATION: Required data missing
    - RESEARCH_MARKET_BEFORE_PROCEEDING: Market not approved
    - BUILD_BUYER_LIST_FIRST: Buyer demand too weak
    - SOURCE_OR_MATCH_BUYERS_FIRST: No matched buyers
    - RENEGOTIATE: Price exceeds MAO
    - STRONG_CANDIDATE_APPROVAL_REQUIRED: All gates green, score 85+
    - POSSIBLE_DEAL_MORE_DUE_DILIGENCE: Deal viable, score 70+
    - PASS_OR_NURTURE: Score too weak
    
    Returns:
    - heimdall_command: Top-level command + reasoning + next steps
    - subsystem_results: All scoring engine outputs for review
    - human_approval_required: Always true
    - legal_review_required_before_contract: Always true
    """
    return unified_deal_command(payload.model_dump())
