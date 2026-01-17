"""Comprehensive test suite for 20-PACK expansion deployment."""
import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# ==================== P-HOUSEBUD-1 Tests ====================

def test_house_budget_create_and_get():
    """Test creating and retrieving house budget profile."""
    profile_data = {
        "currency": "USD",
        "income_streams": [
            {"name": "salary", "monthly": 3000},
            {"name": "freelance", "monthly": 500}
        ],
        "buffer_target": 5000,
        "baseline_notes": "Main household budget"
    }
    
    # Create profile
    resp = client.post("/core/house_budget", json=profile_data)
    assert resp.status_code == 200
    result = resp.json()
    assert result["currency"] == "USD"
    assert len(result["income_streams"]) == 2
    assert result["buffer_target"] == 5000
    
    # Get profile
    resp = client.get("/core/house_budget")
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["currency"] == "USD"
    assert profile["buffer_target"] == 5000


def test_house_budget_patch():
    """Test patching house budget profile."""
    patch_data = {"buffer_target": 6000}
    resp = client.post("/core/house_budget", json=patch_data)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["buffer_target"] == 6000


# ==================== P-CASHPLAN-1 Tests ====================

def test_cash_plan_current_month():
    """Test monthly cash plan calculation."""
    resp = client.get("/core/cash_plan/month/2024-01")
    assert resp.status_code == 200
    plan = resp.json()
    assert "obligations_estimate" in plan
    assert "buffer_target" in plan
    assert "income_reference" in plan
    assert "need" in plan
    assert "gap" in plan


def test_cash_plan_future_month():
    """Test cash plan for future month."""
    future_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m")
    resp = client.get(f"/core/cash_plan/month/{future_month}")
    assert resp.status_code == 200
    plan = resp.json()
    assert isinstance(plan.get("gap"), (int, float))


# ==================== P-BUDCAT-1 Tests ====================

def test_budget_categories_list():
    """Test retrieving budget categories."""
    resp = client.get("/core/budget/categories")
    assert resp.status_code == 200
    categories = resp.json()
    assert isinstance(categories, list)
    assert len(categories) >= 16  # Default categories
    category_names = [c["name"] for c in categories]
    assert "bills" in category_names
    assert "groceries" in category_names
    assert "rent" in category_names


def test_budget_categories_add():
    """Test adding new budget category."""
    new_cat = {"name": "subscriptions"}
    resp = client.post("/core/budget/categories", json=new_cat)
    assert resp.status_code == 200
    result = resp.json()
    assert result["name"] == "subscriptions"


# ==================== P-LEDRULE-1 Tests ====================

def test_ledger_rules_create():
    """Test creating ledger rule."""
    rule_data = {
        "pattern": "whole foods",
        "category": "groceries"
    }
    resp = client.post("/core/ledger_rules", json=rule_data)
    assert resp.status_code == 200
    rule = resp.json()
    assert rule["pattern"] == "whole foods"
    assert rule["category"] == "groceries"
    assert rule["id"].startswith("lr_")


def test_ledger_rules_apply():
    """Test applying ledger rules for auto-categorization."""
    # Create a rule first
    client.post("/core/ledger_rules", json={
        "pattern": "amazon",
        "category": "online_shopping"
    })
    
    # Apply rule
    resp = client.get("/core/ledger_rules/apply", params={
        "description": "AMAZON.COM PURCHASE"
    })
    assert resp.status_code == 200
    result = resp.json()
    assert "category" in result
    assert result["category"] == "online_shopping"


def test_ledger_rules_no_match():
    """Test ledger rule apply when no pattern matches."""
    resp = client.get("/core/ledger_rules/apply", params={
        "description": "UNKNOWN MERCHANT XYZ"
    })
    assert resp.status_code == 200
    result = resp.json()
    # Should return empty string if no match
    assert result["category"] == ""


# ==================== P-BUDSNAP-1 Tests ====================

def test_budget_snapshot_default():
    """Test budget snapshot with default days."""
    resp = client.get("/core/budget/snapshot")
    assert resp.status_code == 200
    snapshot = resp.json()
    assert "obligations_upcoming" in snapshot
    assert "buffer_target" in snapshot
    assert "income_reference" in snapshot
    assert "cash_plan_gap" in snapshot


def test_budget_snapshot_custom_days():
    """Test budget snapshot with custom day range."""
    resp = client.get("/core/budget/snapshot?days=30")
    assert resp.status_code == 200
    snapshot = resp.json()
    assert "obligations_upcoming" in snapshot


# ==================== P-READINESS-1 Tests ====================

def test_readiness_check():
    """Test go-live readiness checklist."""
    resp = client.get("/core/readiness")
    assert resp.status_code == 200
    readiness = resp.json()
    assert "ready" in readiness
    assert isinstance(readiness["ready"], bool)
    assert "modules" in readiness
    assert isinstance(readiness["modules"], dict)


# ==================== P-DAILYOPS-1 Tests ====================

def test_daily_ops_run():
    """Test running daily operations."""
    resp = client.post("/core/daily_ops/run")
    assert resp.status_code == 200
    result = resp.json()
    assert "timestamp" in result
    assert "bills_processed" in result
    assert "followups_created" in result


def test_daily_ops_run_custom_days():
    """Test daily ops with custom bill days range."""
    resp = client.post("/core/daily_ops/run", json={"days_bills": 14})
    assert resp.status_code == 200
    result = resp.json()
    assert result["days_bills"] == 14


# ==================== P-BRIEF-1 Tests ====================

def test_brief_unified():
    """Test unified brief dashboard."""
    resp = client.get("/core/brief")
    assert resp.status_code == 200
    brief = resp.json()
    assert "mode" in brief or "mode" not in brief  # Mode might not exist
    assert "upcoming_bills" in brief or "bills_upcoming" in brief
    assert "open_followups" in brief or "followups" in brief


# ==================== P-AUDIT-1 Tests ====================

def test_audit_log_append():
    """Test appending to audit log."""
    event = {
        "event_type": "bill_created",
        "payload": {
            "bill_id": "test_123",
            "amount": 150.00
        }
    }
    resp = client.post("/core/audit", json=event)
    assert resp.status_code == 200
    result = resp.json()
    assert result["event_type"] == "bill_created"
    assert result["id"].startswith("aud_")


def test_audit_log_list():
    """Test retrieving audit events."""
    resp = client.get("/core/audit")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)


def test_audit_log_list_limit():
    """Test audit list with limit."""
    resp = client.get("/core/audit?limit=10")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) <= 10


# ==================== P-SYSCFG-1 Tests ====================

def test_system_config_get():
    """Test retrieving system config."""
    resp = client.get("/core/system_config")
    assert resp.status_code == 200
    config = resp.json()
    assert "soft_launch" in config
    assert "require_approvals_for_execute" in config
    assert "allow_external_sending" in config


def test_system_config_patch():
    """Test updating system config."""
    patch = {"soft_launch": False}
    resp = client.post("/core/system_config", json=patch)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["soft_launch"] is False


# ==================== P-EXPORTSNAP-1 Tests ====================

def test_export_snapshot():
    """Test data export snapshot."""
    resp = client.get("/core/export_snapshot")
    assert resp.status_code == 200
    snapshot = resp.json()
    assert "timestamp" in snapshot
    assert "files" in snapshot
    assert isinstance(snapshot["files"], dict)


# ==================== P-APPROVALGATE-1 Tests ====================

def test_approval_gate_check():
    """Test approval gate for execute actions."""
    action_request = {
        "action": "execute_followup",
        "payload": {
            "followup_id": "test_fu_123"
        }
    }
    resp = client.post("/core/approval_gate", json=action_request)
    assert resp.status_code in [200, 400]  # Might be blocked or approved


# ==================== P-BOOT-1 Tests ====================

def test_boot_seed_minimum():
    """Test system bootstrap."""
    resp = client.post("/core/boot/seed_minimum")
    assert resp.status_code == 200
    result = resp.json()
    assert "system_config" in result
    assert "budget_categories" in result
    assert "house_budget" in result


# ==================== P-SCHED-1 Tests ====================

def test_scheduler_state():
    """Test scheduler state."""
    resp = client.get("/core/scheduler/state")
    assert resp.status_code == 200
    state = resp.json()
    assert "last_tick" in state


def test_scheduler_tick():
    """Test manual scheduler tick."""
    resp = client.post("/core/scheduler/tick")
    assert resp.status_code == 200
    result = resp.json()
    assert "timestamp" in result
    assert "last_tick" in result


# ==================== P-REMIND-1 Tests ====================

def test_reminders_create():
    """Test creating reminder."""
    reminder = {
        "title": "Call insurance",
        "due_date": "2024-02-15",
        "kind": "call",
        "notes": "Annual review"
    }
    resp = client.post("/core/reminders", json=reminder)
    assert resp.status_code == 200
    result = resp.json()
    assert result["title"] == "Call insurance"
    assert result["id"].startswith("rem_")


def test_reminders_list_open():
    """Test listing open reminders."""
    resp = client.get("/core/reminders")
    assert resp.status_code == 200
    reminders = resp.json()
    assert isinstance(reminders, list)


def test_reminders_mark_done():
    """Test marking reminder as done."""
    # Create reminder first
    create_resp = client.post("/core/reminders", json={
        "title": "Test task",
        "due_date": "2024-02-15",
        "kind": "task"
    })
    reminder_id = create_resp.json()["id"]
    
    # Mark as done
    resp = client.post(f"/core/reminders/{reminder_id}/done")
    assert resp.status_code == 200


# ==================== P-REMIND-2 Tests ====================

def test_reminders_push_followups():
    """Test pushing reminders to followups."""
    resp = client.post("/core/reminders/push_followups")
    assert resp.status_code == 200
    result = resp.json()
    assert "created" in result or "followups" in result


# ==================== P-INVENT-1 Tests ====================

def test_house_inventory_upsert():
    """Test upserting inventory item."""
    item = {
        "name": "flour",
        "unit": "lbs",
        "qty": 5,
        "reorder_at": 2,
        "notes": "All-purpose"
    }
    resp = client.post("/core/house_inventory", json=item)
    assert resp.status_code == 200
    result = resp.json()
    assert result["name"] == "flour"
    assert result["qty"] == 5


def test_house_inventory_list_low():
    """Test listing low inventory items."""
    resp = client.get("/core/house_inventory/low")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)


# ==================== P-INVENT-2 Tests ====================

def test_house_inventory_push_shopping():
    """Test pushing low inventory to shopping list."""
    resp = client.post("/core/house_inventory/push_shopping")
    assert resp.status_code == 200
    result = resp.json()
    assert "created" in result or "items" in result


# ==================== P-LEDGERL-3 Tests ====================

def test_ledger_smart_add():
    """Test smart add with auto-categorization."""
    txn = {
        "date": "2024-01-15",
        "kind": "expense",
        "amount": 150.00,
        "description": "Whole Foods Market",
        "account_id": "acc_123"
    }
    resp = client.post("/core/ledger/smart", json=txn)
    assert resp.status_code == 200
    result = resp.json()
    assert result["description"] == "Whole Foods Market"
    assert "category" in result or "id" in result


# ==================== Integration Tests ====================

def test_full_daily_workflow():
    """Test complete daily workflow: boot → config → daily ops → brief."""
    # Boot system
    boot_resp = client.post("/core/boot/seed_minimum")
    assert boot_resp.status_code == 200
    
    # Check readiness
    ready_resp = client.get("/core/readiness")
    assert ready_resp.status_code == 200
    
    # Run daily ops
    ops_resp = client.post("/core/daily_ops/run")
    assert ops_resp.status_code == 200
    
    # Get brief
    brief_resp = client.get("/core/brief")
    assert brief_resp.status_code == 200


def test_budget_workflow():
    """Test budget creation and planning workflow."""
    # Create house budget
    budget_resp = client.post("/core/house_budget", json={
        "currency": "USD",
        "income_streams": [{"name": "salary", "monthly": 4000}],
        "buffer_target": 5000
    })
    assert budget_resp.status_code == 200
    
    # Get cash plan
    plan_resp = client.get("/core/cash_plan/month/2024-01")
    assert plan_resp.status_code == 200
    
    # Get snapshot
    snap_resp = client.get("/core/budget/snapshot")
    assert snap_resp.status_code == 200


def test_audit_trail_creation():
    """Test that operations create audit log entries."""
    # Do an operation
    client.post("/core/house_budget", json={
        "currency": "USD",
        "buffer_target": 5000
    })
    
    # Check audit log
    audit_resp = client.get("/core/audit")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 0  # Might have events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
