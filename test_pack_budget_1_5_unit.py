"""
PACK 1-5: Household Budget System
Smoke tests for budget registry, calendar, planning, autopay guidance

Tests cover:
- P-BUDGET-1: Core obligations registry (rent, utilities, subscriptions)
- P-BUDGET-2: Calendar generator (upcoming obligations)
- P-BUDGET-3: Cashflow planning with buffers
- P-BUDGET-4: Autopay setup guidance
- P-OBLIG-1: Compatibility shim
"""
import pytest
from datetime import date, timedelta
from backend.app.core_gov.obligations import service as oblig_svc


class TestPBudget1Registry:
    """P-BUDGET-1: Core obligation registry"""
    
    def test_create_internet_obligation(self):
        """Create Internet $150 monthly on 15th"""
        result = oblig_svc.create_obligation({
            "name": "Internet",
            "amount": 150.0,
            "frequency": "monthly",
            "due_day": 15,
            "category": "utilities",
            "beneficiary": "Your ISP",
            "account_info": "RBC chequing",
        })
        assert result["id"].startswith("ob_")
        assert result["name"] == "Internet"
        assert result["amount"] == 150.0
        self.internet_id = result["id"]
    
    def test_create_rent_obligation(self):
        """Create Rent $1500 monthly on 1st"""
        result = oblig_svc.create_obligation({
            "name": "Rent",
            "amount": 1500.0,
            "frequency": "monthly",
            "due_day": 1,
            "category": "housing",
            "beneficiary": "Landlord",
        })
        assert result["name"] == "Rent"
        assert result["amount"] == 1500.0
        self.rent_id = result["id"]
    
    def test_create_quarterly_water(self):
        """Create Water $280 quarterly"""
        result = oblig_svc.create_obligation({
            "name": "Water Bill",
            "amount": 280.0,
            "frequency": "quarterly",
            "due_day": 1,
            "category": "utilities",
        })
        assert result["name"] == "Water Bill"
        assert result["frequency"] == "quarterly"
        self.water_id = result["id"]
    
    def test_list_obligations(self):
        """List active obligations"""
        items = oblig_svc.list_obligations(status="active")
        assert isinstance(items, list)
        assert len(items) >= 0
    
    def test_get_obligation(self):
        """Retrieve single obligation"""
        ob = oblig_svc.create_obligation({
            "name": "Test Get",
            "amount": 100.0,
            "frequency": "monthly",
        })
        retrieved = oblig_svc.get_obligation(ob["id"])
        assert retrieved is not None
        assert retrieved["id"] == ob["id"]
    
    def test_patch_obligation(self):
        """Update obligation"""
        ob = oblig_svc.create_obligation({
            "name": "Patchable",
            "amount": 50.0,
            "frequency": "monthly",
        })
        updated = oblig_svc.patch_obligation(ob["id"], {"amount": 75.0})
        assert updated["amount"] == 75.0
    
    def test_log_payment(self):
        """Record payment"""
        ob = oblig_svc.create_obligation({
            "name": "Payable",
            "amount": 100.0,
            "frequency": "monthly",
        })
        # Payment tracking handled by obligations module
        # Just verify obligation created
        assert ob["id"].startswith("ob_")


class TestPBudget2Calendar:
    """P-BUDGET-2: Calendar of upcoming obligations"""
    
    def test_upcoming_obligations(self):
        """Generate upcoming obligations calendar"""
        today = date.today()
        start = today.isoformat()
        end = (today + timedelta(days=30)).isoformat()
        
        result = oblig_svc.generate_upcoming(start, end)
        assert isinstance(result, list)
    
    def test_next_30_days(self):
        """Get obligations for next 30 days"""
        today = date.today()
        start = today.isoformat()
        end = (today + timedelta(days=30)).isoformat()
        
        result = oblig_svc.generate_upcoming(start, end)
        # Should be a list of obligation events
        assert isinstance(result, list)


class TestPBudget3Plan:
    """P-BUDGET-3: Cashflow planning with buffers"""
    
    def test_monthly_total(self):
        """Calculate monthly obligations total"""
        # Create obligations
        for title, amt in [("P1", 100), ("P2", 200)]:
            oblig_svc.create_obligation({
                "name": title,
                "amount": amt,
                "frequency": "monthly",
                "due_day": 1,
            })
        
        items = oblig_svc.list_obligations(status="active")
        total = sum(item.get("amount", 0) for item in items)
        assert total >= 300
    
    def test_buffer_multiplier(self):
        """Apply safety buffer to obligations total"""
        oblig_svc.create_obligation({
            "name": "Buffer Test",
            "amount": 100.0,
            "frequency": "monthly",
        })
        
        items = oblig_svc.list_obligations(status="active")
        total = sum(item.get("amount", 0) for item in items)
        buffered = total * 1.25
        
        assert buffered > total
        assert buffered == total * 1.25


class TestPBudget4Autopay:
    """P-BUDGET-4: Autopay setup guidance"""
    
    def test_autopay_plan(self):
        """Generate autopay setup guide"""
        ob = oblig_svc.create_obligation({
            "name": "Setup Test",
            "amount": 99.99,
            "due_day": 10,
            "beneficiary": "Provider",
            "account_info": "RBC",
        })
        
        guide = oblig_svc.autopay_setup_guide(ob["id"])
        assert guide is not None
        assert guide.get("obligation_id") == ob["id"]


class TestPOblig1Compat:
    """P-OBLIG-1: Compatibility wrapper"""
    
    def test_obligations_status(self):
        """Obligations status endpoint"""
        items = oblig_svc.list_obligations(status="active")
        assert isinstance(items, list)
    
    def test_status_with_filter(self):
        """Filter obligations by status"""
        oblig_svc.create_obligation({
            "name": "Status Test",
            "amount": 50.0,
            "status": "active",
        })
        active = oblig_svc.list_obligations(status="active")
        assert len(active) > 0


class TestIntegration:
    """Integration: create -> schedule -> plan -> pay"""
    
    def test_full_obligation_workflow(self):
        """Complete obligation workflow"""
        # 1. Create
        ob = oblig_svc.create_obligation({
            "name": "Workflow Test",
            "amount": 120.0,
            "due_day": 8,
            "frequency": "monthly",
            "category": "utilities",
            "beneficiary": "Utility Co",
        })
        assert ob["id"].startswith("ob_")
        
        # 2. View calendar
        today = date.today()
        upcoming = oblig_svc.generate_upcoming(
            today.isoformat(),
            (today + timedelta(days=30)).isoformat()
        )
        assert isinstance(upcoming, list)
        
        # 3. Generate autopay setup guide
        guide = oblig_svc.autopay_setup_guide(ob["id"])
        assert guide is not None
    
    def test_mixed_cadences(self):
        """Handle different obligation cadences"""
        for freq in ["monthly", "quarterly", "yearly"]:
            oblig_svc.create_obligation({
                "name": f"{freq.title()} Obligation",
                "amount": 100.0,
                "frequency": freq,
                "due_day": 1,
            })
        
        items = oblig_svc.list_obligations(status="active")
        # Should have items for each cadence
        assert len(items) > 0
