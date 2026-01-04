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

    # Call payday followups
    try:
        from backend.app.core_gov.payday.followups import create_income_followups
        create_income_followups(days=14)
    except Exception:
        pass

    # Call calendar to reminders
    try:
        from backend.app.core_gov.house_calendar.reminders import push_to_reminders
        push_to_reminders(limit=25)
    except Exception:
        pass

    # Call legal hotlist scan
    try:
        from backend.app.core_gov.scheduler.legal_hotlist import scan_hotlist
        scan_hotlist(limit=25)
    except Exception:
        pass

    # Call bills reminders push
    try:
        from backend.app.core_gov.bills.reminders import push as bills_push  # type: ignore
        bills_push(days_ahead=7)
    except Exception:
        pass

    # Call bills missed detector
    try:
        from backend.app.core_gov.bills.pay_log import missed  # type: ignore
        m = missed()
        if (m.get("missed") or []):
            pass  # bills missed detected
    except Exception:
        pass

    # Call pipeline daily tick
    try:
        from backend.app.core_gov.pipeline.daily import tick as pipe_tick  # type: ignore
        pipe_tick(limit=10)
    except Exception:
        pass

    return result
