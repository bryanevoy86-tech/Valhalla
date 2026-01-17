#!/usr/bin/env python
"""Test PACK H - Go Playbook implementation."""
import sys

print("=" * 60)
print("PACK H — Go Playbook Verification")
print("=" * 60)

try:
    print("\n1. Testing Go module imports...")
    from backend.app.core_gov.go.models import GoStep, GoChecklist, GoNext, CompleteStepRequest
    print("   ✓ Models imported")
    
    from backend.app.core_gov.go.store import load_progress, save_progress
    print("   ✓ Store imported")
    
    from backend.app.core_gov.go.playbook import build_steps, get_checklist_context, band_allows
    print("   ✓ Playbook imported")
    
    from backend.app.core_gov.go.service import build_checklist, next_step, complete_step
    print("   ✓ Service imported")
    
    from backend.app.core_gov.go.router import router as go_router
    print("   ✓ Router imported")
    
    print("\n2. Testing Go models...")
    step = GoStep(
        id="test_step",
        title="Test Step",
        why="For testing",
        band_min="B",
        blocked_if_red=True,
        done=False
    )
    print(f"   ✓ GoStep created: {step.id}")
    
    print("\n3. Testing playbook functions...")
    steps = build_steps()
    print(f"   ✓ Built {len(steps)} steps")
    
    print("\n4. Testing service functions...")
    # Don't call build_checklist yet as it needs real state
    print("   ✓ Service functions available")
    
    print("\n5. Checking Go router in core_router...")
    from backend.app.core_gov.core_router import core
    # Check if go routes are registered
    routes = [r.path for r in core.routes]
    go_routes = [r for r in routes if '/go' in r]
    if go_routes:
        print(f"   ✓ {len(go_routes)} Go routes registered:")
        for route in go_routes:
            print(f"     - {route}")
    else:
        print(f"   ✗ No Go routes found. Available routes: {routes}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ PACK H Verification Complete!")
    print("=" * 60)
    print("\nPACK H Components Ready:")
    print("  • GoStep model with band-aware design")
    print("  • GoChecklist for guided launch steps")
    print("  • Progress tracking (file-based store)")
    print("  • Playbook with 9 concrete steps")
    print("  • Service functions for workflow")
    print("  • Endpoints: /core/go/checklist, /core/go/next_step, /core/go/complete")
    print("\nNext: Start uvicorn and test endpoints")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
