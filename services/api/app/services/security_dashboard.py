"""
PACK TT: Security Dashboard Services
Aggregates all security data from other services.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.services.security_policy import list_blocks, get_policy
from app.services.security_actions import list_action_requests
from app.services.honeypot_bridge import list_instances, list_events


async def get_security_dashboard(db: Session):
    """Get unified security dashboard snapshot."""
    
    # Get security mode (from security_monitor)
    try:
        from app.services.security_monitor import get_security_mode
        mode_data = await get_security_mode(db)
        security_mode = {
            "mode": mode_data.get("mode", "normal"),
            "updated_at": mode_data.get("updated_at", datetime.utcnow())
        }
    except:
        security_mode = {
            "mode": "normal",
            "updated_at": datetime.utcnow()
        }
    
    # Get incidents (from security_monitor)
    try:
        from app.services.security_monitor import get_open_incidents
        incidents_data = await get_open_incidents(db)
        incidents = {
            "total_open": incidents_data.get("total", 0),
            "critical": incidents_data.get("critical", 0),
            "high": incidents_data.get("high", 0),
            "medium": incidents_data.get("medium", 0),
            "low": incidents_data.get("low", 0)
        }
    except:
        incidents = {
            "total_open": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
    
    # Get blocklist
    blocklist_data = await list_blocks(db, active_only=True)
    blocked_items = blocklist_data.get("items", [])
    blocklist = {
        "total_blocked": len(blocked_items),
        "ips": sum(1 for b in blocked_items if b.entity_type == "ip"),
        "users": sum(1 for b in blocked_items if b.entity_type == "user"),
        "api_keys": sum(1 for b in blocked_items if b.entity_type == "api_key")
    }
    
    # Get honeypot summary
    instances_data = await list_instances(db, active_only=True)
    events_data = await list_events(db, limit=1000)
    honeypot = {
        "total_instances": instances_data.get("total", 0),
        "active_instances": instances_data.get("active_instances", 0),
        "recent_events": events_data.get("total", 0),
        "threats_detected": sum(1 for e in events_data.get("items", []) if e.detected_threat)
    }
    
    # Get action requests
    actions_data = await list_action_requests(db)
    action_types = {}
    for action in actions_data.get("items", []):
        if action.status == "pending":
            atype = action.action_type
            action_types[atype] = action_types.get(atype, 0) + 1
    
    action_requests = {
        "total_pending": actions_data.get("pending", 0),
        "pending_by_type": action_types
    }
    
    return {
        "timestamp": datetime.utcnow(),
        "security_mode": security_mode,
        "incidents": incidents,
        "blocklist": blocklist,
        "honeypot": honeypot,
        "action_requests": action_requests,
        "last_update": datetime.utcnow()
    }
