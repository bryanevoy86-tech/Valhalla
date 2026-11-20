from decimal import Decimal

from sqlalchemy.orm import Session

from app.leads.models import Lead
from app.models.deal import Deal
from app.models.freeze_events import FreezeEvent
from app.offers.models import Offer


def _seed_costs(engine):
    with Session(engine) as db:
        lead = Lead(lead_name="Tax scenario", lead_email="tax@example.com", lead_phone="555-010-0101", source="test")
        db.add(lead)
        db.flush()
        deal = Deal(lead_id=lead.id, title="Tax scenario", stage="draft", estimated_repair_cost=30000)
        db.add(deal)
        db.flush()
        db.add(Offer(deal_id=deal.id, offer_price=240000, status="accepted"))
        db.commit()
        return deal.id


def test_tax_snapshot_happy_path(deal_client):
    client, engine = deal_client
    deal_id = _seed_costs(engine)
    response = client.post("/api/flow/tax_snapshot_for_deal", json={
        "backend_deal_id": deal_id, "sale_price": 340000, "sale_closing_costs": 10000,
        "extra_expenses": 5000, "tax_rate": "0.25",
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["backend_deal_id"] == deal_id
    numbers = data["numbers"]
    assert numbers["sale_price"] == 340000
    assert numbers["gross_profit"] == 55000
    assert numbers["tax_amount"] == 13750
    assert numbers["net_after_tax"] == 41250
    assert Decimal(str(numbers["tax_rate_applied"])) == Decimal("0.25")
    assert data["policy"]["breach_min_tax_rate"] is False
    with Session(engine) as db:
        assert db.query(FreezeEvent).count() == 0


def test_tax_snapshot_below_min_tax_rate_flags_policy(deal_client):
    client, engine = deal_client
    deal_id = _seed_costs(engine)
    response = client.post("/api/flow/tax_snapshot_for_deal", json={
        "backend_deal_id": deal_id, "sale_price": 340000, "sale_closing_costs": 5000,
        "extra_expenses": 2000, "tax_rate": "0.05",
    })
    assert response.status_code == 200, response.text
    assert response.json()["policy"]["breach_min_tax_rate"] is True
    assert response.json()["numbers"]["tax_amount"] == 3150
    with Session(engine) as db:
        freeze = db.query(FreezeEvent).filter_by(deal_id=str(deal_id), source="tax_snapshot").one()
        assert freeze.payload["tax_rate"] == "0.05"
