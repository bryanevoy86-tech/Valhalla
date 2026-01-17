"""
P-AUDIT-1: Audit log store for event persistence.

Handles appending and listing audit events.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any

AUDIT_FILE = "backend/data/audit_log.json"


def _ensure_file() -> None:
    """Ensure audit log file exists."""
    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
    if not os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, "w") as f:
            json.dump([], f)


def append(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append an event to the audit log.
    
    Args:
        event_type: Type of event (e.g., 'system_boot', 'user_action')
        payload: Event payload dict
    
    Returns:
        Event dict with timestamp and ID
    """
    _ensure_file()
    
    event = {
        "id": int(datetime.utcnow().timestamp() * 1000),
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(AUDIT_FILE, "r") as f:
        events = json.load(f)
    
    events.append(event)
    
    with open(AUDIT_FILE, "w") as f:
        json.dump(events, f, indent=2)
    
    return event


def list_events(limit: int = 100) -> List[Dict[str, Any]]:
    """
    List audit events.
    
    Args:
        limit: Maximum number of events to return
    
    Returns:
        List of events (most recent first)
    """
    _ensure_file()
    
    with open(AUDIT_FILE, "r") as f:
        events = json.load(f)
    
    # Return most recent first
    return sorted(events, key=lambda e: e["timestamp"], reverse=True)[:limit]
