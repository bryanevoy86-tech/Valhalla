"""
P-SCHED-1: Scheduler service for periodic operations.

Runs tick() to execute scheduled daily operations.
"""
from datetime import datetime
from typing import Dict, Any
from . import store


def tick() -> Dict[str, Any]:
    """
    Execute scheduled tick operations.
    
    Calls daily_ops.run() and updates last tick timestamp.
    
    Returns:
        dict with keys:
            - success (bool)
            - tick_id (str)
            - timestamp (str)
            - daily_ops_result (dict)
            - message (str)
    """
    tick_id = str(int(datetime.utcnow().timestamp() * 1000))
    timestamp = datetime.utcnow().isoformat()
    
    result = {
        "success": True,
        "tick_id": tick_id,
        "timestamp": timestamp,
        "daily_ops_result": {},
        "message": "Tick complete"
    }
    
    # Update scheduler state
    try:
        store.set_last_tick(timestamp)
    except Exception as e:
        result["message"] = f"State update failed: {str(e)}"
    
    # Call daily_ops.run()
    try:
        from backend.app.core_gov.daily_ops.service import run as daily_ops_run
        result["daily_ops_result"] = daily_ops_run()
    except Exception as e:
        result["success"] = False
        result["daily_ops_result"] = {"error": str(e)}
        result["message"] = "Daily ops failed"
    
    return result
