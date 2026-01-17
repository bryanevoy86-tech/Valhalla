"""
Tests for P8 deployment: 20 new PACKs
- P-UNDERWRITE-1..6: Property underwriting with ARV, repairs, wholesale MAO, BRRRR offer, risk summary
- P-BILLS-1..6: Household bills registry, due calculator, reminders, autopay, payment log, scheduler tick
- P-BUDGET-1..3: Budget categories, monthly snapshot, buffer checks
- P-PIPE-1..4: Deal→Comms pipeline runner, sent sync, daily tick, scheduler integration
- P-JV-5..7: JV board filtering with subject_id, readonly with token filtering, token creation guard
"""
import pytest
import os
import json
from datetime import date, timedelta


class TestUnderwriterModule:
    """P-UNDERWRITE-1..6 tests"""
    
    def test_underwriter_init_exists(self):
        assert os.path.exists("backend/app/core_gov/underwriter/__init__.py")
    
    def test_underwriter_calc_exists(self):
        assert os.path.exists("backend/app/core_gov/underwriter/calc.py")
    
    def test_underwriter_router_exists(self):
        assert os.path.exists("backend/app/core_gov/underwriter/router.py")
    
    def test_underwriter_deal_link_exists(self):
        assert os.path.exists("backend/app/core_gov/underwriter/deal_link.py")
    
    def test_underwriter_deal_mao_exists(self):
        assert os.path.exists("backend/app/core_gov/underwriter/deal_mao.py")
    
    def test_underwriter_risk_exists(self):
        assert os.path.exists("backend/app/core_gov/underwriter/risk.py")
    
    def test_underwriter_imports(self):
        from backend.app.core_gov.underwriter import underwriter_router
        assert underwriter_router is not None
    
    def test_calc_wholesale_mao_function(self):
        from backend.app.core_gov.underwriter.calc import calc_wholesale_mao
        result = calc_wholesale_mao(arv=100000, repairs=10000)
        assert "mao" in result
        assert result["model"] == "wholesale_70_rule_v1"
    
    def test_calc_brrrr_offer_function(self):
        from backend.app.core_gov.underwriter.calc import calc_brrrr_offer
        result = calc_brrrr_offer(arv=100000, repairs=10000)
        assert "max_offer" in result
        assert result["model"] == "brrrr_ltv_v1"


class TestBillsModule:
    """P-BILLS-1..6 tests"""
    
    def test_bills_init_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/__init__.py")
    
    def test_bills_store_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/store.py")
    
    def test_bills_router_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/router.py")
    
    def test_bills_due_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/due.py")
    
    def test_bills_reminders_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/reminders.py")
    
    def test_bills_autopay_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/autopay.py")
    
    def test_bills_pay_log_exists(self):
        assert os.path.exists("backend/app/core_gov/bills/pay_log.py")
    
    def test_bills_imports(self):
        from backend.app.core_gov.bills import bills_router
        assert bills_router is not None
    
    def test_bills_store_new_id(self):
        from backend.app.core_gov.bills import store
        bill_id = store.new_id()
        assert bill_id.startswith("bill_")


class TestBudgetModule:
    """P-BUDGET-1..3 tests"""
    
    def test_budget_snapshot_exists(self):
        assert os.path.exists("backend/app/core_gov/budget/snapshot.py")
    
    def test_budget_buffer_exists(self):
        assert os.path.exists("backend/app/core_gov/budget/buffer.py")
    
    def test_budget_router_updated(self):
        """Budget router should exist with monthly snapshot/budget support"""
        assert os.path.exists("backend/app/core_gov/budget/router.py")
    
    def test_snapshot_function(self):
        from backend.app.core_gov.budget.snapshot import snapshot
        result = snapshot()
        assert "budget" in result
        assert "bills_monthly_est" in result


class TestPipelineModule:
    """P-PIPE-1..4 tests"""
    
    def test_pipeline_init_exists(self):
        assert os.path.exists("backend/app/core_gov/pipeline/__init__.py")
    
    def test_pipeline_store_exists(self):
        assert os.path.exists("backend/app/core_gov/pipeline/store.py")
    
    def test_pipeline_service_exists(self):
        assert os.path.exists("backend/app/core_gov/pipeline/service.py")
    
    def test_pipeline_router_exists(self):
        assert os.path.exists("backend/app/core_gov/pipeline/router.py")
    
    def test_pipeline_sent_exists(self):
        assert os.path.exists("backend/app/core_gov/pipeline/sent.py")
    
    def test_pipeline_daily_exists(self):
        assert os.path.exists("backend/app/core_gov/pipeline/daily.py")
    
    def test_pipeline_imports(self):
        from backend.app.core_gov.pipeline import pipeline_router
        assert pipeline_router is not None
    
    def test_pipeline_store_new_id(self):
        from backend.app.core_gov.pipeline import store
        run_id = store.new_id()
        assert run_id.startswith("run_")


class TestPropertyARV:
    """P-UNDERWRITE-3 tests"""
    
    def test_property_arv_exists(self):
        assert os.path.exists("backend/app/core_gov/property/arv.py")
    
    def test_property_router_has_arv_import(self):
        with open("backend/app/core_gov/property/router.py", "r") as f:
            content = f.read()
            assert "from .arv import set_arv" in content
    
    def test_property_router_has_arv_endpoint(self):
        with open("backend/app/core_gov/property/router.py", "r") as f:
            content = f.read()
            assert "set_arv_ep" in content or "/arv" in content


class TestJVFiltering:
    """P-JV-5..7 tests"""
    
    def test_jv_filtering_exists(self):
        assert os.path.exists("backend/app/core_gov/jv_board/filtering.py")
    
    def test_jv_readonly_uses_filtering(self):
        with open("backend/app/core_gov/jv_board/readonly.py", "r") as f:
            content = f.read()
            assert "filtering" in content or "filter_board" in content
    
    def test_share_tokens_router_updated(self):
        with open("backend/app/core_gov/share_tokens/router.py", "r") as f:
            content = f.read()
            assert "subject_id required for jv_board" in content
    
    def test_filtering_function(self):
        from backend.app.core_gov.jv_board.filtering import filter_board
        board = {"deals": [{"partner_id": "p1"}, {"partner_id": "p2"}]}
        filtered = filter_board(board, subject_id="p1")
        assert len(filtered.get("deals", [])) <= 1


class TestSchedulerIntegration:
    """P-PIPE-4, P-BILLS-6 scheduler integration tests"""
    
    def test_scheduler_service_updated(self):
        with open("backend/app/core_gov/scheduler/service.py", "r") as f:
            content = f.read()
            assert "bills_push" in content or "bills" in content
            assert "pipe_tick" in content or "pipeline" in content


class TestOpsBoardV5:
    """P-OPSBOARD-5 tests"""
    
    def test_ops_board_service_updated(self):
        with open("backend/app/core_gov/ops_board/service.py", "r") as f:
            content = f.read()
            assert "bills_upcoming" in content
            assert "budget_snapshot" in content
            assert "pipeline_recent" in content


class TestCoreWiring:
    """P-WIRING-3 tests"""
    
    def test_core_router_imports_underwriter(self):
        with open("backend/app/core_gov/core_router.py", "r") as f:
            content = f.read()
            assert "underwriter_router" in content
    
    def test_core_router_imports_bills(self):
        with open("backend/app/core_gov/core_router.py", "r") as f:
            content = f.read()
            assert "bills_router" in content
    
    def test_core_router_imports_pipeline(self):
        with open("backend/app/core_gov/core_router.py", "r") as f:
            content = f.read()
            assert "pipeline_router" in content
    
    def test_core_router_includes_underwriter(self):
        with open("backend/app/core_gov/core_router.py", "r") as f:
            content = f.read()
            assert "core.include_router(underwriter_router)" in content
    
    def test_core_router_includes_bills(self):
        with open("backend/app/core_gov/core_router.py", "r") as f:
            content = f.read()
            assert "core.include_router(bills_router)" in content
    
    def test_core_router_includes_pipeline(self):
        with open("backend/app/core_gov/core_router.py", "r") as f:
            content = f.read()
            assert "core.include_router(pipeline_router)" in content


class TestModuleImports:
    """Module-wide import verification"""
    
    def test_all_module_imports(self):
        """Test all module imports work"""
        from backend.app.core_gov.underwriter import underwriter_router
        from backend.app.core_gov.bills import bills_router
        from backend.app.core_gov.budget import budget_router
        from backend.app.core_gov.pipeline import pipeline_router
        
        assert underwriter_router is not None
        assert bills_router is not None
        assert budget_router is not None
        assert pipeline_router is not None


class TestCountAndCoverage:
    """Comprehensive coverage of all 20 PACKs"""
    
    def test_pack_count(self):
        """Verify all 20 PACKs are deployed"""
        packs = [
            "underwriter/__init__.py",
            "underwriter/calc.py",
            "underwriter/router.py",
            "underwriter/deal_link.py",
            "underwriter/deal_mao.py",
            "underwriter/risk.py",
            "bills/__init__.py",
            "bills/store.py",
            "bills/router.py",
            "bills/due.py",
            "bills/reminders.py",
            "bills/autopay.py",
            "bills/pay_log.py",
            "budget/snapshot.py",
            "budget/buffer.py",
            "pipeline/__init__.py",
            "pipeline/store.py",
            "pipeline/service.py",
            "pipeline/router.py",
            "pipeline/sent.py",
            "pipeline/daily.py",
            "property/arv.py",
            "jv_board/filtering.py",
        ]
        
        core_path = "backend/app/core_gov"
        for pack in packs:
            full_path = os.path.join(core_path, pack)
            assert os.path.exists(full_path), f"Missing {pack}"
