"""P-OPSBOARD-1: Operations board service."""
from __future__ import annotations

from typing import Any, Dict

def today() -> Dict[str, Any]:
    """
    Generate unified operations board for today.
    
    Safe-calls: bills (due today/tomorrow), autopay_verify, inventory, reminders, outbox
    """
    board = {
        "bills_due": [],
        "autopay_gaps": [],
        "inventory_low": [],
        "reminders": [],
        "outbox_ready": [],
    }
    
    # Safe-call to budget_obligations
    try:
        from ..budget_obligations import service as obligations_service
        due = obligations_service.list_due(days=1)
        board["bills_due"] = due[:10]
    except:
        pass
    
    # Safe-call to autopay_verify
    try:
        from ..autopay_verify import service as autopay_service
        items = autopay_service.list_items()
        board["autopay_gaps"] = [o for o in items if not o.get("verified")][:5]
    except:
        pass
    
    # Safe-call to inventory
    try:
        from ..house_inventory import service as inventory_service
        low = inventory_service.list_low()
        board["inventory_low"] = low[:5]
    except:
        pass
    
    # Safe-call to reminders
    try:
        from ..house_reminders import service as reminders_service
        today_reminders = reminders_service.list_today()
        board["reminders"] = today_reminders[:5]
    except:
        pass
    
    # Safe-call to outbox
    try:
        from ..outbox import service as outbox_service
        items = outbox_service.list_items()
        board["outbox_ready"] = [o for o in items if o.get("status") == "ready"][:5]
    except:
        pass

    # Safe-call to payday plan
    try:
        from ..payday.service import plan
        board["payday_plan"] = plan(days=14)
    except:
        board["payday_plan"] = {}

    board["cra_risk_hint"] = "GET /core/cra/risk/scan/{YYYY-MM}"

    return board
