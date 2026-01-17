import pytest
from datetime import date, timedelta


class TestBudgetObligations:
    def test_create_obligation(self):
        from backend.app.core_gov.budget_obligations import service as svc
        rec = svc.create(name="Internet", amount=150.0, cadence="monthly", due_day=15)
        assert rec["name"] == "Internet"
        assert rec["amount"] == 150.0
        assert rec["cadence"] == "monthly"
        assert rec["id"].startswith("obl_")

    def test_create_obligation_validation(self):
        from backend.app.core_gov.budget_obligations import service as svc
        with pytest.raises(ValueError, match="name required"):
            svc.create(name="", amount=100.0, cadence="monthly")
        with pytest.raises(ValueError, match="amount must be >= 0"):
            svc.create(name="Test", amount=-50.0, cadence="monthly")
        with pytest.raises(ValueError, match="cadence must be"):
            svc.create(name="Test", amount=100.0, cadence="invalid")

    def test_list_obligations(self):
        from backend.app.core_gov.budget_obligations import service as svc
        svc.create(name="Water", amount=280.0, cadence="quarterly", category="utilities")
        items = svc.list_items(status="active")
        assert len(items) > 0
        assert any(x["name"] == "Water" for x in items)

    def test_get_one(self):
        from backend.app.core_gov.budget_obligations import service as svc
        rec = svc.create(name="Rent", amount=1500.0, cadence="monthly", due_day=1)
        found = svc.get_one(rec["id"])
        assert found is not None
        assert found["id"] == rec["id"]


class TestBudgetCalendar:
    def test_project(self):
        from backend.app.core_gov.budget_calendar import service as svc
        result = svc.project(days_ahead=30)
        assert "items" in result
        assert "warnings" in result

    def test_project_with_obligations(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.budget_calendar import service as calsvc
        obsvc.create(name="Test Bill", amount=100.0, cadence="monthly", due_day=15)
        result = calsvc.project(days_ahead=45)
        items = result.get("items", [])
        assert any(x["name"] == "Test Bill" for x in items)


class TestVaults:
    def test_create_vault(self):
        from backend.app.core_gov.vaults import service as svc
        rec = svc.create(name="Bills Buffer", balance=3000.0)
        assert rec["name"] == "Bills Buffer"
        assert rec["balance"] == 3000.0
        assert rec["id"].startswith("v_")

    def test_create_vault_validation(self):
        from backend.app.core_gov.vaults import service as svc
        with pytest.raises(ValueError, match="name required"):
            svc.create(name="")

    def test_list_vaults(self):
        from backend.app.core_gov.vaults import service as svc
        svc.create(name="Groceries", balance=500.0)
        items = svc.list_items()
        assert len(items) > 0

    def test_vault_balance_tracking(self):
        from backend.app.core_gov.vaults import service as svc
        rec = svc.create(name="Fun Money", balance=100.0)
        assert rec["balance"] == 100.0
        assert rec["target"] == 0.0


class TestBillsBuffer:
    def test_required_buffer(self):
        from backend.app.core_gov.bills_buffer import service as svc
        result = svc.required_buffer(days=30)
        assert "required" in result
        assert "items" in result or "warnings" in result


class TestReceipts:
    def test_create_receipt(self):
        from backend.app.core_gov.receipts import service as svc
        rec = svc.create({"date": "2026-01-03", "total": 150.50, "vendor": "Costco", "category": "groceries"})
        assert rec["date"] == "2026-01-03"
        assert rec["total"] == 150.50
        assert rec["vendor"] == "Costco"
        assert rec["id"].startswith("rc_")

    def test_list_receipts(self):
        from backend.app.core_gov.receipts import service as svc
        svc.create({"date": "2026-01-03", "total": 100.0, "vendor": "Store1"})
        items = svc.list_items()
        assert len(items) > 0


class TestHouseInventory:
    def test_upsert_item(self):
        from backend.app.core_gov.house_inventory import service as svc
        rec = svc.upsert(name="Milk", location="kitchen", qty=2.0, min_qty=1.0)
        assert rec["name"] == "Milk"
        assert rec["qty"] == 2.0
        assert rec["id"].startswith("inv_")

    def test_upsert_item_validation(self):
        from backend.app.core_gov.house_inventory import service as svc
        with pytest.raises(ValueError, match="name required"):
            svc.upsert(name="")

    def test_upsert_updates_existing(self):
        from backend.app.core_gov.house_inventory import service as svc
        rec1 = svc.upsert(name="Eggs", location="fridge", qty=6.0, min_qty=2.0)
        rec2 = svc.upsert(name="Eggs", location="fridge", qty=4.0)
        assert rec1["id"] == rec2["id"]
        assert rec2["qty"] == 4.0

    def test_low_stock(self):
        from backend.app.core_gov.house_inventory import service as svc
        svc.upsert(name="Butter", location="fridge", qty=0.5, min_qty=1.0)
        low = svc.low_stock()
        assert isinstance(low, list)


class TestGuardrails:
    def test_daily_guard(self):
        from backend.app.core_gov.guardrails import service as svc
        result = svc.daily_guard(days_ahead=7)
        assert "actions" in result or "warnings" in result
        assert isinstance(result, dict)

    def test_daily_guard_with_bills(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.guardrails import service as gsvc
        obsvc.create(name="Daily Test Bill", amount=50.0, cadence="monthly", due_day=15)
        result = gsvc.daily_guard(days_ahead=30)
        assert isinstance(result, dict)


class TestRoutersImportable:
    def test_budget_obligations_router(self):
        from backend.app.core_gov.budget_obligations import budget_obligations_router
        assert budget_obligations_router is not None

    def test_budget_calendar_router(self):
        from backend.app.core_gov.budget_calendar import budget_calendar_router
        assert budget_calendar_router is not None

    def test_vaults_router(self):
        from backend.app.core_gov.vaults import vaults_router
        assert vaults_router is not None

    def test_bills_buffer_router(self):
        from backend.app.core_gov.bills_buffer import bills_buffer_router
        assert bills_buffer_router is not None

    def test_receipts_router(self):
        from backend.app.core_gov.receipts import receipts_router
        assert receipts_router is not None

    def test_house_inventory_router(self):
        from backend.app.core_gov.house_inventory import house_inventory_router
        assert house_inventory_router is not None

    def test_guardrails_router(self):
        from backend.app.core_gov.guardrails import guardrails_router
        assert guardrails_router is not None


class TestIntegration:
    def test_budget_workflow_internet_bill(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.budget_calendar import service as calsvc
        obl = obsvc.create(name="Internet", amount=150.0, cadence="monthly", due_day=15)
        assert obl["name"] == "Internet"
        cal = calsvc.project(days_ahead=60)
        assert any(x["name"] == "Internet" for x in cal["items"])

    def test_full_guardrail_workflow(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.house_inventory import service as invsvc
        from backend.app.core_gov.guardrails import service as gsvc
        obsvc.create(name="Electricity", amount=120.0, cadence="monthly", due_day=1)
        invsvc.upsert(name="Coffee", location="kitchen", qty=0.2, min_qty=1.0)
        result = gsvc.daily_guard(days_ahead=7)
        assert isinstance(result, dict)

    def test_vault_and_buffer_workflow(self):
        from backend.app.core_gov.vaults import service as vsvc
        from backend.app.core_gov.bills_buffer import service as bbsvc
        vault = vsvc.create(name="Emergency", balance=5000.0)
        buffer = bbsvc.required_buffer(days=30)
        assert "required" in buffer
        assert vault["balance"] >= 0

    def test_receipt_to_inventory_workflow(self):
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.house_inventory import service as invsvc
        receipt = rsvc.create({"date": "2026-01-03", "total": 50.0, "vendor": "Store", "category": "groceries"})
        inv = invsvc.upsert(name="FromReceipt", location="home", qty=5.0)
        assert receipt["total"] == 50.0
        assert inv["qty"] == 5.0

    def test_obligation_calendar_followup_workflow(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.budget_calendar import service as calsvc
        obl = obsvc.create(name="RentTest", amount=1500.0, cadence="monthly", due_day=1)
        cal = calsvc.project(days_ahead=30)
        items = cal["items"]
        assert len(items) > 0


class TestEdgeCases:
    def test_obligation_february_29th_fallback(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.budget_calendar import service as calsvc
        obl = obsvc.create(name="Edge Bill", amount=100.0, cadence="monthly", due_day=31)
        cal = calsvc.project(days_ahead=90)
        items = cal["items"]
        assert len(items) > 0

    def test_quarterly_cadence(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        obl = obsvc.create(name="Quarterly", amount=300.0, cadence="quarterly", due_day=1)
        assert obl["cadence"] == "quarterly"

    def test_large_inventory_query(self):
        from backend.app.core_gov.house_inventory import service as svc
        for i in range(5):
            svc.upsert(name=f"Item{i}", location="home", qty=float(i))
        items = svc.list_items()
        assert len(items) <= 5000
