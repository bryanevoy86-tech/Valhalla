"""
PACK AW: Crosslink / Relationship Graph Tests
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


def test_create_entity_link():
    payload = {
        "from_type": "user",
        "from_id": "bryan",
        "to_type": "deal",
        "to_id": "deal_123",
        "relation": "owns",
    }
    res = client.post("/links/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["from_type"] == "user"
    assert body["relation"] == "owns"


def test_list_links_from_entity():
    # Create multiple outgoing links
    for i in range(3):
        client.post(
            "/links/",
            json={
                "from_type": "user",
                "from_id": "lanna",
                "to_type": "deal",
                "to_id": f"deal_{i}",
                "relation": "owns",
            },
        )

    res = client.get("/links/from", params={"from_type": "user", "from_id": "lanna"})
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3
    assert all(l["from_id"] == "lanna" for l in body)


def test_list_links_to_entity():
    # Create multiple incoming links
    for i in range(3):
        client.post(
            "/links/",
            json={
                "from_type": "user",
                "from_id": f"user_{i}",
                "to_type": "property",
                "to_id": "prop_x",
                "relation": "owns",
            },
        )

    res = client.get("/links/to", params={"to_type": "property", "to_id": "prop_x"})
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3
    assert all(l["to_id"] == "prop_x" for l in body)


def test_different_relation_types():
    relations = ["owns", "works_on", "parent_of", "member_of", "powered_by"]
    for rel in relations:
        res = client.post(
            "/links/",
            json={
                "from_type": "entity",
                "from_id": "test",
                "to_type": "entity",
                "to_id": f"target_{rel}",
                "relation": rel,
            },
        )
        assert res.status_code == 200
        assert res.json()["relation"] == rel


def test_complex_relationship_graph():
    # Create a small graph: user owns deal, deal has property, property has tenants
    client.post(
        "/links/",
        json={
            "from_type": "user",
            "from_id": "bryan",
            "to_type": "deal",
            "to_id": "deal_x",
            "relation": "owns",
        },
    )
    client.post(
        "/links/",
        json={
            "from_type": "deal",
            "from_id": "deal_x",
            "to_type": "property",
            "to_id": "prop_1",
            "relation": "has",
        },
    )
    client.post(
        "/links/",
        json={
            "from_type": "property",
            "from_id": "prop_1",
            "to_type": "tenant",
            "to_id": "tenant_a",
            "relation": "hosted_by",
        },
    )

    # Check outgoing from user
    res1 = client.get("/links/from", params={"from_type": "user", "from_id": "bryan"})
    assert len(res1.json()) >= 1

    # Check outgoing from deal
    res2 = client.get("/links/from", params={"from_type": "deal", "from_id": "deal_x"})
    assert len(res2.json()) >= 1

    # Check incoming to property
    res3 = client.get("/links/to", params={"to_type": "property", "to_id": "prop_1"})
    assert len(res3.json()) >= 1
