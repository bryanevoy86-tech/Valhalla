"""
PACK SG: Income Routing & Separation Engine
Test suite for income routing functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db import Base, get_db
from app.models.income_routing import IncomeRouteRule, IncomeEvent, IncomeRoutingLog
from datetime import datetime
from uuid import uuid4


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


class TestIncomeRouteRules:
    """Test income route rule creation and management."""

    def test_create_rule(self, client):
        rule_data = {
            "rule_id": "rule-1",
            "source": "paycheck",
            "description": "Monthly salary",
            "allocation_type": "percent",
            "allocation_value": 50.0,
            "target_account": "checking",
            "active": True
        }
        response = client.post("/income/rules", json=rule_data)
        assert response.status_code == 200
        assert response.json()["rule_id"] == "rule-1"
        assert response.json()["allocation_value"] == 50.0

    def test_get_active_rules(self, client):
        rule1 = {
            "rule_id": "rule-1",
            "source": "paycheck",
            "allocation_type": "percent",
            "allocation_value": 50.0,
            "target_account": "checking"
        }
        rule2 = {
            "rule_id": "rule-2",
            "source": "business",
            "allocation_type": "percent",
            "allocation_value": 75.0,
            "target_account": "business_account"
        }
        client.post("/income/rules", json=rule1)
        client.post("/income/rules", json=rule2)
        
        response = client.get("/income/rules")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_filter_rules_by_source(self, client):
        rule1 = {
            "rule_id": "rule-1",
            "source": "paycheck",
            "allocation_type": "percent",
            "allocation_value": 50.0,
            "target_account": "checking"
        }
        client.post("/income/rules", json=rule1)
        
        response = client.get("/income/rules?source=paycheck")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestIncomeEvents:
    """Test income event logging."""

    def test_log_income_event(self, client):
        event_data = {
            "event_id": "event-1",
            "date": datetime.now().isoformat(),
            "source": "paycheck",
            "amount": 500000,
            "notes": "Monthly salary deposit"
        }
        response = client.post("/income/events", json=event_data)
        assert response.status_code == 200
        assert response.json()["event_id"] == "event-1"
        assert response.json()["amount"] == 500000

    def test_list_income_events(self, client):
        event1 = {
            "event_id": "event-1",
            "date": datetime.now().isoformat(),
            "source": "paycheck",
            "amount": 500000
        }
        event2 = {
            "event_id": "event-2",
            "date": datetime.now().isoformat(),
            "source": "business",
            "amount": 300000
        }
        client.post("/income/events", json=event1)
        client.post("/income/events", json=event2)
        
        response = client.get("/income/events")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_filter_events_by_source(self, client):
        event_data = {
            "event_id": "event-1",
            "date": datetime.now().isoformat(),
            "source": "paycheck",
            "amount": 500000
        }
        client.post("/income/events", json=event_data)
        
        response = client.get("/income/events?source=paycheck")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestRouteCalculation:
    """Test routing calculation and allocation."""

    def test_calculate_routing_allocation(self, client):
        # Create rule
        rule_data = {
            "rule_id": "rule-1",
            "source": "paycheck",
            "allocation_type": "percent",
            "allocation_value": 50.0,
            "target_account": "savings"
        }
        client.post("/income/rules", json=rule_data)
        
        # Create event
        event_data = {
            "event_id": "event-1",
            "date": datetime.now().isoformat(),
            "source": "paycheck",
            "amount": 500000
        }
        client.post("/income/events", json=event_data)
        
        # Calculate
        response = client.post("/income/calculate/event-1")
        assert response.status_code == 200
        assert response.json()["total_income"] == 500000

    def test_pending_routings(self, client):
        response = client.get("/income/pending-routings")
        assert response.status_code == 200


class TestRoutingSummary:
    """Test routing summary creation and retrieval."""

    def test_create_summary(self, client):
        summary_data = {
            "summary_id": "summary-1",
            "date": datetime.now().isoformat(),
            "total_income": 500000,
            "allocations": [
                {
                    "target_account": "savings",
                    "amount": 250000,
                    "percent_of_total": 50.0
                }
            ],
            "unallocated_balance": 250000
        }
        response = client.post("/income/summaries", json=summary_data)
        assert response.status_code == 200
        assert response.json()["summary_id"] == "summary-1"
        assert response.json()["total_income"] == 500000

    def test_get_summary(self, client):
        summary_data = {
            "summary_id": "summary-1",
            "date": datetime.now().isoformat(),
            "total_income": 500000,
            "allocations": [],
            "unallocated_balance": 500000
        }
        client.post("/income/summaries", json=summary_data)
        
        response = client.get("/income/summaries/summary-1")
        assert response.status_code == 200
        assert response.json()["summary_id"] == "summary-1"
