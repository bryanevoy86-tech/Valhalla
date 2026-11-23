"""Commissioning contracts use isolated native response fixtures and send no requests."""
from hashlib import sha256

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import httpx
import pytest

from app.integrations.commissioning import read_drive_fixture
from app.integrations.docusign import client as signatures
from app.integrations.quickbooks import client as books
from app.webhooks import docusign


@pytest.mark.parametrize("mode", ["disabled", "accepted", "denied"])
def test_quickbooks_account_readback(monkeypatch, mode):
    prefix = "VALHALLA_QUICKBOOKS_COMMISSIONING_"
    secret = "no-external-secret-fixture"
    monkeypatch.setenv(prefix + "ACCESS_TOKEN", secret)
    monkeypatch.setenv(prefix + "REALM_ID", "73")
    monkeypatch.setenv(prefix + "ACCOUNT_ID", "41")
    monkeypatch.setenv(prefix + "ENABLED", "0" if mode == "disabled" else "1")
    calls = []

    def upstream(request):
        calls.append(request.method)
        assert str(request.url).rstrip("?") == "https://sandbox-quickbooks.api.intuit.com/v3/company/73/account/41"
        assert request.headers["Authorization"] == "Bearer " + secret
        return httpx.Response(200 if mode == "accepted" else 403, json={
            "Account": {"Id": "41", "Active": True, "Classification": "Asset", "CurrentBalance": 4800},
            "opaque": secret,
        })

    if mode != "accepted":
        with pytest.raises(HTTPException) as blocked:
            books.read_account_fixture(transport=httpx.MockTransport(upstream))
        assert blocked.value.status_code == (503 if mode == "disabled" else 409)
        assert calls == ([] if mode == "disabled" else ["GET"])
        assert secret not in blocked.value.detail
        return
    result = books.read_account_fixture(transport=httpx.MockTransport(upstream))
    assert calls == ["GET"]
    assert result["resource_sha256"] == sha256(b"73/41").hexdigest()
    assert result["classification"] == "Asset" and result["bank_balance_verified"] is False
    assert "4800" not in str(result) and secret not in str(result)
    with pytest.raises(HTTPException, match="approved commissioning scope"):
        books.read_account_fixture(account_id="42", transport=httpx.MockTransport(upstream))
    assert calls == ["GET"]


def test_docusign_requires_same_recipient_and_never_claims_reliance(monkeypatch):
    account = "cf6ecbc2-3b13-4c29-b2b1-9ce83e12956f"
    envelope = "39422892-a852-4516-ae59-2c078fb0d2a5"
    signer = "fixture@example.invalid"
    prefix = "VALHALLA_DOCUSIGN_COMMISSIONING_"
    for key, value in {"ACCESS_TOKEN": "test-envelope-token", "ENABLED": "1", "ACCOUNT_ID": account,
                       "ENVELOPE_ID": envelope, "SIGNER_EMAIL": signer}.items():
        monkeypatch.setenv(prefix + key, value)
    recipient = {"email": signer, "status": "completed"}

    def upstream(request):
        assert request.method == "GET" and request.url.host == "demo.docusign.net"
        assert request.headers["Authorization"] == "Bearer test-envelope-token"
        if request.url.path.endswith("/recipients"):
            return httpx.Response(200, json={"recipientCount": "1", "signers": [recipient]})
        assert request.url.path.endswith(f"/accounts/{account}/envelopes/{envelope}")
        return httpx.Response(200, json={"envelopeId": envelope, "status": "completed"})

    transport = httpx.MockTransport(upstream)
    result = signatures.read_envelope_fixture(transport=transport)
    assert result["envelope_status"] == "completed" and result["legal_reliance_authorized"] is False
    assert signer not in str(result) and envelope not in str(result)
    recipient["status"] = "sent"
    with pytest.raises(HTTPException, match="did not reconcile"):
        signatures.read_envelope_fixture(transport=transport)
    recipient.update(status="completed", email="other@example.invalid")
    with pytest.raises(HTTPException, match="did not reconcile"):
        signatures.read_envelope_fixture(transport=transport)


def test_drive_fixture_checks_exact_metadata_and_write_paths_fail_closed(monkeypatch):
    prefix = "VALHALLA_GOOGLE_DRIVE_COMMISSIONING_"
    file_id = "google-fixture-scope"
    monkeypatch.setenv(prefix + "ENABLED", "1")
    monkeypatch.setenv(prefix + "FILE_ID", file_id)
    monkeypatch.setenv(prefix + "ACCESS_TOKEN", "fixture-drive-token")
    body = {"id": file_id, "mimeType": "application/vnd.google-apps.document", "trashed": False}

    def upstream(request):
        assert request.url.host == "www.googleapis.com" and request.url.path == "/drive/v3/files/" + file_id
        assert request.method == "GET" and request.url.params["fields"] == "id,mimeType,trashed"
        assert "alt" not in request.url.params
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(upstream)
    receipt = read_drive_fixture(transport=transport)
    assert receipt["content_downloaded"] is False and receipt["external_action_authorized"] is False
    body["id"] = "different"
    with pytest.raises(HTTPException, match="did not match"):
        read_drive_fixture(transport=transport)
    for adapter in (books, signatures):
        monkeypatch.setattr(adapter, "enforce_engine", lambda *args, **kwargs: None)
        monkeypatch.setattr(adapter, "is_live", lambda: True)
    with pytest.raises(HTTPException, match="has not been commissioned"):
        books.post_journal_entry({})
    with pytest.raises(HTTPException, match="has not been commissioned"):
        signatures.send_envelope("fixture", "fixture@example.invalid", "https://example.invalid")
    monkeypatch.setattr(docusign, "is_live", lambda: True)
    isolated = FastAPI()
    isolated.include_router(docusign.router)
    response = TestClient(isolated).post("/webhooks/docusign", json={"status": "completed", "envelope_id": "unverified"})
    assert response.status_code == 503 and "mark_contract_executable" not in response.text
