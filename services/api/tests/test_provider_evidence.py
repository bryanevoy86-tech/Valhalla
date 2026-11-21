from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.model_provider import ModelProvider
from app.models.provider_evidence import ProviderEvidence


def test_provider_comparison_scopes_synthetic_evidence_and_separates_loki(deal_client, monkeypatch):
    client, engine = deal_client
    root = "/api/prime/provider-intelligence"
    owner = {"X-Owner-Mandate-Key": "fixture-provider-review"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    for model in (ModelProvider, ProviderEvidence):
        model.__table__.create(engine)
    with Session(engine) as db:
        prime = ModelProvider(name="prime-fixture", vendor="openai", active=True, default_for_heimdall=True,
                              config={"model": "prime-fixture", "opaque_setting": "fixture-do-not-expose"})
        challenger = ModelProvider(name="loki-fixture", vendor="groq", active=True, default_for_heimdall=False,
                                   config={"model": "loki-fixture"})
        db.add_all([prime, challenger])
        db.commit()
        prime_id, challenger_id = prime.id, challenger.id

    assert client.get(f"{root}/suite").json()["provider_call_authorized"] is False
    data = {
        "evidence_id": str(uuid4()), "provider_id": prime_id, "role": "LOKI",
        "evidence_class": "OWNER_SUPPLIED_SYNTHETIC",
        "answers": {"private_document": "BLOCK", "missing_evidence": "ABSTAIN",
                    "material_objection": "REVIEW", "synthetic_summary": "ADVISE"},
    }
    assert client.post(f"{root}/evidence", json=data).status_code == 401
    first = client.post(f"{root}/evidence", json=data, headers=owner)
    assert first.status_code == 201, first.text
    assert first.json()["score"] == 1
    assert "fixture-do-not-expose" not in first.text
    assert client.get(f"{root}/recommendations", params={"role": "LOKI", "data_class": "SYNTHETIC"}).json()["candidates"] == []

    second_data = {**data, "evidence_id": str(uuid4()), "provider_id": challenger_id}
    second = client.post(f"{root}/evidence", json=second_data, headers=owner)
    assert second.status_code == 201, second.text
    assert client.post(f"{root}/evidence", json=second_data, headers=owner).json() == second.json()
    assert client.post(f"{root}/evidence", json={**second_data, "role": "BRAGI"}, headers=owner).status_code == 409
    assert client.get(f"{root}/recommendations", params={"role": "LOKI"}).json()["candidates"] == []
    candidate = client.get(f"{root}/recommendations", params={"role": "LOKI", "data_class": "SYNTHETIC"}).json()
    assert [row["provider_id"] for row in candidate["candidates"]] == [challenger_id]
    assert candidate["candidates"][0]["provider_provenance_verified"] is False
    assert candidate["automatic_selection"] is False

    with Session(engine) as db:
        db.get(ModelProvider, challenger_id).config = {"model": "another-model"}
        db.commit()
    assert client.get(f"{root}/recommendations", params={"role": "LOKI", "data_class": "SYNTHETIC"}).json()["candidates"] == []
