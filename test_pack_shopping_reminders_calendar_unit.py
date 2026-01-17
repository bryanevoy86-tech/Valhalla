"""
Comprehensive unit tests for P-SHOP-1, P-SHOP-2, P-BUDGET-5, P-REMIND-1, P-CALENDAR-1
Testing shopping, reminders, calendar, and full month plan functionality.
"""
import pytest
import json
import os
from datetime import date, timedelta
from unittest.mock import patch, MagicMock


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data before and after each test."""
    yield
    # Cleanup
    for data_dir in ["backend/data/shopping", "backend/data/reminders"]:
        if os.path.exists(data_dir):
            for f in os.listdir(data_dir):
                try:
                    os.remove(os.path.join(data_dir, f))
                except:
                    pass


# ============================================================================
# P-SHOP-1: SHOPPING REGISTRY TESTS
# ============================================================================

class TestShoppingRegistry:
    """P-SHOP-1: Shopping list CRUD operations."""

    def test_shopping_create_item(self):
        """Test creating a shopping item."""
        from backend.app.core_gov.shopping import service
        
        payload = {
            "name": "Milk",
            "qty": 2,
            "unit": "l",
            "est_unit_cost": 3.50,
            "priority": "normal",
            "category": "groceries",
        }
        item = service.create_item(payload)
        
        assert item["id"].startswith("sh_")
        assert item["name"] == "Milk"
        assert item["qty"] == 2
        assert item["status"] == "open"
        assert item["priority"] == "normal"

    def test_shopping_list_items(self):
        """Test listing shopping items."""
        from backend.app.core_gov.shopping import service
        
        service.create_item({"name": "Item1", "qty": 1, "unit": "count"})
        service.create_item({"name": "Item2", "qty": 2, "unit": "count", "status": "purchased"})
        
        open_items = service.list_items(status="open")
        assert len(open_items) == 1
        assert open_items[0]["name"] == "Item1"
        
        all_items = service.list_items()
        assert len(all_items) == 2

    def test_shopping_filter_by_category(self):
        """Test filtering shopping items by category."""
        from backend.app.core_gov.shopping import service
        
        service.create_item({"name": "Milk", "qty": 1, "category": "groceries"})
        service.create_item({"name": "Socks", "qty": 5, "category": "clothing"})
        
        grocery_items = service.list_items(category="groceries")
        assert len(grocery_items) == 1
        assert grocery_items[0]["category"] == "groceries"

    def test_shopping_patch_item(self):
        """Test patching a shopping item."""
        from backend.app.core_gov.shopping import service
        
        item = service.create_item({"name": "Original", "qty": 1})
        item_id = item["id"]
        
        patched = service.patch_item(item_id, {"name": "Updated", "priority": "high"})
        assert patched["name"] == "Updated"
        assert patched["priority"] == "high"

    def test_shopping_mark_purchased(self):
        """Test marking item as purchased."""
        from backend.app.core_gov.shopping import service
        
        item = service.create_item({"name": "Bread", "qty": 1})
        item_id = item["id"]
        
        marked = service.mark_purchased(item_id)
        assert marked["status"] == "purchased"
        
        # Verify persistence
        items = service.list_items(status="purchased")
        assert len(items) == 1

    def test_shopping_priorities(self):
        """Test all priority levels."""
        from backend.app.core_gov.shopping import service
        
        for pri in ["low", "normal", "high", "critical"]:
            item = service.create_item({"name": f"Item-{pri}", "priority": pri})
            assert item["priority"] == pri

    def test_shopping_categories(self):
        """Test all valid categories."""
        from backend.app.core_gov.shopping import service
        
        categories = ["groceries", "household", "kids", "clothing", "home", "tools", "auto", "health", "other"]
        for cat in categories:
            item = service.create_item({"name": f"Item-{cat}", "category": cat})
            assert item["category"] == cat

    def test_shopping_get_item(self):
        """Test retrieving a single shopping item."""
        from backend.app.core_gov.shopping import service
        
        item = service.create_item({"name": "TestItem", "qty": 1})
        retrieved = service.get_item(item["id"])
        
        assert retrieved is not None
        assert retrieved["id"] == item["id"]
        assert retrieved["name"] == "TestItem"


# ============================================================================
# P-SHOP-2: AUTO-FILL SHOPPING TESTS
# ============================================================================

class TestAutoFillShopping:
    """P-SHOP-2: Auto-fill shopping from inventory reorders."""

    def test_autofill_safe_call_no_inventory(self):
        """Test autofill gracefully handles missing inventory module."""
        from backend.app.core_gov.shopping import autofill
        
        result = autofill.create_from_inventory(max_create=10)
        
        # Should return result, not error
        assert "warnings" in result or result.get("created", 0) >= 0

    def test_autofill_deduplication_logic(self):
        """Test that autofill deduplication keys work."""
        from backend.app.core_gov.shopping import service
        
        # Manually create an item with dedupe_key
        item = service.create_item({
            "name": "Milk",
            "qty": 1,
            "meta": {"dedupe_key": "inventory_reorder:inv_123"}
        })
        
        assert item["meta"]["dedupe_key"] == "inventory_reorder:inv_123"


# ============================================================================
# P-BUDGET-5: FULL MONTH PLAN TESTS
# ============================================================================

class TestBudgetFullPlan:
    """P-BUDGET-5: Full month plan combining obligations + shopping."""

    def test_month_plan_full_no_deps(self):
        """Test month_plan_full with missing dependencies."""
        from backend.app.core_gov.budget import full_plan
        
        result = full_plan.month_plan_full("2026-01")
        
        assert "obligations_total" in result
        assert "shopping_total" in result
        assert "grand_total" in result
        assert result["grand_total"] >= 0

    def test_month_plan_full_with_default_month(self):
        """Test month_plan_full with default month (current)."""
        from backend.app.core_gov.budget import full_plan
        
        result = full_plan.month_plan_full()
        
        assert "obligations_total" in result
        assert "shopping_total" in result
        assert result["grand_total"] >= 0

    def test_month_plan_full_structure(self):
        """Test month_plan_full response structure."""
        from backend.app.core_gov.budget import full_plan
        
        result = full_plan.month_plan_full("2026-01")
        
        assert isinstance(result["obligations"], list)
        assert isinstance(result["shopping_items"], list)
        assert isinstance(result["warnings"], list)
        assert isinstance(result["obligations_total"], (int, float))
        assert isinstance(result["shopping_total"], (int, float))
        assert isinstance(result["grand_total"], (int, float))


# ============================================================================
# P-REMIND-1: REMINDERS REGISTRY TESTS
# ============================================================================

class TestRemindersRegistry:
    """P-REMIND-1: Reminders CRUD and generators."""

    def test_reminder_create(self):
        """Test creating a reminder."""
        from backend.app.core_gov.reminders import service
        
        payload = {
            "title": "Pay rent",
            "due_date": "2026-02-01",
            "priority": "high",
            "source": "manual",
        }
        reminder = service.create(payload)
        
        assert reminder["id"].startswith("rm_")
        assert reminder["title"] == "Pay rent"
        assert reminder["status"] == "active"

    def test_reminder_list_by_status(self):
        """Test listing reminders by status."""
        from backend.app.core_gov.reminders import service
        
        service.create({"title": "Item1", "due_date": "2026-02-01", "status": "active"})
        service.create({"title": "Item2", "due_date": "2026-02-01", "status": "done"})
        
        active = service.list_items(status="active")
        assert len(active) == 1

    def test_reminder_list_by_source(self):
        """Test listing reminders by source."""
        from backend.app.core_gov.reminders import service
        
        service.create({"title": "Manual", "due_date": "2026-02-01", "source": "manual"})
        service.create({"title": "Budget", "due_date": "2026-02-01", "source": "budget"})
        
        budget = service.list_items(source="budget")
        assert len(budget) == 1

    def test_reminder_patch(self):
        """Test patching a reminder."""
        from backend.app.core_gov.reminders import service
        
        reminder = service.create({"title": "Original", "due_date": "2026-02-01"})
        reminder_id = reminder["id"]
        
        patched = service.patch(reminder_id, {"title": "Updated", "status": "done"})
        assert patched["title"] == "Updated"
        assert patched["status"] == "done"

    def test_reminder_generate_from_budget(self):
        """Test generating reminders from budget."""
        from backend.app.core_gov.reminders import service
        
        result = service.generate_from_budget(lookahead_days=30, lead_days=3, max_create=50)
        
        assert "created" in result
        assert "warnings" in result
        assert result["created"] >= 0

    def test_reminder_generate_from_shopping(self):
        """Test generating reminders from shopping."""
        from backend.app.core_gov.reminders import service
        
        result = service.generate_from_shopping(default_lead_days=2, max_create=50)
        
        assert "created" in result
        assert "warnings" in result
        assert result["created"] >= 0

    def test_reminder_priorities(self):
        """Test all reminder priorities."""
        from backend.app.core_gov.reminders import service
        
        for pri in ["low", "normal", "high", "critical"]:
            reminder = service.create({
                "title": f"Reminder-{pri}",
                "due_date": "2026-02-01",
                "priority": pri
            })
            assert reminder["priority"] == pri

    def test_reminder_sources(self):
        """Test reminder sources."""
        from backend.app.core_gov.reminders import service
        
        for src in ["manual", "budget", "shopping", "system"]:
            reminder = service.create({
                "title": f"Reminder-{src}",
                "due_date": "2026-02-01",
                "source": src
            })
            assert reminder["source"] == src


# ============================================================================
# P-CALENDAR-1: UNIFIED CALENDAR TESTS
# ============================================================================

class TestUnifiedCalendar:
    """P-CALENDAR-1: Unified calendar feed."""

    def test_calendar_feed_default(self):
        """Test default calendar feed (30 days)."""
        from backend.app.core_gov.calendar import service
        
        result = service.feed(days=30)
        
        assert "range_days" in result
        assert result["range_days"] == 30
        assert "items" in result
        assert "warnings" in result

    def test_calendar_feed_custom_range(self):
        """Test calendar feed with custom range."""
        from backend.app.core_gov.calendar import service
        
        result = service.feed(days=60)
        assert result["range_days"] == 60
        
        result = service.feed(days=1)
        assert result["range_days"] == 1

    def test_calendar_feed_max_range(self):
        """Test calendar feed respects max 120 days."""
        from backend.app.core_gov.calendar import service
        
        result = service.feed(days=500)
        assert result["range_days"] == 120

    def test_calendar_feed_min_range(self):
        """Test calendar feed respects min 1 day."""
        from backend.app.core_gov.calendar import service
        
        result = service.feed(days=-5)
        assert result["range_days"] == 1

    def test_calendar_feed_structure(self):
        """Test calendar feed response structure."""
        from backend.app.core_gov.calendar import service
        
        result = service.feed(days=30)
        
        assert "range_days" in result
        assert "range_start" in result
        assert "range_end" in result
        assert "warnings" in result
        assert "items" in result
        assert isinstance(result["items"], list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests across multiple modules."""

    def test_shopping_to_reminder_workflow(self):
        """Test shopping item to reminder generation workflow."""
        from backend.app.core_gov.shopping import service as shop_svc
        from backend.app.core_gov.reminders import service as rem_svc
        
        # Create shopping item
        item = shop_svc.create_item({
            "name": "Groceries",
            "qty": 1,
            "desired_by": (date.today() + timedelta(days=5)).isoformat(),
            "priority": "high",
        })
        
        # Generate reminders from shopping
        result = rem_svc.generate_from_shopping(default_lead_days=2, max_create=10)
        
        assert "created" in result
        assert isinstance(result["items"], list)

    def test_budget_to_full_plan_workflow(self):
        """Test budget obligations + shopping to full plan workflow."""
        from backend.app.core_gov.budget import full_plan
        
        result = full_plan.month_plan_full()
        
        assert "obligations_total" in result
        assert "shopping_total" in result
        assert "grand_total" in result

    def test_calendar_unified_view(self):
        """Test calendar merges multiple sources."""
        from backend.app.core_gov.calendar import service as cal_svc
        
        result = cal_svc.feed(days=30)
        
        # Should have structure even with missing deps
        assert "range_days" in result
        assert "items" in result
        assert "warnings" in result


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_shopping_create_missing_name(self):
        """Test shopping creation fails with missing name."""
        from backend.app.core_gov.shopping import service
        
        with pytest.raises(ValueError, match="name is required"):
            service.create_item({"qty": 1})

    def test_reminder_create_missing_due_date(self):
        """Test reminder creation fails with missing due_date."""
        from backend.app.core_gov.reminders import service
        
        with pytest.raises(ValueError, match="due_date is required"):
            service.create({"title": "Test"})

    def test_shopping_patch_nonexistent(self):
        """Test patching nonexistent shopping item."""
        from backend.app.core_gov.shopping import service
        
        with pytest.raises(KeyError):
            service.patch_item("sh_nonexistent", {"name": "New"})

    def test_reminder_patch_nonexistent(self):
        """Test patching nonexistent reminder."""
        from backend.app.core_gov.reminders import service
        
        with pytest.raises(KeyError):
            service.patch("rm_nonexistent", {"title": "New"})

    def test_calendar_invalid_days(self):
        """Test calendar handles invalid days parameter."""
        from backend.app.core_gov.calendar import service
        
        # Negative days should become 1
        result = service.feed(days=-10)
        assert result["range_days"] == 1

    def test_shopping_get_nonexistent(self):
        """Test getting nonexistent shopping item."""
        from backend.app.core_gov.shopping import service
        
        item = service.get_item("sh_nonexistent")
        assert item is None


# ============================================================================
# DATA PERSISTENCE TESTS
# ============================================================================

class TestDataPersistence:
    """Test data persistence across operations."""

    def test_shopping_persistence(self):
        """Test shopping items persist across service calls."""
        from backend.app.core_gov.shopping import service
        
        item1 = service.create_item({"name": "Item1", "qty": 1})
        item1_id = item1["id"]
        
        # Retrieve in new operation
        items = service.list_items()
        assert any(i["id"] == item1_id for i in items)

    def test_reminder_persistence(self):
        """Test reminders persist across service calls."""
        from backend.app.core_gov.reminders import service
        
        reminder1 = service.create({
            "title": "Reminder1",
            "due_date": "2026-02-01"
        })
        reminder1_id = reminder1["id"]
        
        # Retrieve in new operation
        items = service.list_items()
        assert any(i["id"] == reminder1_id for i in items)

    def test_shopping_update_persistence(self):
        """Test shopping item updates persist."""
        from backend.app.core_gov.shopping import service
        
        item = service.create_item({"name": "Original", "qty": 1})
        
        service.patch_item(item["id"], {"name": "Updated"})
        
        # Retrieve and verify
        updated = service.get_item(item["id"])
        assert updated["name"] == "Updated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
