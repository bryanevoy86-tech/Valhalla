from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.jarvis_audit import log_event
from app.services.jarvis_interactions import add_interaction
from app.services.jarvis_rules import JARVIS_RULES
from app.services.jarvis_store import (
    get_contact,
    load_contacts,
    mark_actioned,
    update_contact,
)

router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _choose_channel(contact: dict[str, Any]) -> str:
    """Smart channel selection respecting consent preferences."""
    if contact.get("consent_sms"):
        return "sms"
    elif contact.get("consent_email"):
        return "email"
    else:
        return "phone"


def _priority_for(contact: dict[str, Any]) -> str:
    """Rule-based priority from contact state and JARVIS_RULES."""
    heat = contact.get("heat_score", 0)
    days_stale = contact.get("days_stale", 0)
    contact_type = contact.get("type", "")

    # High priority: heat >= threshold
    if heat >= JARVIS_RULES.get("high_heat_threshold", 85):
        return "high"

    # High priority: buyers with fast-cash potential (heat >= 80)
    if (
        contact_type == "buyer"
        and heat >= 80
        and JARVIS_RULES.get("buyer_fast_cash_priority", True)
    ):
        return "high"

    # Medium priority: stale leads
    if days_stale >= JARVIS_RULES.get("stale_lead_days", 3):
        return "medium"

    # Low priority: everything else
    return "low"


def _script_for(contact: dict[str, Any]) -> str:
    """Generate context-aware followup script."""
    contact_type = contact.get("type", "")
    name = contact.get("name", "there")

    if contact_type == "buyer":
        return f"Hi {name}, checking in to see what you're currently looking for. How can we help?"
    else:
        return f"Hi {name}, just following up on your interest. Are you still looking to move forward?"


@router.get("/dashboard")
async def heimdall_dashboard() -> dict[str, Any]:
    """Overall system dashboard with key metrics."""
    contacts = load_contacts()
    open_contacts = [c for c in contacts if c.get("status") != "closed"]
    hot_contacts = [c for c in open_contacts if c.get("heat_score", 0) >= JARVIS_RULES.get("high_heat_threshold", 85)]
    top = max(open_contacts, key=lambda x: x.get("heat_score", 0), default=None)

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Heimdall has analyzed your system",
        "generated_at": _now_iso(),
        "summary": {
            "total_contacts": len(contacts),
            "open_contacts": len(open_contacts),
            "hot_contacts": len(hot_contacts),
            "next_best_action": "Call highest-heat stale contact",
            "top_contact": top.get("name") if top else None,
            "top_contact_heat": top.get("heat_score") if top else None,
        },
    }


@router.get("/hot-contacts")
async def heimdall_hot_contacts() -> dict[str, Any]:
    """List hot contacts ranked by heat score."""
    contacts = load_contacts()
    open_contacts = [c for c in contacts if c.get("status") != "closed"]
    ranked = sorted(open_contacts, key=lambda x: x.get("heat_score", 0), reverse=True)

    return {
        "ok": True,
        "agent": "Heimdall",
        "count": len(ranked),
        "items": ranked,
    }


@router.get("/next-actions")
async def heimdall_next_actions() -> dict[str, Any]:
    """List prioritized next actions for open, non-actioned contacts."""
    contacts = load_contacts()
    # Filter: only open and non-actioned (status != "closed" and status != "actioned")
    open_contacts = [
        c for c in contacts 
        if c.get("status") not in ("closed", "actioned")
    ]
    ranked = sorted(
        open_contacts,
        key=lambda x: (x.get("heat_score", 0), x.get("days_stale", 0)),
        reverse=True,
    )

    actions = []
    for contact in ranked:
        channel = _choose_channel(contact)
        priority = _priority_for(contact)
        script = _script_for(contact)

        action = {
            "contact_id": contact["id"],
            "contact_name": contact.get("name", "Unknown"),
            "priority": priority,
            "action": f"Follow up via {channel}",
            "channel": channel,
            "heat_score": contact.get("heat_score"),
            "days_stale": contact.get("days_stale"),
            "status": contact.get("status", "open"),
            "script": script,
        }
        actions.append(action)

    return {
        "ok": True,
        "agent": "Heimdall",
        "generated_at": _now_iso(),
        "count": len(actions),
        "items": actions,
    }


@router.post("/recommend-action")
async def heimdall_recommend_action(payload: dict[str, Any]) -> dict[str, Any]:
    """Recommend specific action for a contact with optional context."""
    contact_id = payload.get("contact_id")
    context = payload.get("context", "")

    contact = get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    channel = _choose_channel(contact)
    priority = _priority_for(contact)
    script = _script_for(contact)

    recommendation = {
        "agent": "Heimdall",
        "contact_id": contact_id,
        "contact": contact.get("name", "Unknown"),
        "type": contact.get("type", "unknown"),
        "heat_score": contact.get("heat_score"),
        "channel": channel,
        "priority": priority,
        "context": context if context else None,
        "script": script,
        "recommended_action": f"Send {channel} message with script above",
    }

    log_event("recommend_action", recommendation)

    return {
        "ok": True,
        **recommendation,
    }


@router.post("/mark-actioned")
async def heimdall_mark_actioned(payload: dict[str, Any]) -> dict[str, Any]:
    """Mark a contact action as completed and reset staleness tracking."""
    contact_id = payload.get("contact_id")
    action_type = payload.get("action_type", "followup")

    if not get_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")

    updated = mark_actioned(contact_id, action_type)

    event = {
        "agent": "Heimdall",
        "action": "mark_actioned",
        "contact_id": contact_id,
        "contact_name": updated.get("name"),
        "action_type": action_type,
        "action_count": updated.get("action_count"),
        "last_action_at": updated.get("last_action_at"),
        "days_stale_reset": True,
    }

    log_event("mark_actioned", event)
    
    # Record interaction history for future scoring evolution
    add_interaction(
        contact_id=contact_id,
        contact_name=updated.get("name", "Unknown"),
        interaction_type=action_type,
        notes=f"Action recorded by Heimdall at {updated.get('last_action_at')}",
    )

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Action recorded and contact state reset",
        "contact": updated,
    }


@router.post("/run-playbook")
async def heimdall_run_playbook(payload: dict[str, Any]) -> dict[str, Any]:
    """Trigger a playbook automation sequence."""
    event = {
        "agent": "Heimdall",
        "event": "playbook_triggered",
        "payload": payload,
        "timestamp": _now_iso(),
    }

    log_event("run_playbook", event)

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Playbook queued",
        "event": event,
    }
