"""
Explicit approval objects – single-use, expiring
"""

from datetime import datetime, timedelta
from pydantic import BaseModel


class TransferApproval(BaseModel):
    """Single-use, expiring transfer approval."""
    approval_id: str
    from_account: str
    to_account: str
    amount: float
    expires_at: datetime
    used: bool = False


def create_approval(
    approval_id: str,
    from_account: str,
    to_account: str,
    amount: float,
    ttl_minutes: int = 30,
):
    """
    Create a transfer approval that expires after TTL minutes.
    
    Default TTL: 30 minutes
    Single-use only (used flag prevents replay)
    """
    return TransferApproval(
        approval_id=approval_id,
        from_account=from_account,
        to_account=to_account,
        amount=amount,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
    )
