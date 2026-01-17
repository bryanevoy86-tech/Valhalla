"""Tests for PACK SD: Credit Card & Spending Framework"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.main import app
from app.core.db import Base, SessionLocal, engine

# Create test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def db():
    """Database fixture"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestCreditCardProfiles:
    """Test credit card profile management"""
    
    def test_create_card_profile(self, db: Session):
        """Test creating card profile"""
        response = client.post("/cards/profiles", json={
            "card_id": "visa-001",
            "nickname": "Business Visa",
            "issuer": "Chase",
            "card_type": "business",
            "status": "active",
            "allowed_categories": [{"category": "travel", "notes": "business travel only"}],
            "notes": "Primary business card"
        })
        assert response.status_code == 200
        assert response.json()["card_id"] == "visa-001"
    
    def test_list_card_profiles(self, db: Session):
        """Test listing card profiles"""
        # Create a profile first
        client.post("/cards/profiles", json={
            "card_id": "amex-001",
            "nickname": "Corporate Amex",
            "card_type": "business"
        })
        
        response = client.get("/cards/profiles")
        assert response.status_code == 200
        assert len(response.json()) > 0
    
    def test_get_card_profile(self, db: Session):
        """Test getting specific card profile"""
        create_resp = client.post("/cards/profiles", json={
            "card_id": "card-test-001",
            "nickname": "Test Card",
            "card_type": "personal"
        })
        card_id = create_resp.json()["id"]
        
        response = client.get(f"/cards/profiles/{card_id}")
        assert response.status_code == 200
        assert response.json()["nickname"] == "Test Card"
    
    def test_get_nonexistent_card(self):
        """Test getting nonexistent card"""
        response = client.get("/cards/profiles/99999")
        assert response.status_code == 404


class TestSpendingRules:
    """Test spending rule creation and management"""
    
    def test_create_spending_rule(self, db: Session):
        """Test creating spending rule"""
        # Create card first
        card_resp = client.post("/cards/profiles", json={
            "card_id": "visa-rules-001",
            "nickname": "Rules Test Card",
            "card_type": "business"
        })
        card_id = card_resp.json()["id"]
        
        # Create rule
        response = client.post("/cards/rules", json={
            "rule_id": "rule-fuel-001",
            "card_id": card_id,
            "category": "fuel",
            "business_allowed": True,
            "personal_allowed": False,
            "notes": "Fuel purchases - business only"
        })
        assert response.status_code == 200
        assert response.json()["category"] == "fuel"
    
    def test_get_card_rules(self, db: Session):
        """Test getting rules for card"""
        # Create card and rules
        card_resp = client.post("/cards/profiles", json={
            "card_id": "visa-rules-002",
            "nickname": "Rules Test Card 2",
            "card_type": "business"
        })
        card_id = card_resp.json()["id"]
        
        client.post("/cards/rules", json={
            "rule_id": "rule-food-001",
            "card_id": card_id,
            "category": "food",
            "business_allowed": True,
            "personal_allowed": True
        })
        
        response = client.get(f"/cards/rules/{card_id}")
        assert response.status_code == 200
        assert len(response.json()) > 0


class TestTransactions:
    """Test transaction logging and compliance checking"""
    
    def test_log_transaction(self, db: Session):
        """Test logging a transaction"""
        # Setup
        card_resp = client.post("/cards/profiles", json={
            "card_id": "visa-txn-001",
            "nickname": "Transaction Test",
            "card_type": "business"
        })
        card_id = card_resp.json()["id"]
        
        # Log transaction
        response = client.post("/cards/transactions", json={
            "transaction_id": "txn-001",
            "card_id": card_id,
            "date": datetime.now().isoformat(),
            "merchant": "Shell Gas Station",
            "amount": 5000,
            "detected_category": "fuel",
            "user_classification": "business"
        })
        assert response.status_code == 200
        assert response.json()["transaction_id"] == "txn-001"
    
    def test_flagged_transactions(self, db: Session):
        """Test retrieving flagged transactions"""
        card_resp = client.post("/cards/profiles", json={
            "card_id": "visa-flag-001",
            "nickname": "Flag Test",
            "card_type": "business"
        })
        card_id = card_resp.json()["id"]
        
        # Create rule
        client.post("/cards/rules", json={
            "rule_id": "rule-test-001",
            "card_id": card_id,
            "category": "food",
            "business_allowed": False,
            "personal_allowed": True
        })
        
        # Log non-compliant transaction
        client.post("/cards/transactions", json={
            "transaction_id": "txn-flag-001",
            "card_id": card_id,
            "date": datetime.now().isoformat(),
            "merchant": "Restaurant",
            "amount": 10000,
            "detected_category": "food",
            "user_classification": "business"
        })
        
        response = client.get(f"/cards/flagged/{card_id}")
        assert response.status_code == 200
        # Should have flagged transaction
        assert len(response.json()) > 0


class TestMonthlySummary:
    """Test monthly spending summary generation"""
    
    def test_generate_monthly_summary(self, db: Session):
        """Test generating monthly summary"""
        card_resp = client.post("/cards/profiles", json={
            "card_id": "visa-summary-001",
            "nickname": "Summary Test",
            "card_type": "business"
        })
        card_id = card_resp.json()["id"]
        
        response = client.post(f"/cards/summary/{card_id}/2025/1", json={})
        assert response.status_code == 200
        assert response.json()["month"] == "2025-01"
    
    def test_get_monthly_summary(self, db: Session):
        """Test retrieving monthly summary"""
        card_resp = client.post("/cards/profiles", json={
            "card_id": "visa-summary-002",
            "nickname": "Summary Test 2",
            "card_type": "personal"
        })
        card_id = card_resp.json()["id"]
        
        # Generate first
        client.post(f"/cards/summary/{card_id}/2025/1", json={})
        
        # Then get
        response = client.get(f"/cards/summary/{card_id}/2025/1")
        assert response.status_code == 200
        assert response.json()["card_id"] == card_id
