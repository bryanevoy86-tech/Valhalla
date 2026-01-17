"""
Comprehensive unit tests for P-RECEIPTS-1, P-CATS-1, P-BUDGET-6, P-TAXRISK-1, P-REPORT-1
Testing receipts, categorization, actuals, tax risk, and reporting functionality.
"""
import pytest
import json
import os
from datetime import date, timedelta
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data before and after each test."""
    yield
    # Cleanup
    for data_dir in ["backend/data/receipts", "backend/data/categorizer", "backend/data/reports"]:
        if os.path.exists(data_dir):
            for f in os.listdir(data_dir):
                try:
                    os.remove(os.path.join(data_dir, f))
                except:
                    pass


# ============================================================================
# P-RECEIPTS-1: RECEIPT VAULT TESTS
# ============================================================================

class TestReceiptVault:
    """P-RECEIPTS-1: Receipt registry CRUD."""

    def test_receipt_create(self):
        """Test creating a receipt."""
        from backend.app.core_gov.receipts import service
        
        payload = {
            "vendor": "Real Canadian Superstore",
            "date": "2026-01-03",
            "total": 87.22,
            "tax": 0,
            "source": "manual",
            "notes": "weekly groceries",
        }
        receipt = service.create(payload)
        
        assert receipt["id"].startswith("rc_")
        assert receipt["vendor"] == "Real Canadian Superstore"
        assert receipt["total"] == 87.22
        assert receipt["status"] == "new"

    def test_receipt_list_items(self):
        """Test listing receipts."""
        from backend.app.core_gov.receipts import service
        
        service.create({"vendor": "Store A", "date": "2026-01-01", "total": 50.0})
        service.create({"vendor": "Store B", "date": "2026-01-02", "total": 75.0})
        
        items = service.list_items()
        assert len(items) == 2

    def test_receipt_filter_by_status(self):
        """Test filtering receipts by status."""
        from backend.app.core_gov.receipts import service
        
        r1 = service.create({"vendor": "Store A", "date": "2026-01-01", "total": 50.0, "status": "new"})
        r2 = service.create({"vendor": "Store B", "date": "2026-01-02", "total": 75.0, "status": "categorized"})
        
        new_items = service.list_items(status="new")
        assert len(new_items) == 1

    def test_receipt_filter_by_vendor(self):
        """Test filtering receipts by vendor (substring)."""
        from backend.app.core_gov.receipts import service
        
        service.create({"vendor": "Real Canadian Superstore", "date": "2026-01-01", "total": 50.0})
        service.create({"vendor": "Costco", "date": "2026-01-02", "total": 100.0})
        
        results = service.list_items(vendor="superstore")
        assert len(results) == 1

    def test_receipt_get_one(self):
        """Test retrieving a single receipt."""
        from backend.app.core_gov.receipts import service
        
        receipt = service.create({"vendor": "Store", "date": "2026-01-01", "total": 50.0})
        retrieved = service.get_one(receipt["id"])
        
        assert retrieved is not None
        assert retrieved["id"] == receipt["id"]

    def test_receipt_patch(self):
        """Test patching a receipt."""
        from backend.app.core_gov.receipts import service
        
        receipt = service.create({"vendor": "Store", "date": "2026-01-01", "total": 50.0})
        patched = service.patch(receipt["id"], {"category": "groceries", "status": "categorized"})
        
        assert patched["category"] == "groceries"
        assert patched["status"] == "categorized"

    def test_receipt_create_missing_vendor(self):
        """Test receipt creation fails without vendor."""
        from backend.app.core_gov.receipts import service
        
        with pytest.raises(ValueError, match="vendor is required"):
            service.create({"date": "2026-01-01", "total": 50.0})


# ============================================================================
# P-CATS-1: CATEGORIZATION RULES TESTS
# ============================================================================

class TestCategorizer:
    """P-CATS-1: Categorization rules and receipt categorization."""

    def test_rule_create(self):
        """Test creating a categorization rule."""
        from backend.app.core_gov.categorizer import service
        
        payload = {
            "name": "Superstore groceries",
            "rule_type": "vendor_contains",
            "pattern": "superstore",
            "category": "groceries",
            "confidence": 0.85,
            "tags_add": ["family"],
        }
        rule = service.create_rule(payload)
        
        assert rule["id"].startswith("cr_")
        assert rule["name"] == "Superstore groceries"
        assert rule["category"] == "groceries"
        assert rule["confidence"] == 0.85

    def test_rule_list(self):
        """Test listing rules."""
        from backend.app.core_gov.categorizer import service
        
        service.create_rule({"name": "Rule1", "pattern": "pattern1", "category": "cat1"})
        service.create_rule({"name": "Rule2", "pattern": "pattern2", "category": "cat2", "status": "paused"})
        
        items = service.list_rules()
        assert len(items) == 2
        
        active = service.list_rules(status="active")
        assert len(active) == 1

    def test_rule_confidence_sorting(self):
        """Test rules are sorted by confidence (highest first)."""
        from backend.app.core_gov.categorizer import service
        
        service.create_rule({"name": "Rule1", "pattern": "p1", "category": "c1", "confidence": 0.5})
        service.create_rule({"name": "Rule2", "pattern": "p2", "category": "c2", "confidence": 0.9})
        
        items = service.list_rules()
        assert items[0]["confidence"] == 0.9
        assert items[1]["confidence"] == 0.5

    def test_categorize_receipt_vendor_match(self):
        """Test categorizing receipt by vendor match."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.categorizer import service as csvc
        
        # Create receipt
        receipt = rsvc.create({
            "vendor": "Real Canadian Superstore",
            "date": "2026-01-01",
            "total": 50.0,
        })
        
        # Create matching rule
        csvc.create_rule({
            "name": "Superstore rule",
            "pattern": "superstore",
            "category": "groceries",
            "confidence": 0.85,
            "tags_add": ["family"],
        })
        
        # Categorize
        result = csvc.categorize_receipt(receipt["id"], apply=False)
        
        assert result["category"] == "groceries"
        assert result["confidence"] == 0.85
        assert "family" in result["tags_add"]

    def test_categorize_receipt_no_match(self):
        """Test categorizing receipt with no matching rule."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.categorizer import service as csvc
        
        receipt = rsvc.create({
            "vendor": "Unknown Store",
            "date": "2026-01-01",
            "total": 50.0,
        })
        
        result = csvc.categorize_receipt(receipt["id"], apply=False)
        
        assert result["category"] == ""
        assert "no rule match" in result["warnings"]

    def test_categorize_receipt_apply(self):
        """Test applying categorization to receipt."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.categorizer import service as csvc
        
        receipt = rsvc.create({"vendor": "Superstore", "date": "2026-01-01", "total": 50.0})
        csvc.create_rule({"name": "Rule", "pattern": "superstore", "category": "groceries", "tags_add": ["family"]})
        
        result = csvc.categorize_receipt(receipt["id"], apply=True)
        
        # Verify receipt was updated
        updated = rsvc.get_one(receipt["id"])
        assert updated["category"] == "groceries"
        assert "family" in updated["tags"]


# ============================================================================
# P-BUDGET-6: ACTUALS LEDGER TESTS
# ============================================================================

class TestActualsLedger:
    """P-BUDGET-6: Actuals rollup from payments + receipts."""

    def test_month_actuals_structure(self):
        """Test month_actuals returns correct structure."""
        from backend.app.core_gov.budget import actuals
        
        result = actuals.month_actuals("2026-01")
        
        assert result["month"] == "2026-01"
        assert "payments_total" in result
        assert "receipts_total" in result
        assert "grand_total" in result
        assert "receipt_category_totals" in result

    def test_actuals_invalid_month(self):
        """Test actuals rejects invalid month format."""
        from backend.app.core_gov.budget import actuals
        
        with pytest.raises(ValueError, match="month must be YYYY-MM"):
            actuals.month_actuals("01-2026")

    def test_actuals_receipts_total(self):
        """Test actuals calculates receipts total."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.budget import actuals
        
        rsvc.create({"vendor": "Store1", "date": "2026-01-05", "total": 50.0})
        rsvc.create({"vendor": "Store2", "date": "2026-01-10", "total": 30.0})
        rsvc.create({"vendor": "Store3", "date": "2026-02-05", "total": 20.0})
        
        jan_result = actuals.month_actuals("2026-01")
        assert jan_result["receipts_count"] == 2
        assert jan_result["receipts_total"] == 80.0

    def test_actuals_category_rollup(self):
        """Test actuals rolls up by category."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.budget import actuals
        
        rsvc.create({"vendor": "Store", "date": "2026-01-01", "total": 50.0, "category": "groceries"})
        rsvc.create({"vendor": "Store", "date": "2026-01-02", "total": 30.0, "category": "groceries"})
        rsvc.create({"vendor": "Store", "date": "2026-01-03", "total": 20.0, "category": "utilities"})
        
        result = actuals.month_actuals("2026-01")
        
        assert result["receipt_category_totals"]["groceries"] == 80.0
        assert result["receipt_category_totals"]["utilities"] == 20.0


# ============================================================================
# P-TAXRISK-1: TAX RISK ASSESSMENT TESTS
# ============================================================================

class TestTaxRisk:
    """P-TAXRISK-1: Write-off risk assessment."""

    def test_assess_safe_category(self):
        """Test assessment of safe category."""
        from backend.app.core_gov.taxrisk import service
        
        result = service.assess(category="utilities")
        
        assert result["risk"] == "safe"
        assert result["score"] <= 0.35
        assert "category_safe" in result["reasons"]

    def test_assess_aggressive_category(self):
        """Test assessment of aggressive category."""
        from backend.app.core_gov.taxrisk import service
        
        result = service.assess(category="meals")
        
        assert result["risk"] == "aggressive"
        assert result["score"] >= 0.65
        assert "category_often_audited" in result["reasons"]

    def test_assess_with_safe_tags(self):
        """Test assessment with business-supporting tags."""
        from backend.app.core_gov.taxrisk import service
        
        result = service.assess(category="meals", tags=["business", "client"])
        
        # Tags should lower the risk
        assert result["score"] < service.assess(category="meals")["score"]
        assert "tags_support_business_use" in result["reasons"]

    def test_assess_with_aggressive_tags(self):
        """Test assessment with personal-indicating tags."""
        from backend.app.core_gov.taxrisk import service
        
        result = service.assess(category="utilities", tags=["personal", "family"])
        
        # Tags should increase the risk
        assert result["score"] > service.assess(category="utilities")["score"]

    def test_assess_score_bounds(self):
        """Test assessment score stays within 0-1."""
        from backend.app.core_gov.taxrisk import service
        
        # Extreme case with all aggressive tags
        result = service.assess(
            category="meals",
            tags=["personal", "family", "gift", "luxury", "vacation"]
        )
        
        assert 0.0 <= result["score"] <= 1.0


# ============================================================================
# P-REPORT-1: MONTHLY REPORT TESTS
# ============================================================================

class TestMonthlyReport:
    """P-REPORT-1: Monthly expense report generation."""

    def test_build_monthly_report(self):
        """Test building a monthly report."""
        from backend.app.core_gov.reports import service
        
        report = service.build_monthly_report("2026-01")
        
        assert report["id"].startswith("mr_")
        assert report["month"] == "2026-01"
        assert "report" in report
        assert "warnings" in report

    def test_report_structure(self):
        """Test report contains expected structure."""
        from backend.app.core_gov.reports import service
        
        report = service.build_monthly_report("2026-01")
        
        assert "plan" in report["report"]
        assert "actuals" in report["report"]
        assert "variance" in report["report"]

    def test_list_monthly(self):
        """Test listing monthly reports."""
        from backend.app.core_gov.reports import service
        
        service.build_monthly_report("2026-01")
        service.build_monthly_report("2026-02")
        
        items = service.list_monthly(limit=25)
        assert len(items) >= 2

    def test_get_monthly(self):
        """Test retrieving a specific report."""
        from backend.app.core_gov.reports import service
        
        report = service.build_monthly_report("2026-01")
        retrieved = service.get_monthly(report["id"])
        
        assert retrieved is not None
        assert retrieved["id"] == report["id"]

    def test_report_includes_details(self):
        """Test report with include_details=True."""
        from backend.app.core_gov.reports import service
        
        report = service.build_monthly_report("2026-01", include_details=True)
        
        # Report structure should be preserved
        assert "report" in report

    def test_report_excludes_details(self):
        """Test report with include_details=False."""
        from backend.app.core_gov.reports import service
        
        report = service.build_monthly_report("2026-01", include_details=False)
        
        # Heavy lists should be removed
        assert "report" in report


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests across multiple modules."""

    def test_receipt_to_categorization_workflow(self):
        """Test full receipt entry and categorization."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.categorizer import service as csvc
        
        # 1. Create rule
        csvc.create_rule({
            "name": "Superstore rule",
            "pattern": "superstore",
            "category": "groceries",
            "confidence": 0.85,
        })
        
        # 2. Add receipt
        receipt = rsvc.create({
            "vendor": "Real Canadian Superstore",
            "date": "2026-01-03",
            "total": 87.22,
        })
        
        # 3. Categorize
        cat_result = csvc.categorize_receipt(receipt["id"], apply=True)
        
        # 4. Verify
        updated = rsvc.get_one(receipt["id"])
        assert updated["category"] == "groceries"
        assert updated["status"] == "categorized"

    def test_receipts_to_actuals_workflow(self):
        """Test receipts → actuals workflow."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.budget import actuals
        
        # Add receipts
        rsvc.create({"vendor": "Store1", "date": "2026-01-01", "total": 50.0, "category": "groceries"})
        rsvc.create({"vendor": "Store2", "date": "2026-01-02", "total": 75.0, "category": "utilities"})
        
        # Get actuals
        result = actuals.month_actuals("2026-01")
        
        assert result["receipts_count"] == 2
        assert result["receipts_total"] == 125.0
        assert "groceries" in result["receipt_category_totals"]

    def test_full_reporting_workflow(self):
        """Test complete flow: receipt → categorize → report."""
        from backend.app.core_gov.receipts import service as rsvc
        from backend.app.core_gov.categorizer import service as csvc
        from backend.app.core_gov.reports import service as repsvc
        
        # Setup
        csvc.create_rule({"name": "Rule", "pattern": "store", "category": "groceries"})
        receipt = rsvc.create({"vendor": "Store", "date": "2026-01-01", "total": 100.0})
        csvc.categorize_receipt(receipt["id"], apply=True)
        
        # Generate report
        report = repsvc.build_monthly_report("2026-01")
        
        assert report["month"] == "2026-01"
        assert "report" in report


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling across modules."""

    def test_receipt_missing_date(self):
        """Test receipt creation fails without date."""
        from backend.app.core_gov.receipts import service
        
        with pytest.raises(ValueError, match="date is required"):
            service.create({"vendor": "Store"})

    def test_rule_missing_pattern(self):
        """Test rule creation fails without pattern."""
        from backend.app.core_gov.categorizer import service
        
        with pytest.raises(ValueError, match="pattern is required"):
            service.create_rule({"name": "Rule", "category": "cat"})

    def test_receipt_patch_nonexistent(self):
        """Test patching nonexistent receipt."""
        from backend.app.core_gov.receipts import service
        
        with pytest.raises(KeyError):
            service.patch("rc_nonexistent", {"category": "cat"})


# ============================================================================
# DATA PERSISTENCE TESTS
# ============================================================================

class TestDataPersistence:
    """Test data persistence across operations."""

    def test_receipt_persistence(self):
        """Test receipts persist across calls."""
        from backend.app.core_gov.receipts import service
        
        receipt = service.create({"vendor": "Store", "date": "2026-01-01", "total": 50.0})
        
        items = service.list_items()
        assert any(i["id"] == receipt["id"] for i in items)

    def test_rule_persistence(self):
        """Test rules persist across calls."""
        from backend.app.core_gov.categorizer import service
        
        rule = service.create_rule({"name": "Rule", "pattern": "pat", "category": "cat"})
        
        items = service.list_rules()
        assert any(i["id"] == rule["id"] for i in items)

    def test_report_persistence(self):
        """Test reports persist across calls."""
        from backend.app.core_gov.reports import service
        
        report = service.build_monthly_report("2026-01")
        
        items = service.list_monthly()
        assert any(i["id"] == report["id"] for i in items)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
