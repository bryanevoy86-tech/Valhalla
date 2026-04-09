"""
Heimdall Task Engine
Assigns work to operators based on scoring + priority.
Tracks completion and outcome recording.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE = Path("var/heimdall_tasks.json")


def _ensure() -> None:
    """Ensure tasks store exists."""
    STORE.parent.mkdir(parents=True, exist_ok=True)
    if not STORE.exists():
        STORE.write_text('{"tasks": []}', encoding="utf-8")


def load_tasks() -> list[dict[str, Any]]:
    """Load all tasks."""
    _ensure()
    data = json.loads(STORE.read_text(encoding="utf-8"))
    return data.get("tasks", [])


def save_tasks(tasks: list[dict[str, Any]]) -> None:
    """Persist tasks to store."""
    _ensure()
    STORE.write_text(json.dumps({"tasks": tasks}, indent=2), encoding="utf-8")


def create_task(
    contact_id: int, action: str, priority: str
) -> dict[str, Any]:
    """
    Create a task to be completed.
    
    Priority: high, medium, low
    Status: pending, completed, skipped
    """
    tasks = load_tasks()

    task = {
        "id": max([t.get("id", 0) for t in tasks], default=0) + 1,
        "contact_id": contact_id,
        "action": action,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "completion_notes": None,
        "outcome_recorded": False,
    }

    tasks.append(task)
    save_tasks(tasks)

    return task


def complete_task(task_id: int, notes: str | None = None) -> dict[str, Any] | None:
    """Mark a task as completed with optional completion notes."""
    tasks = load_tasks()
    updated = None

    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            t["completed_at"] = datetime.now(timezone.utc).isoformat()
            t["completion_notes"] = notes
            updated = t
            break

    save_tasks(tasks)
    return updated


def mark_task_outcome_recorded(task_id: int) -> dict[str, Any] | None:
    """Mark a task as having its outcome recorded."""
    tasks = load_tasks()
    updated = None

    for t in tasks:
        if t["id"] == task_id:
            t["outcome_recorded"] = True
            updated = t
            break

    save_tasks(tasks)
    return updated


def get_pending_tasks() -> list[dict[str, Any]]:
    """Get all pending tasks sorted by priority."""
    tasks = [t for t in load_tasks() if t.get("status") == "pending"]
    priority_order = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))
    return tasks


def get_completed_tasks_needing_outcome() -> list[dict[str, Any]]:
    """Get all completed tasks that haven't had outcomes recorded yet."""
    return [
        t for t in load_tasks()
        if t.get("status") == "completed" and not t.get("outcome_recorded", False)
    ]


def find_pending_task(contact_id: int, action: str) -> dict[str, Any] | None:
    """Find an existing pending task for a contact with a specific action."""
    for task in get_pending_tasks():
        if int(task.get("contact_id", 0)) == int(contact_id) and task.get("action") == action:
            return task
    return None


def create_task_if_missing(
    contact_id: int, action: str, priority: str
) -> tuple[dict[str, Any], bool]:
    """
    Create a task only if one doesn't exist for this contact + action combo.
    Returns (task, was_created).
    """
    existing = find_pending_task(contact_id, action)
    if existing:
        return existing, False

    task = create_task(contact_id, action, priority)
    return task, True


