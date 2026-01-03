"""Test suite for 10 new PACKs expansion (Session 14 Part 5)."""
import os
import pytest


# ==================== Module Tests ====================

@pytest.mark.parametrize("module", [
    "income",
    "payday",
    "cra_risk",
    "jv_board",
    "know_inbox",
    "know_chunks",
    "know_retrieve",
    "envelopes",
])
def test_module_exists(module):
    """Test that module directory exists."""
    assert os.path.exists(f"backend/app/core_gov/{module}/__init__.py")
    assert os.path.exists(f"backend/app/core_gov/{module}/router.py")


def test_income_module():
    """Test income module files."""
    assert os.path.exists("backend/app/core_gov/income/__init__.py")
    assert os.path.exists("backend/app/core_gov/income/store.py")
    assert os.path.exists("backend/app/core_gov/income/service.py")
    assert os.path.exists("backend/app/core_gov/income/router.py")
    assert os.path.exists("backend/app/core_gov/income/post_to_ledger.py")


def test_payday_module():
    """Test payday module files."""
    assert os.path.exists("backend/app/core_gov/payday/__init__.py")
    assert os.path.exists("backend/app/core_gov/payday/service.py")
    assert os.path.exists("backend/app/core_gov/payday/router.py")
    assert os.path.exists("backend/app/core_gov/payday/followups.py")


def test_cra_risk_module():
    """Test cra_risk module files."""
    assert os.path.exists("backend/app/core_gov/cra_risk/__init__.py")
    assert os.path.exists("backend/app/core_gov/cra_risk/store.py")
    assert os.path.exists("backend/app/core_gov/cra_risk/router.py")
    assert os.path.exists("backend/app/core_gov/cra_risk/scan.py")


def test_house_calendar_enhancements():
    """Test house_calendar enhancements."""
    assert os.path.exists("backend/app/core_gov/house_calendar/reminders.py")


def test_jv_board_module():
    """Test jv_board module files."""
    assert os.path.exists("backend/app/core_gov/jv_board/__init__.py")
    assert os.path.exists("backend/app/core_gov/jv_board/service.py")
    assert os.path.exists("backend/app/core_gov/jv_board/router.py")
    assert os.path.exists("backend/app/core_gov/jv_board/outbox_updates.py")


def test_know_inbox_module():
    """Test know_inbox module files."""
    assert os.path.exists("backend/app/core_gov/know_inbox/__init__.py")
    assert os.path.exists("backend/app/core_gov/know_inbox/store.py")
    assert os.path.exists("backend/app/core_gov/know_inbox/router.py")


def test_know_chunks_module():
    """Test know_chunks module files."""
    assert os.path.exists("backend/app/core_gov/know_chunks/__init__.py")
    assert os.path.exists("backend/app/core_gov/know_chunks/store.py")
    assert os.path.exists("backend/app/core_gov/know_chunks/service.py")
    assert os.path.exists("backend/app/core_gov/know_chunks/router.py")


def test_know_retrieve_module():
    """Test know_retrieve module files."""
    assert os.path.exists("backend/app/core_gov/know_retrieve/__init__.py")
    assert os.path.exists("backend/app/core_gov/know_retrieve/service.py")
    assert os.path.exists("backend/app/core_gov/know_retrieve/router.py")


def test_envelopes_module():
    """Test envelopes module files."""
    assert os.path.exists("backend/app/core_gov/envelopes/__init__.py")
    assert os.path.exists("backend/app/core_gov/envelopes/store.py")
    assert os.path.exists("backend/app/core_gov/envelopes/service.py")
    assert os.path.exists("backend/app/core_gov/envelopes/router.py")


def test_receipts_enhancements():
    """Test receipts enhancements."""
    assert os.path.exists("backend/app/core_gov/receipts/attachments.py")
    assert os.path.exists("backend/app/core_gov/receipts/attach_meta.py")


# ==================== Router Wiring Tests ====================

def test_core_router_has_new_imports():
    """Test that core router has new imports."""
    with open("backend/app/core_gov/core_router.py") as f:
        content = f.read()

    new_routers = [
        "income_router",
        "payday_router",
        "cra_risk_router",
        "jv_board_router",
        "know_inbox_router",
        "know_chunks_router",
        "know_retrieve_router",
        "envelopes_router",
    ]

    for router in new_routers:
        assert router in content, f"Missing import for {router}"


def test_core_router_has_new_includes():
    """Test that core router includes new routers."""
    with open("backend/app/core_gov/core_router.py") as f:
        content = f.read()

    new_routers = [
        "income_router",
        "payday_router",
        "cra_risk_router",
        "jv_board_router",
        "know_inbox_router",
        "know_chunks_router",
        "know_retrieve_router",
        "envelopes_router",
    ]

    for router in new_routers:
        assert f"core.include_router({router})" in content, f"Missing include for {router}"


# ==================== Feature Tests ====================

def test_income_router_has_endpoints():
    """Test income router has required endpoints."""
    with open("backend/app/core_gov/income/router.py") as f:
        content = f.read()
    assert "@router.post" in content
    assert "@router.get" in content
    assert "post_ledger" in content


def test_payday_router_has_endpoints():
    """Test payday router has required endpoints."""
    with open("backend/app/core_gov/payday/router.py") as f:
        content = f.read()
    assert "@router.get" in content
    assert "plan" in content
    assert "@router.post" in content
    assert "followups" in content


def test_cra_risk_router_has_scan():
    """Test cra_risk router has scan endpoint."""
    with open("backend/app/core_gov/cra_risk/router.py") as f:
        content = f.read()
    assert "/scan/{month}" in content


def test_envelopes_router_has_month():
    """Test envelopes router has month endpoint."""
    with open("backend/app/core_gov/envelopes/router.py") as f:
        content = f.read()
    assert "/month/{month}" in content


def test_scheduler_updated():
    """Test scheduler has payday and calendar pushes."""
    with open("backend/app/core_gov/scheduler/service.py") as f:
        content = f.read()
    assert "payday" in content.lower()
    assert "calendar" in content.lower()


def test_ops_board_updated():
    """Test ops board has payday plan and CRA hint."""
    with open("backend/app/core_gov/ops_board/service.py") as f:
        content = f.read()
    assert "payday" in content.lower()
    assert "cra_risk" in content.lower()


def test_receipts_has_attachments():
    """Test receipts router has attachment endpoints."""
    with open("backend/app/core_gov/receipts/router.py") as f:
        content = f.read()
    assert "fingerprint" in content.lower()
    assert "attach" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
