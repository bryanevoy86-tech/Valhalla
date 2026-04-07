from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any


@dataclass
class PaymentIntent:
    deal_id: str
    payer: str
    payee: str
    amount: float
    purpose: str
    status: str = "pending"
    created_at: str = datetime.now(UTC).isoformat()

    def approve(self):
        self.status = "approved"

    def mark_sent(self):
        self.status = "sent"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__
