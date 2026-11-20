import hashlib
import hmac
import json

from sqlalchemy.orm import Session

from app.models.contracts import Contract, ContractEnvelope, ContractEvent, ContractState, ContractTemplate, SignProvider


def test_contract_flow(contract_client):
    client, engine = contract_client
    response = client.post("/api/contract/template", json={
        "name": "Test", "jurisdiction": "MB", "structure": ["Draft clause for {{ name }}"],
    })
    assert response.status_code == 200, response.text
    template_id = response.json()["template_id"]
    assert client.get("/api/contract/template/list?jurisdiction=MB").json()["templates"][0]["id"] == template_id
    response = client.post("/api/contract/draft", json={
        "deal_id": 1, "template_id": template_id, "variables": {"name": "Jane"},
        "counterparty_email": "jane@example.com", "counterparty_name": "Jane",
    })
    assert response.status_code == 200, response.text
    contract_id = response.json()["contract_id"]
    pdf = client.post(f"/api/contract/pdf/{contract_id}")
    assert pdf.status_code == 200, pdf.text
    assert client.get(pdf.json()["pdf_url"]).content.startswith(b"%PDF-")

    blocked = client.post(f"/api/contract/send/{contract_id}")
    assert blocked.status_code == 409, blocked.text
    status = client.get(f"/api/contract/status/{contract_id}").json()
    assert status["status"] == "draft"
    assert status["signers"] == [{"name": "Jane", "signed_at": None}]
    with Session(engine) as db:
        assert db.get(Contract, contract_id).state == ContractState.DRAFT
        assert db.query(ContractEnvelope).count() == 0


def test_contract_webhook(contract_client, monkeypatch):
    client, engine = contract_client
    payload = {"event": "signed", "contract_id": 999}
    denied = client.post("/api/contract/webhook/esign", json=payload, headers={"X-Prime-Control-Key": "wrong"})
    assert denied.status_code == 401
    assert client.post("/api/contract/webhook/esign", json=payload).status_code == 503
    with Session(engine) as db:
        assert db.query(ContractEnvelope).count() == 0
        db.add(ContractTemplate(id="review-template", code="review-template", name="Verified fixture"))
        db.flush()
        contract = Contract(
            id="review-contract", template_id="review-template", title="Verified fixture",
            state=ContractState.SENT_FOR_SIGNATURE, sign_provider=SignProvider.DOCUSIGN,
        )
        db.add(contract)
        db.flush()
        db.add(ContractEnvelope(
            id="review-envelope", contract_id=contract.id, provider=SignProvider.DOCUSIGN,
            provider_envelope_id="gateway-envelope-ref", status="sent",
        ))
        db.flush()
        contract.active_envelope_id = "review-envelope"
        db.commit()

    secret = "isolated-webhook-signature-test"
    monkeypatch.setenv("VALHALLA_CONTRACT_WEBHOOK_SECRET", secret)
    body = json.dumps({"provider_envelope_id": "gateway-envelope-ref", "status": "signed"}).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert client.post("/api/contracts/webhooks/provider", content=body).status_code == 401
    headers = {"X-Contract-Signature": signature}
    response = client.post("/api/contracts/webhooks/provider", content=body, headers=headers)
    assert response.status_code == 200 and response.json()["applied"] is True
    assert client.post("/api/contracts/webhooks/provider", content=body, headers=headers).json()["applied"] is False
    with Session(engine) as db:
        assert db.get(Contract, "review-contract").state == ContractState.FULLY_EXECUTED
        assert db.query(ContractEvent).filter_by(contract_id="review-contract").count() == 1
