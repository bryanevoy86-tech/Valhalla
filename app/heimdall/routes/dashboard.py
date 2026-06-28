from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.dashboard_service import (
    get_heimdall_dashboard,
    get_property_dashboard,
    get_action_queue,
)

router = APIRouter(
    prefix="/heimdall/dashboard",
    tags=["Heimdall Dashboard"],
)


@router.get("/main")
def main_dashboard(db: Session = Depends(get_db)):
    """
    Complete Heimdall dashboard snapshot.
    
    Returns:
    - Summary counts: total properties, deals, tasks, approvals, messages
    - Grouped by status/state
    - All active records (properties, deals, open tasks, pending approvals, draft messages)
    
    Use this for WeWeb main dashboard view showing system-wide overview.
    """
    return get_heimdall_dashboard(db)


@router.get("/properties")
def property_dashboard(db: Session = Depends(get_db)):
    """
    Detailed property intelligence dashboard (newest first).
    
    Returns:
    - Full property records with distress scores, research status, lead lanes
    - Property data (owner name, address, contact)
    - Distress analysis
    - Notes / response history
    - Conversion status
    
    Use this for WeWeb property pipeline view showing all drive-for-dollars prospects.
    """
    return get_property_dashboard(db)


@router.get("/action-queue")
def action_queue(db: Session = Depends(get_db)):
    """
    Queue of pending actions awaiting human decision or execution.
    
    Returns:
    - PENDING approvals (outreach letters, deal packets, messages waiting approval)
    - OPEN/PENDING tasks (call owner, follow up, verify data, manual review)
    - Messages waiting approval or ready to send
    
    Use this for WeWeb action center / task list view.
    Prioritize by:
    - Approvals: CRITICAL > HIGH > MEDIUM > LOW
    - Tasks: CRITICAL > HIGH > MEDIUM > LOW
    - Messages: DRAFT_PENDING_APPROVAL (needs approval) > READY_TO_SEND (can send)
    """
    return get_action_queue(db)
