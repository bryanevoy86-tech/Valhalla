"""Bridge reminders to followups system."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

# Safe imports
try:
    from . import service as reminders_service
except ImportError:
    reminders_service = None

try:
    from ..budget_obligations.followups import create as create_followup
except ImportError:
    create_followup = None


def push_open_to_followups() -> Dict[str, Any]:
    """Convert open reminders to followup tasks.
    
    Returns:
        Dict with created followup count
    """
    created = 0
    
    if not reminders_service:
        return {"created": 0}
    
    try:
        # Get all open reminders
        open_reminders = reminders_service.list_open()
        
        if create_followup:
            for reminder in open_reminders:
                try:
                    # Convert reminder to followup
                    followup = {
                        "title": reminder.get("title", "Reminder"),
                        "due_date": reminder.get("due_date", ""),
                        "kind": "reminder",
                        "notes": reminder.get("notes", ""),
                        "source_id": reminder.get("id", "")
                    }
                    create_followup(**followup)
                    created += 1
                except Exception:
                    pass  # Skip failed conversions
    except Exception:
        pass
    
    return {"created": created}
