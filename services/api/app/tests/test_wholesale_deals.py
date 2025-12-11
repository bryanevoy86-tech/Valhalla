"""
Tests for PACK SJ: Wholesale Deal Machine
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db, Base
from app.models.wholesale_deals import (
    WholesaleLead, WholesaleOffer, BuyerProfile, AssignmentRecord, WholesalePipelineSnapshot
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


class TestWholesaleLeads:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_lead(self):
        payload = {
            "lead_id": "lead_001",
            "source": "cold_call",
            "seller_name": "John Smith",
            "seller_contact": "555-0001",
            "property_address": "123 Main St",
            "motivation_level": "high",
            "situation_notes": "Distressed property",
            "stage": "new"
        }
        response = client.post("/wholesale/leads", json=payload)
        assert response.status_code == 200
        assert response.json()["lead_id"] == "lead_001"

    def test_list_leads(self):
        client.post("/wholesale/leads", json={
            "lead_id": "lead_001",
            "source": "cold_call",
            "seller_name": "John Smith",
            "seller_contact": "555-0001",
            "property_address": "123 Main St",
            "motivation_level": "high",
            "situation_notes": "Distressed",
            "stage": "new"
        })
        response = client.get("/wholesale/leads")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_lead(self):
        create_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_002",
            "source": "referral",
            "seller_name": "Jane Doe",
            "seller_contact": "555-0002",
            "property_address": "456 Oak Ave",
            "motivation_level": "medium",
            "situation_notes": "Need to sell quickly",
            "stage": "new"
        })
        lead_id = create_resp.json()["id"]
        response = client.get(f"/wholesale/leads/{lead_id}")
        assert response.status_code == 200

    def test_update_lead_stage(self):
        create_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_003",
            "source": "cold_call",
            "seller_name": "Bob Johnson",
            "seller_contact": "555-0003",
            "property_address": "789 Pine Rd",
            "motivation_level": "high",
            "situation_notes": "Motivated seller",
            "stage": "new"
        })
        lead_id = create_resp.json()["id"]
        response = client.put(f"/wholesale/leads/{lead_id}/stage", json={"stage": "contacted"})
        assert response.status_code == 200
        assert response.json()["stage"] == "contacted"


class TestOffers:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_offer(self):
        lead_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_004",
            "source": "cold_call",
            "seller_name": "Alice",
            "seller_contact": "555-0004",
            "property_address": "321 Elm St",
            "motivation_level": "high",
            "situation_notes": "Estate sale",
            "stage": "new"
        })
        lead_id = lead_resp.json()["id"]

        payload = {
            "lead_id": lead_id,
            "offer_price": 250000 * 100,
            "arv": 350000 * 100,
            "repair_estimate": 30000 * 100,
            "status": "draft"
        }
        response = client.post("/wholesale/offers", json=payload)
        assert response.status_code == 200
        assert response.json()["offer_price"] == 250000 * 100

    def test_list_offers_by_lead(self):
        lead_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_005",
            "source": "referral",
            "seller_name": "Charlie",
            "seller_contact": "555-0005",
            "property_address": "555 Cedar Ln",
            "motivation_level": "medium",
            "situation_notes": "Potential deal",
            "stage": "new"
        })
        lead_id = lead_resp.json()["id"]

        client.post("/wholesale/offers", json={
            "lead_id": lead_id,
            "offer_price": 200000 * 100,
            "arv": 300000 * 100,
            "repair_estimate": 25000 * 100,
            "status": "draft"
        })

        response = client.get(f"/wholesale/offers/lead/{lead_id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_update_offer_status(self):
        lead_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_006",
            "source": "cold_call",
            "seller_name": "Diana",
            "seller_contact": "555-0006",
            "property_address": "777 Birch Way",
            "motivation_level": "high",
            "situation_notes": "Quick sale needed",
            "stage": "new"
        })
        lead_id = lead_resp.json()["id"]

        offer_resp = client.post("/wholesale/offers", json={
            "lead_id": lead_id,
            "offer_price": 275000 * 100,
            "arv": 400000 * 100,
            "repair_estimate": 40000 * 100,
            "status": "draft"
        })
        offer_id = offer_resp.json()["id"]

        response = client.put(f"/wholesale/offers/{offer_id}/status", json={"status": "sent"})
        assert response.status_code == 200


class TestBuyers:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_buyer_profile(self):
        payload = {
            "name": "Investor LLC",
            "contact": "investor@email.com",
            "criteria": {"min_roi": 30, "max_repair": 50000, "focus_areas": ["multi-unit"]},
            "status": "active"
        }
        response = client.post("/wholesale/buyers", json=payload)
        assert response.status_code == 200

    def test_list_buyers(self):
        client.post("/wholesale/buyers", json={
            "name": "Buyer A",
            "contact": "buyera@email.com",
            "criteria": {},
            "status": "active"
        })
        response = client.get("/wholesale/buyers")
        assert response.status_code == 200


class TestAssignments:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_assignment(self):
        lead_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_007",
            "source": "cold_call",
            "seller_name": "Edward",
            "seller_contact": "555-0007",
            "property_address": "999 Maple Dr",
            "motivation_level": "high",
            "situation_notes": "Ready to sell",
            "stage": "new"
        })
        lead_id = lead_resp.json()["id"]

        buyer_resp = client.post("/wholesale/buyers", json={
            "name": "Buyer B",
            "contact": "buyerb@email.com",
            "criteria": {},
            "status": "active"
        })
        buyer_id = buyer_resp.json()["id"]

        payload = {
            "lead_id": lead_id,
            "buyer_id": buyer_id,
            "buyer_name": "Buyer B",
            "buyer_contact": "buyerb@email.com",
            "assignment_fee": 10000 * 100,
            "status": "draft"
        }
        response = client.post("/wholesale/assignments", json=payload)
        assert response.status_code == 200

    def test_get_assignments_by_lead(self):
        lead_resp = client.post("/wholesale/leads", json={
            "lead_id": "lead_008",
            "source": "referral",
            "seller_name": "Frank",
            "seller_contact": "555-0008",
            "property_address": "101 Willow St",
            "motivation_level": "medium",
            "situation_notes": "Interested",
            "stage": "new"
        })
        lead_id = lead_resp.json()["id"]

        buyer_resp = client.post("/wholesale/buyers", json={
            "name": "Buyer C",
            "contact": "buyerc@email.com",
            "criteria": {},
            "status": "active"
        })
        buyer_id = buyer_resp.json()["id"]

        client.post("/wholesale/assignments", json={
            "lead_id": lead_id,
            "buyer_id": buyer_id,
            "buyer_name": "Buyer C",
            "buyer_contact": "buyerc@email.com",
            "assignment_fee": 15000 * 100,
            "status": "draft"
        })

        response = client.get(f"/wholesale/assignments/lead/{lead_id}")
        assert response.status_code == 200


class TestPipeline:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_get_pipeline_summary(self):
        client.post("/wholesale/leads", json={
            "lead_id": "lead_009",
            "source": "cold_call",
            "seller_name": "Grace",
            "seller_contact": "555-0009",
            "property_address": "202 Spruce Ave",
            "motivation_level": "high",
            "situation_notes": "Hot lead",
            "stage": "new"
        })

        response = client.get("/wholesale/pipeline")
        assert response.status_code == 200
        assert "by_stage" in response.json()

    def test_create_pipeline_snapshot(self):
        payload = {
            "date": datetime.utcnow().isoformat(),
            "total_leads": 5,
            "by_stage": {"new": 2, "contacted": 2, "inspection": 1},
            "hot_leads": 1,
            "active_offers": 1,
            "ready_for_assignment": 0
        }
        response = client.post("/wholesale/pipeline/snapshot", json=payload)
        assert response.status_code == 200
