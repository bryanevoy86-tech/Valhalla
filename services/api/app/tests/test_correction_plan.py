"""
Tests for PACK CL14: Correction Plans
"""

from fastapi.testclient import TestClient


def test_create_and_list_correction_plans(client: TestClient):
    resp = client.post(
        "/heimdall/corrections/plans",
        json={
            "plan_id": "plan-001",
            "run_id": "run-001",
            "title": "Adjust lead scoring weight",
            "description": "Reduce overweighting of one signal",
            "actions": [{"type": "adjust_weight", "path": "leads.score.weight_x", "value": 0.15}],
            "requires_human_approval": True,
        },
    )
    assert resp.status_code == 201, resp.text

    lst = client.get("/heimdall/corrections/plans")
    assert lst.status_code == 200
    assert lst.json()["total"] >= 1
