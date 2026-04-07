from __future__ import annotations

from app.legal.recipient_registry import resolve_legal_contacts


def test_registry_resolution_returns_structure():
    result = resolve_legal_contacts(
        company_name="Valhalla Legacy Inc.",
        region_code="MB",
        deal_type="wholesale",
    )
    assert "recipients" in result
    assert "cc" in result
    assert "title_company" in result


def test_registry_resolution_handles_missing_company():
    result = resolve_legal_contacts(
        company_name="Missing Co",
        region_code="XX",
        deal_type="wholesale",
    )
    assert result["recipients"] == []
    assert result["cc"] == []
