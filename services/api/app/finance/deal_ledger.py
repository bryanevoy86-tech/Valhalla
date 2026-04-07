from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Any


@dataclass
class DealLedger:
    deal_id: str
    purchase_price: float = 0.0
    assignment_fee: float = 0.0
    earnest_money: float = 0.0
    closing_costs: float = 0.0
    revenue: float = 0.0
    expenses: float = 0.0
    profit_expected: float = 0.0
    profit_actual: float = 0.0
    created_at: str = datetime.now(UTC).isoformat()

    def calculate_expected_profit(self):
        self.profit_expected = self.assignment_fee - self.closing_costs
        return self.profit_expected

    def calculate_actual_profit(self):
        self.profit_actual = self.revenue - self.expenses
        return self.profit_actual

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
