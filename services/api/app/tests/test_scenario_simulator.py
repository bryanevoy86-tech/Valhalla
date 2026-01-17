"""
PACK AI: Scenario Simulator Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.db import get_db
from app.models.base import Base


@pytest.fixture
def db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client(db: Session):
    """FastAPI test client with in-memory database"""
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_scenario(client):
    """Test creating a scenario"""
    payload = {
        "key": "brrrr_scale_v1",
        "name": "BRRRR Scale v1",
        "description": "Test scaling scenario for BRRRR strategy",
        "created_by": "user_123",
    }
    res = client.post("/scenarios/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == "brrrr_scale_v1"
    assert data["name"] == "BRRRR Scale v1"
    assert data["created_by"] == "user_123"


def test_list_scenarios(client):
    """Test listing scenarios"""
    # Create multiple scenarios
    for i in range(3):
        client.post(
            "/scenarios/",
            json={
                "key": f"scenario_{i}",
                "name": f"Scenario {i}",
            },
        )

    # List scenarios
    res = client.get("/scenarios/")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 3


def test_get_scenario_by_key(client):
    """Test getting a scenario by key"""
    # Create a scenario
    client.post(
        "/scenarios/",
        json={
            "key": "wholesale_analysis",
            "name": "Wholesale Analysis",
        },
    )

    # Get by key
    res = client.get("/scenarios/by-key/wholesale_analysis")
    assert res.status_code == 200
    assert res.json()["key"] == "wholesale_analysis"


def test_get_nonexistent_scenario(client):
    """Test getting non-existent scenario returns 404"""
    res = client.get("/scenarios/by-key/nonexistent")
    assert res.status_code == 404


def test_create_scenario_run(client):
    """Test creating a scenario run"""
    # Create scenario
    res = client.post(
        "/scenarios/",
        json={
            "key": "test_scenario",
            "name": "Test Scenario",
        },
    )
    scenario_id = res.json()["id"]

    # Create run
    res = client.post(
        "/scenarios/runs",
        json={
            "scenario_id": scenario_id,
            "input_payload": {
                "doors": 10,
                "purchase_price": 100000,
                "target_roi": 0.25,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == scenario_id
    assert data["status"] == "pending"
    assert data["input_payload"]["doors"] == 10


def test_update_run_with_results(client):
    """Test updating a run with completion and results"""
    # Create scenario and run
    res = client.post(
        "/scenarios/",
        json={"key": "test", "name": "Test"},
    )
    scenario_id = res.json()["id"]

    res = client.post(
        "/scenarios/runs",
        json={
            "scenario_id": scenario_id,
            "input_payload": {"value": 1000},
        },
    )
    run_id = res.json()["id"]

    # Update with results
    res = client.patch(
        f"/scenarios/runs/{run_id}",
        json={
            "status": "completed",
            "result_payload": {
                "estimated_profit": 25000,
                "irr": 0.18,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["result_payload"]["estimated_profit"] == 25000
    assert data["completed_at"] is not None


def test_update_run_with_error(client):
    """Test marking a run as failed with error message"""
    # Create scenario and run
    res = client.post(
        "/scenarios/",
        json={"key": "fail_test", "name": "Fail Test"},
    )
    scenario_id = res.json()["id"]

    res = client.post(
        "/scenarios/runs",
        json={"scenario_id": scenario_id},
    )
    run_id = res.json()["id"]

    # Mark as failed
    res = client.patch(
        f"/scenarios/runs/{run_id}",
        json={
            "status": "failed",
            "error_message": "Division by zero in financing calculation",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failed"
    assert "Division by zero" in data["error_message"]


def test_list_runs_for_scenario(client):
    """Test listing all runs for a scenario"""
    # Create scenario
    res = client.post(
        "/scenarios/",
        json={"key": "multi_run_test", "name": "Multi Run Test"},
    )
    scenario_id = res.json()["id"]

    # Create multiple runs
    run_ids = []
    for i in range(3):
        res = client.post(
            "/scenarios/runs",
            json={
                "scenario_id": scenario_id,
                "input_payload": {"iteration": i},
            },
        )
        run_ids.append(res.json()["id"])

    # List runs for scenario
    res = client.get(f"/scenarios/runs/by-scenario/{scenario_id}")
    assert res.status_code == 200
    runs = res.json()
    assert len(runs) == 3
    assert all(r["scenario_id"] == scenario_id for r in runs)


def test_run_status_transitions(client):
    """Test transitioning run status from pending to completed"""
    # Create scenario and run
    res = client.post(
        "/scenarios/",
        json={"key": "status_test", "name": "Status Test"},
    )
    scenario_id = res.json()["id"]

    res = client.post(
        "/scenarios/runs",
        json={"scenario_id": scenario_id},
    )
    run_id = res.json()["id"]
    assert res.json()["status"] == "pending"

    # Update to running
    res = client.patch(
        f"/scenarios/runs/{run_id}",
        json={"status": "running"},
    )
    assert res.json()["status"] == "running"
    assert res.json()["completed_at"] is None

    # Update to completed
    res = client.patch(
        f"/scenarios/runs/{run_id}",
        json={
            "status": "completed",
            "result_payload": {"result": "success"},
        },
    )
    assert res.json()["status"] == "completed"
    assert res.json()["completed_at"] is not None


def test_complex_input_and_result_payloads(client):
    """Test handling complex nested JSON payloads"""
    # Create scenario
    res = client.post(
        "/scenarios/",
        json={"key": "complex_test", "name": "Complex Test"},
    )
    scenario_id = res.json()["id"]

    # Create run with complex input
    complex_input = {
        "properties": [
            {"address": "123 Main St", "value": 100000},
            {"address": "456 Oak Ave", "value": 150000},
        ],
        "financing": {
            "down_payment_percent": 0.25,
            "interest_rate": 0.045,
            "term_years": 30,
        },
        "strategy": "brrrr",
    }

    res = client.post(
        "/scenarios/runs",
        json={
            "scenario_id": scenario_id,
            "input_payload": complex_input,
        },
    )
    assert res.status_code == 200
    run_id = res.json()["id"]
    assert res.json()["input_payload"]["properties"][0]["value"] == 100000

    # Update with complex result
    complex_result = {
        "portfolio": {
            "total_value": 250000,
            "total_debt": 187500,
            "equity": 62500,
        },
        "projections": {
            "year_1": {"cash_flow": 5000, "appreciation": 7500},
            "year_5": {"cash_flow": 8000, "appreciation": 50000},
        },
    }

    res = client.patch(
        f"/scenarios/runs/{run_id}",
        json={
            "status": "completed",
            "result_payload": complex_result,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["result_payload"]["portfolio"]["equity"] == 62500


def test_update_nonexistent_run(client):
    """Test updating non-existent run returns 404"""
    res = client.patch(
        "/scenarios/runs/999",
        json={"status": "completed"},
    )
    assert res.status_code == 404


def test_scenario_and_run_isolation(client):
    """Test that runs are properly isolated by scenario"""
    # Create two scenarios
    res1 = client.post(
        "/scenarios/",
        json={"key": "scenario_a", "name": "Scenario A"},
    )
    scenario_a_id = res1.json()["id"]

    res2 = client.post(
        "/scenarios/",
        json={"key": "scenario_b", "name": "Scenario B"},
    )
    scenario_b_id = res2.json()["id"]

    # Create runs for each
    client.post(
        "/scenarios/runs",
        json={"scenario_id": scenario_a_id},
    )
    client.post(
        "/scenarios/runs",
        json={"scenario_id": scenario_b_id},
    )

    # List runs for scenario A
    res_a = client.get(f"/scenarios/runs/by-scenario/{scenario_a_id}")
    assert len(res_a.json()) == 1

    # List runs for scenario B
    res_b = client.get(f"/scenarios/runs/by-scenario/{scenario_b_id}")
    assert len(res_b.json()) == 1
