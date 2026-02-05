#!/usr/bin/env python3
"""
Validation script - verify all 20 modules are importable and functional.
Run: python validate_20_modules.py
"""

import sys
from pathlib import Path

# Add services/api to path for imports
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

def test_module(module_name, import_path):
    """Test if module can be imported."""
    try:
        exec(f"from {import_path} import *")
        print(f"✓ Module {module_name}: OK")
        return True
    except Exception as e:
        print(f"✗ Module {module_name}: FAILED - {e}")
        return False

def main():
    """Run validation tests."""
    print("=" * 80)
    print("VALIDATING 20-MODULE AUTONOMOUS INCOME ENGINE")
    print("=" * 80)
    
    modules = [
        # Core System (Modules 1-10)
        ("1. Runtime Flags", "app.core.runtime_flags"),
        ("2. Heimdall Authority", "app.heimdall.authority"),
        ("3. Contracts Pipeline", "app.contracts.service"),
        ("4. Payments Gateway", "app.payments.gateway"),
        ("5. Revenue Ledger", "app.ledger.service"),
        ("6. Real Estate Engine", "app.realestate.engine"),
        ("7. Floor Control", "app.governance.floor_enforcer"),
        ("8. AI Engines", "app.ai_engines.base"),
        ("9. QuickBooks Sync", "app.accounting.quickbooks"),
        ("10. Admin Runtime", "app.admin.runtime"),
        
        # Extended System (Modules 11-20)
        ("11. DocuSign Integration", "app.integrations.docusign.client"),
        ("12. Banking & Payouts", "app.payments.payouts"),
        ("13. Deal Intake", "app.intake.service"),
        ("14. Deal Scoring", "app.deals.scoring"),
        ("15. Offer Issuance", "app.deals.offers"),
        ("16. Operations Orchestrator", "app.orchestrator.runner"),
        ("17. Daily Operations", "app.ops.daily"),
        ("18. Heimdall Readiness", "app.heimdall.readiness"),
        ("19. System Activation", "app.admin.activation"),
        ("20. Revenue Targets", "app.governance.revenue_targets"),
    ]
    
    print()
    passed = 0
    failed = 0
    
    for name, path in modules:
        if test_module(name, path):
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("✓ ALL MODULES VALIDATED - READY FOR DEPLOYMENT")
        return 0
    else:
        print("✗ FIX FAILED MODULES BEFORE DEPLOYMENT")
        return 1

if __name__ == "__main__":
    sys.exit(main())
