from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.jarvis_audit import log_event
from app.services.jarvis_interactions import add_interaction
from app.services.jarvis_store import get_contact, load_contacts, mark_actioned
from app.services.heimdall_scoring import score_contact

router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _choose_channel(contact: dict[str, Any]) -> str:
    """Smart channel selection respecting consent preferences."""
    if contact.get("consent_sms"):
        return "sms"
    if contact.get("consent_email"):
        return "email"
    return "phone"


@router.get("/dashboard")
async def heimdall_dashboard() -> dict[str, Any]:
    """Dashboard with live Community contacts and explainable scoring."""
    contacts = load_contacts()
    open_contacts = [c for c in contacts if c.get("status") != "closed"]

    scored = []
    for contact in open_contacts:
        result = score_contact(contact)
        scored.append({**contact, "_score": result["score"], "_priority": result["priority"]})

    top = max(scored, key=lambda x: x["_score"], default=None)

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Heimdall has analyzed your live contact system",
        "generated_at": _now_iso(),
        "summary": {
            "total_contacts": len(contacts),
            "open_contacts": len(open_contacts),
            "high_priority_contacts": sum(1 for c in scored if c["_priority"] == "high"),
            "top_contact": top["name"] if top else None,
            "top_contact_score": top["_score"] if top else None,
        },
    }


@router.get("/hot-contacts")
async def heimdall_hot_contacts() -> dict[str, Any]:
    """List all contacts ranked by Heimdall scoring with explanations."""
    contacts = load_contacts()

    ranked = []
    for contact in contacts:
        scoring = score_contact(contact)
        ranked.append(
            {
                **contact,
                "heimdall_score": scoring["score"],
                "priority": scoring["priority"],
                "why": scoring["why"],
            }
        )

    ranked.sort(key=lambda x: x["heimdall_score"], reverse=True)

    return {
        "ok": True,
        "agent": "Heimdall",
        "count": len(ranked),
        "items": ranked,
    }


@router.get("/next-actions")
async def heimdall_next_actions() -> dict[str, Any]:
    """Prioritized next actions with scoring explanations."""
    contacts = load_contacts()

    actions: list[dict[str, Any]] = []
    for contact in contacts:
        if contact.get("status") == "closed":
            continue

        scoring = score_contact(contact)
        channel = _choose_channel(contact)

        action = {
            "contact_id": contact["id"],
            "contact_name": contact["name"],
            "priority": scoring["priority"],
            "heimdall_score": scoring["score"],
            "action": f"Follow up via {channel}",
            "channel": channel,
            "reason": contact.get("reason"),
            "script": contact.get("recommended_script"),
            "why": scoring["why"],
            "heat_score": contact.get("heat_score"),
            "days_stale": contact.get("days_stale"),
            "status": contact.get("status"),
        }
        actions.append(action)

    actions.sort(key=lambda x: x["heimdall_score"], reverse=True)

    return {
        "ok": True,
        "agent": "Heimdall",
        "generated_at": _now_iso(),
        "count": len(actions),
        "items": actions,
    }


@router.post("/recommend-action")
async def heimdall_recommend_action(payload: dict[str, Any]) -> dict[str, Any]:
    """Get action recommendation with scoring explanation."""
    contact_id = payload.get("contact_id")
    context = payload.get("context")

    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")

    contact = get_contact(int(contact_id))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    scoring = score_contact(contact)
    channel = _choose_channel(contact)

    recommendation = {
        "agent": "Heimdall",
        "contact_id": contact["id"],
        "contact": contact["name"],
        "channel": channel,
        "priority": scoring["priority"],
        "heimdall_score": scoring["score"],
        "reason": contact.get("reason"),
        "script": contact.get("recommended_script"),
        "why": scoring["why"],
        "context": context,
    }

    log_event("recommend_action", recommendation)

    return {
        "ok": True,
        **recommendation,
    }


@router.post("/run-playbook")
async def heimdall_run_playbook(payload: dict[str, Any]) -> dict[str, Any]:
    """Trigger an automation playbook."""
    event = {
        "agent": "Heimdall",
        "event": "playbook_triggered",
        "payload": payload,
        "timestamp": _now_iso(),
        "status": "queued",
    }

    log_event("run_playbook", event)

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Playbook queued",
        "event": event,
    }


@router.post("/mark-actioned")
async def heimdall_mark_actioned(payload: dict[str, Any]) -> dict[str, Any]:
    """Mark action complete, track interaction, reset staleness."""
    contact_id = payload.get("contact_id")
    action_type = payload.get("action_type", "manual_followup")
    notes = payload.get("notes")

    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")

    updated = mark_actioned(int(contact_id), action_type)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found in local tracking store")

    interaction = add_interaction(
        contact_id=int(contact_id),
        contact_name=updated["name"],
        interaction_type=action_type,
        notes=notes or f"Action recorded by Heimdall at {updated['last_action_at']}",
    )

    event = {
        "agent": "Heimdall",
        "event": "mark_actioned",
        "contact_id": updated["id"],
        "contact_name": updated["name"],
        "action_type": action_type,
        "timestamp": updated["last_action_at"],
        "interaction_logged": interaction,
    }
    log_event("mark_actioned", event)

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Contact marked as actioned",
        "contact": updated,
        "interaction": interaction,
    }
