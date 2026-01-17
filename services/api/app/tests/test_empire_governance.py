"""
Tests for PACK SO: Long-Term Empire Governance Map
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db, Base

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


class TestEmpireGovernance:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_create_role(self):
        payload = {
            "role_id": "role_001",
            "name": "King",
            "domain": {"finance": True, "operations": True, "family": True},
            "permissions": [{"action": "approve_deal", "allowed": True}],
            "responsibilities": ["Overall empire strategy", "Major decisions"],
            "authority_level": 10,
            "notes": "Supreme authority with override power"
        }
        response = client.post("/empire/roles", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "King"

    def test_list_roles(self):
        client.post("/empire/roles", json={
            "role_id": "role_002",
            "name": "Queen",
            "domain": {"family": True, "operations": True},
            "authority_level": 9
        })
        response = client.get("/empire/roles")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_role_by_name(self):
        client.post("/empire/roles", json={
            "role_id": "role_003",
            "name": "Odin",
            "domain": {"operations": True},
            "authority_level": 8
        })
        response = client.get("/empire/roles/Odin")
        assert response.status_code == 200
        assert response.json()["name"] == "Odin"

    def test_create_hierarchy(self):
        payload = {
            "hierarchy_id": "hierarchy_001",
            "superior_role_id": "King",
            "subordinate_role_id": "Queen",
            "override_rules": "Queen can override King in family matters",
            "escalation_path": "King",
            "context": "family"
        }
        response = client.post("/empire/hierarchy", json=payload)
        assert response.status_code == 200

    def test_get_hierarchy(self):
        client.post("/empire/hierarchy", json={
            "hierarchy_id": "hierarchy_002",
            "superior_role_id": "King",
            "subordinate_role_id": "Loki",
            "context": "creativity"
        })
        response = client.get("/empire/hierarchy")
        assert response.status_code == 200

    def test_create_succession_plan(self):
        payload = {
            "plan_id": "plan_001",
            "triggered_role": "King",
            "trigger_condition": "King unavailable for 30+ days",
            "description": "Contingency for King absence",
            "fallback_roles": ["Queen", "Odin"],
            "temporary_authority": {"Queen": 9, "Odin": 8},
            "documents_required": ["Authorization letter", "Authority matrix"],
            "review_frequency": "yearly"
        }
        response = client.post("/empire/succession", json=payload)
        assert response.status_code == 200

    def test_list_succession_plans(self):
        client.post("/empire/succession", json={
            "plan_id": "plan_002",
            "triggered_role": "Odin",
            "trigger_condition": "Operational override needed",
            "fallback_roles": ["Tyr", "Loki"]
        })
        response = client.get("/empire/succession")
        assert response.status_code == 200

    def test_create_governance_map(self):
        payload = {
            "map_id": "map_001",
            "version": 1,
            "roles_count": 5,
            "role_graph": {"King": ["Queen", "Odin"], "Queen": ["Loki", "Tyr"]},
            "conflict_rules": [{"roles": ["King", "Queen"], "resolution_path": "Queen for family"}],
            "escalation_rules": [{"trigger": "Blocked", "next_role": "King", "max_wait_time": 24}],
            "risk_thresholds": {"finance": 100000, "operations": 50000},
            "automation_rules": []
        }
        response = client.post("/empire/governance-map", json=payload)
        assert response.status_code == 200

    def test_get_governance_status(self):
        client.post("/empire/roles", json={
            "role_id": "role_004",
            "name": "TestRole",
            "authority_level": 5
        })
        response = client.get("/empire/status")
        assert response.status_code == 200
        assert "total_roles" in response.json()
