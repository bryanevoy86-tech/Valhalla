from decimal import Decimal

from sqlalchemy.orm import Session

from app.leads.models import Lead
from app.models.deal import Deal, DealBriefLink
from app.models.freeze_events import FreezeEvent
from app.models.match import DealBrief


def test_portfolio_summary_endpoint(deal_client):
    client, _ = deal_client
    response = client.get("/api/portfolio/summary")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["total_deals"] == 0
    assert result["status_counts"]["active"] == 0
    assert result["freeze_counts"]["total_events"] == 0
    assert result["estimated_gross_profit_active"] is None


def test_portfolio_deals_endpoint(deal_client):
    client, engine = deal_client
    with Session(engine) as db:
        lead = Lead(lead_name="Owner", lead_email="portfolio@example.com", lead_phone="555-010-0101", source="test")
        db.add(lead)
        db.flush()
        deal = Deal(lead_id=lead.id, title="Actual deal", stage="draft", arv=250000, estimated_repair_cost=20000)
        db.add_all([deal, DealBrief(id=1, headline="Unrelated", price=1)])
        db.flush()
        db.add(DealBrief(id=2, headline="Actual brief", price=170000, region="Winnipeg"))
        db.flush()
        db.add_all([
            DealBriefLink(deal_id=deal.id, brief_id=2),
            FreezeEvent(deal_id=str(deal.id), event_type="freeze", severity="warn"),
            FreezeEvent(deal_id=str(deal.id), event_type="milestone"),
        ])
        db.commit()
    response = client.get("/api/portfolio/deals")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["deals"][0]["region"] == "Winnipeg"
    assert result["deals"][0]["freeze_severity"] == "warn"
    assert result["summary"]["freeze_counts"]["total_events"] == 1
    assert Decimal(result["summary"]["estimated_gross_profit_active"]) == 60000
