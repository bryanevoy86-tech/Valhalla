"""
Integration test for contracts router - hits real API endpoints.
Run with: pytest -m integration
Uses a disposable loopback server with the canonical app.
"""
import pytest


@pytest.mark.integration
def test_contract_gen_pdf_live(loopback_contract_api):
    network = loopback_contract_api
    # Add template
    tmpl = {
        "name": "MB Assignment v1",
        "version": "1.0",
        "body_text": "Assignment Agreement\nSeller: {{ seller_name }}\nBuyer: {{ buyer_name }}\nPrice: ${{ price }}\nDeal: {{ deal_headline }}\n",
    }
    r = network.post(f"/contracts/templates", json=tmpl)
    assert r.status_code == 200, r.text
    tid = r.json()["id"]

    # Generate contract
    gen = {
        "template_id": tid,
        "filename": "assignment_{{deal_id}}.pdf",
        "data": {
            "seller_name": "Jane Seller",
            "buyer_name": "ABC Capital",
            "price": 289000,
            "deal_headline": "SFH in Transcona",
            "deal_id": 123,
        },
    }
    r = network.post(f"/contracts/generate", json=gen)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]

    # Fetch PDF
    r = network.get(f"/contracts/records/{rec_id}/pdf")
    assert r.status_code == 200, r.text
    assert r.headers.get("Content-Type", "").startswith("application/pdf")
    assert r.content.startswith(b"%PDF-")
