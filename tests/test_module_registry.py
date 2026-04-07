"""
MODULE REGISTRY TEST SUITE
==========================

Tests for module activation, deactivation, and management.
"""

import pytest
from typing import Dict, Any
from app.core_activation import (
    ModuleRegistry,
    ModuleStatus,
    initialize_registry,
)


@pytest.fixture
def feature_flags() -> Dict[str, bool]:
    """Feature flags dictionary."""
    return {}


@pytest.fixture
def registry(feature_flags) -> ModuleRegistry:
    """Module registry fixture."""
    return ModuleRegistry(feature_flags)


class TestModuleRegistry:
    """Tests for ModuleRegistry class."""

    def test_registry_initialization(self, registry):
        """Test registry initializes correctly."""
        assert registry is not None
        assert all(
            module in registry.module_states
            for module in registry.FEATURE_FLAGS.keys()
        )
        assert all(
            status == ModuleStatus.INACTIVE
            for status in registry.module_states.values()
        )

    def test_activate_module_success(self, registry):
        """Test successful module activation."""
        result = registry.activate_module("payments")
        
        assert result["status"] == "success"
        assert result["activated"] is True
        assert result["module"] == "payments"
        assert registry.module_states["payments"] == ModuleStatus.ACTIVE

    def test_deactivate_module_success(self, registry):
        """Test successful module deactivation."""
        # First activate
        registry.activate_module("payments")
        assert registry.module_states["payments"] == ModuleStatus.ACTIVE
        
        # Then deactivate
        result = registry.deactivate_module("payments")
        
        assert result["status"] == "success"
        assert result["deactivated"] is True
        assert registry.module_states["payments"] == ModuleStatus.INACTIVE

    def test_activate_nonexistent_module(self, registry):
        """Test activating non-existent module fails."""
        result = registry.activate_module("nonexistent")
        
        assert result["status"] == "failed"
        assert "not found" in result["error"].lower()
        assert result["activated"] is False

    def test_activate_already_active_module(self, registry):
        """Test activating already active module is skipped."""
        # First activation
        result1 = registry.activate_module("payments")
        assert result1["status"] == "success"
        
        # Second activation
        result2 = registry.activate_module("payments")
        assert result2["status"] == "skipped"
        assert "already active" in result2["message"].lower()

    def test_deactivate_inactive_module(self, registry):
        """Test deactivating inactive module is skipped."""
        result = registry.deactivate_module("payments")
        
        assert result["status"] == "skipped"
        assert "already inactive" in result["message"].lower()

    def test_feature_flag_set_on_activation(self, registry):
        """Test feature flag is set when module activates."""
        registry.activate_module("payments")
        
        flag_name = registry.FEATURE_FLAGS["payments"]
        assert registry.feature_flags[flag_name] is True

    def test_feature_flag_cleared_on_deactivation(self, registry):
        """Test feature flag is cleared when module deactivates."""
        registry.activate_module("payments")
        registry.deactivate_module("payments")
        
        flag_name = registry.FEATURE_FLAGS["payments"]
        assert registry.feature_flags[flag_name] is False

    def test_dependency_check_fails_when_unmet(self, registry):
        """Test activation fails when dependencies not met."""
        # Try to activate banking without payments
        result = registry.activate_module("banking")
        
        assert result["status"] == "failed"
        assert "requires" in result["error"].lower() or "dependencies" in result["error"].lower()
        # When dependency check fails, module state is set to ERROR
        assert registry.module_states["banking"] == ModuleStatus.ERROR

    def test_dependency_chain_activation(self, registry):
        """Test activating modules in dependency order."""
        # Activate payments (no dependencies)
        result1 = registry.activate_module("payments")
        assert result1["status"] == "success"
        
        # Now activate banking (depends on payments)
        result2 = registry.activate_module("banking")
        assert result2["status"] == "success"
        
        assert registry.module_states["payments"] == ModuleStatus.ACTIVE
        assert registry.module_states["banking"] == ModuleStatus.ACTIVE

    def test_activation_condition_check(self, registry):
        """Test custom activation conditions."""
        # Register a condition that always fails
        def failing_condition():
            return False
        
        registry.register_activation_condition("payments", failing_condition)
        
        result = registry.activate_module("payments")
        
        assert result["status"] == "failed"
        assert "condition" in result["error"].lower()

    def test_registration_of_activation_condition(self, registry):
        """Test registering activation condition."""
        condition_called = []
        
        def test_condition():
            condition_called.append(True)
            return True
        
        registry.register_activation_condition("payments", test_condition)
        registry.activate_module("payments")
        
        assert len(condition_called) == 1

    def test_post_activation_setup_hook(self, registry):
        """Test post-activation setup is called."""
        setup_called = []
        
        def test_setup():
            setup_called.append(True)
        
        registry.register_post_setup("payments", test_setup)
        registry.activate_module("payments")
        
        assert len(setup_called) == 1

    def test_post_activation_setup_error_doesnt_fail_activation(self, registry):
        """Test post-setup error doesn't cause activation to fail."""
        def failing_setup():
            raise Exception("Setup error")
        
        registry.register_post_setup("payments", failing_setup)
        result = registry.activate_module("payments")
        
        # Activation should still succeed
        assert result["status"] == "success"
        assert registry.module_states["payments"] == ModuleStatus.ACTIVE

    def test_get_module_status(self, registry):
        """Test getting module status."""
        registry.activate_module("payments")
        status = registry.get_module_status("payments")
        
        assert status["module"] == "payments"
        assert status["status"] == ModuleStatus.ACTIVE.value
        assert status["flag_enabled"] is True

    def test_get_all_status(self, registry):
        """Test getting all modules status."""
        registry.activate_module("payments")
        
        all_status = registry.get_all_status()
        
        assert "modules" in all_status
        assert "active_count" in all_status
        assert all_status["active_count"] == 1
        assert "payments" in all_status["modules"]

    def test_activation_logging(self, registry):
        """Test activation actions are logged."""
        initial_log_size = len(registry.activation_log)
        
        registry.activate_module("payments")
        
        assert len(registry.activation_log) > initial_log_size
        latest_entry = registry.activation_log[-1]
        assert latest_entry["module"] == "payments"
        assert latest_entry["action"] == "activate"
        assert latest_entry["status"] == "success"

    def test_emergency_deactivate_all(self, registry):
        """Test emergency deactivation of all modules."""
        # Activate multiple modules
        registry.activate_module("payments")
        registry.activate_module("automation")
        
        # Emergency deactivate
        result = registry.emergency_deactivate_all()
        
        assert result["status"] == "emergency_deactivation"
        assert all(
            status == ModuleStatus.INACTIVE
            for status in registry.module_states.values()
        )

    def test_get_activation_log(self, registry):
        """Test getting activation log."""
        registry.activate_module("payments")
        registry.deactivate_module("payments")
        
        log = registry.get_activation_log(limit=10)
        
        assert len(log) >= 2
        assert any(entry["action"] == "activate" for entry in log)
        assert any(entry["action"] == "deactivate" for entry in log)


class TestModuleRegistryGlobalFunctions:
    """Tests for global module registry functions."""

    def test_initialize_registry(self, feature_flags):
        """Test registry initialization."""
        from app.core_activation import get_registry
        
        registry = initialize_registry(feature_flags)
        
        assert registry is not None
        assert get_registry() is registry

    def test_global_activate_module(self):
        """Test global activate_module function."""
        from app.core_activation import activate_module, initialize_registry
        
        initialize_registry({})
        result = activate_module("payments")
        
        assert result["status"] == "success"
        assert result["activated"] is True

    def test_global_get_all_status(self):
        """Test global get_all_status function."""
        from app.core_activation import get_all_status, initialize_registry, activate_module
        
        initialize_registry({})
        activate_module("payments")
        
        status = get_all_status()
        
        assert "modules" in status
        assert "payments" in status["modules"]


class TestModuleRegistryIntegration:
    """Integration tests with multiple modules."""

    def test_complex_dependency_chain(self, registry):
        """Test complex dependency chain."""
        # heimdall depends on banking and deal_scoring
        # banking depends on payments
        # deal_scoring depends on payments
        
        # Should fail without payments
        result = registry.activate_module("heimdall")
        assert result["status"] == "failed"
        
        # Activate payments
        registry.activate_module("payments")
        
        # Activate deal_scoring (depends on payments)
        result = registry.activate_module("deal_scoring")
        assert result["status"] == "success"
        
        # Activate banking (depends on payments)
        result = registry.activate_module("banking")
        assert result["status"] == "success"
        
        # Now heimdall should activate
        result = registry.activate_module("heimdall")
        assert result["status"] == "success"

    def test_status_with_mixed_activation(self, registry):
        """Test status reporting with mixed activation states."""
        registry.activate_module("payments")
        registry.activate_module("automation")
        
        status = registry.get_all_status()
        
        assert status["active_count"] == 2
        assert status["modules"]["payments"]["status"] == ModuleStatus.ACTIVE.value
        assert status["modules"]["automation"]["status"] == ModuleStatus.ACTIVE.value
        assert status["modules"]["banking"]["status"] == ModuleStatus.INACTIVE.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
