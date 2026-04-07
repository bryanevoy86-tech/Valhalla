"""Tests for PACK SE: Vehicle Use & Expense Categorization Framework"""

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


class TestVehicleProfiles:
    """Test vehicle profile management"""
    
    def test_create_vehicle_profile(self, db: Session):
        """Test creating vehicle profile"""
        response = client.post("/vehicles/profiles", json={
            "vehicle_id": "urus-001",
            "name": "Urus",
            "type": "luxury-suv",
            "ownership": "company-owned",
            "make": "Lamborghini",
            "model": "Urus",
            "year": 2024,
            "status": "active"
        })
        assert response.status_code == 200
        assert response.json()["name"] == "Urus"
    
    def test_list_vehicle_profiles(self, db: Session):
        """Test listing vehicle profiles"""
        client.post("/vehicles/profiles", json={
            "vehicle_id": "f150-001",
            "name": "F150",
            "type": "truck",
            "ownership": "personally-owned"
        })
        
        response = client.get("/vehicles/profiles")
        assert response.status_code == 200
        assert len(response.json()) > 0
    
    def test_get_vehicle_profile(self, db: Session):
        """Test getting specific vehicle"""
        create_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "model3-001",
            "name": "Model 3",
            "type": "sedan",
            "ownership": "personally-owned"
        })
        vehicle_id = create_resp.json()["id"]
        
        response = client.get(f"/vehicles/profiles/{vehicle_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Model 3"


class TestVehicleTrips:
    """Test vehicle trip logging"""
    
    def test_create_trip_log(self, db: Session):
        """Test creating trip log"""
        # Create vehicle first
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "trip-test-001",
            "name": "Test Vehicle",
            "type": "sedan",
            "ownership": "company-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        # Log trip
        response = client.post("/vehicles/trips", json={
            "trip_id": "trip-001",
            "vehicle_id": vehicle_id,
            "date": datetime.now().isoformat(),
            "start_location": "Toronto",
            "end_location": "Ottawa",
            "kms": 450.5,
            "purpose": "client meeting",
            "business_use": True
        })
        assert response.status_code == 200
        assert response.json()["kms"] == 450.5
    
    def test_get_vehicle_trips(self, db: Session):
        """Test retrieving all trips for vehicle"""
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "trip-test-002",
            "name": "Test Vehicle 2",
            "type": "truck",
            "ownership": "personally-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        # Create multiple trips
        client.post("/vehicles/trips", json={
            "trip_id": "trip-001",
            "vehicle_id": vehicle_id,
            "date": datetime.now().isoformat(),
            "kms": 100,
            "business_use": True
        })
        
        client.post("/vehicles/trips", json={
            "trip_id": "trip-002",
            "vehicle_id": vehicle_id,
            "date": datetime.now().isoformat(),
            "kms": 50,
            "personal_use": True
        })
        
        response = client.get(f"/vehicles/trips/{vehicle_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestVehicleExpenses:
    """Test vehicle expense tracking"""
    
    def test_create_vehicle_expense(self, db: Session):
        """Test logging vehicle expense"""
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "expense-test-001",
            "name": "Expense Test",
            "type": "truck",
            "ownership": "company-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        response = client.post("/vehicles/expenses", json={
            "expense_id": "exp-001",
            "vehicle_id": vehicle_id,
            "date": datetime.now().isoformat(),
            "category": "fuel",
            "amount": 125.50,
            "business_related": True
        })
        assert response.status_code == 200
        assert response.json()["amount"] == 125.50
    
    def test_get_expenses_by_category(self, db: Session):
        """Test retrieving expenses by category"""
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "expense-test-002",
            "name": "Expense Test 2",
            "type": "luxury-suv",
            "ownership": "company-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        # Create multiple expenses
        client.post("/vehicles/expenses", json={
            "expense_id": "exp-fuel-001",
            "vehicle_id": vehicle_id,
            "date": datetime.now().isoformat(),
            "category": "fuel",
            "amount": 100,
            "business_related": True
        })
        
        client.post("/vehicles/expenses", json={
            "expense_id": "exp-maint-001",
            "vehicle_id": vehicle_id,
            "date": datetime.now().isoformat(),
            "category": "maintenance",
            "amount": 500,
            "business_related": True
        })
        
        response = client.get(f"/vehicles/expenses/{vehicle_id}/category/fuel")
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestMileageSummary:
    """Test mileage summary generation"""
    
    def test_generate_monthly_mileage(self, db: Session):
        """Test generating monthly mileage summary"""
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "mileage-test-001",
            "name": "Mileage Test",
            "type": "sedan",
            "ownership": "company-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        response = client.post(f"/vehicles/mileage/{vehicle_id}/2025/1", json={})
        assert response.status_code == 200
        assert response.json()["year"] == 2025
    
    def test_get_annual_mileage(self, db: Session):
        """Test retrieving annual mileage"""
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "mileage-test-002",
            "name": "Mileage Test 2",
            "type": "truck",
            "ownership": "personally-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        response = client.get(f"/vehicles/mileage/{vehicle_id}/2025")
        assert response.status_code == 200
        assert response.json()["total_kms"] == 0  # No trips yet
    
    def test_vehicle_status_summary(self, db: Session):
        """Test vehicle status summary"""
        vehicle_resp = client.post("/vehicles/profiles", json={
            "vehicle_id": "status-test-001",
            "name": "Status Test",
            "type": "sedan",
            "ownership": "company-owned"
        })
        vehicle_id = vehicle_resp.json()["id"]
        
        response = client.get(f"/vehicles/status/{vehicle_id}/2025/1")
        assert response.status_code == 200
        assert response.json()["vehicle_id"] == vehicle_id
