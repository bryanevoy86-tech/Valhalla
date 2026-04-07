from __future__ import annotations

from app.finance.financial_package_builder import build_financial_package


def test_build_financial_package_success():
    result = build_financial_package(
        {
            "deal_id": "DEAL-PKG-001",
            "purchase_price": 500000.0,
            "assignment_fee": 15000.0,
            "earnest_money": 5000.0,
            "closing_costs": 2500.0,
            "requested_by": "heimdall",
        }
    )
    assert result.triggered is True
    assert result.ledger is not None
    assert result.disbursement_count >= 1
    assert result.queued_count >= 1


def test_build_financial_package_requires_deal_id():
    result = build_financial_package(
        {
            "purchase_price": 500000.0,
        }
    )
    assert result.triggered is False
    assert result.reason == "deal_id is required"
