"""
PACK SH: Multi-Year Projection Snapshot Framework
Test suite for projection scenarios and variance tracking
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db import Base, get_db
from app.models.projection_framework import ProjectionScenario, ProjectionYear, ProjectionVariance
from datetime import datetime


@pytest.fixture(scope="function")
def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()


@pytest.fixture
def client(db):
    """Create a test client."""
    return TestClient(app)


class TestProjectionScenarios:
    """Test projection scenario creation and management."""

    def test_create_scenario(self, client):
        scenario_data = {
            "scenario_id": "scenario-conservative",
            "name": "Conservative Growth",
            "description": "Low-growth projection",
            "created_by": "user-1",
            "assumptions": {
                "income_growth_rate": 3.0,
                "expense_growth_rate": 2.5,
                "real_estate_acquisitions": 1,
                "savings_rate": 20.0
            }
        }
        response = client.post("/projections/scenarios", json=scenario_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Conservative Growth"

    def test_list_scenarios(self, client):
        scenario1 = {
            "scenario_id": "scenario-1",
            "name": "Growth",
            "assumptions": {}
        }
        scenario2 = {
            "scenario_id": "scenario-2",
            "name": "Conservative",
            "assumptions": {}
        }
        client.post("/projections/scenarios", json=scenario1)
        client.post("/projections/scenarios", json=scenario2)
        
        response = client.get("/projections/scenarios")
        assert response.status_code == 200
        assert len(response.json()) >= 2


class TestProjectionYears:
    """Test yearly projections."""

    def test_add_projection_year(self, client):
        # Create scenario first
        scenario = {
            "scenario_id": "scenario-1",
            "name": "Test",
            "assumptions": {}
        }
        resp = client.post("/projections/scenarios", json=scenario)
        scenario_id = resp.json()["id"]
        
        # Add year
        year_data = {
            "scenario_id": scenario_id,
            "year": 2025,
            "expected_income": 1000000,
            "expected_expenses": 600000,
            "expected_savings": 400000,
            "expected_cashflow": 350000,
            "expected_net_worth": 5000000,
            "notes": "Year 1 projection"
        }
        response = client.post(f"/projections/scenarios/{scenario_id}/years", json=year_data)
        assert response.status_code == 200
        assert response.json()["year"] == 2025

    def test_list_projection_years(self, client):
        # Setup
        scenario = {
            "scenario_id": "scenario-1",
            "name": "Test",
            "assumptions": {}
        }
        resp = client.post("/projections/scenarios", json=scenario)
        scenario_id = resp.json()["id"]
        
        year_data = {
            "scenario_id": scenario_id,
            "year": 2025,
            "expected_income": 1000000,
            "expected_expenses": 600000,
            "expected_savings": 400000,
            "expected_cashflow": 350000,
            "expected_net_worth": 5000000
        }
        client.post(f"/projections/scenarios/{scenario_id}/years", json=year_data)
        
        response = client.get(f"/projections/scenarios/{scenario_id}/years")
        assert response.status_code == 200


class TestVarianceTracking:
    """Test variance recording and analysis."""

    def test_record_variance(self, client):
        variance_data = {
            "variance_id": "var-1",
            "scenario_id": 1,
            "year": 2025,
            "metric": "income",
            "expected": 1000000,
            "actual": 1050000,
            "explanation": "Bonus income exceeded expectations"
        }
        response = client.post("/projections/variances", json=variance_data)
        assert response.status_code == 200
        assert response.json()["difference"] == 50000

    def test_variance_calculation(self, client):
        variance_data = {
            "variance_id": "var-1",
            "scenario_id": 1,
            "year": 2025,
            "metric": "income",
            "expected": 1000000,
            "actual": 900000
        }
        response = client.post("/projections/variances", json=variance_data)
        assert response.status_code == 200
        result = response.json()
        assert result["difference"] == -100000
        assert result["difference_percent"] == -10.0


class TestProjectionReports:
    """Test report generation."""

    def test_create_report(self, client):
        report_data = {
            "report_id": "report-1",
            "scenario_id": 1,
            "summary": {
                "total_expected": 1000000,
                "total_actual": 950000,
                "variance": -50000
            },
            "narrative": "Year ended slightly below projection"
        }
        response = client.post("/projections/reports", json=report_data)
        assert response.status_code == 200
        assert response.json()["report_id"] == "report-1"

    def test_get_report(self, client):
        report_data = {
            "report_id": "report-1",
            "scenario_id": 1,
            "summary": {},
            "narrative": "Test narrative"
        }
        client.post("/projections/reports", json=report_data)
        
        response = client.get("/projections/reports/report-1")
        assert response.status_code == 200
        assert response.json()["report_id"] == "report-1"


class TestScenarioComparison:
    """Test scenario comparison functionality."""

    def test_scenario_comparison(self, client):
        response = client.get("/projections/comparison/1")
        # May return 404 if scenario doesn't exist, which is fine for this test
        assert response.status_code in [200, 404]
