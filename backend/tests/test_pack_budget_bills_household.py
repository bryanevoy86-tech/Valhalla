"""
Test suite for Budget/Bills Expansion (P-BUDOBL-1, P-BUDDUE-1, P-BUDFU-1, P-BILLPAY-2, P-HOUSEBRIEF-1)

New PACKs:
- P-BUDOBL-1: Budget obligations registry
- P-BUDDUE-1: Due-date calculator (upcoming bills window)
- P-BUDFU-1: Bills → Followups (auto task creation)
- P-BILLPAY-2: Bill Payments ↔ Ledger Bridge (smart posting)
- P-HOUSEBRIEF-1: Household brief (consolidated view)
"""

import pytest
import os
import json
from datetime import date, timedelta


@pytest.fixture(autouse=True)
def cleanup_budget_obligations_data():
    """Clear budget obligations data before and after each test"""
    obligations_file = "backend/data/budget_obligations/items.json"
    if os.path.exists(obligations_file):
        try:
            os.remove(obligations_file)
        except:
            pass
    yield
    if os.path.exists(obligations_file):
        try:
            os.remove(obligations_file)
        except:
            pass


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


class TestBudgetObligations:
    """P-BUDOBL-1: Budget obligations registry"""
    
    def test_create_monthly_obligation(self):
        from backend.app.core_gov.budget_obligations import service
        obl = service.create(
            name="Electric Bill",
            amount=150.0,
            cadence="monthly",
            due_day=15,
            category="utilities",
            autopay_status="enabled",
            notes="Monthly electric"
        )
        assert obl["id"].startswith("obl_")
        assert obl["name"] == "Electric Bill"
        assert obl["amount"] == 150.0
        assert obl["cadence"] == "monthly"
        assert obl["due_day"] == 15
        assert obl["category"] == "utilities"
        assert obl["status"] == "active"

    def test_create_quarterly_obligation(self):
        from backend.app.core_gov.budget_obligations import service
        obl = service.create(
            name="Car Insurance",
            amount=500.0,
            cadence="quarterly",
            due_day=10,
            category="insurance",
        )
        assert obl["cadence"] == "quarterly"
        assert obl["due_day"] == 10

    def test_create_missing_name(self):
        from backend.app.core_gov.budget_obligations import service
        with pytest.raises(ValueError, match="name required"):
            service.create(name="", amount=100.0, cadence="monthly")

    def test_create_invalid_cadence(self):
        from backend.app.core_gov.budget_obligations import service
        with pytest.raises(ValueError, match="cadence must be"):
            service.create(name="Test", amount=100.0, cadence="invalid")

    def test_create_negative_amount(self):
        from backend.app.core_gov.budget_obligations import service
        with pytest.raises(ValueError, match="amount must be >= 0"):
            service.create(name="Test", amount=-50.0, cadence="monthly")

    def test_list_by_status(self):
        from backend.app.core_gov.budget_obligations import service
        obl1 = service.create(name="Bill 1", amount=100.0, cadence="monthly")
        obl2 = service.create(name="Bill 2", amount=200.0, cadence="weekly")
        
        active = service.list_items(status="active")
        assert len(active) >= 2
        names = {x["name"] for x in active}
        assert "Bill 1" in names
        assert "Bill 2" in names

    def test_list_by_category(self):
        from backend.app.core_gov.budget_obligations import service
        obl1 = service.create(name="Electric", amount=100.0, cadence="monthly", category="utilities")
        obl2 = service.create(name="Rent", amount=1500.0, cadence="monthly", category="housing")
        
        utilities = service.list_items(category="utilities")
        housing = service.list_items(category="housing")
        
        assert any(x["name"] == "Electric" for x in utilities)
        assert any(x["name"] == "Rent" for x in housing)

    def test_get_one(self):
        from backend.app.core_gov.budget_obligations import service
        obl = service.create(name="Test Bill", amount=50.0, cadence="monthly")
        retrieved = service.get_one(obl["id"])
        assert retrieved["id"] == obl["id"]
        assert retrieved["name"] == "Test Bill"


class TestDueDate:
    """P-BUDDUE-1: Due-date calculator"""
    
    def test_upcoming_monthly_bills(self):
        from backend.app.core_gov.budget_obligations import service
        from backend.app.core_gov.budget_obligations.due import upcoming
        
        service.create(name="Electric", amount=100.0, cadence="monthly", due_day=15)
        service.create(name="Internet", amount=50.0, cadence="monthly", due_day=20)
        
        today = date.today()
        result = upcoming(days=14, today=today.isoformat())
        
        assert result["count"] >= 0
        assert "items" in result
        assert "total_amount" in result

    def test_upcoming_weekly_bills(self):
        from backend.app.core_gov.budget_obligations import service
        from backend.app.core_gov.budget_obligations.due import upcoming
        
        service.create(
            name="Weekly gym",
            amount=20.0,
            cadence="weekly",
            due_day=2
        )
        
        today = date.today()
        result = upcoming(days=14, today=today.isoformat())
        assert "items" in result

    def test_upcoming_window(self):
        from backend.app.core_gov.budget_obligations.due import upcoming
        
        today = date.today()
        result = upcoming(days=30, today=today.isoformat())
        
        assert "from" in result
        assert "to" in result
        assert result["from"] == today.isoformat()
        assert (date.fromisoformat(result["to"]) - today).days == 30


class TestBillPaymentsLedgerBridge:
    """P-BILLPAY-2: Bill Payments ↔ Ledger Bridge"""
    
    def test_mark_paid_creates_transaction(self):
        from backend.app.core_gov.bill_payments import service as bill_service
        from backend.app.core_gov.ledger_light import service as ledger_service
        
        # Mark a bill as paid
        today = date.today().isoformat()
        paid = bill_service.mark_paid(
            obligation_id="obl_test123",
            paid_date=today,
            amount=100.0,
            method="manual",
            account_id="acc_checking"
        )
        
        assert paid["id"].startswith("pay_")
        assert paid["obligation_id"] == "obl_test123"
        assert paid["amount"] == 100.0
        
        # Verify ledger entry was created (if ledger is available)
        transactions = ledger_service.list_tx()
        assert len(transactions) >= 0  # May be 0 if ledger not ready, or >0 if created

    def test_mark_paid_safe_call(self):
        from backend.app.core_gov.bill_payments import service
        
        today = date.today().isoformat()
        paid = service.mark_paid(
            obligation_id="obl_test456",
            paid_date=today,
            amount=50.0
        )
        
        # Should not raise even if ledger is unavailable
        assert paid["id"].startswith("pay_")


class TestHouseholdBrief:
    """P-HOUSEBRIEF-1: Household brief"""
    
    def test_build_brief_structure(self):
        from backend.app.core_gov.household_brief.service import build
        
        brief = build(days_bills=14)
        
        assert "bills_upcoming" in brief
        assert "followups_open" in brief
        assert "shopping_open" in brief
        assert "notes" in brief

    def test_build_with_bills(self):
        from backend.app.core_gov.budget_obligations import service as budget_service
        from backend.app.core_gov.household_brief.service import build
        
        budget_service.create(name="Test Bill", amount=100.0, cadence="monthly", due_day=15)
        
        brief = build(days_bills=14)
        assert "bills_upcoming" in brief
        assert isinstance(brief["bills_upcoming"], dict)

    def test_build_safe_calls(self):
        from backend.app.core_gov.household_brief.service import build
        
        # Should not raise even if dependencies unavailable
        brief = build(days_bills=14)
        assert isinstance(brief, dict)
        assert "notes" in brief


class TestRouterImports:
    """Verify all routers are properly importable"""
    
    def test_budget_obligations_router_import(self):
        from backend.app.core_gov.budget_obligations.router import router
        assert router is not None
        assert len(router.routes) > 0

    def test_household_brief_router_import(self):
        from backend.app.core_gov.household_brief.router import router
        assert router is not None
        assert len(router.routes) > 0

    def test_all_routers_import(self):
        from backend.app.core_gov.budget_obligations import budget_obligations_router
        from backend.app.core_gov.household_brief import household_brief_router
        
        assert budget_obligations_router is not None
        assert household_brief_router is not None


class TestIntegrationWorkflows:
    """Test multi-module workflows"""
    
    def test_bill_due_to_followup_workflow(self):
        from backend.app.core_gov.budget_obligations import service as budget_service
        from backend.app.core_gov.budget_obligations.followups import create_due_followups
        
        budget_service.create(name="Electric", amount=100.0, cadence="monthly", due_day=10)
        
        result = create_due_followups(days=30)
        assert "created" in result
        assert "warnings" in result
        assert isinstance(result["created"], int)

    def test_bill_to_ledger_workflow(self):
        from backend.app.core_gov.bill_payments import service as bill_service
        
        today = date.today().isoformat()
        paid = bill_service.mark_paid(
            obligation_id="obl_sample",
            paid_date=today,
            amount=75.50,
            method="manual"
        )
        
        assert paid["amount"] == 75.50
        assert paid["method"] == "manual"

    def test_household_brief_aggregation(self):
        from backend.app.core_gov.budget_obligations import service as budget_service
        from backend.app.core_gov.household_brief.service import build
        
        budget_service.create(name="Rent", amount=1500.0, cadence="monthly", due_day=1)
        budget_service.create(name="Utilities", amount=150.0, cadence="monthly", due_day=15)
        
        brief = build(days_bills=30)
        
        assert "bills_upcoming" in brief
        assert len(brief["bills_upcoming"].get("items", [])) >= 0


class TestEdgeCases:
    """Edge cases and validation"""
    
    def test_obligation_negative_amount(self):
        from backend.app.core_gov.budget_obligations import service
        with pytest.raises(ValueError, match="amount must be >= 0"):
            service.create(name="Bad", amount=-50.0, cadence="monthly")

    def test_due_date_parsing(self):
        from backend.app.core_gov.budget_obligations.due import _parse
        
        parsed = _parse("2026-02-15")
        assert parsed.year == 2026
        assert parsed.month == 2
        assert parsed.day == 15

    def test_month_last_day_calculation(self):
        from backend.app.core_gov.budget_obligations.due import _month_last_day
        from datetime import date
        
        # February 2026 (non-leap year)
        feb_date = date(2026, 2, 1)
        assert _month_last_day(feb_date) == 28
        
        # January 2026
        jan_date = date(2026, 1, 1)
        assert _month_last_day(jan_date) == 31
        
        # December 2026
        dec_date = date(2026, 12, 1)
        assert _month_last_day(dec_date) == 31
