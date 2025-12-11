"""
Tests for PACK SL: Personal Master Dashboard
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db, Base
from app.models.personal_dashboard import (
    FocusArea, PersonalRoutine, RoutineCompletion, FamilySnapshot,
    LifeDashboard, PersonalGoal, MoodLog
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


class TestFocusAreas:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_focus_area(self):
        payload = {
            "area_id": "health_001",
            "name": "Physical Health",
            "category": "health",
            "priority_level": 9,
            "notes": "Regular exercise and nutrition"
        }
        response = client.post("/life/focus-areas", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Physical Health"

    def test_list_focus_areas(self):
        client.post("/life/focus-areas", json={
            "area_id": "family_001",
            "name": "Family Time",
            "category": "family",
            "priority_level": 10,
            "notes": "Quality time with kids"
        })
        response = client.get("/life/focus-areas")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestRoutines:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_routine(self):
        payload = {
            "routine_id": "routine_001",
            "name": "Morning Exercise",
            "frequency": "daily",
            "focus_area_id": None,
            "description": "45 min workout",
            "notes": "6 AM start"
        }
        response = client.post("/life/routines", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Morning Exercise"

    def test_list_active_routines(self):
        client.post("/life/routines", json={
            "routine_id": "routine_002",
            "name": "Evening Meditation",
            "frequency": "daily",
            "description": "15 min meditation",
            "notes": "Before bed"
        })
        response = client.get("/life/routines")
        assert response.status_code == 200


class TestCompletion:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_log_completion(self):
        routine_resp = client.post("/life/routines", json={
            "routine_id": "routine_003",
            "name": "Reading",
            "frequency": "daily",
            "description": "30 min reading",
            "notes": "Educational books"
        })
        routine_id = routine_resp.json()["id"]

        payload = {
            "completion_id": "completion_001",
            "date": datetime.utcnow().isoformat(),
            "completed": 1,
            "notes": "Completed successfully"
        }
        response = client.post(f"/life/routines/{routine_id}/completion", json=payload)
        assert response.status_code == 200

    def test_get_completion_rate(self):
        routine_resp = client.post("/life/routines", json={
            "routine_id": "routine_004",
            "name": "Journaling",
            "frequency": "daily",
            "description": "10 min journaling",
            "notes": "Reflection time"
        })
        routine_id = routine_resp.json()["id"]

        # Log 7 days of completions
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            client.post(f"/life/routines/{routine_id}/completion", json={
                "completion_id": f"completion_{i:03d}",
                "date": date.isoformat(),
                "completed": 1 if i < 5 else 0,
                "notes": "Log entry"
            })

        response = client.get(f"/life/routines/{routine_id}/completion-rate?days=30")
        assert response.status_code == 200
        assert "completion_rate_percent" in response.json()


class TestFamilySnapshots:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_family_snapshot(self):
        payload = {
            "snapshot_id": "family_snap_001",
            "date": datetime.utcnow().isoformat(),
            "kids_notes": [
                {"name": "Sarah", "education": "5th grade", "mood": "happy", "interests": ["soccer", "art"]}
            ],
            "partner_notes": "Working late, stressed with project",
            "home_operations": "Roof repair completed",
            "highlights": ["Family movie night", "Soccer practice success"]
        }
        response = client.post("/life/family-snapshots", json=payload)
        assert response.status_code == 200


class TestDashboard:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_weekly_dashboard(self):
        payload = {
            "dashboard_id": "dashboard_001",
            "week_of": datetime.utcnow().isoformat(),
            "wins": ["Completed project", "Great family time"],
            "challenges": ["Tight deadline", "Less exercise"],
            "habits_tracked": [
                {"habit": "Morning exercise", "completion_rate": 0.71},
                {"habit": "Reading", "completion_rate": 0.86}
            ],
            "upcoming_priorities": ["Project deadline", "Family dinner"],
            "notes": "Solid week overall"
        }
        response = client.post("/life/dashboard/weekly", json=payload)
        assert response.status_code == 200


class TestGoals:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_goal(self):
        payload = {
            "goal_id": "goal_001",
            "name": "Run a 5K",
            "category": "health",
            "description": "Complete 5K race",
            "deadline": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "progress_percent": 20,
            "notes": "Training plan started"
        }
        response = client.post("/life/goals", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Run a 5K"

    def test_list_active_goals(self):
        client.post("/life/goals", json={
            "goal_id": "goal_002",
            "name": "Learn Spanish",
            "category": "education",
            "description": "Achieve B1 fluency",
            "deadline": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "progress_percent": 30,
            "notes": "Using Duolingo"
        })
        response = client.get("/life/goals")
        assert response.status_code == 200

    def test_update_goal_progress(self):
        goal_resp = client.post("/life/goals", json={
            "goal_id": "goal_003",
            "name": "Save Emergency Fund",
            "category": "finance",
            "description": "6 months expenses",
            "deadline": (datetime.utcnow() + timedelta(days=180)).isoformat(),
            "progress_percent": 50,
            "notes": "Halfway there"
        })
        goal_id = goal_resp.json()["id"]

        response = client.put(f"/life/goals/{goal_id}/progress", json={"progress_percent": 75})
        assert response.status_code == 200
        assert response.json()["progress_percent"] == 75


class TestMoodLogs:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_log_mood(self):
        payload = {
            "log_id": "mood_001",
            "date": datetime.utcnow().isoformat(),
            "mood": "good",
            "energy_level": 8,
            "notes": "Great day, lots of accomplishments"
        }
        response = client.post("/life/mood", json=payload)
        assert response.status_code == 200

    def test_get_recent_mood(self):
        client.post("/life/mood", json={
            "log_id": "mood_002",
            "date": datetime.utcnow().isoformat(),
            "mood": "excellent",
            "energy_level": 9,
            "notes": "Feeling energized"
        })
        response = client.get("/life/mood/recent?days=30")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestMetrics:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_get_life_metrics(self):
        # Create some data
        client.post("/life/focus-areas", json={
            "area_id": "area_001",
            "name": "Test Area",
            "category": "health",
            "priority_level": 5
        })
        
        client.post("/life/routines", json={
            "routine_id": "routine_test",
            "name": "Test Routine",
            "frequency": "daily"
        })

        response = client.get("/life/metrics")
        assert response.status_code == 200
        assert "total_focus_areas" in response.json()
        assert "active_routines" in response.json()
