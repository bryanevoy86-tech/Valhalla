from sqlalchemy.orm import Session

from app.models.contracts import ContractDocument


def test_contract_gen_pdf_mocked(contract_client):
    client, engine = contract_client
    created = client.post("/api/contracts/templates", json={
        "name": "Assignment draft", "version": "1.0", "body_text": "Draft for {{ seller_name }}",
    })
    assert created.status_code == 200, created.text
    template = created.json()
    denied = client.post("/api/contracts/generate", json={
        "template_id": template["id"], "filename": "../outside.pdf", "data": {"seller_name": "Jane Seller"},
    })
    assert denied.status_code == 422
    created = client.post("/api/contracts/generate", json={
        "template_id": template["id"], "filename": "assignment_{{ deal_id }}.pdf",
        "data": {"seller_name": "Jane Seller", "deal_id": 123},
    })
    assert created.status_code == 200, created.text
    doc = created.json()
    assert doc["template_id"] == template["id"]
    assert doc["filename"] == "assignment_123.pdf"
    result = client.get(f"/api/contracts/records/{doc['id']}/pdf")
    assert result.status_code == 200, result.text
    assert result.headers["Content-Type"].startswith("application/pdf")
    assert result.content.startswith(b"%PDF-")
    with Session(engine) as db:
        stored = db.get(ContractDocument, doc["id"])
        assert stored.bytes == len(result.content)
        assert stored.sha256
        stored.sha256 = "bad-digest"
        db.commit()
    assert client.get(f"/api/contracts/records/{doc['id']}/pdf").status_code == 409
