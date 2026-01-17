"""
PACK TY: Route Index & Debug Explorer Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_route_index_endpoint(client):
    """Test that /debug/routes/ returns route index"""
    res = client.get("/debug/routes/")
    assert res.status_code == 200
    body = res.json()
    assert "total" in body
    assert "routes" in body
    assert isinstance(body["routes"], list)


def test_route_index_contains_expected_fields(client):
    """Test that each route has required fields"""
    res = client.get("/debug/routes/")
    assert res.status_code == 200
    body = res.json()
    
    if body["routes"]:
        route = body["routes"][0]
        assert "path" in route
        assert "methods" in route
        assert "name" in route
        assert "tags" in route
        assert "summary" in route
        assert "deprecated" in route


def test_route_index_filters_options_head(client):
    """Test that OPTIONS and HEAD methods are filtered out"""
    res = client.get("/debug/routes/")
    assert res.status_code == 200
    body = res.json()
    
    for route in body["routes"]:
        methods = route["methods"]
        assert not (methods == ["OPTIONS"])
        assert not (methods == ["HEAD"])
