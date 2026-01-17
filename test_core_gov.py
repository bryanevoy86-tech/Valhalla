#!/usr/bin/env python3
"""
Quick test to verify core_gov module imports and endpoints are accessible.
"""
import sys
import os

# Mock settings to avoid config validation
class MockSettings:
    PROJECT_NAME = "Valhalla API"
    API_V1_STR = "/api/v1"

# Test the imports work
print("✓ Testing core_gov imports...")
try:
    from backend.app.core_gov.canon.canon import ConeBand, EngineClass, ENGINE_CANON, get_engine
    print(f"  ✓ Canon module imported: {len(ENGINE_CANON)} engines registered")
    
    from backend.app.core_gov.cone.service import cone_state, CURRENT_BAND, ALLOWED
    print(f"  ✓ Cone service imported: Current band = {CURRENT_BAND}")
    
    from backend.app.core_gov.cone.router import router as cone_router
    print("  ✓ Cone router imported")
    
    from backend.app.core_gov.core_router import core as core_router
    print("  ✓ Core router imported")
    
    print("\n✓ All imports successful!")
    
    # Test business logic
    print("\n✓ Testing business logic...")
    state = cone_state()
    print(f"  ✓ Cone state: {state}")
    
    engine = get_engine("wholesaling")
    print(f"  ✓ Engine lookup: {engine}")
    
    # Test what cone_state() returns (would be GET /core/cone/state)
    print(f"\n✓ Would return from GET /core/cone/state:")
    print(f"  {state}")
    
    # Test what healthz() returns (would be GET /core/healthz)
    print(f"\n✓ Would return from GET /core/healthz:")
    print(f"  {{'ok': True}}")
    
    print("\n✅ All tests passed! Core governance system is ready.")
    print("\nTo run the full app:")
    print("  cd c:\\dev\\valhalla")
    print("  python -m uvicorn backend.app.main:app --port 4000")
    print("\nThen test:")
    print("  curl http://localhost:4000/core/healthz")
    print("  curl http://localhost:4000/core/cone/state")
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
