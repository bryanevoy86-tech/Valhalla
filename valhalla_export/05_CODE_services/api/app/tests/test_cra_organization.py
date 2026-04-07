"""Tests for PACK SF: CRA / Tax Interaction Organizational Module"""

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


class TestCRADocumentVault:
    """Test CRA document vault"""
    
    def test_create_cra_document(self, db: Session):
        """Test creating CRA document"""
        response = client.post("/cra/documents", json={
            "doc_id": "doc-income-001",
            "year": 2024,
            "category": "income",
            "description": "T4 Slip",
            "file_name": "T4-2024.pdf",
            "notes": "Employment income"
        })
        assert response.status_code == 200
        assert response.json()["doc_id"] == "doc-income-001"
    
    def test_get_documents_by_year(self, db: Session):
        """Test retrieving documents by year"""
        # Create documents
        client.post("/cra/documents", json={
            "doc_id": "doc-expense-001",
            "year": 2024,
            "category": "expense",
            "description": "Office Supplies Receipt"
        })
        
        response = client.get("/cra/documents/2024")
        assert response.status_code == 200
        assert len(response.json()) > 0
    
    def test_get_documents_by_category(self, db: Session):
        """Test retrieving documents by category"""
        client.post("/cra/documents", json={
            "doc_id": "doc-vehicle-001",
            "year": 2024,
            "category": "vehicle",
            "description": "Mileage Log"
        })
        
        response = client.get("/cra/documents/2024/vehicle")
        assert response.status_code == 200
        assert len(response.json()) > 0
    
    def test_flag_document(self, db: Session):
        """Test flagging document for review"""
        create_resp = client.post("/cra/documents", json={
            "doc_id": "doc-flag-001",
            "year": 2024,
            "category": "expense",
            "description": "Receipt"
        })
        doc_id = create_resp.json()["id"]
        
        response = client.patch(f"/cra/documents/{doc_id}/flag?reason=missing_receipt")
        assert response.status_code == 200
        assert response.json()["flagged"] == True


class TestCRASummary:
    """Test annual CRA summary"""
    
    def test_create_annual_summary(self, db: Session):
        """Test creating annual summary"""
        response = client.post("/cra/summary", json={
            "summary_id": "summary-2024",
            "year": 2024,
            "total_income": 150000,
            "total_business_expenses": 50000,
            "total_personal_expenses": 20000
        })
        assert response.status_code == 200
        assert response.json()["year"] == 2024
    
    def test_get_annual_summary(self, db: Session):
        """Test retrieving annual summary"""
        client.post("/cra/summary", json={
            "summary_id": "summary-2024-test",
            "year": 2024,
            "total_income": 100000
        })
        
        response = client.get("/cra/summary/2024")
        assert response.status_code == 200
        assert response.json()["year"] == 2024
    
    def test_update_summary_status(self, db: Session):
        """Test updating summary review status"""
        create_resp = client.post("/cra/summary", json={
            "summary_id": "summary-status-test",
            "year": 2024
        })
        summary_id = create_resp.json()["id"]
        
        response = client.patch(f"/cra/summary/{summary_id}/status?status=reviewed")
        assert response.status_code == 200
        assert response.json()["review_status"] == "reviewed"
    
    def test_add_flagged_item(self, db: Session):
        """Test adding flagged item to summary"""
        create_resp = client.post("/cra/summary", json={
            "summary_id": "summary-flag-test",
            "year": 2024
        })
        summary_id = create_resp.json()["id"]
        
        response = client.post(f"/cra/summary/{summary_id}/flag-item", json={
            "date": "2024-03-15",
            "amount": 5000,
            "reason": "unusually_high"
        })
        assert response.status_code == 200
        flagged_items = response.json()["flagged_items"]
        assert flagged_items is not None
    
    def test_add_accountant_question(self, db: Session):
        """Test adding question for accountant"""
        create_resp = client.post("/cra/summary", json={
            "summary_id": "summary-question-test",
            "year": 2024
        })
        summary_id = create_resp.json()["id"]
        
        response = client.post(f"/cra/summary/{summary_id}/question", json={
            "question": "What percentage of vehicle use is business?",
            "context": "High vehicle expenses this year"
        })
        assert response.status_code == 200


class TestCRACategoryMap:
    """Test CRA category mapping"""
    
    def test_create_category_map(self, db: Session):
        """Test creating category mapping"""
        response = client.post("/cra/categories", json={
            "category_id": "cat-office-supplies",
            "category": "office_supplies",
            "user_defined_description": "Office supplies and stationery",
            "cra_line_reference": "Line 8232"
        })
        assert response.status_code == 200
        assert response.json()["category"] == "office_supplies"
    
    def test_list_category_maps(self, db: Session):
        """Test listing all category mappings"""
        client.post("/cra/categories", json={
            "category_id": "cat-fuel",
            "category": "fuel",
            "user_defined_description": "Vehicle fuel expenses"
        })
        
        response = client.get("/cra/categories")
        assert response.status_code == 200
        assert len(response.json()) > 0
    
    def test_get_category_map(self, db: Session):
        """Test retrieving specific category mapping"""
        client.post("/cra/categories", json={
            "category_id": "cat-vehicle-maintenance",
            "category": "vehicle_maintenance",
            "user_defined_description": "Vehicle maintenance costs"
        })
        
        response = client.get("/cra/categories/vehicle_maintenance")
        assert response.status_code == 200
        assert response.json()["category"] == "vehicle_maintenance"
    
    def test_add_example_transaction(self, db: Session):
        """Test adding example transaction to category"""
        create_resp = client.post("/cra/categories", json={
            "category_id": "cat-example-test",
            "category": "example_test",
            "user_defined_description": "Example test category"
        })
        cat_id = create_resp.json()["id"]
        
        response = client.post(f"/cra/categories/{cat_id}/example", json={
            "description": "Oil change",
            "amount": 75.00,
            "date": "2024-02-15"
        })
        assert response.status_code == 200


class TestFiscalYearSnapshot:
    """Test fiscal year snapshots"""
    
    def test_create_fiscal_snapshot(self, db: Session):
        """Test creating fiscal year snapshot"""
        response = client.post("/cra/snapshot", json={
            "snapshot_id": "snap-2024",
            "year": 2024,
            "fiscal_year_end": "2024-12-31T23:59:59",
            "transaction_count": 150,
            "total_amount": 250000,
            "documents_count": 50,
            "flagged_count": 5
        })
        assert response.status_code == 200
        assert response.json()["year"] == 2024
    
    def test_get_fiscal_snapshot(self, db: Session):
        """Test retrieving fiscal snapshot"""
        client.post("/cra/snapshot", json={
            "snapshot_id": "snap-2024-test",
            "year": 2024,
            "fiscal_year_end": "2024-12-31T23:59:59"
        })
        
        response = client.get("/cra/snapshot/2024")
        assert response.status_code == 200
        assert response.json()["year"] == 2024


class TestAnnualReport:
    """Test annual CRA reporting"""
    
    def test_get_annual_report(self, db: Session):
        """Test generating annual report"""
        # Setup: create summary
        client.post("/cra/summary", json={
            "summary_id": "summary-report-2024",
            "year": 2024,
            "total_income": 150000,
            "total_business_expenses": 50000
        })
        
        # Create documents
        client.post("/cra/documents", json={
            "doc_id": "doc-report-001",
            "year": 2024,
            "category": "income",
            "description": "T4"
        })
        
        # Get report
        response = client.get("/cra/report/2024")
        assert response.status_code == 200
        assert response.json()["year"] == 2024
        assert "completeness_score" in response.json()
