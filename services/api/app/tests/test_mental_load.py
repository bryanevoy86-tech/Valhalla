"""
Tests for PACK SN: Mental Load Offloading Engine
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db, Base

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


class TestMentalLoad:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_add_mental_load_entry(self):
        payload = {
            "entry_id": "entry_001",
            "category": "task",
            "description": "Finish quarterly review",
            "urgency_level": 4,
            "emotional_weight": 7,
            "action_required": True,
            "user_notes": "Due Friday"
        }
        response = client.post("/mental-load/entries", json=payload)
        assert response.status_code == 200
        assert response.json()["description"] == "Finish quarterly review"

    def test_get_pending_load(self):
        client.post("/mental-load/entries", json={
            "entry_id": "entry_002",
            "category": "worry",
            "description": "Upcoming meeting with board",
            "urgency_level": 5,
            "emotional_weight": 8,
            "action_required": False
        })
        response = client.get("/mental-load/pending")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_by_category(self):
        client.post("/mental-load/entries", json={
            "entry_id": "entry_003",
            "category": "household",
            "description": "Fix leaky faucet",
            "urgency_level": 2,
            "action_required": True
        })
        response = client.get("/mental-load/by-category/household")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_clear_entry(self):
        create_resp = client.post("/mental-load/entries", json={
            "entry_id": "entry_004",
            "category": "reminder",
            "description": "Call dentist",
            "urgency_level": 3,
            "action_required": True
        })
        entry_id = create_resp.json()["id"]

        response = client.put(f"/mental-load/entries/{entry_id}/clear")
        assert response.status_code == 200
        assert response.json()["cleared"] == True

    def test_create_daily_summary(self):
        payload = {
            "summary_id": "summary_001",
            "date": datetime.utcnow().isoformat(),
            "total_items": 12,
            "urgent_items": ["Board meeting", "Quarterly review"],
            "action_items": ["Reply to emails", "Call dentist"],
            "delegated_items": ["Marketing report to VA"],
            "cleared_items": ["Expense report"],
            "waiting_items": ["Legal review on contract"],
            "notes": "Productive day, cleared one major item"
        }
        response = client.post("/mental-load/daily-summary", json=payload)
        assert response.status_code == 200

    def test_start_brain_dump(self):
        payload = {
            "workflow_id": "workflow_001",
            "brain_dump": "Call dentist. Fix roof. Review contracts. Kids' school forms. Planning next quarter. What's the status on the London deal? Remember to get car serviced. Birthday gift for Sarah. Update will. Check insurance policies."
        }
        response = client.post("/mental-load/brain-dump", json=payload)
        assert response.status_code == 200

    def test_get_load_status(self):
        client.post("/mental-load/entries", json={
            "entry_id": "entry_005",
            "category": "task",
            "description": "Important project",
            "urgency_level": 5,
            "action_required": True
        })
        response = client.get("/mental-load/load-status")
        assert response.status_code == 200
        assert "cognitive_pressure" in response.json()
