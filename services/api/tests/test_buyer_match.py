from sqlalchemy.orm import Session

from app.models.buyer_candidate import BuyerCandidate
from app.models.deal_buyer_match import DealBuyerMatch
from app.models.match import DealBrief


def _setup(deal_client):
    client, engine = deal_client
    for model in (BuyerCandidate, DealBuyerMatch):
        model.__table__.create(engine)
    with Session(engine) as db:
        brief = DealBrief(headline="Winnipeg property", region="MB-WPG", property_type="single_family", arv=320000)
        db.add(brief)
        db.commit()
        return client, engine, brief.id


def _buyer(client, email):
    response = client.post("/api/buyer/upsert", json={"email": email, "name": "Buyer"})
    assert response.status_code == 200, response.text
    return response.json()["buyer_id"]


def test_buyer_upsert_and_match(deal_client):
    client, engine, deal_id = _setup(deal_client)
    buyer_id = _buyer(client, "buyer@example.com")
    assert _buyer(client, "BUYER@example.com") == buyer_id
    response = client.post(f"/api/buyer/{buyer_id}/prefs", json={
        "regions": ["MB-WPG"], "asset_types": ["single_family"], "min_arv": 0, "max_arv": 999999,
    })
    assert response.status_code == 200, response.text
    result = client.get(f"/api/buyer/match/{deal_id}?min_score=60&limit=25")
    assert result.status_code == 200, result.text
    assert result.json()["matches"][0]["buyer_id"] == buyer_id
    with Session(engine) as db:
        assert db.query(BuyerCandidate).count() == 1


def test_buyer_claim_assign(deal_client):
    client, engine, deal_id = _setup(deal_client)
    buyer_id = _buyer(client, "buyer@example.com")
    other_id = _buyer(client, "other@example.com")
    params = {"deal_id": deal_id, "buyer_id": buyer_id}
    assert client.post("/api/buyer/assign", params=params).status_code == 409
    claim = client.post("/api/buyer/claim", params=params)
    assert claim.status_code == 200, claim.text
    assert claim.json()["status"] == "claimed"
    assert client.post("/api/buyer/claim", params={**params, "buyer_id": other_id}).status_code == 409
    assign = client.post("/api/buyer/assign", params=params)
    assert assign.status_code == 200, assign.text
    assert assign.json()["status"] == "assigned"
    with Session(engine) as db:
        match = db.query(DealBuyerMatch).filter_by(deal_id=deal_id).one()
        assert match.buyer_id == buyer_id and match.match_status == "assigned"
