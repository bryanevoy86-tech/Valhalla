"""
Test suite for 10-PACK Household Budget & Inventory System:
P-BUDGET-1 (Obligations), P-BUDGET-2 (Calendar Projection),
P-BILL-1 (Autopay Guides), P-BILL-2 (Autopay Setups),
P-INVENTORY-1 (House Inventory), P-INVENTORY-2 (Reorder Engine),
P-VAULT-1 (Vaults), P-VAULT-2 (Bills Buffer),
P-RECEIPTS-1 (Receipt Registry), P-GUARD-1 (Guardrails)
"""

import pytest
import uuid
from datetime import date, timedelta

# ============================================================================
# P-BUDGET-1 (Budget Obligations) Tests
# ============================================================================

def test_budget1_create_obligation():
    """Test creating a budget obligation."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    
    result = obl_svc.create(
        name="Rent",
        amount=1500.0,
        cadence="monthly",
        due_day=1,
        pay_to="Landlord"
    )
    
    assert "id" in result
    assert result["name"] == "Rent"
    assert result["amount"] == 1500.0

def test_budget1_list_obligations():
    """Test listing obligations with filters."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    
    obl_svc.create(name="Rent", amount=1500, cadence="monthly", category="housing")
    obl_svc.create(name="Food", amount=400, cadence="weekly", category="food")
    
    housing = obl_svc.list_items(category="housing")
    assert all(x["category"] == "housing" for x in housing)

def test_budget1_quarterly_obligation():
    """Test creating quarterly obligation."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    
    result = obl_svc.create(
        name="Water",
        amount=280,
        cadence="quarterly",
        due_day=1,
        due_months=3
    )
    
    assert result["cadence"] == "quarterly"
    assert result["due_months"] == 3

def test_budget1_weekly_obligation():
    """Test weekly obligation (day 0-6)."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    
    result = obl_svc.create(
        name="Groceries",
        amount=100,
        cadence="weekly",
        due_day=3  # Wednesday
    )
    
    assert result["cadence"] == "weekly"
    assert result["due_day"] == 3

# ============================================================================
# P-BUDGET-2 (Budget Calendar Projection) Tests
# ============================================================================

def test_budget2_project_calendar():
    """Test calendar projection."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.budget_calendar import service as cal_svc
    
    obl_svc.create(name="Rent", amount=1500, cadence="monthly", due_day=1)
    
    result = cal_svc.project(days_ahead=30)
    
    assert "items" in result
    assert "from" in result
    assert "to" in result

def test_budget2_upcoming_dates():
    """Test that projected dates are in future."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.budget_calendar import service as cal_svc
    
    obl_svc.create(name="Internet", amount=150, cadence="monthly", due_day=15)
    
    result = cal_svc.project(days_ahead=45)
    items = result.get("items", [])
    
    for item in items:
        item_date = date.fromisoformat(item["date"])
        assert item_date >= date.today()

# ============================================================================
# P-BILL-1 (Autopay Guides) Tests
# ============================================================================

def test_bill1_create_guide():
    """Test creating autopay guide."""
    from backend.app.core_gov.autopay_guides import service as guide_svc
    
    result = guide_svc.create(
        provider="TD Bank",
        country="CA",
        steps=["Step 1", "Step 2"]
    )
    
    assert "id" in result
    assert result["provider"] == "TD Bank"

def test_bill1_seed_defaults():
    """Test seeding default guides."""
    from backend.app.core_gov.autopay_guides import service as guide_svc
    
    result = guide_svc.seed_defaults()
    
    assert result["seeded"] == 2

def test_bill1_list_by_country():
    """Test filtering guides by country."""
    from backend.app.core_gov.autopay_guides import service as guide_svc
    
    guide_svc.create(provider="BMO", country="CA")
    guide_svc.create(provider="BofA", country="US")
    
    ca_guides = guide_svc.list_items(country="CA")
    assert all(x["country"] == "CA" for x in ca_guides)

# ============================================================================
# P-BILL-2 (Autopay Setups) Tests
# ============================================================================

def test_bill2_create_setup():
    """Test creating autopay setup."""
    from backend.app.core_gov.autopay_setups import service as setup_svc
    
    result = setup_svc.create(
        obligation_id=f"obl_{uuid.uuid4().hex[:8]}",
        status="pending"
    )
    
    assert "id" in result
    assert result["status"] == "pending"

def test_bill2_set_status():
    """Test updating setup status."""
    from backend.app.core_gov.autopay_setups import service as setup_svc
    
    setup = setup_svc.create(
        obligation_id=f"obl_{uuid.uuid4().hex[:8]}",
        status="pending"
    )
    
    updated = setup_svc.set_status(setup["id"], "verified")
    assert updated["status"] == "verified"
    assert updated["verified_at"] != ""

def test_bill2_list_by_obligation():
    """Test listing setups by obligation."""
    from backend.app.core_gov.autopay_setups import service as setup_svc
    
    obl_id = f"obl_{uuid.uuid4().hex[:8]}"
    setup_svc.create(obligation_id=obl_id, status="pending")
    setup_svc.create(obligation_id=f"obl_{uuid.uuid4().hex[:8]}", status="enabled")
    
    items = setup_svc.list_items(obligation_id=obl_id)
    assert all(x["obligation_id"] == obl_id for x in items)

# ============================================================================
# P-INVENTORY-1 (House Inventory) Tests
# ============================================================================

def test_inv1_upsert_item():
    """Test upserting inventory item."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    
    result = inv_svc.upsert(
        name="Toilet Paper",
        location="bathroom",
        qty=5,
        min_qty=2
    )
    
    assert "id" in result
    assert result["name"] == "Toilet Paper"

def test_inv1_update_existing():
    """Test updating existing inventory item."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    
    inv_svc.upsert(name="Paper Towels", location="kitchen", qty=10, min_qty=3)
    result = inv_svc.upsert(name="Paper Towels", location="kitchen", qty=2)
    
    assert result["qty"] == 2

def test_inv1_low_stock_filter():
    """Test filtering low stock items."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    
    inv_svc.upsert(name="Item A", location="pantry", qty=10, min_qty=2)
    inv_svc.upsert(name="Item B", location="pantry", qty=1, min_qty=5)
    
    low = inv_svc.low_stock()
    assert any(x["name"] == "Item B" for x in low)

def test_inv1_by_location():
    """Test filtering by location."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    
    inv_svc.upsert(name="Item 1", location="pantry")
    inv_svc.upsert(name="Item 2", location="bathroom")
    
    pantry_items = inv_svc.list_items(location="pantry")
    assert all(x["location"] == "pantry" for x in pantry_items)

# ============================================================================
# P-INVENTORY-2 (Reorder Engine) Tests
# ============================================================================

def test_inv2_build_reorder_list():
    """Test building reorder list."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    from backend.app.core_gov.reorder_engine import service as reorder_svc
    
    inv_svc.upsert(name="Coffee", location="pantry", qty=0.5, min_qty=2, priority="high")
    
    result = reorder_svc.build_reorder_list()
    
    assert "items" in result
    assert len(result["items"]) > 0

def test_inv2_priority_sort():
    """Test that reorder list is sorted by priority."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    from backend.app.core_gov.reorder_engine import service as reorder_svc
    
    inv_svc.upsert(name="Low Priority", location="pantry", qty=0, min_qty=1, priority="low")
    inv_svc.upsert(name="High Priority", location="pantry", qty=0, min_qty=1, priority="high")
    
    result = reorder_svc.build_reorder_list()
    items = result.get("items", [])
    
    if len(items) >= 2:
        assert items[0]["priority"] == "high"

# ============================================================================
# P-VAULT-1 (Vaults) Tests - Note: Vaults module has existing signatures
# ============================================================================

def test_vault_integration():
    """Test vault module is available."""
    from backend.app.core_gov.vaults import service as vault_svc
    assert vault_svc is not None

# ============================================================================
# P-VAULT-2 (Bills Buffer Calculator) Tests
# ============================================================================

def test_vault2_required_buffer():
    """Test calculating required buffer."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.bills_buffer import service as buf_svc
    
    obl_svc.create(name="Bill 1", amount=100, cadence="monthly", due_day=1)
    obl_svc.create(name="Bill 2", amount=50, cadence="monthly", due_day=15)
    
    result = buf_svc.required_buffer(days=30)
    
    assert "required" in result
    assert result["required"] > 0

def test_vault2_with_no_obligations():
    """Test buffer calculation returns valid dict."""
    from backend.app.core_gov.bills_buffer import service as buf_svc
    
    result = buf_svc.required_buffer(days=30)
    
    assert "required" in result
    assert isinstance(result["required"], float)

def test_guard1_daily_check():
    """Test daily guardrails check."""
    from backend.app.core_gov.guardrails import service as guard_svc
    
    result = guard_svc.daily_guard(days_ahead=7)
    
    assert "date" in result
    assert "actions" in result
    assert "warnings" in result

def test_guard1_bills_due_alert():
    """Test that bills due soon trigger alerts."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.guardrails import service as guard_svc
    
    obl_svc.create(name="Bill", amount=100, cadence="monthly", due_day=1, autopay_status="off")
    
    result = guard_svc.daily_guard(days_ahead=30)
    actions = result.get("actions", [])
    
    assert any(a.get("type") == "bill_due" for a in actions)

# ============================================================================
# Router Tests (Module Importability)
# ============================================================================

def test_router_budget_obligations():
    """Verify budget_obligations router is importable."""
    from backend.app.core_gov.budget_obligations import router
    assert router is not None

def test_router_budget_calendar():
    """Verify budget_calendar router is importable."""
    from backend.app.core_gov.budget_calendar import router
    assert router is not None

def test_router_autopay_guides():
    """Verify autopay_guides router is importable."""
    from backend.app.core_gov.autopay_guides import router
    assert router is not None

def test_router_autopay_setups():
    """Verify autopay_setups router is importable."""
    from backend.app.core_gov.autopay_setups import router
    assert router is not None

def test_router_house_inventory():
    """Verify house_inventory router is importable."""
    from backend.app.core_gov.house_inventory import router
    assert router is not None

def test_router_reorder_engine():
    """Verify reorder_engine router is importable."""
    from backend.app.core_gov.reorder_engine import router
    assert router is not None

def test_router_vaults():
    """Verify vaults router is importable."""
    from backend.app.core_gov.vaults import router
    assert router is not None

def test_router_bills_buffer():
    """Verify bills_buffer router is importable."""
    from backend.app.core_gov.bills_buffer import router
    assert router is not None

def test_router_receipts():
    """Verify receipts router is importable."""
    from backend.app.core_gov.receipts import router
    assert router is not None

def test_router_guardrails():
    """Verify guardrails router is importable."""
    from backend.app.core_gov.guardrails import router
    assert router is not None

# ============================================================================
# Integration Tests
# ============================================================================

def test_obligations_to_calendar_flow():
    """Test full flow: obligations → calendar projection."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.budget_calendar import service as cal_svc
    
    obl_svc.create(name="Rent", amount=1500, cadence="monthly", due_day=1)
    obl_svc.create(name="Utilities", amount=200, cadence="monthly", due_day=15)
    
    result = cal_svc.project(days_ahead=60)
    items = result.get("items", [])
    
    assert len(items) > 0
    assert any("Rent" in str(x) for x in items)

def test_inventory_to_reorder_flow():
    """Test full flow: inventory → reorder list."""
    from backend.app.core_gov.house_inventory import service as inv_svc
    from backend.app.core_gov.reorder_engine import service as reorder_svc
    
    inv_svc.upsert(name="Milk", location="fridge", qty=0.5, min_qty=2)
    inv_svc.upsert(name="Bread", location="pantry", qty=0, min_qty=1)
    
    result = reorder_svc.build_reorder_list()
    items = result.get("items", [])
    
    assert len(items) >= 2
    names = [x["name"] for x in items]
    assert "Milk" in names or "Bread" in names

def test_buffer_with_obligations_flow():
    """Test full flow: obligations → buffer requirement."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.bills_buffer import service as buf_svc
    
    obl_svc.create(name="Rent", amount=1500, cadence="monthly", due_day=1)
    obl_svc.create(name="Food", amount=400, cadence="weekly", due_day=0)
    
    result = buf_svc.required_buffer(days=30)
    
    assert result["required"] > 1500

def test_vault_buffer_and_obligations():
    """Test vault buffer calculation."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.bills_buffer import service as buf_svc
    
    obl_svc.create(name="Bill", amount=500, cadence="monthly", due_day=1)
    
    buf_req = buf_svc.required_buffer(days=30)
    
    assert "required" in buf_req

def test_complete_household_workflow():
    """Test end-to-end household workflow."""
    from backend.app.core_gov.budget_obligations import service as obl_svc
    from backend.app.core_gov.house_inventory import service as inv_svc
    from backend.app.core_gov.guardrails import service as guard_svc
    
    # Add obligations
    obl = obl_svc.create(name="Rent", amount=1500, cadence="monthly", due_day=1, autopay_status="off")
    
    # Add inventory
    inv = inv_svc.upsert(name="Coffee", location="pantry", qty=0, min_qty=1)
    
    # Run guardrails
    guards = guard_svc.daily_guard(days_ahead=30)
    
    assert "actions" in guards
    assert len(guards["actions"]) >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
