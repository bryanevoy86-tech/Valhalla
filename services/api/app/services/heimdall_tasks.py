"""
Heimdall Task Engine
Assigns work to operators based on scoring + priority.
This is an operating system, not just suggestions.
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
    }

    tasks.append(task)
    save_tasks(tasks)

    return task


def complete_task(task_id: int) -> bool:
    """Mark a task as completed."""
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            t["completed_at"] = datetime.now(timezone.utc).isoformat()
            break

    save_tasks(tasks)
    return True


def get_pending_tasks() -> list[dict[str, Any]]:
    """Get all pending tasks sorted by priority."""
    tasks = load_tasks()
    pending = [t for t in tasks if t.get("status") == "pending"]
    
    # Sort: high first, then creation time
    priority_order = {"high": 0, "medium": 1, "low": 2}
    pending.sort(
        key=lambda x: (priority_order.get(x.get("priority"), 3), x.get("created_at"))
    )
    
    return pending
