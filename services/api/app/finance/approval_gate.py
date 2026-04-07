from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Any


@dataclass
class FinanceApprovalGate:
    deal_id: str
    intent_id: str
    amount: float
    purpose: str
    requested_by: str
    approval_required: bool = True
    approved: bool = False
    approved_by: str | None = None
    blocked: bool = False
    block_reason: str | None = None
    created_at: str = datetime.now(UTC).isoformat()
    approved_at: str | None = None

    def approve(self, approver: str) -> None:
        if self.blocked:
            raise ValueError(f"Cannot approve blocked item: {self.block_reason}")
        self.approved = True
        self.approved_by = approver
        self.approved_at = datetime.now(UTC).isoformat()

    def block(self, reason: str) -> None:
        self.blocked = True
        self.block_reason = reason

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
