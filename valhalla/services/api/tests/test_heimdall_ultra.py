"""
PACK TC: Heimdall Ultra Mode Tests
Comprehensive test suite for Ultra Mode configuration.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.heimdall_ultra import HeimdallUltraConfig
from app.services.heimdall_ultra import (
    get_ultra_config,
    update_ultra_config,
    toggle_ultra_mode,
    set_initiative_level,
    set_escalation_chain,
    set_priority_matrix,
)
from app.schemas.heimdall_ultra import UltraConfigUpdate


class TestHeimdallUltraService:
    """Test Heimdall Ultra Mode service layer."""

    def test_get_ultra_config_creates_singleton(self, db: Session):
        """Test that get_ultra_config creates a singleton config if none exists."""
        cfg = get_ultra_config(db)
        assert cfg is not None
        assert cfg.id == 1
        assert cfg.initiative_level == "maximum"
        assert cfg.enabled is False

    def test_get_ultra_config_returns_existing(self, db: Session):
        """Test that get_ultra_config returns existing config."""
        cfg1 = get_ultra_config(db)
        cfg1_id = cfg1.id
        
        cfg2 = get_ultra_config(db)
        assert cfg2.id == cfg1_id

    def test_toggle_ultra_mode_enable(self, db: Session):
        """Test enabling Ultra Mode."""
        cfg = toggle_ultra_mode(db, True)
        assert cfg.enabled is True

    def test_toggle_ultra_mode_disable(self, db: Session):
        """Test disabling Ultra Mode."""
        toggle_ultra_mode(db, True)
        cfg = toggle_ultra_mode(db, False)
        assert cfg.enabled is False

    def test_set_initiative_level_maximum(self, db: Session):
        """Test setting initiative level to maximum."""
        cfg = set_initiative_level(db, "maximum")
        assert cfg.initiative_level == "maximum"

    def test_set_initiative_level_normal(self, db: Session):
        """Test setting initiative level to normal."""
        cfg = set_initiative_level(db, "normal")
        assert cfg.initiative_level == "normal"

    def test_set_initiative_level_minimal(self, db: Session):
        """Test setting initiative level to minimal."""
        cfg = set_initiative_level(db, "minimal")
        assert cfg.initiative_level == "minimal"

    def test_set_initiative_level_invalid(self, db: Session):
        """Test that invalid initiative level raises error."""
        with pytest.raises(ValueError):
            set_initiative_level(db, "invalid_level")

    def test_set_escalation_chain(self, db: Session):
        """Test updating escalation chain."""
        new_chain = {
            "operations": "ODIN",
            "risk": "TYR",
            "creativity": "LOKI",
            "family": "QUEEN",
            "urgent": "KING",
        }
        cfg = set_escalation_chain(db, new_chain)
        assert cfg.escalation_chain == new_chain
        assert cfg.escalation_chain["urgent"] == "KING"

    def test_set_priority_matrix(self, db: Session):
        """Test updating priority matrix."""
        new_priorities = [
            "family_stability",
            "mental_health",
            "financial_safety",
            "empire_growth",
        ]
        cfg = set_priority_matrix(db, new_priorities)
        assert cfg.priority_matrix == new_priorities
        assert "mental_health" in cfg.priority_matrix

    def test_update_ultra_config_partial(self, db: Session):
        """Test partial update of Ultra Mode config."""
        update_data = UltraConfigUpdate(
            enabled=True,
            initiative_level="normal",
        )
        cfg = update_ultra_config(db, update_data)
        assert cfg.enabled is True
        assert cfg.initiative_level == "normal"
        # Other fields should be unchanged
        assert cfg.auto_prepare_tasks is True

    def test_update_ultra_config_full(self, db: Session):
        """Test full update of Ultra Mode config."""
        update_data = UltraConfigUpdate(
            enabled=True,
            initiative_level="minimal",
            auto_prepare_tasks=False,
            auto_generate_next_steps=False,
            auto_close_loops=False,
            scan_enabled=False,
            scan_frequency_minutes=120,
            track_all_user_inputs=False,
            tempo_profile="custom",
        )
        cfg = update_ultra_config(db, update_data)
        assert cfg.enabled is True
        assert cfg.initiative_level == "minimal"
        assert cfg.auto_prepare_tasks is False
        assert cfg.auto_generate_next_steps is False
        assert cfg.auto_close_loops is False
        assert cfg.scan_enabled is False
        assert cfg.scan_frequency_minutes == 120
        assert cfg.track_all_user_inputs is False
        assert cfg.tempo_profile == "custom"

    def test_default_escalation_chain_structure(self, db: Session):
        """Test that default escalation chain has correct structure."""
        cfg = get_ultra_config(db)
        assert "operations" in cfg.escalation_chain
        assert "risk" in cfg.escalation_chain
        assert "creativity" in cfg.escalation_chain
        assert "family" in cfg.escalation_chain
        assert "default" in cfg.escalation_chain
        assert cfg.escalation_chain["operations"] == "ODIN"
        assert cfg.escalation_chain["risk"] == "TYR"
        assert cfg.escalation_chain["creativity"] == "LOKI"
        assert cfg.escalation_chain["family"] == "QUEEN"

    def test_default_priority_matrix_order(self, db: Session):
        """Test that default priority matrix has correct order."""
        cfg = get_ultra_config(db)
        expected_order = [
            "family_stability",
            "financial_safety",
            "empire_growth",
            "operational_velocity",
            "energy_conservation",
            "mental_load_reduction",
        ]
        assert cfg.priority_matrix == expected_order

    def test_scan_configuration(self, db: Session):
        """Test scan-related configuration."""
        cfg = get_ultra_config(db)
        assert cfg.scan_enabled is True
        assert cfg.scan_frequency_minutes == 60

    def test_auto_task_orchestration_defaults(self, db: Session):
        """Test that task orchestration settings default to True."""
        cfg = get_ultra_config(db)
        assert cfg.auto_prepare_tasks is True
        assert cfg.auto_generate_next_steps is True
        assert cfg.auto_close_loops is True

    def test_track_all_inputs_default(self, db: Session):
        """Test that input tracking defaults to True."""
        cfg = get_ultra_config(db)
        assert cfg.track_all_user_inputs is True


class TestHeimdallUltraRouter:
    """Test Heimdall Ultra Mode router endpoints."""

    def test_read_ultra_config(self, client):
        """Test GET /heimdall/ultra/ endpoint."""
        response = client.get("/heimdall/ultra/")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["initiative_level"] == "maximum"
        assert body["enabled"] is False

    def test_enable_ultra_mode(self, client):
        """Test POST /heimdall/ultra/enable endpoint."""
        response = client.post("/heimdall/ultra/enable")
        assert response.status_code == 200
        assert response.json()["enabled"] is True

    def test_disable_ultra_mode(self, client):
        """Test POST /heimdall/ultra/disable endpoint."""
        client.post("/heimdall/ultra/enable")
        response = client.post("/heimdall/ultra/disable")
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_update_config(self, client):
        """Test POST /heimdall/ultra/update endpoint."""
        payload = {
            "enabled": True,
            "initiative_level": "normal",
            "scan_frequency_minutes": 120,
        }
        response = client.post("/heimdall/ultra/update", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is True
        assert body["initiative_level"] == "normal"
        assert body["scan_frequency_minutes"] == 120

    def test_set_initiative_level(self, client):
        """Test POST /heimdall/ultra/initiative/{level} endpoint."""
        response = client.post("/heimdall/ultra/initiative/minimal")
        assert response.status_code == 200
        assert response.json()["initiative_level"] == "minimal"

    def test_set_initiative_level_invalid(self, client):
        """Test that invalid initiative level returns 400."""
        response = client.post("/heimdall/ultra/initiative/invalid_level")
        assert response.status_code == 400

    def test_update_escalation(self, client):
        """Test POST /heimdall/ultra/escalation endpoint."""
        new_chain = {
            "operations": "ODIN",
            "urgent": "KING",
        }
        response = client.post("/heimdall/ultra/escalation", json=new_chain)
        assert response.status_code == 200
        assert response.json()["escalation_chain"]["urgent"] == "KING"

    def test_update_priorities(self, client):
        """Test POST /heimdall/ultra/priorities endpoint."""
        new_priorities = [
            "family_stability",
            "mental_health",
            "financial_safety",
        ]
        response = client.post("/heimdall/ultra/priorities", json=new_priorities)
        assert response.status_code == 200
        assert "mental_health" in response.json()["priority_matrix"]

    def test_config_persistence(self, client):
        """Test that config changes persist across requests."""
        # Set initial state
        client.post("/heimdall/ultra/enable")
        client.post("/heimdall/ultra/initiative/minimal")
        
        # Verify persistence
        response = client.get("/heimdall/ultra/")
        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is True
        assert body["initiative_level"] == "minimal"

    def test_response_schema_completeness(self, client):
        """Test that response includes all expected fields."""
        response = client.get("/heimdall/ultra/")
        assert response.status_code == 200
        body = response.json()
        
        required_fields = [
            "id",
            "enabled",
            "initiative_level",
            "auto_prepare_tasks",
            "auto_generate_next_steps",
            "auto_close_loops",
            "escalation_chain",
            "priority_matrix",
            "scan_enabled",
            "scan_frequency_minutes",
            "track_all_user_inputs",
            "tempo_profile",
        ]
        for field in required_fields:
            assert field in body, f"Missing field: {field}"
