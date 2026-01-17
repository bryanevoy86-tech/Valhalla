"""
PACK AO: Explainability Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_explanation_creation():
    payload = {
        "context_type": "scorecard",
        "context_id": "lawyer_123",
        "payload": {"metric_count": 5, "keys": "timeliness, responsiveness"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["context_type"] == "scorecard"
    assert body["context_id"] == "lawyer_123"
    assert "Scorecard" in body["explanation"]


def test_explanation_template_rendering():
    """Verify template placeholders are replaced."""
    payload = {
        "context_type": "scorecard",
        "context_id": "lawyer_456",
        "payload": {"metric_count": 8, "keys": "accuracy, speed"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    
    # Check template was rendered
    assert "8" in body["explanation"]  # metric_count should be in text
    assert "accuracy, speed" in body["explanation"]  # keys should be in text


def test_explanation_audit_event():
    payload = {
        "context_type": "audit_event",
        "context_id": "audit_789",
        "payload": {"reason": "unauthorized access attempt detected"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "Audit event" in body["explanation"]
    assert "unauthorized access attempt detected" in body["explanation"]


def test_explanation_decision():
    payload = {
        "context_type": "decision",
        "context_id": "decision_100",
        "payload": {"criteria": "risk score > 80 and duration > 6 months"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "Decision" in body["explanation"]
    assert "risk score > 80" in body["explanation"]


def test_explanation_fallback_template():
    """Unknown context types should use fallback template."""
    payload = {
        "context_type": "unknown_type",
        "context_id": "unknown_123",
        "payload": {"some_field": "some_value"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    # Should use fallback: "Explanation for {{context_type}} generated."
    assert "Explanation for unknown_type generated." == body["explanation"]


def test_explanation_metadata_preserved():
    payload = {
        "context_type": "scorecard",
        "context_id": "lawyer_meta",
        "payload": {
            "metric_count": 3,
            "keys": "quality, cost",
            "extra_field": "extra_value",
        },
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    
    # Metadata should contain original payload
    assert body["metadata"]["metric_count"] == 3
    assert body["metadata"]["keys"] == "quality, cost"
    assert body["metadata"]["extra_field"] == "extra_value"


def test_explanation_without_context_id():
    payload = {
        "context_type": "audit_event",
        "payload": {"reason": "system check"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["context_id"] is None


def test_explanation_timestamp():
    payload = {
        "context_type": "decision",
        "context_id": "decision_time",
        "payload": {"criteria": "test"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    
    assert "created_at" in body
    assert isinstance(body["created_at"], str)
    assert "T" in body["created_at"]  # ISO format


def test_explanation_multiple_placeholders():
    """Test rendering with multiple placeholders."""
    payload = {
        "context_type": "decision",
        "context_id": "decision_multi",
        "payload": {
            "criteria": "complex rule",
            "threshold": "95",
            "action": "escalate",
        },
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    
    # Template for decision: "Decision {{context_id}} was made based on {{criteria}}."
    # Metadata should preserve all fields
    assert body["metadata"]["threshold"] == "95"
    assert body["metadata"]["action"] == "escalate"


def test_explanation_special_characters():
    """Test rendering with special characters in payload."""
    payload = {
        "context_type": "audit_event",
        "context_id": "audit_special",
        "payload": {"reason": "user@example.com attempted access with [restricted] tags"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    
    assert "user@example.com" in body["explanation"]
    assert "[restricted]" in body["explanation"]


def test_explanation_numeric_payload():
    """Test rendering with numeric values."""
    payload = {
        "context_type": "scorecard",
        "context_id": "numeric_test",
        "payload": {"metric_count": 42, "keys": "precision"},
    }
    res = client.post("/explain/", json=payload)
    assert res.status_code == 200
    body = res.json()
    
    # Number should be converted to string in explanation
    assert "42" in body["explanation"]
