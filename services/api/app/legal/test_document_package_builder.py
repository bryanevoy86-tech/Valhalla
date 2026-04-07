from __future__ import annotations

from app.legal.document_package_builder import get_stage_package_map, queue_legal_package_for_stage


def test_package_map_exists():
    stage_map = get_stage_package_map()
    assert "deal_ready_for_offer" in stage_map
    assert "purchase_sale_agreement" in stage_map["deal_ready_for_offer"]


def test_queue_package_for_offer_stage():
    result = queue_legal_package_for_stage(
        "deal_ready_for_offer",
        {
            "deal_id": "deal_pkg_001",
            "seller_name": "John Seller",
            "buyer_name": "Valhalla Legacy Inc.",
            "your_company": "Valhalla Legacy Inc.",
            "property_address": "789 Package Rd",
            "purchase_price": "210000",
            "earnest_money": "3000",
            "title_company": "Example Title Co.",
            "inspection_days": 10,
            "closing_date": "2026-05-01",
            "lawyer_email": "lawyer@example.com",
            "accountant_email": "accountant@example.com",
        },
    )
    assert result.triggered is True
    assert result.queued_count >= 1
    assert len(result.documents) >= 1


def test_package_without_recipients_fails_cleanly():
    result = queue_legal_package_for_stage(
        "deal_ready_for_offer",
        {
            "deal_id": "deal_pkg_002",
            "property_address": "No Recipient Ave"
        },
    )
    assert result.triggered is False
    assert result.reason == "No legal recipients configured"
