# services/api/app/services/deal_finalization.py

from __future__ import annotations

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.contract_record import ContractRecord
from app.models.document_route import DocumentRoute
from app.models.pro_task_link import ProfessionalTaskLink

# Configuration for finalization requirements
REQUIRED_CONTRACT_STATUS = "signed"
REQUIRED_DOC_ROUTE_STATUS = "acknowledged"
REQUIRED_TASK_STATUS = "done"


def check_deal_ready_for_finalization(db: Session, deal_id: int) -> Dict[str, Any]:
    """
    Check if a deal is ready for finalization by validating:
    1. At least one signed contract exists
    2. All document routes are acknowledged
    3. All professional tasks are done
    
    Returns checklist breakdown and overall ready flag.
    """

    # 1) Check contracts - need at least one signed
    contracts = db.query(ContractRecord).filter(ContractRecord.deal_id == deal_id).all()
    has_signed_contract = any(c.status == REQUIRED_CONTRACT_STATUS for c in contracts)

    # 2) Check document routes - all must be acknowledged
    routes = db.query(DocumentRoute).filter(DocumentRoute.deal_id == deal_id).all()
    if routes:
        all_required_docs_ack = all(r.status == REQUIRED_DOC_ROUTE_STATUS for r in routes)
    else:
        # No documents required = automatically satisfied
        all_required_docs_ack = True

    # 3) Check professional tasks - all must be done
    links = db.query(ProfessionalTaskLink).filter(ProfessionalTaskLink.deal_id == deal_id).all()
    if links:
        all_tasks_done = all(l.status == REQUIRED_TASK_STATUS for l in links)
    else:
        # No tasks = automatically satisfied
        all_tasks_done = True

    # Build checklist
    checklist = {
        "has_signed_contract": has_signed_contract,
        "all_required_docs_acknowledged": all_required_docs_ack,
        "all_professional_tasks_done": all_tasks_done,
    }

    # Overall ready flag
    ready = all(checklist.values())

    return {
        "deal_id": deal_id,
        "ready": ready,
        "checklist": checklist,
    }


def finalize_deal(db: Session, deal_id: int) -> Dict[str, Any]:
    """
    Finalize a deal if all requirements are met.
    
    If not ready, returns checklist with finalized=False.
    If ready, marks deal as finalized (placeholder for actual deal model update).
    """

    status = check_deal_ready_for_finalization(db, deal_id)
    
    if not status["ready"]:
        status["finalized"] = False
        return status

    # TODO: Update actual Deal model when integrated
    # Example (uncomment and adapt to your deal model):
    # from app.models.deal import Deal
    # deal = db.query(Deal).filter(Deal.id == deal_id).first()
    # if deal:
    #     deal.status = "finalized"
    #     db.commit()
    #     db.refresh(deal)

    status["finalized"] = True
    return status


def get_finalization_requirements() -> Dict[str, str]:
    """
    Get the current finalization requirements configuration.
    Useful for documentation and debugging.
    """
    return {
        "required_contract_status": REQUIRED_CONTRACT_STATUS,
        "required_doc_route_status": REQUIRED_DOC_ROUTE_STATUS,
        "required_task_status": REQUIRED_TASK_STATUS,
    }
