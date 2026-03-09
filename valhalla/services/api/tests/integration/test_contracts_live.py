"""
Integration test for contracts router - hits real API endpoints.
Run with: pytest -m integration
Requires API_BASE and API_TOKEN environment variables or valid defaults.
"""
import os
import httpx
import pytest


@pytest.mark.integration
def test_contract_gen_pdf_live():
    """Live integration test hitting real API (network-dependent, optional CI run)."""
    api_base = os.environ.get("API_BASE", "http://localhost:8000/api")
    api_token = os.environ.get("API_TOKEN", "test123")
    headers = {"X-API-Key": api_token, "Content-Type": "application/json"}
    
    # Add template
    tmpl = {
        "name": "MB Assignment v1",
        "version": "1.0",
        "body_text": "Assignment Agreement\nSeller: {{ seller_name }}\nBuyer: {{ buyer_name }}\nPrice: ${{ price }}\nDeal: {{ deal_headline }}\n",
    }
    r = httpx.post(f"{api_base}/contracts/templates", headers=headers, json=tmpl, timeout=10)
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
    r = httpx.post(f"{api_base}/contracts/generate", headers=headers, json=gen, timeout=10)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    
    # Fetch PDF
    r = httpx.get(f"{api_base}/contracts/records/{rec_id}/pdf", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    assert r.headers.get("Content-Type", "").startswith("application/pdf")
