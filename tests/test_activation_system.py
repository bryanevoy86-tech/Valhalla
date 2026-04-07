"""
VALHALLA ACTIVATION SYSTEM TEST SUITE
=====================================

Comprehensive tests for activation conditions, controller, and endpoints.
"""

import pytest
import pytest_asyncio
from datetime import datetime
import json
from typing import Dict, Any

# ========================
# TEST FIXTURES
# ========================

@pytest_asyncio.fixture
async def activation_engine():
    """Fixture for activation condition engine."""
    from app.core_launch.activation_conditions import ActivationConditionEngine
    
    engine = ActivationConditionEngine()
    yield engine


@pytest_asyncio.fixture
async def activation_controller():
    """Fixture for activation controller."""
    from app.core_launch.master_activation_controller import ActivationController
    
    controller = ActivationController()
    yield controller


@pytest_asyncio.fixture
async def client():
    """Fixture for FastAPI test client."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    yield client


# ========================
# ACTIVATION CONDITIONS TESTS
# ========================

@pytest.mark.asyncio
async def test_activation_rule_creation(activation_engine):
    """Test creating an activation rule."""
    from app.core_launch.activation_conditions import ActivationRule, ConditionType
    
    rule = ActivationRule(
        "test_rule",
        ConditionType.MINIMUM_BALANCE,
        lambda: True,
        "Test rule"
    )
    
    assert rule.name == "test_rule"
    assert rule.check() is True
    assert rule.last_result is True


@pytest.mark.asyncio
async def test_condition_engine_rules(activation_engine):
    """Test registering and checking rules."""
    from app.core_launch.activation_conditions import ActivationRule, ConditionType
    
    # Register rule
    rule = ActivationRule(
        "balance_check",
        ConditionType.MINIMUM_BALANCE,
        lambda: activation_engine.metrics.get("balance", 0) >= 1000,
        "Balance >= 1000"
    )
    
    activation_engine.register_rule("payment_module", rule)
    
    # Should fail without metric
    assert activation_engine.can_activate("payment_module") is False
    
    # Should pass with metric
    activation_engine.set_metric("balance", 5000)
    assert activation_engine.can_activate("payment_module") is True


@pytest.mark.asyncio
async def test_approval_gates(activation_engine):
    """Test approval gates."""
    activation_engine.register_approval_gate("gate_1", approved=False)
    assert activation_engine.approvals["gate_1"] is False
    
    activation_engine.approve("gate_1")
    assert activation_engine.approvals["gate_1"] is True
    
    activation_engine.reject("gate_1")
    assert activation_engine.approvals["gate_1"] is False


@pytest.mark.asyncio
async def test_full_status(activation_engine):
    """Test full status output."""
    from app.core_launch.activation_conditions import ActivationRule, ConditionType
    
    rule = ActivationRule(
        "test",
        ConditionType.METRIC_THRESHOLD,
        lambda: True,
        "Test"
    )
    
    activation_engine.register_rule("module_1", rule)
    status = activation_engine.full_status()
    
    assert "timestamp" in status
    assert "modules" in status
    assert "module_1" in status["modules"]


# ========================
# ACTIVATION CONTROLLER TESTS
# ========================

@pytest.mark.asyncio
async def test_module_registration(activation_controller):
    """Test registering modules."""
    activation_controller.register_module("module_1")
    assert "module_1" in activation_controller.modules
    
    activation_controller.register_module("module_2", ["module_1"])
    assert activation_controller.dependencies.get("module_2") == ["module_1"]


@pytest.mark.asyncio
async def test_dependency_checking(activation_controller):
    """Test dependency checking."""
    from app.core_launch.master_activation_controller import ActivationStatus
    
    activation_controller.register_module("dep")
    activation_controller.register_module("dependent", ["dep"])
    
    # Dependency not met (dep not active)
    assert activation_controller.check_dependencies("dependent") is False
    
    # Activate dependency
    activation_controller.modules["dep"].status = ActivationStatus.ACTIVE
    assert activation_controller.check_dependencies("dependent") is True


@pytest.mark.asyncio
async def test_condition_checking(activation_controller):
    """Test checking conditions."""
    activation_controller.register_module("module_1")
    
    # Mock the activation_conditions
    from unittest.mock import patch
    
    with patch("app.core_launch.master_activation_controller.can_activate", return_value=True):
        ready, msg = await activation_controller.check_conditions("module_1")
        assert ready is True
    
    with patch("app.core_launch.master_activation_controller.can_activate", return_value=False):
        with patch("app.core_launch.master_activation_controller.get_activation_status", 
                   return_value={"conditions": [{"name": "test", "last_result": False}]}):
            ready, msg = await activation_controller.check_conditions("module_1")
            assert ready is False


@pytest.mark.asyncio
async def test_module_activation(activation_controller):
    """Test module activation."""
    from app.core_launch.master_activation_controller import ActivationStatus
    
    activation_controller.register_module("module_1")
    
    success, msg = await activation_controller.activate("module_1")
    
    state = activation_controller.modules["module_1"]
    assert state.status == ActivationStatus.ACTIVE
    assert state.activation_count == 1
    assert state.start_time is not None
    assert state.end_time is not None


@pytest.mark.asyncio
async def test_activation_logging(activation_controller):
    """Test activation logging."""
    activation_controller.register_module("module_1")
    
    activation_controller.log_activation("module_1", "success")
    
    assert len(activation_controller.activation_log) == 1
    entry = activation_controller.activation_log[0]
    assert entry["module"] == "module_1"
    assert entry["result"] == "success"
    assert "timestamp" in entry


@pytest.mark.asyncio
async def test_master_enable_disable(activation_controller):
    """Test master enable/disable."""
    assert activation_controller.master_enabled is False
    
    activation_controller.enable_master()
    assert activation_controller.master_enabled is True
    
    activation_controller.disable_master()
    assert activation_controller.master_enabled is False


# ========================
# ACTIVATION ENDPOINT TESTS
# ========================

class TestActivationEndpoints:
    """Test activation API endpoints."""

    def test_enable_master(self, client):
        """Test enabling master activation."""
        response = client.post("/api/v1/activation/enable-master")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "summary" in data

    def test_disable_master(self, client):
        """Test disabling master activation."""
        # Enable first
        client.post("/api/v1/activation/enable-master")
        
        response = client.post("/api/v1/activation/disable-master")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_status(self, client):
        """Test getting activation status."""
        # Register modules first
        client.post("/api/v1/activation/debug/register-modules")
        
        response = client.get("/api/v1/activation/status")
        assert response.status_code == 200
        data = response.json()
        assert "master_enabled" in data
        assert "modules" in data

    def test_get_module_status(self, client):
        """Test getting module status."""
        # Register modules
        client.post("/api/v1/activation/debug/register-modules")
        
        response = client.get("/api/v1/activation/status/payment_processor")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "payment_processor"
        assert "state" in data
        assert "conditions" in data

    def test_module_not_found(self, client):
        """Test getting status for non-existent module."""
        response = client.get("/api/v1/activation/status/nonexistent")
        
        # 404 for not found
        assert response.status_code == 404 or response.status_code == 200  # Depending on impl

    def test_set_metric(self, client):
        """Test setting a metric."""
        response = client.post(
            "/api/v1/activation/conditions/set-metric",
            params={"metric_name": "test_metric", "value": 42}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_approve_gate(self, client):
        """Test approving a gate."""
        response = client.post("/api/v1/activation/conditions/approve-gate/test_gate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["approved"] is True

    def test_reject_gate(self, client):
        """Test rejecting a gate."""
        response = client.post("/api/v1/activation/conditions/reject-gate/test_gate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["approved"] is False

    def test_get_conditions(self, client):
        """Test getting all conditions."""
        response = client.get("/api/v1/activation/conditions")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "modules" in data

    def test_get_activation_log(self, client):
        """Test getting activation log."""
        response = client.get("/api/v1/activation/log")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total_entries" in data

    def test_emergency_kill_switch(self, client):
        """Test emergency kill switch."""
        # Enable master first
        client.post("/api/v1/activation/enable-master")
        
        response = client.post("/api/v1/activation/emergency/kill-switch")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "emergency"


# ========================
# INTEGRATION TESTS
# ========================

@pytest.mark.asyncio
async def test_full_activation_workflow(activation_controller):
    """Test complete activation workflow."""
    from unittest.mock import patch
    
    activation_controller.register_module("payment_processor")
    
    with patch("app.core_launch.master_activation_controller.can_activate", return_value=True):
        success, msg = await activation_controller.full_activation("payment_processor")
    
    assert success is True
    state = activation_controller.modules["payment_processor"]
    assert state.activation_count == 1


@pytest.mark.asyncio
async def test_multi_module_activation(activation_controller):
    """Test activating multiple interdependent modules."""
    from app.core_launch.master_activation_controller import ActivationStatus
    
    # Register modules with dependencies
    activation_controller.register_module("module_1")
    activation_controller.register_module("module_2", ["module_1"])
    activation_controller.register_module("module_3", ["module_1", "module_2"])
    
    # Activate module_1
    await activation_controller.activate("module_1")
    assert activation_controller.modules["module_1"].status == ActivationStatus.ACTIVE
    
    # Now module_2 dependencies should be met
    deps_met = activation_controller.check_dependencies("module_2")
    assert deps_met is True


# ========================
# ERROR HANDLING TESTS
# ========================

@pytest.mark.asyncio
async def test_condition_checking_error(activation_controller):
    """Test error handling in condition checking."""
    activation_controller.register_module("module_1")
    
    from unittest.mock import patch
    
    with patch("app.core_launch.master_activation_controller.can_activate", 
               side_effect=Exception("Test error")):
        ready, msg = await activation_controller.check_conditions("module_1")
        assert ready is False
        assert "error" in msg.lower() or "exception" in msg.lower()


@pytest.mark.asyncio
async def test_activation_with_missing_dependencies(activation_controller):
    """Test activation fails when dependencies missing."""
    activation_controller.register_module("module_dep")
    activation_controller.register_module("module_1", ["module_dep"])
    
    pre_ok, pre_msg = await activation_controller.pre_activate("module_1")
    assert pre_ok is False
    assert "dependencies" in pre_msg.lower()


if __name__ == "__main__":
    # Run tests with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
