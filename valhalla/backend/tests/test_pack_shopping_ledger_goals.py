"""
Test suite for 10-PACK Financial/Shopping System Expansion (P-SHOP-1 through P-PROP-1)

New PACKs:
- P-SHOP-1: Shopping list management
- P-SHOP-2: Shopping to followups integration
- P-ACCTS-1: Accounts registry
- P-LEDGERL-1: Simple transactions
- P-LEDGERL-2: Monthly reports
- P-BILLPAY-1: Bill payments with proof
- P-GOALS-1: Goals and big purchases
- P-HCAL-1: Household calendar
- P-AUTOPAY-1: Autopay setup checklist
- P-PROP-1: Property intel scaffolding
"""

import pytest
import os
import json


@pytest.fixture(autouse=True)
def cleanup_ledger_data():
    """Clear ledger data before and after each test"""
    ledger_file = "backend/data/ledger_light/tx.json"
    if os.path.exists(ledger_file):
        try:
            os.remove(ledger_file)
        except:
            pass
    yield
    if os.path.exists(ledger_file):
        try:
            os.remove(ledger_file)
        except:
            pass


@pytest.fixture(autouse=True)
def cleanup_accounts_data():
    """Clear accounts data before and after each test"""
    accounts_file = "backend/data/accounts/items.json"
    if os.path.exists(accounts_file):
        try:
            os.remove(accounts_file)
        except:
            pass
    yield
    if os.path.exists(accounts_file):
        try:
            os.remove(accounts_file)
        except:
            pass


@pytest.fixture(autouse=True)
def cleanup_goals_data():
    """Clear goals data before and after each test"""
    goals_file = "backend/data/goals/items.json"
    if os.path.exists(goals_file):
        try:
            os.remove(goals_file)
        except:
            pass
    yield
    if os.path.exists(goals_file):
        try:
            os.remove(goals_file)
        except:
            pass


@pytest.fixture(autouse=True)
def cleanup_shopping_data():
    """Clear shopping data before and after each test"""
    shopping_file = "backend/data/shopping_list/items.json"
    if os.path.exists(shopping_file):
        try:
            os.remove(shopping_file)
        except:
            pass
    yield
    if os.path.exists(shopping_file):
        try:
            os.remove(shopping_file)
        except:
            pass


class TestShoppingList:
    """P-SHOP-1: Shopping list management"""
    
    def test_add_basic_item(self):
        from backend.app.core_gov.shopping_list import service
        item = service.add(item="Milk", category="grocery", priority="normal", qty=2.0)
        assert item["id"].startswith("shp_")
        assert item["item"] == "Milk"
        assert item["category"] == "grocery"
        assert item["priority"] == "normal"
        assert item["qty"] == 2.0
        assert item["status"] == "open"

    def test_add_item_missing_required(self):
        from backend.app.core_gov.shopping_list import service
        with pytest.raises(ValueError, match="item required"):
            service.add(item="")

    def test_list_items_by_status(self):
        from backend.app.core_gov.shopping_list import service
        item1 = service.add(item="Bread", priority="high")
        item2 = service.add(item="Butter", priority="low")
        service.mark(item_id=item1["id"], status="done")
        
        open_items = service.list_items(status="open")
        assert len(open_items) > 0
        assert all(x["status"] == "open" for x in open_items)

    def test_mark_item_done(self):
        from backend.app.core_gov.shopping_list import service
        item = service.add(item="Coffee", priority="high")
        updated = service.mark(item_id=item["id"], status="done")
        assert updated["status"] == "done"


class TestShoppingToFollowups:
    """P-SHOP-2: Shopping to followups integration"""
    
    def test_to_followups_safe_call(self):
        from backend.app.core_gov.shopping_list import service, ops
        item = service.add(item="Laundry Detergent", priority="high")
        result = ops.to_followups(status="open")
        assert "created" in result
        assert "warnings" in result


class TestAccounts:
    """P-ACCTS-1: Accounts registry"""
    
    def test_create_account(self):
        from backend.app.core_gov.accounts import service
        acc = service.create(
            name="Chequing Account",
            kind="chequing",
            currency="CAD",
            masked="****1234"
        )
        assert acc["id"].startswith("acc_")
        assert acc["name"] == "Chequing Account"
        assert acc["kind"] == "chequing"
        assert acc["currency"] == "CAD"

    def test_create_account_missing_name(self):
        from backend.app.core_gov.accounts import service
        with pytest.raises(ValueError, match="name required"):
            service.create(name="")

    def test_list_accounts_by_status(self):
        from backend.app.core_gov.accounts import service
        acc1 = service.create(name="Active Account")
        acc2 = service.create(name="Inactive Account", status="inactive")
        
        active = service.list_items(status="active")
        assert any(x["id"] == acc1["id"] for x in active)


class TestLedgerLight:
    """P-LEDGERL-1: Simple transactions"""
    
    def test_create_transaction(self):
        from backend.app.core_gov.ledger_light import service
        tx = service.create(
            date_str="2026-01-15",
            kind="income",
            amount=5000.0,
            description="Salary deposit",
            category="income"
        )
        assert tx["id"].startswith("tx_")
        assert tx["date"] == "2026-01-15"
        assert tx["kind"] == "income"
        assert tx["amount"] == 5000.0

    def test_create_transaction_invalid_kind(self):
        from backend.app.core_gov.ledger_light import service
        with pytest.raises(ValueError, match="kind must be"):
            service.create(date_str="2026-01-15", kind="invalid", amount=100.0)

    def test_create_transaction_negative_amount(self):
        from backend.app.core_gov.ledger_light import service
        with pytest.raises(ValueError, match="amount must be >= 0"):
            service.create(date_str="2026-01-15", kind="income", amount=-100.0)

    def test_list_transactions_by_kind(self):
        from backend.app.core_gov.ledger_light import service
        service.create(date_str="2026-01-15", kind="income", amount=1000.0)
        service.create(date_str="2026-01-15", kind="expense", amount=50.0)
        
        income_tx = service.list_tx(kind="income")
        assert all(x["kind"] == "income" for x in income_tx)


class TestLedgerReports:
    """P-LEDGERL-2: Ledger reports"""
    
    def test_month_summary(self):
        from backend.app.core_gov.ledger_light import service, reports
        service.create(date_str="2026-02-10", kind="income", amount=5000.0)
        service.create(date_str="2026-02-15", kind="expense", amount=100.0, category="groceries")
        
        summary = reports.month_summary("2026-02")
        assert summary["month"] == "2026-02"
        assert summary["income"] == 5000.0

    def test_expense_by_category(self):
        from backend.app.core_gov.ledger_light import service, reports
        service.create(date_str="2026-03-10", kind="expense", amount=100.0, category="groceries")
        service.create(date_str="2026-03-20", kind="expense", amount=30.0, category="utilities")
        
        summary = reports.month_summary("2026-03")
        cats = {x["category"]: x["total"] for x in summary["expense_by_category"]}
        assert "groceries" in cats or "utilities" in cats


class TestGoals:
    """P-GOALS-1: Goals and big purchases"""
    
    def test_create_goal(self):
        from backend.app.core_gov.goals import service
        goal = service.create(
            title="New Car",
            target_amount=50000.0,
            due_date="2027-12-31",
            priority="high"
        )
        assert goal["id"].startswith("gol_")
        assert goal["title"] == "New Car"
        assert goal["target_amount"] == 50000.0

    def test_create_goal_missing_title(self):
        from backend.app.core_gov.goals import service
        with pytest.raises(ValueError, match="title required"):
            service.create(title="", target_amount=1000.0)

    def test_create_goal_negative_amount(self):
        from backend.app.core_gov.goals import service
        with pytest.raises(ValueError, match="target_amount must be >= 0"):
            service.create(title="Goal", target_amount=-1000.0)

    def test_create_goal_invalid_priority(self):
        from backend.app.core_gov.goals import service
        with pytest.raises(ValueError, match="priority must be"):
            service.create(title="Goal", target_amount=5000.0, priority="urgent")


class TestAutopayChecklist:
    """P-AUTOPAY-1: Autopay setup checklist"""
    
    def test_build_autopay_checklist(self):
        from backend.app.core_gov.autopay_checklists import service
        checklist = service.build_for_obligation(obligation_id="obl_test")
        assert "obligation_id" in checklist
        assert "steps" in checklist
        assert len(checklist["steps"]) == 5

    def test_checklist_structure(self):
        from backend.app.core_gov.autopay_checklists import service
        checklist = service.build_for_obligation(obligation_id="obl_xyz")
        for step in checklist["steps"]:
            assert "step" in step
            assert "title" in step
            assert "done" in step
            assert "notes" in step

    def test_autopay_checklist_missing_id(self):
        from backend.app.core_gov.autopay_checklists import service
        with pytest.raises(ValueError, match="obligation_id required"):
            service.build_for_obligation(obligation_id="")


class TestRouterImports:
    """Verify all routers can be imported"""
    
    def test_shopping_list_router_importable(self):
        from backend.app.core_gov.shopping_list import shopping_list_router
        assert shopping_list_router is not None

    def test_accounts_router_importable(self):
        from backend.app.core_gov.accounts import accounts_router
        assert accounts_router is not None

    def test_ledger_light_router_importable(self):
        from backend.app.core_gov.ledger_light import ledger_light_router
        assert ledger_light_router is not None

    def test_bill_payments_router_importable(self):
        from backend.app.core_gov.bill_payments import bill_payments_router
        assert bill_payments_router is not None

    def test_goals_router_importable(self):
        from backend.app.core_gov.goals import goals_router
        assert goals_router is not None

    def test_house_calendar_router_importable(self):
        from backend.app.core_gov.house_calendar import house_calendar_router
        assert house_calendar_router is not None

    def test_autopay_checklists_router_importable(self):
        from backend.app.core_gov.autopay_checklists import autopay_checklists_router
        assert autopay_checklists_router is not None

    def test_property_intel_router_importable(self):
        from backend.app.core_gov.property_intel import property_intel_router
        assert property_intel_router is not None


class TestIntegrationWorkflows:
    """Cross-module integration tests"""
    
    def test_shopping_list_workflow(self):
        from backend.app.core_gov.shopping_list import service as shop_svc
        item = shop_svc.add(item="Groceries", category="grocery", qty=1.0)
        assert item["id"].startswith("shp_")

    def test_goal_tracking(self):
        from backend.app.core_gov.goals import service as goal_svc
        goal = goal_svc.create(
            title="Vacation Fund",
            target_amount=3000.0
        )
        assert goal["target_amount"] == 3000.0

    def test_ledger_flow(self):
        from backend.app.core_gov.ledger_light import service as ledger_svc
        tx = ledger_svc.create(
            date_str="2026-01-15",
            kind="income",
            amount=1000.0
        )
        assert tx["kind"] == "income"


class TestEdgeCases:
    """Edge cases and boundary conditions"""
    
    def test_shopping_list_special_characters(self):
        from backend.app.core_gov.shopping_list import service
        item = service.add(item="Café au lait & pastries")
        assert "Café" in item["item"]

    def test_transaction_large_amount(self):
        from backend.app.core_gov.ledger_light import service
        tx = service.create(
            date_str="2026-01-15",
            kind="transfer",
            amount=9999999.99
        )
        assert tx["amount"] == 9999999.99

    def test_account_long_name(self):
        from backend.app.core_gov.accounts import service
        long_name = "Very Long Account Name " * 3
        acc = service.create(name=long_name)
        assert long_name.strip() in acc["name"]
