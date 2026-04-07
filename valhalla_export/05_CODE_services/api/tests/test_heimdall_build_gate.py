from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def _base_build_request():
    return {
        "title": "Add makeup vertical product catalog",
        "description": "Create initial makeup product models, CRUD APIs, and admin UI endpoints.",
        "vertical": "makeup",
        "priority": 7,
        "estimated_hours": 16,
        "complexity_score": 6,
        "estimated_annual_profit_impact": 150000,
        "strategic_importance": 8,
        "is_core_infrastructure": False,
        "touches_financial_flows": False,
        "touches_legal_contracts": False,
        "experimental_only": False,
        "governance_flags": {},
        "scope": {
            "target_dirs": [
                "services/api/app/routers",
                "services/api/app/models",
                "services/api/app/schemas",
            ],
            "max_files": 10,
            "allow_migrations": False,
            "allow_new_routes": True,
            "allow_schema_changes": False,
        },
    }

def test_heimdall_build_request_approved():
    """
    Healthy build request with reasonable complexity and strong strategic importance.
    Governance should allow; builder_task_created may be True or False
    depending on whether /api/builder/tasks is implemented.
    """
    payload = _base_build_request()

    resp = client.post("/governance/heimdall_build_request", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert "accepted" in data
    assert "governance" in data
    assert data["governance"]["worst_severity"] in ["info", "warn"]
    assert data["accepted"] is True

def test_heimdall_build_request_blocked_by_tyr():
    """
    If governance flags a hard legal/ethical line (e.g., tax evasion), the build
    should be rejected and no builder task attempted.
    """
    payload = _base_build_request()
    payload["governance_flags"] = {
        "tax_evasion": "true",
    }

    resp = client.post("/governance/heimdall_build_request", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["accepted"] is False
    assert data["builder_task_created"] is False
    gov = data["governance"]

    assert gov["overall_allowed"] is False
    assert gov["worst_severity"] == "critical"
    assert "tyr" in gov["blocked_by"]
