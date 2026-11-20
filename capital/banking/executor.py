"""
Fail-closed internal transfer policy preflight.

No bank adapter or actual settlement verification is connected. This module
must not report success or consume owner approval for a simulated transfer.
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
    
    Raises RuntimeError until a trusted, receipt-verifying bank connector exists.
    The approval remains unconsumed when no money is actually moved.
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

    # No provider call exists in this module. Never mark approval used,
    # claim settled funds, or report a successful transfer from a stub.
    # Real implementation requires owner-scoped authorization, persistent
    # idempotency, provider receipt, bank reconciliation and incident controls.
    raise RuntimeError("BANK_TRANSFER_PROVIDER_NOT_CONNECTED")
