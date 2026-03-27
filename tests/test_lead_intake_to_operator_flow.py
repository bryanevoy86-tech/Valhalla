#!/usr/bin/env python
"""
TEST: Lead Intake to Operator Flow

End-to-end test coverage for the canonical lead intake path:
Lead → DB Persist → Deal Conversion → Operator Visibility → Audit Trail

This test exercises the real API contract and verifies no 500s occur.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app

# Database
DB_PATH = Path(__file__).parent / "valhalla_local.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Client
client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}


class TestLeadIntakePipeline:
    """Test lead intake end-to-end."""
    
    def test_01_create_lead_via_canonical_path(self):
        """TEST: Create lead through POST /api/leads"""
        print("\n[TEST 1] Create lead via canonical path")
        
        payload = {
            "lead_name": "John Doe - Test",
            "lead_email": "john.test@example.com",
            "lead_phone": "+1-555-0200",
            "property_address": "456 Oak Ave",
            "property_city": "Boulder",
            "property_state": "CO",
            "property_zip": "80301",
            "estimated_arv": 400000,
            "source": "test_suite",
            "lead_status": "new"
        }
        
        response = client.post("/api/leads", json=payload, headers=HEADERS)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"], "No lead ID returned"
        assert data["lead_name"] == payload["lead_name"]
        assert data["lead_email"] == payload["lead_email"]
        
        print(f"   ✅ Lead created (ID={data['id']})")
        return data["id"]
    
    def test_02_verify_lead_persists(self, lead_id: int):
        """TEST: Verify lead exists in database"""
        print("\n[TEST 2] Verify lead persists to database")
        
        db = SessionLocal()
        try:
            row = db.execute(text(
                "SELECT id, lead_name, lead_email, estimated_arv FROM leads WHERE id = :id"
            ), {"id": lead_id}).first()
            
            assert row is not None, f"Lead {lead_id} not found in DB"
            assert row[1] == "John Doe - Test"
            assert row[2] == "john.test@example.com"
            assert row[3] == Decimal("400000")
            
            print(f"   ✅ Lead {lead_id} persisted correctly")
        finally:
            db.close()
    
    def test_03_convert_lead_to_deal(self, lead_id: int):
        """TEST: Convert lead to deal via POST /api/deals/from-lead/{lead_id}"""
        print("\n[TEST 3] Convert lead to deal")
        
        payload = {
            "lead_id": lead_id,
            "title": f"Deal from Lead {lead_id}",
            "stage": "lead_received",
            "status": "active",
            "arv": 400000,
            "estimated_repair_cost": 40000,
            "max_allowable_offer": 300000,
            "target_assignment_fee": 12000,
            "score": 80,
            "notes": "Test deal from lead intake"
        }
        
        response = client.post(f"/api/deals/from-lead/{lead_id}", json=payload, headers=HEADERS)
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"], "No deal ID returned"
        assert data["lead_id"] == lead_id, "Lead ID not preserved"
        assert data["stage"] == "lead_received"
        assert data["status"] == "active"
        
        print(f"   ✅ Deal created (ID={data['id']}) linked to lead {lead_id}")
        return data["id"]
    
    def test_04_verify_no_duplicate_deal(self, lead_id: int, deal_id: int):
        """TEST: Ensure no accidental duplicate deals created"""
        print("\n[TEST 4] Verify no duplicate deals")
        
        db = SessionLocal()
        try:
            count = db.execute(text(
                "SELECT COUNT(*) FROM deals WHERE lead_id = :lead_id"
            ), {"lead_id": lead_id}).scalar()
            
            assert count == 1, f"Expected 1 deal for lead {lead_id}, got {count}"
            
            print(f"   ✅ Only 1 deal for lead {lead_id} (no duplicates)")
        finally:
            db.close()
    
    def test_05_deal_visible_in_list(self, deal_id: int):
        """TEST: Deal appears in GET /api/deals"""
        print("\n[TEST 5] Deal visible in operator list")
        
        response = client.get("/api/deals", headers=HEADERS)
        
        assert response.status_code == 200
        deals = response.json()
        found = any(d["id"] == deal_id for d in deals)
        assert found, f"Deal {deal_id} not found in list"
        
        print(f"   ✅ Deal {deal_id} visible in /api/deals")
    
    def test_06_deal_detail_accessible(self, deal_id: int):
        """TEST: Deal details accessible via GET /api/deals/{deal_id}"""
        print("\n[TEST 6] Deal detail accessible")
        
        response = client.get(f"/api/deals/{deal_id}", headers=HEADERS)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == deal_id
        assert data["title"]
        assert data["stage"]
        
        print(f"   ✅ Deal {deal_id} detail accessible")
    
    def test_07_audit_lead_creation(self, lead_id: int):
        """TEST: Lead creation event in audit"""
        print("\n[TEST 7] Lead creation audited")
        
        db = SessionLocal()
        try:
            event = db.execute(text(
                "SELECT * FROM audit_logs WHERE entity_type='lead' AND entity_id=:id AND action='created'"
            ), {"id": lead_id}).first()
            
            assert event is not None, f"No creation audit event for lead {lead_id}"
            
            print(f"   ✅ Lead {lead_id} creation event in audit log")
        finally:
            db.close()
    
    def test_08_audit_deal_creation(self, deal_id: int):
        """TEST: Deal creation event in audit"""
        print("\n[TEST 8] Deal creation audited")
        
        db = SessionLocal()
        try:
            event = db.execute(text(
                "SELECT * FROM audit_logs WHERE entity_type='deal' AND entity_id=:id AND action='created'"
            ), {"id": deal_id}).first()
            
            assert event is not None, f"No creation audit event for deal {deal_id}"
            
            print(f"   ✅ Deal {deal_id} creation event in audit log")
        finally:
            db.close()
    
    def test_09_no_500_errors(self):
        """TEST: No HTTP 500 errors in test flow"""
        print("\n[TEST 9] No HTTP 500 errors")
        
        # Run all tests and capture responses
        lead_id = self.test_01_create_lead_via_canonical_path()
        self.test_02_verify_lead_persists(lead_id)
        deal_id = self.test_03_convert_lead_to_deal(lead_id)
        self.test_04_verify_no_duplicate_deal(lead_id, deal_id)
        self.test_05_deal_visible_in_list(deal_id)
        self.test_06_deal_detail_accessible(deal_id)
        self.test_07_audit_lead_creation(lead_id)
        self.test_08_audit_deal_creation(deal_id)
        
        print(f"   ✅ All tests passed - no HTTP 500 errors")
    
    def run_all(self):
        """Run complete test suite."""
        print("\n" + "="*80)
        print("LEAD INTAKE TO OPERATOR FLOW TEST SUITE")
        print("="*80)
        
        try:
            lead_id = self.test_01_create_lead_via_canonical_path()
            self.test_02_verify_lead_persists(lead_id)
            deal_id = self.test_03_convert_lead_to_deal(lead_id)
            self.test_04_verify_no_duplicate_deal(lead_id, deal_id)
            self.test_05_deal_visible_in_list(deal_id)
            self.test_06_deal_detail_accessible(deal_id)
            self.test_07_audit_lead_creation(lead_id)
            self.test_08_audit_deal_creation(deal_id)
            self.test_09_no_500_errors()
            
            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED")
            print("="*80)
            return True
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            print("="*80)
            return False


if __name__ == "__main__":
    suite = TestLeadIntakePipeline()
    success = suite.run_all()
    sys.exit(0 if success else 1)
