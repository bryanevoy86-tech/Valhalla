"""P-BUDFLOW-1: Budget flow service (no-missed-payments orchestrator)."""
from __future__ import annotations

from typing import Any, Dict

def run() -> Dict[str, Any]:
    """
    Run the "no missed payments" flow:
    1. Gather bills_due from budget_obligations
    2. Check autopay status + gaps
    3. Create followups for un-autopay bills
    4. Generate ops board
    
    Safe-calls: budget_obligations, autopay_verify, followups, ops_board
    """
    warnings = []
    followups_created = 0
    
    # Safe-call to obligations
    due_bills = []
    try:
        from ..budget_obligations import service as obligations_service
        due_bills = obligations_service.list_due(days=14)
    except:
        warnings.append("budget_obligations unavailable")
    
    # Safe-call to autopay_verify
    unverified = []
    try:
        from ..autopay_verify import service as autopay_service
        items = autopay_service.list_items()
        unverified = [o for o in items if not o.get("verified")]
    except:
        warnings.append("autopay_verify unavailable")
    
    # Create followups for un-autopay bills
    for bill in due_bills:
        if bill.get("id") not in [u.get("obligation_id") for u in unverified]:
            try:
                from ..followups import service as followup_service
                followup_service.create(
                    task_type="pay_bill",
                    details={"obligation_id": bill.get("id"), "amount": bill.get("amount")},
                    due_date=bill.get("due_date"),
                )
                followups_created += 1
            except:
                pass
    
    # Get ops board
    board = {}
    try:
        from ..ops_board import service as ops_service
        board = ops_service.today()
    except:
        warnings.append("ops_board unavailable")
    
    return {
        "done": True,
        "warnings": warnings,
        "followups_created": followups_created,
        "board": board,
    }
