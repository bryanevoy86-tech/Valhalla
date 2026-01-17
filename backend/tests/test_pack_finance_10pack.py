import pytest
from datetime import date, timedelta
from io import StringIO


class TestLedger:
    def test_create_income(self):
        from backend.app.core_gov.ledger import service as svc
        rec = svc.create(kind="income", date="2026-01-03", amount=2000.0, description="Payday", category="salary")
        assert rec["kind"] == "income"
        assert rec["amount"] == 2000.0
        assert rec["id"].startswith("led_")

    def test_create_expense(self):
        from backend.app.core_gov.ledger import service as svc
        rec = svc.create(kind="expense", date="2026-01-03", amount=50.0, merchant="Grocery Store", description="Milk")
        assert rec["kind"] == "expense"
        assert rec["merchant"] == "Grocery Store"

    def test_list_by_kind(self):
        from backend.app.core_gov.ledger import service as svc
        svc.create(kind="income", date="2026-01-03", amount=1000.0)
        svc.create(kind="expense", date="2026-01-03", amount=100.0)
        items = svc.list_items(kind="income")
        assert any(x["kind"] == "income" for x in items)

    def test_summary(self):
        from backend.app.core_gov.ledger import service as svc
        svc.create(kind="income", date="2026-01-03", amount=5000.0)
        svc.create(kind="expense", date="2026-01-03", amount=2000.0)
        result = svc.summary()
        assert result["income"] >= 5000.0
        assert result["expense"] >= 2000.0
        assert result["net"] >= 3000.0


class TestBankAccounts:
    def test_create_account(self):
        from backend.app.core_gov.bank_accounts import service as svc
        rec = svc.create(name="Chequing", bank="TD Bank", account_type="chequing", country="CA", currency="CAD")
        assert rec["name"] == "Chequing"
        assert rec["bank"] == "TD Bank"
        assert rec["id"].startswith("acct_")

    def test_list_accounts(self):
        from backend.app.core_gov.bank_accounts import service as svc
        svc.create(name="Savings", bank="RBC", account_type="savings")
        items = svc.list_items()
        assert len(items) > 0
        assert any(x["name"] == "Savings" for x in items)

    def test_missing_name(self):
        from backend.app.core_gov.bank_accounts import service as svc
        with pytest.raises(ValueError, match="name required"):
            svc.create(name="", bank="TD")

    def test_missing_bank(self):
        from backend.app.core_gov.bank_accounts import service as svc
        with pytest.raises(ValueError, match="bank required"):
            svc.create(name="Chequing", bank="")


class TestTransactionImport:
    def test_import_csv_basic(self):
        from backend.app.core_gov.txn_import import service as svc
        csv_text = "date,amount,description,merchant\n2026-01-03,50.00,Milk,Grocery\n2026-01-04,100.00,Gas,Shell"
        result = svc.import_csv(csv_text=csv_text, date_col="date", amount_col="amount", desc_col="description", merchant_col="merchant")
        assert result["imported"] == 2
        assert len(result["items"]) == 2

    def test_import_csv_empty(self):
        from backend.app.core_gov.txn_import import service as svc
        with pytest.raises(ValueError, match="csv_text required"):
            svc.import_csv(csv_text="", date_col="date", amount_col="amount")

    def test_import_csv_negative_amounts(self):
        from backend.app.core_gov.txn_import import service as svc
        csv_text = "date,amount,description\n2026-01-03,-50.00,Expense"
        result = svc.import_csv(csv_text=csv_text, date_col="date", amount_col="amount", desc_col="description")
        assert result["imported"] == 1
        # negative amount should become positive with expense kind


class TestCategoryRules:
    def test_create_rule(self):
        from backend.app.core_gov.category_rules import service as svc
        rec = svc.create(match_field="merchant", contains="Grocery", category="groceries", priority=100)
        assert rec["match_field"] == "merchant"
        assert rec["contains"] == "Grocery"
        assert rec["category"] == "groceries"
        assert rec["id"].startswith("cr_")

    def test_apply_one_merchant(self):
        from backend.app.core_gov.category_rules import service as svc
        svc.create(match_field="merchant", contains="XyzMerchant999", category="xyz_category")
        result = svc.apply_one(merchant="XyzMerchant999 Store", description="")
        assert result == "xyz_category"

    def test_apply_one_description(self):
        from backend.app.core_gov.category_rules import service as svc
        svc.create(match_field="description", contains="AbcDesc888", category="abc_category")
        result = svc.apply_one(merchant="", description="Payment AbcDesc888 Monthly")
        assert result == "abc_category"

    def test_apply_one_no_match(self):
        from backend.app.core_gov.category_rules import service as svc
        result = svc.apply_one(merchant="UnknownStore", description="UnknownDesc")
        assert result == ""


class TestAllocationRules:
    def test_create_rule(self):
        from backend.app.core_gov.allocation_rules import service as svc
        splits = [
            {"vault_name": "Bills Buffer", "pct": 60},
            {"vault_name": "Groceries", "pct": 20},
            {"vault_name": "Fun", "pct": 10},
        ]
        rec = svc.create(name="Payday Split", splits=splits)
        assert rec["name"] == "Payday Split"
        assert len(rec["splits"]) == 3
        assert rec["id"].startswith("alr_")

    def test_split_pct_validation(self):
        from backend.app.core_gov.allocation_rules import service as svc
        splits = [{"vault_name": "Bills", "pct": 101}]
        with pytest.raises(ValueError, match="pct must be 0..100"):
            svc.create(name="Invalid", splits=splits)

    def test_split_total_validation(self):
        from backend.app.core_gov.allocation_rules import service as svc
        splits = [
            {"vault_name": "V1", "pct": 60},
            {"vault_name": "V2", "pct": 50},
        ]
        with pytest.raises(ValueError, match="split total must be <= 100"):
            svc.create(name="Invalid", splits=splits)

    def test_list_rules(self):
        from backend.app.core_gov.allocation_rules import service as svc
        svc.create(name="Rule1", splits=[{"vault_name": "V1", "pct": 100}])
        items = svc.list_items()
        assert len(items) > 0


class TestAllocationEngine:
    def test_preview(self):
        from backend.app.core_gov.allocation_rules import service as arule_svc
        from backend.app.core_gov.allocation_engine import service as aeng_svc
        splits = [{"vault_name": "Bills", "pct": 60}, {"vault_name": "Groceries", "pct": 40}]
        rule = arule_svc.create(name="Test", splits=splits)
        result = aeng_svc.preview(rule_id=rule["id"], amount=1000.0)
        assert result["amount"] == 1000.0
        assert len(result["allocations"]) == 2
        assert result["allocations"][0]["amount"] == 600.0
        assert result["allocations"][1]["amount"] == 400.0

    def test_preview_leftover(self):
        from backend.app.core_gov.allocation_rules import service as arule_svc
        from backend.app.core_gov.allocation_engine import service as aeng_svc
        splits = [{"vault_name": "Bills", "pct": 50}]
        rule = arule_svc.create(name="Test", splits=splits)
        result = aeng_svc.preview(rule_id=rule["id"], amount=1000.0)
        assert result["leftover"] == 500.0


class TestHouseCalendar:
    def test_create_event(self):
        from backend.app.core_gov.house_calendar import service as svc
        rec = svc.create(title="Water Bill", date="2026-01-10", category="bills", notes="Monthly check")
        assert rec["title"] == "Water Bill"
        assert rec["date"] == "2026-01-10"
        assert rec["id"].startswith("evt_")

    def test_list_events_by_date(self):
        from backend.app.core_gov.house_calendar import service as svc
        svc.create(title="Event1", date="2026-01-05")
        svc.create(title="Event2", date="2026-01-15")
        items = svc.list_items(date_from="2026-01-10", date_to="2026-01-20")
        assert any(x["title"] == "Event2" for x in items)

    def test_missing_title(self):
        from backend.app.core_gov.house_calendar import service as svc
        with pytest.raises(ValueError, match="title required"):
            svc.create(title="", date="2026-01-10")

    def test_missing_date(self):
        from backend.app.core_gov.house_calendar import service as svc
        with pytest.raises(ValueError, match="date required"):
            svc.create(title="Event", date="")


class TestHouseReminders:
    def test_create_followups(self):
        from backend.app.core_gov.house_reminders import service as svc
        result = svc.create_followups(days_ahead=7)
        assert "created" in result
        assert "warnings" in result


class TestShoppingList:
    def test_add_item(self):
        from backend.app.core_gov.shopping_list import service as svc
        rec = svc.add(item="Milk", qty=2.0, unit="liters", category="grocery", priority="normal")
        assert rec["item"] == "Milk"
        assert rec["qty"] == 2.0
        assert rec["id"].startswith("shp_")

    def test_list_items(self):
        from backend.app.core_gov.shopping_list import service as svc
        svc.add(item="Eggs", category="grocery")
        items = svc.list_items(category="grocery")
        assert len(items) > 0
        assert any(x["item"] == "Eggs" for x in items)

    def test_mark_bought(self):
        from backend.app.core_gov.shopping_list import service as svc
        rec = svc.add(item="Bread")
        updated = svc.mark(item_id=rec["id"], status="bought")
        assert updated["status"] == "bought"

    def test_missing_item(self):
        from backend.app.core_gov.shopping_list import service as svc
        with pytest.raises(ValueError, match="item required"):
            svc.add(item="")


class TestBigPurchases:
    def test_create_purchase(self):
        from backend.app.core_gov.big_purchases import service as svc
        rec = svc.create(title="New Mattress", target_amount=1200.0, target_date="2026-06-01", vault_name="Reserves", priority="normal")
        assert rec["title"] == "New Mattress"
        assert rec["target_amount"] == 1200.0
        assert rec["id"].startswith("bp_")

    def test_list_purchases(self):
        from backend.app.core_gov.big_purchases import service as svc
        svc.create(title="Laptop", target_amount=1500.0)
        items = svc.list_items()
        assert len(items) > 0
        assert any(x["title"] == "Laptop" for x in items)

    def test_missing_title(self):
        from backend.app.core_gov.big_purchases import service as svc
        with pytest.raises(ValueError, match="title required"):
            svc.create(title="", target_amount=1000.0)

    def test_invalid_target_amount(self):
        from backend.app.core_gov.big_purchases import service as svc
        with pytest.raises(ValueError, match="target_amount must be > 0"):
            svc.create(title="Item", target_amount=0)


class TestRoutersImportable:
    def test_ledger_router(self):
        from backend.app.core_gov.ledger import ledger_router
        assert ledger_router is not None

    def test_bank_accounts_router(self):
        from backend.app.core_gov.bank_accounts import bank_accounts_router
        assert bank_accounts_router is not None

    def test_txn_import_router(self):
        from backend.app.core_gov.txn_import import txn_import_router
        assert txn_import_router is not None

    def test_category_rules_router(self):
        from backend.app.core_gov.category_rules import category_rules_router
        assert category_rules_router is not None

    def test_allocation_rules_router(self):
        from backend.app.core_gov.allocation_rules import allocation_rules_router
        assert allocation_rules_router is not None

    def test_allocation_engine_router(self):
        from backend.app.core_gov.allocation_engine import allocation_engine_router
        assert allocation_engine_router is not None

    def test_house_calendar_router(self):
        from backend.app.core_gov.house_calendar import house_calendar_router
        assert house_calendar_router is not None

    def test_house_reminders_router(self):
        from backend.app.core_gov.house_reminders import house_reminders_router
        assert house_reminders_router is not None

    def test_shopping_list_router(self):
        from backend.app.core_gov.shopping_list import shopping_list_router
        assert shopping_list_router is not None

    def test_big_purchases_router(self):
        from backend.app.core_gov.big_purchases import big_purchases_router
        assert big_purchases_router is not None


class TestIntegration:
    def test_full_ledger_workflow(self):
        from backend.app.core_gov.ledger import service as svc
        svc.create(kind="income", date="2026-01-03", amount=5000.0, description="Payday")
        svc.create(kind="expense", date="2026-01-03", amount=100.0, description="Groceries")
        svc.create(kind="expense", date="2026-01-04", amount=50.0, description="Gas")
        items = svc.list_items()
        assert len(items) >= 3
        summary = svc.summary()
        assert summary["count"] >= 3

    def test_category_rule_workflow(self):
        from backend.app.core_gov.category_rules import service as svc
        svc.create(match_field="merchant", contains="Walmart", category="retail", priority=50)
        svc.create(match_field="merchant", contains="Costco", category="bulk", priority=40)
        cat1 = svc.apply_one(merchant="Walmart Supercenter", description="")
        cat2 = svc.apply_one(merchant="Costco Warehouse", description="")
        assert cat1 == "retail"
        assert cat2 == "bulk"

    def test_shopping_list_workflow(self):
        from backend.app.core_gov.shopping_list import service as svc
        svc.add(item="Milk", priority="high", category="grocery")
        svc.add(item="Bread", priority="normal", category="grocery")
        svc.add(item="Butter", priority="low", category="dairy")
        items = svc.list_items(status="open")
        assert len(items) >= 3
        high_priority = [x for x in items if x.get("priority") == "high"]
        assert len(high_priority) >= 1

    def test_big_purchase_workflow(self):
        from backend.app.core_gov.big_purchases import service as svc
        svc.create(title="Sofa", target_amount=2000.0, target_date="2026-06-01", priority="high")
        svc.create(title="TV", target_amount=1500.0, target_date="2026-08-01", priority="normal")
        items = svc.list_items()
        assert len(items) >= 2

    def test_allocation_rule_workflow(self):
        from backend.app.core_gov.allocation_rules import service as svc
        splits = [
            {"vault_name": "Bills Buffer", "pct": 60},
            {"vault_name": "Groceries", "pct": 20},
            {"vault_name": "Fun", "pct": 20},
        ]
        rule = svc.create(name="Monthly Allocation", splits=splits)
        assert rule["name"] == "Monthly Allocation"
        items = svc.list_items()
        assert len(items) > 0
