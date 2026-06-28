from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import (
    HeimdallDeal,
    HeimdallTask,
    HeimdallApproval,
    HeimdallMessage,
)
from app.heimdall.models.property_intel import HeimdallPropertyIntel


def serialize_dt(value):
    """Serialize datetime to ISO format string."""
    return value.isoformat() if value else None


def get_heimdall_dashboard(db: Session) -> Dict[str, Any]:
    """
    Complete dashboard snapshot: all properties, deals, tasks, approvals, messages.
    
    Returns:
    - Summary counts by state/status
    - All active records grouped by type
    """
    
    deals = db.query(HeimdallDeal).all()
    tasks = db.query(HeimdallTask).all()
    approvals = db.query(HeimdallApproval).all()
    messages = db.query(HeimdallMessage).all()
    properties = db.query(HeimdallPropertyIntel).all()

    # Count by state/status
    deals_by_state: Dict[str, int] = {}
    properties_by_status: Dict[str, int] = {}

    for deal in deals:
        deals_by_state[deal.state] = deals_by_state.get(deal.state, 0) + 1

    for prop in properties:
        properties_by_status[prop.research_status] = (
            properties_by_status.get(prop.research_status, 0) + 1
        )

    # Filter active records
    open_tasks = [t for t in tasks if t.status in ["OPEN", "PENDING"]]
    pending_approvals = [a for a in approvals if a.status == "PENDING"]
    draft_messages = [
        m
        for m in messages
        if m.status in ["DRAFT", "DRAFT_PENDING_APPROVAL", "READY_TO_SEND"]
    ]

    return {
        "summary": {
            "total_properties": len(properties),
            "properties_by_status": properties_by_status,
            "total_deals": len(deals),
            "deals_by_state": deals_by_state,
            "open_tasks": len(open_tasks),
            "pending_approvals": len(pending_approvals),
            "draft_or_ready_messages": len(draft_messages),
        },
        "properties": [
            {
                "id": p.id,
                "address": p.address,
                "city": p.city,
                "research_status": p.research_status,
                "distress_score": p.distress_score,
                "lead_lane": p.lead_lane,
                "ownership_verified": p.ownership_verified,
                "outreach_allowed": p.outreach_allowed,
                "converted_to_lead": p.converted_to_lead,
                "created_at": serialize_dt(p.created_at),
                "updated_at": serialize_dt(p.updated_at),
            }
            for p in properties
        ],
        "deals": [
            {
                "id": d.id,
                "state": d.state,
                "property_address": d.property_address,
                "data": d.data,
                "created_at": serialize_dt(d.created_at),
                "updated_at": serialize_dt(d.updated_at),
            }
            for d in deals
        ],
        "open_tasks": [
            {
                "id": t.id,
                "deal_id": t.deal_id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "owner_role": t.owner_role,
                "data": t.data,
            }
            for t in open_tasks
        ],
        "pending_approvals": [
            {
                "id": a.id,
                "deal_id": a.deal_id,
                "approval_type": a.approval_type,
                "status": a.status,
                "data": a.data,
            }
            for a in pending_approvals
        ],
        "messages": [
            {
                "id": m.id,
                "deal_id": m.deal_id,
                "recipient_type": m.recipient_type,
                "status": m.status,
                "data": m.data,
            }
            for m in draft_messages
        ],
    }


def get_property_dashboard(db: Session) -> Dict[str, Any]:
    """
    Detailed property intel dashboard (newest first).
    
    Returns:
    - Full property records with distress scores, research status, notes
    """
    
    properties = db.query(HeimdallPropertyIntel).order_by(
        HeimdallPropertyIntel.created_at.desc()
    ).all()

    return {
        "count": len(properties),
        "records": [
            {
                "id": p.id,
                "address": p.address,
                "city": p.city,
                "province_or_state": p.province_or_state,
                "country": p.country,
                "research_status": p.research_status,
                "distress_score": p.distress_score,
                "lead_lane": p.lead_lane,
                "ownership_verified": p.ownership_verified,
                "outreach_allowed": p.outreach_allowed,
                "converted_to_lead": p.converted_to_lead,
                "property_data": p.property_data,
                "distress_analysis": p.distress_analysis,
                "notes": p.notes,
                "created_at": serialize_dt(p.created_at),
                "updated_at": serialize_dt(p.updated_at),
            }
            for p in properties
        ],
    }


def get_action_queue(db: Session) -> Dict[str, Any]:
    """
    Queue of pending actions: approvals, tasks, messages.
    
    Returns:
    - PENDING approvals (waiting for decision)
    - OPEN/PENDING tasks (waiting for assignment/execution)
    - DRAFT_PENDING_APPROVAL and READY_TO_SEND messages (waiting for send)
    """
    
    approvals = db.query(HeimdallApproval).filter(
        HeimdallApproval.status == "PENDING"
    ).all()

    tasks = db.query(HeimdallTask).filter(
        HeimdallTask.status.in_(["OPEN", "PENDING"])
    ).all()

    messages = db.query(HeimdallMessage).filter(
        HeimdallMessage.status.in_(["DRAFT_PENDING_APPROVAL", "READY_TO_SEND"])
    ).all()

    return {
        "pending_approvals": [
            {
                "id": a.id,
                "deal_id": a.deal_id,
                "approval_type": a.approval_type,
                "status": a.status,
                "data": a.data,
            }
            for a in approvals
        ],
        "open_tasks": [
            {
                "id": t.id,
                "deal_id": t.deal_id,
                "title": t.title,
                "priority": t.priority,
                "owner_role": t.owner_role,
                "status": t.status,
                "data": t.data,
            }
            for t in tasks
        ],
        "messages_waiting": [
            {
                "id": m.id,
                "deal_id": m.deal_id,
                "recipient_type": m.recipient_type,
                "status": m.status,
                "data": m.data,
            }
            for m in messages
        ],
    }
