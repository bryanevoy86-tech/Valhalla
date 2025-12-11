"""
PACK AN: Integrity Monitor Tests
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


def test_integrity_report():
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    assert "total_issues" in body
    assert "issues" in body
    assert isinstance(body["total_issues"], int)
    assert isinstance(body["issues"], list)


def test_integrity_report_structure():
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    
    # Each issue should have required fields
    for issue in body["issues"]:
        assert "category" in issue
        assert "entity_type" in issue
        assert "entity_id" in issue
        assert "message" in issue


def test_integrity_report_count_matches():
    """Total issue count should match length of issues list."""
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    assert body["total_issues"] == len(body["issues"])


def test_integrity_report_empty_db():
    """Empty database should have zero issues (no records to check)."""
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    assert body["total_issues"] == 0
    assert len(body["issues"]) == 0


def test_integrity_report_issue_categories():
    """Issues should have recognized categories."""
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    
    allowed_categories = {
        "pipeline_mismatch",
        "retainer_invalid",
        "missing_document",
    }
    
    for issue in body["issues"]:
        assert issue["category"] in allowed_categories


def test_integrity_report_idempotent():
    """Multiple calls should return same report."""
    res1 = client.get("/integrity/report")
    res2 = client.get("/integrity/report")
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json() == res2.json()


def test_integrity_issue_format():
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    
    if body["issues"]:
        issue = body["issues"][0]
        assert isinstance(issue["category"], str)
        assert isinstance(issue["entity_type"], str)
        assert isinstance(issue["message"], str)
        # entity_id can be str, int, or None
        assert issue["entity_id"] is None or isinstance(issue["entity_id"], (str, int))


def test_integrity_report_no_false_positives():
    """Empty database should not generate false positives."""
    res = client.get("/integrity/report")
    assert res.status_code == 200
    body = res.json()
    # With no data, there should be nothing to report
    assert body["total_issues"] == 0
