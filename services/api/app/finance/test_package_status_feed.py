from __future__ import annotations

from app.finance.package_status_feed import get_financial_package_history


def test_financial_package_history_returns_structure():
    result = get_financial_package_history(limit=10)
    assert "package_count" in result
    assert "packages" in result
    assert isinstance(result["packages"], list)
