"""
Unit test for contracts router with mocked HTTP calls.
Uses respx to mock external API calls without network dependencies.
"""
import respx
import httpx
import json


@respx.mock
def test_contract_gen_pdf_mocked():
    """Test contract generation flow with mocked HTTP responses (no real network calls)."""
    api_base = "http://localhost:8000/api"
    
    # Mock POST /contracts/templates
    template_route = respx.post(f"{api_base}/contracts/templates").mock(
        return_value=httpx.Response(200, json={"id": 999, "name": "MB Assignment v1"})
    )
    
    # Mock POST /contracts/generate
    generate_route = respx.post(f"{api_base}/contracts/generate").mock(
        return_value=httpx.Response(200, json={"id": 1234, "filename": "assignment_123.pdf"})
    )
    
    # Mock GET /contracts/records/{id}/pdf
    pdf_route = respx.get(f"{api_base}/contracts/records/1234/pdf").mock(
        return_value=httpx.Response(
            200, 
            content=b"%PDF-1.4 fake", 
            headers={"Content-Type": "application/pdf"}
        )
    )
    
    # Execute test flow
    headers = {"X-API-Key": "test123", "Content-Type": "application/json"}
    
    # Add template
    tmpl = {
        "name": "MB Assignment v1",
        "version": "1.0",
        "body_text": "Assignment Agreement\nSeller: {{ seller_name }}\n",
    }
    r = httpx.post(f"{api_base}/contracts/templates", headers=headers, json=tmpl)
    assert r.status_code == 200
    tid = r.json()["id"]
    assert tid == 999
    
    # Generate contract
    gen = {
        "template_id": tid,
        "filename": "assignment_{{deal_id}}.pdf",
        "data": {"seller_name": "Jane Seller", "deal_id": 123},
    }
    r = httpx.post(f"{api_base}/contracts/generate", headers=headers, json=gen)
    assert r.status_code == 200
    rec_id = r.json()["id"]
    assert rec_id == 1234
    
    # Fetch PDF
    r = httpx.get(f"{api_base}/contracts/records/{rec_id}/pdf", headers=headers)
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("application/pdf")
    
    # Verify mocked routes were called
    assert template_route.called
    assert generate_route.called
    assert pdf_route.called
