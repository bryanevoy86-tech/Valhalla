from __future__ import annotations

from app.legal.legal_send_service import queue_legal_document, approve_queued_send


def test_queue_and_approve():
    result = queue_legal_document(
        approval_id="test_purchase_001",
        template_key="purchase_sale_agreement",
        payload={
            "date": "2026-04-06",
            "seller_name": "Test Seller",
            "buyer_name": "Valhalla Legacy Inc.",
            "property_address": "123 Test St",
            "purchase_price": "100000",
            "earnest_money": "1000",
            "title_company": "Test Title",
            "inspection_days": "10",
            "closing_date": "2026-04-30",
            "additional_terms": "Lawyer review required."
        },
        recipients=["lawyer@example.com"],
        cc=["accountant@example.com"],
        body_intro="Please review this legal draft."
    )
    assert result["queued"] is True

    approved = approve_queued_send("test_purchase_001")
    assert approved["approved"] is True
