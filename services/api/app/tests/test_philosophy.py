"""
PACK TM: Core Philosophy Archive Tests
"""

import pytest
from fastapi.testclient import TestClient


def test_create_philosophy_record(client: TestClient):
    """Test creating a philosophy record."""
    response = client.post(
        "/philosophy/records",
        json={
            "title": "Why I Built Valhalla",
            "mission_statement": "Protect and grow the family empire.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Why I Built Valhalla"
    assert data["mission_statement"] == "Protect and grow the family empire."
    assert "id" in data
    assert "date" in data


def test_list_philosophy_records(client: TestClient):
    """Test listing philosophy records."""
    # Create a record first
    client.post(
        "/philosophy/records",
        json={"title": "Core Values", "values": "Family\nIntegrity\nGrowth"},
    )

    # List records
    response = client.get("/philosophy/records")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_empire_principle(client: TestClient):
    """Test creating an empire principle."""
    response = client.post(
        "/philosophy/principles",
        json={
            "category": "ethics",
            "description": "Kids first, always.",
            "enforcement_level": "strong",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "ethics"
    assert data["description"] == "Kids first, always."
    assert data["enforcement_level"] == "strong"
    assert "id" in data


def test_list_empire_principles(client: TestClient):
    """Test listing empire principles."""
    # Create a principle first
    client.post(
        "/philosophy/principles",
        json={
            "category": "growth",
            "description": "Always learn and improve.",
            "enforcement_level": "soft",
        },
    )

    # List principles
    response = client.get("/philosophy/principles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_philosophy_snapshot(client: TestClient):
    """Test getting philosophy snapshot."""
    # Create a record
    client.post(
        "/philosophy/records",
        json={
            "title": "Life Philosophy",
            "mission_statement": "Build lasting legacy",
        },
    )

    # Create principles
    client.post(
        "/philosophy/principles",
        json={
            "category": "ethics",
            "description": "Honesty is non-negotiable",
        },
    )

    # Get snapshot
    response = client.get("/philosophy/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "latest_record" in data
    assert "principles" in data
    assert data["latest_record"]["title"] == "Life Philosophy"
