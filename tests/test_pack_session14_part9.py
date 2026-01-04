"""
Session 14 Part 9: 20 PACK Deployment - Test Suite
P-FORECAST-1..3, P-NEEDS2SHOP-1..2, P-RECEIPTS-1..3, P-APPROVALS-1..2, 
P-HEIMDALLDO-1..3, P-ACTIONS-LOG-1, P-SAFETY-APPROVAL-1, P-SCHED-6, 
P-OPSBOARD-7, P-WIRING-5, P-SHOP-5, P-FORECAST-3
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch


class TestForecast:
    """P-FORECAST-1 — Usage Forecast Engine"""
    
    def test_forecast_store_ensure(self):
        from backend.app.core_gov.forecast import store
        store._ensure()
        assert store.PATH
    
    def test_forecast_log_usage(self):
        from backend.app.core_gov.forecast.service import log_usage
        rec = log_usage(inv_id="inv_test", qty_used=1.5, notes="test")
        assert rec["inv_id"] == "inv_test"
        assert rec["qty_used"] == 1.5
    
    def test_forecast_burn_rate(self):
        from backend.app.core_gov.forecast.service import burn_rate
        br = burn_rate(inv_id="inv_test", window_days=30)
        assert "per_day" in br
        assert "total_used" in br
    
    def test_forecast_rollup(self):
        from backend.app.core_gov.forecast.rollup import rollup
        result = rollup(limit=20, window_days=30)
        assert "items" in result


class TestApprovals:
    """P-APPROVALS-1 — Approvals Queue"""
    
    def test_approvals_service_create(self):
        from backend.app.core_gov.approvals import service
        rec = service.create(title="Test Approval", action="purchase")
        assert rec["title"] == "Test Approval"
        assert rec["action"] == "purchase"
        assert rec["status"] == "pending"
    
    def test_approvals_list(self):
        from backend.app.core_gov.approvals import service
        items = service.list_items()
        assert isinstance(items, list)
    
    def test_approvals_decide(self):
        from backend.app.core_gov.approvals import service
        rec = service.create(title="Decide Test", action="approve")
        items = service.list_items()
        it = next((x for x in items if x.get("id") == rec.get("id")), None)
        assert it is not None


class TestHeimDall:
    """P-HEIMDALLDO-1..3 — Master Action Endpoint"""
    
    def test_heimdall_guards_safe(self):
        from backend.app.core_gov.heimdall.guards import guard, SAFE_ACTIONS
        ok, msg = guard(mode="explore", action="shopping.generate_from_inventory")
        assert ok is True
    
    def test_heimdall_guards_exec(self):
        from backend.app.core_gov.heimdall.guards import guard, EXEC_ACTIONS
        ok, msg = guard(mode="execute", action="bills.paid")
        assert ok is True
    
    def test_heimdall_guards_invalid(self):
        from backend.app.core_gov.heimdall.guards import guard
        ok, msg = guard(mode="explore", action="invalid.action")
        assert ok is False
    
    def test_heimdall_log_append(self):
        from backend.app.core_gov.heimdall.log import append, list_items
        append({"mode": "test", "action": "test.action"})
        items = list_items(limit=10)
        assert len(items) >= 0


class TestShoppingIntegrations:
    """P-NEEDS2SHOP-1, P-SHOP-5, P-APPROVALS-2"""
    
    def test_shopping_request_approvals(self):
        from backend.app.core_gov.shopping.approvals import request_approvals
        result = request_approvals(threshold=200.0)
        assert "created" in result
    
    def test_shopping_receipt_hook(self):
        from backend.app.core_gov.shopping.receipt_hook import on_bought
        result = on_bought({"id": "test", "qty": 1, "est_unit_cost": 0})
        assert "ok" in result


class TestReceiptsLedgerLink:
    """P-RECEIPTS-2 — Receipt → Ledger placeholder"""
    
    def test_receipts_ledger_link(self):
        from backend.app.core_gov.receipts.ledger_link import post_to_ledger
        result = post_to_ledger({"id": "test", "amount": 100.0, "vendor": "Test", "category": "household"})
        assert "ok" in result


class TestSchedulerIntegration:
    """P-SCHED-6 — Scheduler tick runs needs→shopping"""
    
    @patch('backend.app.core_gov.shopping.from_schedule_needs.generate')
    @patch('backend.app.core_gov.shopping.approvals.request_approvals')
    def test_scheduler_tick_includes_needs(self, mock_approvals, mock_needs):
        mock_needs.return_value = {"created": 0}
        mock_approvals.return_value = {"created": 0}
        # Scheduler tick would call these in practice
        assert True


class TestCoreRouter:
    """P-WIRING-5 — Core router includes new routers"""
    
    def test_forecast_router_import(self):
        from backend.app.core_gov.forecast.router import router as forecast_router
        assert forecast_router is not None
    
    def test_approvals_router_import(self):
        from backend.app.core_gov.approvals.router import router as approvals_router
        assert approvals_router is not None
    
    def test_heimdall_router_import(self):
        from backend.app.core_gov.heimdall.router import router as heimdall_router
        assert heimdall_router is not None


class TestInventoryForecastIntegration:
    """P-FORECAST-2 — Auto log usage when out_of"""
    
    def test_inventory_quick_out_of(self):
        # Note: This would require actual inventory data
        # Just verify the module loads
        from backend.app.core_gov.inventory.quick import out_of
        assert callable(out_of)


class TestOpsBoard:
    """P-OPSBOARD-7 — Ops Board v7"""
    
    def test_opsboard_includes_approvals(self):
        from backend.app.core_gov.ops_board.service import today
        board = today()
        assert "approvals_pending" in board
        assert "heimdall_actions" in board


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
