from __future__ import annotations

from app.legal.deal_stage_triggers import queue_legal_for_stage, get_stage_template_map


def test_stage_template_map_exists():
    stage_map = get_stage_template_map()
    assert "deal_ready_for_offer" in stage_map
    assert stage_map["deal_ready_for_offer"] == "purchase_sale_agreement"


def test_queue_purchase_agreement_from_stage():
    result = queue_legal_for_stage(
        "deal_ready_for_offer",
        {
            "deal_id": "deal_001",
            "seller_name": "John Seller",
            "buyer_name": "Valhalla Legacy Inc.",
            "property_address": "123 Main St",
            "purchase_price": "185000",
            "earnest_money": "2500",
            "title_company": "Example Title Co.",
            "inspection_days": 10,
            "closing_date": "2026-04-30",
            "lawyer_email": "lawyer@example.com",
            "accountant_email": "accountant@example.com",
        },
    )
    assert result.triggered is True
    assert result.queued is True
    assert result.template_key == "purchase_sale_agreement"


def test_stage_without_recipients_fails_cleanly():
    result = queue_legal_for_stage(
        "buyer_matched",
        {
            "deal_id": "deal_002",
            "property_address": "456 Side St",
        },
    )
    assert result.triggered is False
    assert result.queued is False
    assert result.reason == "No legal recipients configured"
