from sqlalchemy.orm import Session

from app.leads.models import Lead
from app.models.audit_log import AuditLog
from app.models.deal import Deal


def _create_test_deal(engine) -> int:
    with Session(engine) as db:
        lead = Lead(lead_name="Lifecycle Seller", lead_email="lifecycle@example.com", lead_phone="555-010-4567", source="test")
        db.add(lead)
        db.flush()
        deal = Deal(lead_id=lead.id, title="Test Deal", stage="draft", status="draft")
        db.add(deal)
        db.commit()
        return deal.id


def test_lifecycle_status_nonexistent_deal(deal_client):
    client, _ = deal_client
    response = client.get("/api/lifecycle/status/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_lifecycle_status_new_deal(deal_client):
    client, engine = deal_client
    deal_id = _create_test_deal(engine)
    response = client.get(f"/api/lifecycle/status/{deal_id}")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["backend_deal_id"] == deal_id
    assert result["current_stage"] == "backend_deal_created"
    assert result["next_recommended_stage"] == "underwriting_complete"
    steps = {step["name"]: step["status"] for step in result["steps"]}
    assert steps["lead_created"] == steps["backend_deal_created"] == "completed"
    assert steps["deal_brief_created"] == "pending"


def test_lifecycle_run_invalid_action(deal_client):
    client, engine = deal_client
    deal_id = _create_test_deal(engine)
    response = client.post("/api/lifecycle/run_action", json={
        "backend_deal_id": deal_id, "action": "invalid_action_name",
    })
    assert response.status_code == 400
    assert "Unknown action" in response.json()["detail"]


def test_lifecycle_available_actions_at_stage(deal_client):
    client, engine = deal_client
    deal_id = _create_test_deal(engine)
    response = client.get(f"/api/lifecycle/status/{deal_id}")
    assert response.status_code == 200, response.text
    assert "run_underwriting" in response.json()["automated_actions_available"]


def test_lifecycle_action_orchestrates_flows(deal_client):
    client, engine = deal_client
    deal_id = _create_test_deal(engine)
    command = {"backend_deal_id": deal_id, "action": "run_underwriting"}
    assert client.post("/api/lifecycle/run_action", json=command).status_code == 422
    command["inputs"] = {"deal": {"deal_id": 987654, "arv": 340000, "purchase_price": 220000, "repairs": 30000}}
    response = client.post("/api/lifecycle/run_action", json=command)
    assert response.status_code == 200, response.text
    assert response.json()["output"]["deal_id"] == deal_id
    with Session(engine) as db:
        assert db.get(Deal, deal_id).estimated_repair_cost == 30000
        assert db.query(AuditLog).filter_by(deal_id=deal_id, event_type="lifecycle:run_underwriting").count() == 1
    result = client.get(f"/api/lifecycle/status/{deal_id}").json()
    assert result["current_stage"] == "underwriting_complete"
