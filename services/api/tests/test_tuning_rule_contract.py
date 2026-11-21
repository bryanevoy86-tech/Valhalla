from app.models.tuning_rules import TuningRule


def test_canonical_tuning_rule_crud_and_threshold_evaluation(deal_client):
    client, engine = deal_client
    TuningRule.__table__.create(engine)
    endpoint = "/api/v1/tuning/rules"
    created = client.post(endpoint, json={
        "name": "Planning ceiling", "rule_type": "threshold",
        "config": {"field": "budget", "operator": "lte", "threshold": 100},
    })
    assert created.status_code == 201, created.text
    rule_id = created.json()["id"]
    assert client.get(endpoint).json()["total"] == 1
    assert client.get(f"{endpoint}/{rule_id}").json()["name"] == "Planning ceiling"
    assert client.post(f"{endpoint}/evaluate", json={"budget": 101}).json()["violations"][0]["rule_id"] == rule_id
    assert client.post(f"{endpoint}/evaluate", json={"budget": 100}).json()["passed"][0]["rule_id"] == rule_id
    assert client.patch(f"{endpoint}/{rule_id}", json={"active": False}).status_code == 200
    assert client.get(endpoint, params={"active_only": True}).json()["total"] == 0
    assert client.delete(f"{endpoint}/{rule_id}").status_code == 204
    assert client.get(f"{endpoint}/{rule_id}").status_code == 404
