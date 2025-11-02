"""
FastAPI smoke tests to verify core endpoints are working.
Can be run against local or remote API by setting API_BASE env var.
"""

import os
import httpx

API = os.getenv("API_BASE", "http://localhost:4000")
KEY = os.getenv("BUILDER_KEY", "test123")


def test_healthz():
    """Test health check endpoint"""
    r = httpx.get(f"{API}/healthz", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_builder_list_tasks():
    """Test builder tasks endpoint with authentication"""
    r = httpx.get(f"{API}/builder/tasks", headers={"X-API-Key": KEY}, timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_research_playbooks_list_public():
    """Test public playbooks endpoint (no auth required)"""
    r = httpx.get(f"{API}/playbooks", timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
