"""
PACK W: System Status Tests
Test suite for system metadata and completion status endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.system_metadata import SystemMetadata
from app.services.system_status import (
    ensure_system_metadata,
    get_system_status,
    set_backend_complete,
    update_version,
    get_pack_by_id,
    count_packs_by_status,
)


class TestSystemStatusService:
    """Test system status service functions."""
    
    def test_ensure_system_metadata_creates_on_first_call(self, db: Session):
        """Ensure metadata is created if not present."""
        # Clear any existing metadata
        db.query(SystemMetadata).delete()
        db.commit()
        
        meta = ensure_system_metadata(db)
        assert meta is not None
        assert meta.id == 1
        assert meta.version == "1.0.0"
        assert meta.backend_complete is False
    
    def test_ensure_system_metadata_returns_existing(self, db: Session):
        """Ensure metadata returns existing row on subsequent calls."""
        meta1 = ensure_system_metadata(db)
        meta2 = ensure_system_metadata(db)
        assert meta1.id == meta2.id
    
    def test_get_system_status_includes_required_fields(self, db: Session):
        """System status includes all required fields."""
        status = get_system_status(db)
        assert "version" in status
        assert "backend_complete" in status
        assert "packs" in status
        assert "summary" in status
        assert "extra" in status
    
    def test_system_status_has_version(self, db: Session):
        """System status includes semantic version."""
        status = get_system_status(db)
        assert isinstance(status["version"], str)
        parts = status["version"].split(".")
        assert len(parts) == 3  # major.minor.patch
    
    def test_system_status_includes_all_packs(self, db: Session):
        """System status includes all 16 packs."""
        status = get_system_status(db)
        packs = status["packs"]
        assert len(packs) == 16
        
        # Check all pack IDs are present
        pack_ids = [p["id"] for p in packs]
        expected_ids = [
            "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
            "S", "T", "U", "V", "W"
        ]
        assert set(pack_ids) == set(expected_ids)
    
    def test_system_status_packs_have_required_fields(self, db: Session):
        """Each pack has required fields."""
        status = get_system_status(db)
        for pack in status["packs"]:
            assert "id" in pack
            assert "name" in pack
            assert "status" in pack
            assert pack["status"] == "installed"
    
    def test_set_backend_complete_true(self, db: Session):
        """Can mark backend as complete."""
        set_backend_complete(db, True, "Test completion")
        meta = ensure_system_metadata(db)
        assert meta.backend_complete is True
        assert meta.notes == "Test completion"
        assert meta.completed_at is not None
    
    def test_set_backend_complete_false(self, db: Session):
        """Can mark backend as incomplete."""
        # First mark as complete
        set_backend_complete(db, True, "Mark complete")
        
        # Then mark as incomplete
        set_backend_complete(db, False, "Mark incomplete")
        meta = ensure_system_metadata(db)
        assert meta.backend_complete is False
        assert meta.completed_at is None
    
    def test_update_version(self, db: Session):
        """Can update system version."""
        new_version = "1.1.0"
        update_version(db, new_version, "Version bump")
        status = get_system_status(db)
        assert status["version"] == new_version
    
    def test_get_pack_by_id_found(self):
        """Can retrieve pack by ID."""
        pack = get_pack_by_id("H")
        assert pack is not None
        assert pack.id == "H"
        assert pack.name == "Public Behavioral Signal Extractor"
    
    def test_get_pack_by_id_not_found(self):
        """Returns None for non-existent pack."""
        pack = get_pack_by_id("ZZ")
        assert pack is None
    
    def test_count_packs_by_status(self):
        """Can count packs by status."""
        installed = count_packs_by_status("installed")
        assert installed == 16


class TestSystemStatusEndpoints:
    """Test system status API endpoints."""
    
    def test_get_system_status_endpoint(self, client: TestClient):
        """GET /system/status/ returns full status."""
        res = client.get("/system/status/")
        assert res.status_code == 200
        body = res.json()
        
        assert "version" in body
        assert "backend_complete" in body
        assert "packs" in body
        assert "summary" in body
    
    def test_system_status_response_structure(self, client: TestClient):
        """Response has correct structure."""
        res = client.get("/system/status/")
        body = res.json()
        
        assert isinstance(body["version"], str)
        assert isinstance(body["backend_complete"], bool)
        assert isinstance(body["packs"], list)
        assert isinstance(body["summary"], str)
        assert isinstance(body["extra"], dict)
    
    def test_system_status_includes_16_packs(self, client: TestClient):
        """Status endpoint lists all 16 packs."""
        res = client.get("/system/status/")
        body = res.json()
        
        assert len(body["packs"]) == 16
        pack_ids = [p["id"] for p in body["packs"]]
        assert "H" in pack_ids
        assert "W" in pack_ids
    
    def test_get_system_summary_endpoint(self, client: TestClient):
        """GET /system/status/summary returns lightweight summary."""
        res = client.get("/system/status/summary")
        assert res.status_code == 200
        body = res.json()
        
        assert "total_packs" in body
        assert "installed_packs" in body
        assert "summary" in body
    
    def test_mark_backend_complete_endpoint(self, client: TestClient):
        """POST /system/status/complete marks backend complete."""
        res = client.post(
            "/system/status/complete",
            json={"notes": "Test completion"}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["backend_complete"] is True
    
    def test_mark_backend_incomplete_endpoint(self, client: TestClient):
        """POST /system/status/incomplete marks backend incomplete."""
        # First mark complete
        client.post("/system/status/complete")
        
        # Then mark incomplete
        res = client.post(
            "/system/status/incomplete",
            json={"notes": "Test incomplete"}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["backend_complete"] is False
    
    def test_list_packs_endpoint(self, client: TestClient):
        """GET /system/status/packs lists all packs."""
        res = client.get("/system/status/packs")
        assert res.status_code == 200
        body = res.json()
        
        assert "packs" in body
        assert "total" in body
        assert "installed" in body
        assert len(body["packs"]) == 16
        assert body["total"] == 16
        assert body["installed"] == 16
    
    def test_get_pack_info_endpoint(self, client: TestClient):
        """GET /system/status/packs/{pack_id} returns pack info."""
        res = client.get("/system/status/packs/H")
        assert res.status_code == 200
        body = res.json()
        
        assert body["id"] == "H"
        assert body["name"] == "Public Behavioral Signal Extractor"
        assert body["status"] == "installed"
    
    def test_get_pack_info_not_found(self, client: TestClient):
        """GET /system/status/packs/{pack_id} returns 404 for invalid pack."""
        res = client.get("/system/status/packs/ZZ")
        assert res.status_code == 404
    
    def test_get_pack_info_case_insensitive(self, client: TestClient):
        """Pack ID lookup is case-insensitive."""
        res = client.get("/system/status/packs/h")
        assert res.status_code == 200
        body = res.json()
        assert body["id"] == "H"
    
    def test_system_status_includes_summary(self, client: TestClient):
        """Status includes human-readable summary."""
        res = client.get("/system/status/")
        body = res.json()
        
        assert body["summary"]
        assert "professional" in body["summary"].lower()
        assert "valhalla" in body["summary"].lower()


class TestSystemStatusIntegration:
    """Integration tests for system status functionality."""
    
    def test_complete_status_workflow(self, client: TestClient, db: Session):
        """Test full workflow: check status, mark complete, verify."""
        # 1. Check initial status
        res = client.get("/system/status/")
        assert res.json()["backend_complete"] is False
        
        # 2. Mark as complete
        res = client.post(
            "/system/status/complete",
            json={"notes": "All tests passing"}
        )
        assert res.json()["backend_complete"] is True
        
        # 3. Verify status persisted
        res = client.get("/system/status/")
        assert res.json()["backend_complete"] is True
        
        # 4. Check extra metadata
        extra = res.json()["extra"]
        assert extra["notes"] == "All tests passing"
        assert extra["completed_at"] is not None
    
    def test_version_persistence(self, client: TestClient):
        """Version updates persist across requests."""
        # Update version
        res = client.post(
            "/system/status/complete",
            json={"version": "1.1.0", "notes": "Version bump"}
        )
        assert res.json()["version"] == "1.1.0"
        
        # Verify persistence
        res = client.get("/system/status/")
        assert res.json()["version"] == "1.1.0"
    
    def test_summary_endpoint_doesnt_require_db(self, client: TestClient):
        """Summary endpoint provides quick status without DB queries."""
        res = client.get("/system/status/summary")
        body = res.json()
        
        # Should have consistent data without DB dependency
        assert body["total_packs"] == 16
        assert body["installed_packs"] == 16
        assert len(body["summary"]) > 0
    
    def test_pack_registry_completeness(self, client: TestClient):
        """All expected packs are registered."""
        res = client.get("/system/status/packs")
        pack_ids = [p["id"] for p in res.json()["packs"]]
        
        # Professional packs
        for pack_id in "HIJKLMNOPQR":
            assert pack_id in pack_ids
        
        # System packs
        for pack_id in "STUVW":
            assert pack_id in pack_ids
