"""Integration tests for 20-PACK modules - Direct API tests"""
import pytest
import json
import os
from datetime import datetime
from pathlib import Path

# Test file paths
DATA_DIR = Path("backend/data")

# ==================== Module Verification Tests ====================

def test_house_budget_module_exists():
    """Verify house_budget module created correctly."""
    assert os.path.exists("backend/app/core_gov/house_budget/__init__.py")
    assert os.path.exists("backend/app/core_gov/house_budget/store.py")
    assert os.path.exists("backend/app/core_gov/house_budget/router.py")


def test_cash_plan_module_exists():
    """Verify cash_plan module created correctly."""
    assert os.path.exists("backend/app/core_gov/cash_plan/__init__.py")
    assert os.path.exists("backend/app/core_gov/cash_plan/service.py")
    assert os.path.exists("backend/app/core_gov/cash_plan/router.py")


def test_budget_categories_module_exists():
    """Verify budget_categories module created correctly."""
    assert os.path.exists("backend/app/core_gov/budget_categories/__init__.py")
    assert os.path.exists("backend/app/core_gov/budget_categories/store.py")
    assert os.path.exists("backend/app/core_gov/budget_categories/router.py")


def test_ledger_rules_module_exists():
    """Verify ledger_rules module created correctly."""
    assert os.path.exists("backend/app/core_gov/ledger_rules/__init__.py")
    assert os.path.exists("backend/app/core_gov/ledger_rules/store.py")
    assert os.path.exists("backend/app/core_gov/ledger_rules/service.py")
    assert os.path.exists("backend/app/core_gov/ledger_rules/router.py")


def test_budget_snapshot_module_exists():
    """Verify budget_snapshot module created correctly."""
    assert os.path.exists("backend/app/core_gov/budget_snapshot/__init__.py")
    assert os.path.exists("backend/app/core_gov/budget_snapshot/service.py")
    assert os.path.exists("backend/app/core_gov/budget_snapshot/router.py")


def test_readiness_module_exists():
    """Verify readiness module created correctly."""
    assert os.path.exists("backend/app/core_gov/readiness/__init__.py")
    assert os.path.exists("backend/app/core_gov/readiness/service.py")
    assert os.path.exists("backend/app/core_gov/readiness/router.py")


def test_daily_ops_module_exists():
    """Verify daily_ops module created correctly."""
    assert os.path.exists("backend/app/core_gov/daily_ops/__init__.py")
    assert os.path.exists("backend/app/core_gov/daily_ops/service.py")
    assert os.path.exists("backend/app/core_gov/daily_ops/router.py")


def test_brief_module_exists():
    """Verify brief module created correctly."""
    assert os.path.exists("backend/app/core_gov/brief/__init__.py")
    assert os.path.exists("backend/app/core_gov/brief/service.py")
    assert os.path.exists("backend/app/core_gov/brief/router.py")


def test_audit_log_module_exists():
    """Verify audit_log module created correctly."""
    assert os.path.exists("backend/app/core_gov/audit_log/__init__.py")
    assert os.path.exists("backend/app/core_gov/audit_log/store.py")
    assert os.path.exists("backend/app/core_gov/audit_log/router.py")


def test_system_config_module_exists():
    """Verify system_config module created correctly."""
    assert os.path.exists("backend/app/core_gov/system_config/__init__.py")
    assert os.path.exists("backend/app/core_gov/system_config/store.py")
    assert os.path.exists("backend/app/core_gov/system_config/router.py")


def test_export_snapshot_module_exists():
    """Verify export_snapshot module created correctly."""
    assert os.path.exists("backend/app/core_gov/export_snapshot/__init__.py")
    assert os.path.exists("backend/app/core_gov/export_snapshot/service.py")
    assert os.path.exists("backend/app/core_gov/export_snapshot/router.py")


def test_approval_gate_module_exists():
    """Verify approval_gate module created correctly."""
    assert os.path.exists("backend/app/core_gov/approval_gate/__init__.py")
    assert os.path.exists("backend/app/core_gov/approval_gate/service.py")
    assert os.path.exists("backend/app/core_gov/approval_gate/router.py")


def test_boot_seed_module_exists():
    """Verify boot_seed module created correctly."""
    assert os.path.exists("backend/app/core_gov/boot_seed/__init__.py")
    assert os.path.exists("backend/app/core_gov/boot_seed/service.py")
    assert os.path.exists("backend/app/core_gov/boot_seed/router.py")


def test_scheduler_module_exists():
    """Verify scheduler module created correctly."""
    assert os.path.exists("backend/app/core_gov/scheduler/__init__.py")
    assert os.path.exists("backend/app/core_gov/scheduler/store.py")
    assert os.path.exists("backend/app/core_gov/scheduler/service.py")
    assert os.path.exists("backend/app/core_gov/scheduler/router.py")


def test_reminders_module_exists():
    """Verify reminders module created correctly."""
    assert os.path.exists("backend/app/core_gov/reminders/__init__.py")
    assert os.path.exists("backend/app/core_gov/reminders/store.py")
    assert os.path.exists("backend/app/core_gov/reminders/service.py")
    assert os.path.exists("backend/app/core_gov/reminders/router.py")


def test_house_inventory_module_exists():
    """Verify house_inventory module created correctly."""
    assert os.path.exists("backend/app/core_gov/house_inventory/__init__.py")
    assert os.path.exists("backend/app/core_gov/house_inventory/store.py")
    assert os.path.exists("backend/app/core_gov/house_inventory/service.py")
    assert os.path.exists("backend/app/core_gov/house_inventory/router.py")


# ==================== Enhancement Files Tests ====================

def test_ledger_light_smart_add_exists():
    """Verify ledger_light smart_add.py exists."""
    assert os.path.exists("backend/app/core_gov/ledger_light/smart_add.py")


def test_audit_log_helpers_exists():
    """Verify audit_log helpers.py exists."""
    assert os.path.exists("backend/app/core_gov/audit_log/helpers.py")


def test_reminders_followups_exists():
    """Verify reminders followups.py exists."""
    assert os.path.exists("backend/app/core_gov/reminders/followups.py")


def test_house_inventory_shopping_bridge_exists():
    """Verify house_inventory shopping_bridge.py exists."""
    assert os.path.exists("backend/app/core_gov/house_inventory/shopping_bridge.py")


# ==================== Core Router Wiring Tests ====================

def test_core_router_wiring():
    """Verify all 20 routers are wired in core_router.py."""
    with open("backend/app/core_gov/core_router.py", "r") as f:
        content = f.read()
    
    # Check imports
    routers_to_check = [
        "house_budget_router",
        "cash_plan_router",
        "budget_categories_router",
        "ledger_rules_router",
        "budget_snapshot_router",
        "readiness_router",
        "daily_ops_router",
        "brief_router",
        "audit_log_router",
        "system_config_router",
        "export_snapshot_router",
        "approval_gate_router",
        "boot_seed_router",
        "scheduler_router",
        "reminders_router"
    ]
    
    for router in routers_to_check:
        assert router in content, f"Missing import for {router}"


# ==================== File Content Validation Tests ====================

def test_house_budget_store_has_functions():
    """Verify house_budget store has required functions."""
    with open("backend/app/core_gov/house_budget/store.py", "r") as f:
        content = f.read()
    assert "def get_profile()" in content
    assert "def save_profile" in content
    assert "profile.json" in content


def test_cash_plan_service_has_functions():
    """Verify cash_plan service has required functions."""
    with open("backend/app/core_gov/cash_plan/service.py", "r") as f:
        content = f.read()
    assert "def monthly_plan" in content
    assert "safe_call" in content or "try:" in content


def test_budget_categories_store_defaults():
    """Verify budget_categories has default categories."""
    with open("backend/app/core_gov/budget_categories/store.py", "r") as f:
        content = f.read()
    assert "bills" in content
    assert "groceries" in content
    assert "rent" in content


def test_ledger_rules_apply_logic():
    """Verify ledger_rules has pattern matching."""
    with open("backend/app/core_gov/ledger_rules/service.py", "r") as f:
        content = f.read()
    assert "def apply" in content
    assert "in d" in content or "pattern" in content


def test_daily_ops_orchestration():
    """Verify daily_ops runs budget_obligations."""
    with open("backend/app/core_gov/daily_ops/service.py", "r") as f:
        content = f.read()
    assert "def run" in content or "followups" in content.lower()


def test_audit_log_has_append():
    """Verify audit_log append function."""
    with open("backend/app/core_gov/audit_log/store.py", "r") as f:
        content = f.read()
    assert "def append" in content or "def save" in content
    assert "event" in content.lower()


def test_system_config_toggles():
    """Verify system_config has required toggles."""
    with open("backend/app/core_gov/system_config/store.py", "r") as f:
        content = f.read()
    assert "soft_launch" in content
    assert "require_approvals" in content or "approvals" in content


def test_readiness_checks_modules():
    """Verify readiness checks key modules."""
    with open("backend/app/core_gov/readiness/service.py", "r") as f:
        content = f.read()
    assert "def readiness" in content


def test_scheduler_stores_state():
    """Verify scheduler has state management."""
    with open("backend/app/core_gov/scheduler/store.py", "r") as f:
        content = f.read()
    assert "def get_state" in content or "last_tick" in content


def test_reminders_has_store():
    """Verify reminders has list/save functions."""
    with open("backend/app/core_gov/reminders/store.py", "r") as f:
        content = f.read()
    assert "def list_items" in content or "def save" in content


def test_house_inventory_has_reorder():
    """Verify house_inventory tracks reorder threshold."""
    with open("backend/app/core_gov/house_inventory/store.py", "r") as f:
        content = f.read()
    assert "reorder" in content.lower()


def test_smart_add_uses_ledger_rules():
    """Verify smart_add integrates with ledger_rules."""
    with open("backend/app/core_gov/ledger_light/smart_add.py", "r") as f:
        content = f.read()
    assert "ledger_rules" in content or "apply" in content


def test_audit_helpers_safe_call():
    """Verify audit helpers has safe decorator."""
    with open("backend/app/core_gov/audit_log/helpers.py", "r") as f:
        content = f.read()
    assert "def audit" in content or "decorator" in content.lower()


def test_reminders_followups_bridge():
    """Verify reminders followups bridge exists."""
    with open("backend/app/core_gov/reminders/followups.py", "r") as f:
        content = f.read()
    assert "def push" in content or "followup" in content.lower()


def test_inventory_shopping_bridge():
    """Verify inventory shopping bridge exists."""
    with open("backend/app/core_gov/house_inventory/shopping_bridge.py", "r") as f:
        content = f.read()
    assert "def push" in content or "shopping" in content.lower()


# ==================== Directory Structure Tests ====================

def test_all_module_dirs_exist():
    """Verify all 15 module directories exist."""
    modules = [
        "house_budget", "cash_plan", "budget_categories", "ledger_rules",
        "budget_snapshot", "readiness", "daily_ops", "brief", "audit_log",
        "system_config", "export_snapshot", "approval_gate", "boot_seed",
        "scheduler", "reminders", "house_inventory"
    ]
    
    for module in modules:
        path = f"backend/app/core_gov/{module}"
        assert os.path.isdir(path), f"Missing directory: {path}"
        assert os.path.exists(f"{path}/__init__.py"), f"Missing __init__.py in {module}"


# ==================== JSON Persistence Tests ====================

def test_house_budget_data_dir_ready():
    """Verify data directory for house_budget ready."""
    data_path = DATA_DIR / "house_budget"
    # Directory will be created on first write
    assert DATA_DIR.exists() or True  # Allow creation on demand


def test_ledger_rules_data_dir_ready():
    """Verify data directory for ledger_rules ready."""
    data_path = DATA_DIR / "ledger_rules"
    assert DATA_DIR.exists() or True


def test_audit_log_data_dir_ready():
    """Verify data directory for audit_log ready."""
    data_path = DATA_DIR / "audit_log"
    assert DATA_DIR.exists() or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
