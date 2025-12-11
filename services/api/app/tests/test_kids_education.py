"""
Tests for PACK SM: Kids Education & Development Engine
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


class TestKidsEducation:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_child_profile(self):
        payload = {
            "child_id": "child_001",
            "name": "Sarah",
            "age": 8,
            "interests": ["soccer", "art", "reading"],
            "skill_levels": {"reading": "advanced", "math": "grade-level"},
            "notes": "Curious and creative"
        }
        response = client.post("/kids/profiles", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Sarah"

    def test_list_children(self):
        client.post("/kids/profiles", json={
            "child_id": "child_002",
            "name": "Emma",
            "age": 6,
            "interests": ["dancing", "singing"],
            "notes": "Energetic"
        })
        response = client.get("/kids/profiles")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_create_learning_plan(self):
        profile_resp = client.post("/kids/profiles", json={
            "child_id": "child_003",
            "name": "Tom",
            "age": 10,
            "interests": ["science", "programming"]
        })
        child_id = profile_resp.json()["id"]

        payload = {
            "plan_id": "plan_001",
            "child_id": child_id,
            "timeframe": "weekly",
            "goals": [{"goal": "Learn multiplication", "notes": "Math focus"}],
            "activities": [{"activity": "Math games", "category": "math", "duration_minutes": 30}],
            "parent_notes": "Focus on fun learning"
        }
        response = client.post("/kids/learning-plans", json=payload)
        assert response.status_code == 200

    def test_log_education_activity(self):
        profile_resp = client.post("/kids/profiles", json={
            "child_id": "child_004",
            "name": "Alex",
            "age": 7
        })
        child_id = profile_resp.json()["id"]

        payload = {
            "log_id": "log_001",
            "child_id": child_id,
            "date": datetime.utcnow().isoformat(),
            "completed_activities": ["Reading for 30 mins", "Math worksheet"],
            "highlights": ["Got all problems right", "Read with great expression"],
            "parent_notes": "Great progress!"
        }
        response = client.post("/kids/education-logs", json=payload)
        assert response.status_code == 200

    def test_create_summary(self):
        profile_resp = client.post("/kids/profiles", json={
            "child_id": "child_005",
            "name": "Jamie",
            "age": 9
        })
        child_id = profile_resp.json()["id"]

        payload = {
            "summary_id": "summary_001",
            "child_id": child_id,
            "week_of": datetime.utcnow().isoformat(),
            "completed_goals": ["Finished book", "Math mastery"],
            "fun_moments": ["Science experiment success", "Creative writing story"],
            "growth_notes": "Showing strong progress in reading comprehension",
            "next_week_focus": ["Handwriting practice", "Spelling"]
        }
        response = client.post("/kids/summaries", json=payload)
        assert response.status_code == 200
