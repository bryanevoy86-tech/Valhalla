"""
FastAPI smoke tests to verify core endpoints are working.
Can be run against local or remote API by setting API_BASE env var.
"""




def test_healthz(legacy_http_client):
    client, _ = legacy_http_client
    """Test health check endpoint"""
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_builder_list_tasks(legacy_http_client):
    client, _ = legacy_http_client
    """Test builder tasks endpoint with authentication"""
    r = client.get("/builder/tasks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_research_playbooks_list_public(legacy_http_client):
    client, _ = legacy_http_client
    """Test public playbooks endpoint (no auth required)"""
    r = client.get("/playbooks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
