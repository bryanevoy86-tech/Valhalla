from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.deal_intake_orchestrator import run_full_deal_intake

router = APIRouter(prefix="/heimdall/intake", tags=["Heimdall Deal Intake"])


class FullDealIntakeRequest(BaseModel):
    lead: Dict[str, Any]
    underwriting: Dict[str, Any]
    buyer_demand: Dict[str, Any]
    market: Dict[str, Any]
    deal: Dict[str, Any]
    buyers: List[Dict[str, Any]] = []


@router.post("/deal")
def intake_deal(payload: FullDealIntakeRequest):
    """
    Full deal intake orchestration endpoint.
    
    Accepts raw lead data and runs complete Heimdall evaluation chain:
    1. Unified deal command engine (runs all 5 scoring engines)
    2. Document packet preparation (for seller, lawyer, buyer, VA, accountant)
    3. Seller message drafting (tone-adaptive based on command)
    4. Buyer outreach queue (if buyers exist)
    5. VA task routing (creates actionable tasks)
    6. Pipeline state advancement (moves deal to correct stage)
    7. Approval item generation (all items requiring human review)
    
    Returns complete deal record with all subsystem outputs, approval queue,
    and guardrails (human_approval_required, send_blocked_until_approved).
    
    No data sent until human approval. Contract execution blocked until lawyer review.
    """
    return run_full_deal_intake(payload.model_dump())
