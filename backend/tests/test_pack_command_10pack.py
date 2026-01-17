import pytest
from datetime import date, timedelta


class TestBillPayments:
    def test_mark_paid(self):
        from backend.app.core_gov.bill_payments import service as svc
        rec = svc.mark_paid(obligation_id="obl_123", paid_date="2026-01-03", amount=150.0, method="manual", confirmation="abc123")
        assert rec["obligation_id"] == "obl_123"
        assert rec["amount"] == 150.0
        assert rec["id"].startswith("pay_")

    def test_mark_paid_with_method(self):
        from backend.app.core_gov.bill_payments import service as svc
        rec = svc.mark_paid(obligation_id="obl_456", paid_date="2026-01-05", amount=50.0, method="autopay")
        assert rec["method"] == "autopay"

    def test_list_by_obligation(self):
        from backend.app.core_gov.bill_payments import service as svc
        svc.mark_paid(obligation_id="obl_xyz", paid_date="2026-01-03", amount=100.0)
        items = svc.list_items(obligation_id="obl_xyz")
        assert any(x["obligation_id"] == "obl_xyz" for x in items)

    def test_missing_obligation_id(self):
        from backend.app.core_gov.bill_payments import service as svc
        with pytest.raises(ValueError, match="obligation_id required"):
            svc.mark_paid(obligation_id="", paid_date="2026-01-03", amount=100.0)


class TestReconcile:
    def test_suggest(self):
        from backend.app.core_gov.reconcile import service as svc
        # Test with non-existent bank transaction (should return empty suggestions)
        result = svc.suggest(bank_txn_id="nonexistent_id")
        assert "bank_txn_id" in result
        assert "suggestions" in result
        assert "warnings" in result


class TestAutopayVerify:
    def test_verify(self):
        from backend.app.core_gov.autopay_verify import service as svc
        result = svc.verify(days_back=7, days_ahead=7)
        assert "flagged" in result
        assert "warnings" in result


class TestMonthlyClose:
    def test_close_month(self):
        from backend.app.core_gov.monthly_close import service as svc
        rec = svc.close(month="2026-01")
        assert rec["month"] == "2026-01"
        assert rec["id"].startswith("mcl_")
        assert "ledger" in rec
        assert "bills_buffer" in rec

    def test_invalid_month(self):
        from backend.app.core_gov.monthly_close import service as svc
        with pytest.raises(ValueError, match="month required"):
            svc.close(month="")

    def test_list_closes(self):
        from backend.app.core_gov.monthly_close import service as svc
        svc.close(month="2025-12")
        items = svc.list_items()
        assert len(items) > 0


class TestExports:
    def test_export_bundle_ledger(self):
        from backend.app.core_gov.exports import service as svc
        result = svc.export_bundle(keys=["ledger"])
        assert "bundle" in result
        assert "ledger" in result["bundle"]

    def test_export_bundle_multiple(self):
        from backend.app.core_gov.exports import service as svc
        result = svc.export_bundle(keys=["ledger", "budget_obligations"])
        assert "bundle" in result

    def test_export_unknown_key(self):
        from backend.app.core_gov.exports import service as svc
        result = svc.export_bundle(keys=["unknown_key"])
        assert "unknown key" in str(result.get("warnings"))


class TestCsvExport:
    def test_ledger_to_csv(self):
        from backend.app.core_gov.csv_export import service as svc
        result = svc.ledger_to_csv()
        assert "csv" in result
        assert "count" in result
        assert "id,kind,date" in result["csv"]

    def test_ledger_to_csv_with_dates(self):
        from backend.app.core_gov.csv_export import service as svc
        result = svc.ledger_to_csv(date_from="2026-01-01", date_to="2026-01-31")
        assert "csv" in result


class TestTaxBuckets:
    def test_create_bucket(self):
        from backend.app.core_gov.tax_buckets import service as svc
        rec = svc.create(code="HOME_OFFICE_001", name="Home Office", risk="safe", notes="work from home")
        assert rec["code"] == "HOME_OFFICE_001"
        assert rec["risk"] == "safe"
        assert rec["id"].startswith("txb_")

    def test_seed_defaults(self):
        from backend.app.core_gov.tax_buckets import service as svc
        result = svc.seed_defaults()
        assert result["seeded"] == 8

    def test_list_buckets(self):
        from backend.app.core_gov.tax_buckets import service as svc
        items = svc.list_items()
        assert len(items) > 0

    def test_invalid_risk(self):
        from backend.app.core_gov.tax_buckets import service as svc
        with pytest.raises(ValueError, match="risk must be safe"):
            svc.create(code="TEST", name="Test", risk="unknown")

    def test_missing_code(self):
        from backend.app.core_gov.tax_buckets import service as svc
        with pytest.raises(ValueError, match="code required"):
            svc.create(code="", name="Test")


class TestTaxTagging:
    def test_tag_ledger(self):
        from backend.app.core_gov.ledger import service as lsvc
        from backend.app.core_gov.tax_tagging import service as tsvc
        rec = lsvc.create(kind="expense", date="2026-01-03", amount=50.0, description="office supplies")
        tagged = tsvc.tag_ledger(ledger_id=rec["id"], tax_code="HOME_OFFICE")
        assert tagged["meta"]["tax_code"] == "HOME_OFFICE"

    def test_tag_ledger_not_found(self):
        from backend.app.core_gov.tax_tagging import service as svc
        with pytest.raises(KeyError):
            svc.tag_ledger(ledger_id="nonexistent", tax_code="HOME_OFFICE")


class TestIntentRouter:
    def test_add_bill_intent(self):
        from backend.app.core_gov.intent_router import service as svc
        result = svc.handle_intent("add_bill", {"name": "Internet", "amount": 150, "cadence": "monthly", "due_day": 15})
        assert result["name"] == "Internet"
        assert result["amount"] == 150.0

    def test_add_item_intent(self):
        from backend.app.core_gov.intent_router import service as svc
        result = svc.handle_intent("add_item", {"item": "Milk", "qty": 2, "priority": "high"})
        assert result["item"] == "Milk"
        assert result["qty"] == 2.0

    def test_add_event_intent(self):
        from backend.app.core_gov.intent_router import service as svc
        result = svc.handle_intent("add_event", {"title": "Dentist", "date": "2026-01-15", "time": "10:00"})
        assert result["title"] == "Dentist"

    def test_set_goal_intent(self):
        from backend.app.core_gov.intent_router import service as svc
        result = svc.handle_intent("set_goal", {"title": "New Laptop", "target_amount": 1500, "priority": "high"})
        assert result["title"] == "New Laptop"

    def test_unknown_intent(self):
        from backend.app.core_gov.intent_router import service as svc
        with pytest.raises(ValueError, match="unknown intent"):
            svc.handle_intent("unknown_intent", {})


class TestTextCommands:
    def test_parse_bill_command(self):
        from backend.app.core_gov.text_commands import service as svc
        result = svc.parse("Internet 150 on 15")
        assert result["intent"] == "add_bill"
        assert result["payload"]["name"] == "Internet"
        assert result["payload"]["amount"] == 150.0
        assert result["payload"]["due_day"] == 15

    def test_parse_bill_with_ordinal(self):
        from backend.app.core_gov.text_commands import service as svc
        result = svc.parse("Phone 50 on 1st")
        assert result["intent"] == "add_bill"
        assert result["payload"]["due_day"] == 1

    def test_parse_add_item_command(self):
        from backend.app.core_gov.text_commands import service as svc
        result = svc.parse("add Milk")
        assert result["intent"] == "add_item"
        assert result["payload"]["item"] == "Milk"

    def test_parse_event_command(self):
        from backend.app.core_gov.text_commands import service as svc
        result = svc.parse("event Dentist 2026-01-15 10:00")
        assert result["intent"] == "add_event"
        assert result["payload"]["title"] == "Dentist"
        assert result["payload"]["date"] == "2026-01-15"
        assert result["payload"]["time"] == "10:00"

    def test_parse_event_without_time(self):
        from backend.app.core_gov.text_commands import service as svc
        result = svc.parse("event Doctor 2026-02-01")
        assert result["intent"] == "add_event"
        assert result["payload"]["date"] == "2026-02-01"

    def test_parse_unknown_command(self):
        from backend.app.core_gov.text_commands import service as svc
        result = svc.parse("unknown command here")
        assert result["intent"] == "unknown"


class TestRoutersImportable:
    def test_bill_payments_router(self):
        from backend.app.core_gov.bill_payments import bill_payments_router
        assert bill_payments_router is not None

    def test_reconcile_router(self):
        from backend.app.core_gov.reconcile import reconcile_router
        assert reconcile_router is not None

    def test_autopay_verify_router(self):
        from backend.app.core_gov.autopay_verify import autopay_verify_router
        assert autopay_verify_router is not None

    def test_monthly_close_router(self):
        from backend.app.core_gov.monthly_close import monthly_close_router
        assert monthly_close_router is not None

    def test_exports_router(self):
        from backend.app.core_gov.exports import exports_router
        assert exports_router is not None

    def test_csv_export_router(self):
        from backend.app.core_gov.csv_export import csv_export_router
        assert csv_export_router is not None

    def test_tax_buckets_router(self):
        from backend.app.core_gov.tax_buckets import tax_buckets_router
        assert tax_buckets_router is not None

    def test_tax_tagging_router(self):
        from backend.app.core_gov.tax_tagging import tax_tagging_router
        assert tax_tagging_router is not None

    def test_intent_router_router(self):
        from backend.app.core_gov.intent_router import intent_router_router
        assert intent_router_router is not None

    def test_text_commands_router(self):
        from backend.app.core_gov.text_commands import text_commands_router
        assert text_commands_router is not None


class TestIntegration:
    def test_bill_payment_workflow(self):
        from backend.app.core_gov.budget_obligations import service as obsvc
        from backend.app.core_gov.bill_payments import service as psvc
        obl = obsvc.create(name="Internet", amount=150.0, cadence="monthly", due_day=15)
        payment = psvc.mark_paid(obligation_id=obl["id"], paid_date="2026-01-15", amount=150.0, method="manual")
        assert payment["obligation_id"] == obl["id"]
        items = psvc.list_items(obligation_id=obl["id"])
        assert any(x["id"] == payment["id"] for x in items)

    def test_text_to_intent_workflow(self):
        from backend.app.core_gov.text_commands import service as tsvc
        from backend.app.core_gov.intent_router import service as isvc
        parsed = tsvc.parse("Internet 150 on 15")
        assert parsed["intent"] == "add_bill"
        # would apply intent next
        result = isvc.handle_intent(parsed["intent"], parsed["payload"])
        assert result["name"] == "Internet"

    def test_monthly_close_workflow(self):
        from backend.app.core_gov.monthly_close import service as svc
        rec = svc.close(month="2026-01")
        items = svc.list_items()
        assert rec["month"] in [x["month"] for x in items]

    def test_tax_tagging_workflow(self):
        from backend.app.core_gov.tax_buckets import service as bsvc
        from backend.app.core_gov.ledger import service as lsvc
        from backend.app.core_gov.tax_tagging import service as tsvc
        bsvc.seed_defaults()
        led = lsvc.create(kind="expense", date="2026-01-03", amount=200.0, description="home office furniture")
        tagged = tsvc.tag_ledger(ledger_id=led["id"], tax_code="HOME_OFFICE")
        assert "tax_code" in tagged["meta"]

    def test_export_workflow(self):
        from backend.app.core_gov.exports import service as svc
        result = svc.export_bundle(keys=["ledger", "budget_obligations"])
        assert "ledger" in result["bundle"]
        assert "budget_obligations" in result["bundle"]
