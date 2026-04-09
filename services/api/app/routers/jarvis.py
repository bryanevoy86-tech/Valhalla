from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.jarvis_audit import log_event
from app.services.jarvis_interactions import add_interaction
from app.services.jarvis_store import get_contact, load_contacts, mark_actioned
from app.services.heimdall_scoring import score_contact
from app.services.heimdall_tasks import (
    create_task,
    complete_task,
    get_pending_tasks,
    load_tasks,
    create_task_if_missing,
    get_completed_tasks_needing_outcome,
    mark_task_outcome_recorded,
)
from app.services.heimdall_outcomes import record_outcome
from app.services.heimdall_feedback import best_channel_for_contact, record_feedback, get_contact_feedback
from app.services.system_state import get_system_state

router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_channel(contact: dict[str, Any]) -> str:
    """Base channel selection from consent preferences."""
    if contact.get("consent_sms"):
        return "sms"
    if contact.get("consent_email"):
        return "email"
    return "phone"


def _choose_channel(contact: dict[str, Any]) -> tuple[str, list[str]]:
    """Smart channel selection with feedback-driven optimization."""
    fallback = _base_channel(contact)
    contact_id = int(contact.get("id", 0))
    return best_channel_for_contact(contact_id=contact_id, fallback_channel=fallback)


def _build_next_actions() -> list[dict[str, Any]]:
    """Build ranked list of next actions from live contacts and scoring."""
    contacts = load_contacts()

    actions: list[dict[str, Any]] = []
    for contact in contacts:
        if contact.get("status") == "closed":
            continue

        scoring = score_contact(contact)
        channel, channel_reasons = _choose_channel(contact)

        action = {
            "contact_id": contact["id"],
            "contact_name": contact["name"],
            "priority": scoring["priority"],
            "heimdall_score": scoring["score"],
            "action": f"Follow up via {channel}",
            "channel": channel,
            "reason": contact.get("reason"),
            "script": contact.get("recommended_script"),
            "why": scoring["why"] + channel_reasons,
            "heat_score": contact.get("heat_score"),
            "days_stale": contact.get("days_stale"),
            "status": contact.get("status"),
        }
        actions.append(action)

    actions.sort(key=lambda x: x["heimdall_score"], reverse=True)
    return actions


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
    """Prioritized next actions with scoring explanations and channel learning."""
    actions = _build_next_actions()

    return {
        "ok": True,
        "agent": "Heimdall",
        "generated_at": _now_iso(),
        "count": len(actions),
        "items": actions,
    }


@router.post("/recommend-action")
async def heimdall_recommend_action(payload: dict[str, Any]) -> dict[str, Any]:
    """Get action recommendation with scoring explanation and channel feedback."""
    contact_id = payload.get("contact_id")
    context = payload.get("context")

    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")

    contact = get_contact(int(contact_id))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    scoring = score_contact(contact)
    channel, channel_reasons = _choose_channel(contact)

    recommendation = {
        "agent": "Heimdall",
        "contact_id": contact["id"],
        "contact": contact["name"],
        "channel": channel,
        "priority": scoring["priority"],
        "heimdall_score": scoring["score"],
        "reason": contact.get("reason"),
        "script": contact.get("recommended_script"),
        "why": scoring["why"] + channel_reasons,
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


@router.post("/create-task")
async def heimdall_create_task(payload: dict[str, Any]) -> dict[str, Any]:
    """Heimdall assigns a task to be completed."""
    contact_id = payload.get("contact_id")
    action = payload.get("action")
    priority = payload.get("priority", "medium")

    if not contact_id or not action:
        raise HTTPException(status_code=400, detail="Missing contact_id or action")

    task = create_task(int(contact_id), action, priority)

    event = {
        "agent": "Heimdall",
        "event": "task_created",
        "task_id": task["id"],
        "contact_id": contact_id,
        "action": action,
        "priority": priority,
    }
    log_event("task_created", event)

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Task created",
        "task": task,
    }


@router.get("/tasks")
async def heimdall_tasks() -> dict[str, Any]:
    """View all pending tasks sorted by priority."""
    pending = get_pending_tasks()

    return {
        "ok": True,
        "agent": "Heimdall",
        "count": len(pending),
        "tasks": pending,
    }


@router.get("/tasks-needing-outcome")
async def heimdall_tasks_needing_outcome() -> dict[str, Any]:
    """View completed tasks that haven't had outcomes recorded yet."""
    items = get_completed_tasks_needing_outcome()

    return {
        "ok": True,
        "agent": "Heimdall",
        "count": len(items),
        "items": items,
    }


@router.post("/auto-generate-tasks")
async def heimdall_auto_generate_tasks(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Automatically generate tasks from top-ranked next-actions."""
    payload = payload or {}
    limit = int(payload.get("limit", 3))

    actions = _build_next_actions()
    selected = actions[:limit]

    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for item in selected:
        task, was_created = create_task_if_missing(
            contact_id=item["contact_id"],
            action=item["action"],
            priority=item["priority"],
        )

        result = {
            "contact_id": item["contact_id"],
            "contact_name": item["contact_name"],
            "action": item["action"],
            "priority": item["priority"],
            "task": task,
        }

        if was_created:
            created.append(result)
            log_event(
                "auto_task_created",
                {
                    "agent": "Heimdall",
                    "contact_id": item["contact_id"],
                    "task": task,
                },
            )
        else:
            skipped.append(result)

    return {
        "ok": True,
        "agent": "Heimdall",
        "generated_at": _now_iso(),
        "requested_limit": limit,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
    }


@router.post("/complete-task")
async def heimdall_complete_task(payload: dict[str, Any]) -> dict[str, Any]:
    """Mark a task as completed with optional completion notes."""
    task_id = payload.get("task_id")
    notes = payload.get("notes")

    if not task_id:
        raise HTTPException(status_code=400, detail="task_id is required")

    updated = complete_task(int(task_id), notes=notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")

    log_event(
        "task_completed",
        {
            "agent": "Heimdall",
            "task_id": int(task_id),
            "task": updated,
            "timestamp": updated.get("completed_at"),
        },
    )

    return {
        "ok": True,
        "agent": "Heimdall",
        "message": "Task marked as completed",
        "task": updated,
        "next_step": "Record outcome for this completed task",
    }


@router.post("/record-outcome")
async def heimdall_record_outcome(payload: dict[str, Any]) -> dict[str, Any]:
    """Record outcome of a task-driven action with closed-loop tracking."""
    contact_id = payload.get("contact_id")
    result = payload.get("result")
    notes = payload.get("notes")
    channel = payload.get("channel")
    task_id = payload.get("task_id")

    if not contact_id or not result:
        raise HTTPException(status_code=400, detail="Missing required fields")

    outcome = record_outcome(
        contact_id=int(contact_id),
        result=result,
        notes=notes,
        channel=channel,
        task_id=int(task_id) if task_id else None,
    )

    # Record channel feedback for learning
    feedback = None
    if channel:
        feedback = record_feedback(
            contact_id=int(contact_id),
            channel=channel,
            result=result,
            notes=notes,
        )

    # Mark task outcome as recorded
    updated_task = None
    if task_id:
        updated_task = mark_task_outcome_recorded(int(task_id))

    log_event(
        "record_outcome",
        {
            "agent": "Heimdall",
            "outcome": outcome,
            "feedback": feedback,
            "task": updated_task,
        },
    )

    return {
        "ok": True,
        "agent": "Heimdall",
        "outcome": outcome,
        "feedback": feedback,
        "task": updated_task,
    }



@router.get("/feedback/{contact_id}")
async def heimdall_feedback(contact_id: int) -> dict[str, Any]:
    """View feedback history for a contact showing channel effectiveness."""
    items = get_contact_feedback(contact_id)

    return {
        "ok": True,
        "agent": "Heimdall",
        "contact_id": contact_id,
        "count": len(items),
        "items": items,
    }


@router.get("/system-status")
async def heimdall_system_status() -> dict[str, Any]:
    """Get system state: mode (SAFE/LIVE), blockers, warnings, go-live readiness."""
    state = get_system_state()

    return {
        "ok": True,
        "agent": "Heimdall",
        "system": state,
    }
