"""
PACK SI: Real Estate Acquisition & BRRRR Planner
Test suite for BRRRR deal tracking and analysis
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db import Base, get_db
from app.models.brrrr_planner import BRRRRDeal, BRRRRFundingPlan, BRRRRCashflowEntry
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


class TestBRRRRDeals:
    """Test BRRRR deal creation and management."""

    def test_create_deal(self, client):
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "description": "Starter BRRRR property",
            "purchase_price": 200000,
            "reno_budget": 50000,
            "strategy_notes": "Quick flip with rental hold"
        }
        response = client.post("/brrrr/deals", json=deal_data)
        assert response.status_code == 200
        assert response.json()["deal_id"] == "deal-1"
        assert response.json()["status"] == "analysis"

    def test_list_deals(self, client):
        deal1 = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        deal2 = {
            "deal_id": "deal-2",
            "address": "456 Oak Ave",
            "purchase_price": 250000,
            "reno_budget": 60000
        }
        client.post("/brrrr/deals", json=deal1)
        client.post("/brrrr/deals", json=deal2)
        
        response = client.get("/brrrr/deals")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_filter_deals_by_status(self, client):
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        client.post("/brrrr/deals", json=deal_data)
        
        response = client.get("/brrrr/deals?status=analysis")
        assert response.status_code == 200


class TestDealStatus:
    """Test deal status transitions."""

    def test_update_deal_status(self, client):
        # Create deal
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        # Update status
        response = client.patch(f"/brrrr/deals/{deal_id}/status?new_status=in_progress")
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    def test_set_arv(self, client):
        # Create deal
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        # Set ARV after comp analysis
        response = client.patch(f"/brrrr/deals/{deal_id}/arv?arv=300000")
        assert response.status_code == 200
        assert response.json()["arv"] == 300000


class TestFundingPlans:
    """Test deal funding plan creation."""

    def test_create_funding_plan(self, client):
        # Create deal first
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        # Create funding plan
        plan_data = {
            "plan_id": "plan-1",
            "deal_id": deal_id,
            "down_payment": 40000,
            "renovation_funds_source": "hard money lender",
            "holding_costs_plan": "HELOC",
            "refinance_strategy": "Cash-out refi at 80% LTV after ARV proof"
        }
        response = client.post("/brrrr/funding-plans", json=plan_data)
        assert response.status_code == 200
        assert response.json()["plan_id"] == "plan-1"

    def test_get_funding_plan(self, client):
        # Setup
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        plan_data = {
            "plan_id": "plan-1",
            "deal_id": deal_id,
            "down_payment": 40000
        }
        client.post("/brrrr/funding-plans", json=plan_data)
        
        response = client.get(f"/brrrr/funding-plans/{deal_id}")
        assert response.status_code == 200


class TestCashflowTracking:
    """Test monthly cashflow logging."""

    def test_log_cashflow(self, client):
        # Create deal first
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        # Log cashflow
        entry_data = {
            "entry_id": "entry-1",
            "deal_id": deal_id,
            "date": datetime.now().isoformat(),
            "rent": 150000,
            "expenses": 60000
        }
        response = client.post("/brrrr/cashflow", json=entry_data)
        assert response.status_code == 200
        assert response.json()["entry_id"] == "entry-1"
        assert response.json()["net"] == 90000

    def test_list_cashflow_entries(self, client):
        # Setup
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        entry_data = {
            "entry_id": "entry-1",
            "deal_id": deal_id,
            "date": datetime.now().isoformat(),
            "rent": 150000,
            "expenses": 60000
        }
        client.post("/brrrr/cashflow", json=entry_data)
        
        response = client.get(f"/brrrr/cashflow/{deal_id}")
        assert response.status_code == 200

    def test_cashflow_average(self, client):
        # Setup
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        response = client.get(f"/brrrr/cashflow/{deal_id}/average")
        assert response.status_code == 200


class TestRefinancing:
    """Test refinance tracking."""

    def test_log_refinance(self, client):
        # Create deal
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        # Log refinance
        refi_data = {
            "snapshot_id": "refi-1",
            "deal_id": deal_id,
            "date": datetime.now().isoformat(),
            "new_loan_amount": 240000,
            "interest_rate": 6.5,
            "cash_out_amount": 40000,
            "new_payment": 152000
        }
        response = client.post("/brrrr/refinance", json=refi_data)
        assert response.status_code == 200
        assert response.json()["snapshot_id"] == "refi-1"

    def test_list_refinances(self, client):
        # Setup
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        response = client.get(f"/brrrr/refinance/{deal_id}")
        assert response.status_code == 200


class TestDealSummaries:
    """Test deal summary compilation."""

    def test_create_summary(self, client):
        # Create deal
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        # Create summary
        summary_data = {
            "summary_id": "summary-1",
            "deal_id": deal_id,
            "purchase_price": 200000,
            "reno_actual": 48000,
            "arv": 320000,
            "initial_equity": 120000,
            "refi_loan_amount": 240000,
            "cash_out": 40000,
            "current_monthly_cashflow": 90000,
            "annualized_cashflow": 1080000
        }
        response = client.post("/brrrr/summaries", json=summary_data)
        assert response.status_code == 200
        assert response.json()["summary_id"] == "summary-1"

    def test_get_summary(self, client):
        # Setup
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        summary_data = {
            "summary_id": "summary-1",
            "deal_id": deal_id,
            "purchase_price": 200000
        }
        client.post("/brrrr/summaries", json=summary_data)
        
        response = client.get("/brrrr/summaries/summary-1")
        assert response.status_code == 200


class TestDealMetrics:
    """Test deal metrics and KPIs."""

    def test_deal_metrics(self, client):
        # Create deal
        deal_data = {
            "deal_id": "deal-1",
            "address": "123 Main St",
            "purchase_price": 200000,
            "reno_budget": 50000
        }
        resp = client.post("/brrrr/deals", json=deal_data)
        deal_id = resp.json()["id"]
        
        response = client.get(f"/brrrr/metrics/{deal_id}")
        assert response.status_code == 200
        assert response.json()["deal_id"] == "deal-1"
