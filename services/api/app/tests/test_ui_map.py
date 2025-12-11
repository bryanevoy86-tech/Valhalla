# services/api/app/tests/test_ui_map.py

"""
Tests for PACK U: Frontend Preparation / API → WeWeb Mapping
Verifies UI map endpoint and structure for frontend consumption.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_ui_map_endpoint_exists(client: TestClient):
    """Test that /ui-map/ endpoint exists and returns 200."""
    res = client.get("/ui-map/")
    assert res.status_code == 200


def test_ui_map_structure(client: TestClient):
    """Test that UI map has the expected top-level structure."""
    res = client.get("/ui-map/")
    assert res.status_code == 200
    
    body = res.json()
    assert "modules" in body
    assert isinstance(body["modules"], list)
    assert len(body["modules"]) > 0


def test_ui_map_module_structure(client: TestClient):
    """Test that each module has the expected structure."""
    res = client.get("/ui-map/")
    body = res.json()
    
    for module in body["modules"]:
        assert "id" in module
        assert "label" in module
        assert "sections" in module
        assert isinstance(module["sections"], list)
        assert len(module["sections"]) > 0


def test_ui_map_section_structure(client: TestClient):
    """Test that each section has the expected structure."""
    res = client.get("/ui-map/")
    body = res.json()
    
    for module in body["modules"]:
        for section in module["sections"]:
            assert "id" in section
            assert "label" in section
            assert "endpoints" in section
            assert isinstance(section["endpoints"], list)


def test_ui_map_endpoint_structure(client: TestClient):
    """Test that each endpoint has the expected structure."""
    res = client.get("/ui-map/")
    body = res.json()
    
    for module in body["modules"]:
        for section in module["sections"]:
            for endpoint in section["endpoints"]:
                assert "method" in endpoint
                assert "path" in endpoint
                assert "summary" in endpoint
                assert endpoint["method"] in ["GET", "POST", "PATCH", "PUT", "DELETE"]
                assert endpoint["path"].startswith("/")


def test_ui_map_has_key_modules(client: TestClient):
    """Test that UI map includes key modules."""
    res = client.get("/ui-map/")
    body = res.json()
    
    module_ids = [m["id"] for m in body["modules"]]
    
    # Check for essential modules
    assert "professionals" in module_ids
    assert "contracts" in module_ids
    assert "deals" in module_ids
    assert "audit_governance" in module_ids
    assert "debug_system" in module_ids


def test_ui_map_metadata(client: TestClient):
    """Test that UI map includes metadata."""
    res = client.get("/ui-map/")
    body = res.json()
    
    assert "metadata" in body
    metadata = body["metadata"]
    assert "version" in metadata
    assert "description" in metadata


def test_ui_map_professionals_module(client: TestClient):
    """Test professionals module structure and content."""
    res = client.get("/ui-map/")
    body = res.json()
    
    modules = {m["id"]: m for m in body["modules"]}
    pros_module = modules.get("professionals")
    
    assert pros_module is not None
    section_ids = [s["id"] for s in pros_module["sections"]]
    
    assert "scorecard" in section_ids
    assert "retainers" in section_ids
    assert "tasks" in section_ids
    assert "handoff" in section_ids


def test_ui_map_contracts_module(client: TestClient):
    """Test contracts module structure and content."""
    res = client.get("/ui-map/")
    body = res.json()
    
    modules = {m["id"]: m for m in body["modules"]}
    contracts_module = modules.get("contracts")
    
    assert contracts_module is not None
    section_ids = [s["id"] for s in contracts_module["sections"]]
    
    assert "lifecycle" in section_ids
    assert "documents" in section_ids


def test_ui_map_audit_governance_module(client: TestClient):
    """Test audit & governance module structure and content."""
    res = client.get("/ui-map/")
    body = res.json()
    
    modules = {m["id"]: m for m in body["modules"]}
    audit_module = modules.get("audit_governance")
    
    assert audit_module is not None
    section_ids = [s["id"] for s in audit_module["sections"]]
    
    assert "audit" in section_ids
    assert "governance" in section_ids


def test_ui_map_endpoint_paths_valid(client: TestClient):
    """Test that all endpoint paths are valid API paths."""
    res = client.get("/ui-map/")
    body = res.json()
    
    for module in body["modules"]:
        for section in module["sections"]:
            for endpoint in section["endpoints"]:
                path = endpoint["path"]
                # Path should start with / and be a reasonable length
                assert path.startswith("/")
                assert len(path) < 200
                # Should not have double slashes (except in URLs)
                assert "//" not in path


def test_ui_map_tags_present(client: TestClient):
    """Test that endpoints include tags for categorization."""
    res = client.get("/ui-map/")
    body = res.json()
    
    for module in body["modules"]:
        for section in module["sections"]:
            for endpoint in section["endpoints"]:
                if "tags" in endpoint:
                    assert isinstance(endpoint["tags"], list)
                    assert len(endpoint["tags"]) > 0
