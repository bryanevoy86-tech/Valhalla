import os, httpx, json
API = os.getenv("API_BASE", "http://localhost:8000/api")
KEY = os.getenv("HEIMDALL_BUILDER_API_KEY", "test123")
H = {"X-API-Key": KEY, "Content-Type": "application/json"}


def test_contract_gen_pdf(tmp_path):
    # add template
    tmpl = {
        "name": "MB Assignment v1",
        "version": "1.0",
        "body_text": "Assignment Agreement\nSeller: {{ seller_name }}\nBuyer: {{ buyer_name }}\nPrice: ${{ price }}\nDeal: {{ deal_headline }}\n",
    }
    r = httpx.post(f"{API}/contracts/templates", headers=H, data=json.dumps(tmpl), timeout=10)
    assert r.status_code == 200, r.text
    tid = r.json()["id"]

    # generate
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
    r = httpx.post(f"{API}/contracts/generate", headers=H, data=json.dumps(gen), timeout=10)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]

    # fetch pdf
    r = httpx.get(f"{API}/contracts/records/{rec_id}/pdf", headers=H, timeout=10)
    assert r.status_code == 200, r.text
    assert r.headers.get("Content-Type", "").startswith("application/pdf")
