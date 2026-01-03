"""
P-APPROVALGATE-1: Approval gate service for execution approval workflow.

Checks system config and mode to determine if approvals are needed.
Safe-calls approvals module to gate execution.
"""
from typing import Dict, Any, Optional


def require_execute_approval(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if an action requires approval and attempt to gate execution.
    
    Args:
        action: Action identifier (e.g., 'transfer_funds', 'delete_account')
        payload: Action payload dict
    
    Returns:
        dict with keys:
            - requires_approval (bool)
            - approved (bool)
            - approval_id (str, optional)
            - message (str)
    """
    result = {
        "requires_approval": False,
        "approved": False,
        "approval_id": None,
        "message": ""
    }
    
    # Check system config
    try:
        from backend.app.core_gov.system_config.store import get as config_get
        config = config_get()
        require_approvals = config.get("require_approvals_for_execute", False)
    except Exception:
        require_approvals = False
    
    if not require_approvals:
        result["requires_approval"] = False
        result["approved"] = True
        result["message"] = "No approvals required"
        return result
    
    # Check if soft launch mode
    try:
        from backend.app.core_gov.system_config.store import get as config_get
        config = config_get()
        is_soft_launch = config.get("soft_launch", False)
    except Exception:
        is_soft_launch = False
    
    result["requires_approval"] = True
    
    # Safe call: approvals module
    try:
        from backend.app.core_gov.approvals.service import create as create_approval
        approval = create_approval(
            action_type=action,
            payload=payload,
            auto_approve=is_soft_launch
        )
        result["approved"] = approval.get("auto_approved", False)
        result["approval_id"] = approval.get("id")
        result["message"] = "Approval created"
    except Exception as e:
        result["message"] = f"Approval system error: {str(e)}"
    
    return result
