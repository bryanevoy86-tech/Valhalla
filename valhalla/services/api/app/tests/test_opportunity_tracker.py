"""
Tests for PACK SK: Arbitrage/Side-Hustle Opportunity Tracker
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db, Base
from app.models.opportunity_tracker import (
    Opportunity, OpportunityScore, OpportunityPerformance, OpportunitySummary
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestOpportunities:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_opportunity(self):
        payload = {
            "name": "Dropshipping Store",
            "category": "digital",
            "startup_cost": 50000,
            "expected_effort": 10,
            "potential_return": 500000,
            "risk_level": "medium",
            "status": "idea"
        }
        response = client.post("/opportunities/", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Dropshipping Store"

    def test_list_opportunities(self):
        client.post("/opportunities/", json={
            "name": "Freelance Service",
            "category": "service",
            "startup_cost": 10000,
            "expected_effort": 15,
            "potential_return": 200000,
            "risk_level": "low",
            "status": "idea"
        })
        response = client.get("/opportunities/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_opportunity(self):
        create_resp = client.post("/opportunities/", json={
            "name": "Arbitrage Trading",
            "category": "arbitrage",
            "startup_cost": 100000,
            "expected_effort": 20,
            "potential_return": 500000,
            "risk_level": "high",
            "status": "idea"
        })
        opp_id = create_resp.json()["id"]
        response = client.get(f"/opportunities/{opp_id}")
        assert response.status_code == 200

    def test_update_opportunity_status(self):
        create_resp = client.post("/opportunities/", json={
            "name": "Seasonal Business",
            "category": "seasonal",
            "startup_cost": 25000,
            "expected_effort": 12,
            "potential_return": 300000,
            "risk_level": "medium",
            "status": "idea"
        })
        opp_id = create_resp.json()["id"]
        response = client.put(f"/opportunities/{opp_id}/status", json={"status": "researching"})
        assert response.status_code == 200
        assert response.json()["status"] == "researching"


class TestScoring:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_opportunity_score(self):
        opp_resp = client.post("/opportunities/", json={
            "name": "Gig Economy Work",
            "category": "gig",
            "startup_cost": 5000,
            "expected_effort": 8,
            "potential_return": 150000,
            "risk_level": "low",
            "status": "idea"
        })
        opp_id = opp_resp.json()["id"]

        payload = {
            "time_efficiency": 8,
            "scalability": 6,
            "difficulty": 5,
            "personal_interest": 7,
            "notes": "Good fit for current schedule"
        }
        response = client.post(f"/opportunities/{opp_id}/score", json=payload)
        assert response.status_code == 200
        assert response.json()["time_efficiency"] == 8


class TestPerformance:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_log_performance(self):
        opp_resp = client.post("/opportunities/", json={
            "name": "Online Course Sales",
            "category": "digital",
            "startup_cost": 20000,
            "expected_effort": 14,
            "potential_return": 400000,
            "risk_level": "medium",
            "status": "active"
        })
        opp_id = opp_resp.json()["id"]

        payload = {
            "date": datetime.utcnow().isoformat(),
            "effort_hours": 5.5,
            "revenue": 50000
        }
        response = client.post(f"/opportunities/{opp_id}/performance", json=payload)
        assert response.status_code == 200

    def test_get_performance_logs(self):
        opp_resp = client.post("/opportunities/", json={
            "name": "Affiliate Marketing",
            "category": "digital",
            "startup_cost": 10000,
            "expected_effort": 10,
            "potential_return": 300000,
            "risk_level": "medium",
            "status": "active"
        })
        opp_id = opp_resp.json()["id"]

        client.post(f"/opportunities/{opp_id}/performance", json={
            "date": datetime.utcnow().isoformat(),
            "effort_hours": 3,
            "revenue": 25000
        })

        response = client.get(f"/opportunities/{opp_id}/performance")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestSummaries:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_opportunity_summary(self):
        opp_resp = client.post("/opportunities/", json={
            "name": "Product Launch",
            "category": "product",
            "startup_cost": 75000,
            "expected_effort": 18,
            "potential_return": 600000,
            "risk_level": "high",
            "status": "testing"
        })
        opp_id = opp_resp.json()["id"]

        payload = {
            "period": "2024-01",
            "total_effort_hours": 120,
            "total_revenue": 150000,
            "roi": 1.0,
            "status_update": "Good progress"
        }
        response = client.post(f"/opportunities/{opp_id}/summary", json=payload)
        assert response.status_code == 200

    def test_get_opportunity_summary(self):
        opp_resp = client.post("/opportunities/", json={
            "name": "Consulting Business",
            "category": "service",
            "startup_cost": 30000,
            "expected_effort": 16,
            "potential_return": 400000,
            "risk_level": "low",
            "status": "active"
        })
        opp_id = opp_resp.json()["id"]

        client.post(f"/opportunities/{opp_id}/summary", json={
            "period": "2024-01",
            "total_effort_hours": 150,
            "total_revenue": 200000,
            "roi": 5.67,
            "status_update": "Exceeding expectations"
        })

        response = client.get(f"/opportunities/{opp_id}/summary")
        assert response.status_code == 200


class TestComparison:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_compare_opportunities(self):
        client.post("/opportunities/", json={
            "name": "Opp 1",
            "category": "service",
            "startup_cost": 10000,
            "expected_effort": 10,
            "potential_return": 100000,
            "risk_level": "low",
            "status": "active"
        })
        
        client.post("/opportunities/", json={
            "name": "Opp 2",
            "category": "digital",
            "startup_cost": 20000,
            "expected_effort": 15,
            "potential_return": 200000,
            "risk_level": "medium",
            "status": "active"
        })

        response = client.get("/opportunities/comparison/metrics")
        assert response.status_code == 200
        assert "opportunities" in response.json()
