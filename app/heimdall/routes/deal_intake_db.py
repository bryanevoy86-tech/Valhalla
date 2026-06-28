from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.deal_intake_db_service import run_and_persist_deal_intake

router = APIRouter(prefix="/heimdall/intake-db", tags=["Heimdall DB Deal Intake"])


class FullDealIntakeDBRequest(BaseModel):
    lead: Dict[str, Any]
    underwriting: Dict[str, Any]
    buyer_demand: Dict[str, Any]
    market: Dict[str, Any]
    deal: Dict[str, Any]
    buyers: List[Dict[str, Any]] = []


@router.post("/deal")
def intake_deal_db(payload: FullDealIntakeDBRequest, db: Session = Depends(get_db)):
    """
    Full deal intake with automatic persistence to PostgreSQL.
    
    Single endpoint to:
    1. Accept raw lead data
    2. Run complete Heimdall evaluation (all 5 scoring engines)
    3. Generate command, packets, messages, tasks
    4. Save deal record with pipeline state
    5. Save VA tasks with priorities and deadlines
    6. Save approval records (all require human review)
    7. Save seller message draft
    8. Save buyer outreach drafts
    9. Return deal_id and all saved record IDs
    
    Everything is blocked:
    - send_blocked_until_approved: True
    - contract_blocked_until_lawyer_review: True
    - human_approval_required: True
    
    Returns:
    - deal_id: Primary identifier for this deal
    - saved_task_ids: IDs of all generated VA tasks
    - saved_approval_ids: IDs of all approval records (need human decision)
    - saved_message_ids: IDs of all draft messages (seller + buyer)
    - heimdall_command: Recommendation (BUILD_BUYER_LIST_FIRST, STRONG_CANDIDATE_APPROVAL_REQUIRED, etc.)
    - pipeline: Current state and state history
    """
    return run_and_persist_deal_intake(db, payload.model_dump())
