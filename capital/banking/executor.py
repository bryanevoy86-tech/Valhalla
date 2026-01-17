"""
Executes only approved, capped, whitelisted internal transfers
"""

from .registry import INTERNAL_WHITELIST
from .kill_switch import is_killed
from .approvals import TransferApproval
from .caps import DEFAULT_CAPS
from datetime import datetime


def execute_internal_transfer(
    approval: TransferApproval,
    account_purpose: str,
):
    """
    Execute an internal transfer only if:
    1. Kill switch is NOT active
    2. Approval has not been used before
    3. Approval has not expired
    4. Destination account is whitelisted (internal)
    5. Amount is within caps for this account purpose
    
    Returns: {"status": "executed", "approval_id": approval_id}
    Raises: RuntimeError if any condition fails
    """
    
    # Check kill switch
    if is_killed():
        raise RuntimeError("KILL SWITCH ACTIVE")

    # Check approval not already used
    if approval.used:
        raise RuntimeError("Approval already used")

    # Check approval not expired
    if datetime.utcnow() > approval.expires_at:
        raise RuntimeError("Approval expired")

    # Check destination is whitelisted (internal only)
    if approval.to_account not in INTERNAL_WHITELIST:
        raise RuntimeError("Destination not whitelisted")

    # Check against caps
    caps = DEFAULT_CAPS.get(account_purpose, {})
    per_cap = caps.get("per_transfer")

    if per_cap and approval.amount > per_cap:
        raise RuntimeError("Transfer exceeds cap")

    # ---- EXECUTION PLACEHOLDER ----
    # This is where a real bank API call would go
    # For now, we mark approval as used and return success
    # In production: This calls the actual banking service
    # --------------------------------

    approval.used = True
    return {"status": "executed", "approval_id": approval.approval_id}
