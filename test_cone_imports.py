#!/usr/bin/env python
"""Test cone imports step by step."""
import sys

try:
    print("Importing APIRouter...")
    from fastapi import APIRouter, Depends
    print("  OK")
    
    print("Importing ConeBand...")
    from backend.app.core_gov.canon.canon import ConeBand
    print("  OK")
    
    print("Importing ConeDecision, ConeState...")
    from backend.app.core_gov.cone.models import ConeDecision, ConeState
    print("  OK")
    
    print("Importing service functions...")
    from backend.app.core_gov.cone.service import decide, get_cone_state, set_cone_state
    print("  OK")
    
    print("Importing RBAC functions...")
    from backend.app.core_gov.security.rbac import require_scopes, require_active_subscription
    print("  OK")
    
    print("Importing require_dev_key...")
    from backend.app.core_gov.security.devkey.deps import require_dev_key
    print("  OK")
    
    print("Importing rate_limit...")
    from backend.app.core_gov.rate_limit.deps import rate_limit
    print("  OK")
    
    print("\nAll imports successful. Now creating router...")
    router = APIRouter(prefix="/cone", tags=["Core: Cone"])
    
    print("Creating read_state endpoint...")
    @router.get("/state", response_model=ConeState)
    def read_state():
        return get_cone_state()
    print("  OK")
    
    print("Creating write_state endpoint...")
    @router.post("/state", response_model=ConeState)
    def write_state(
        band: ConeBand,
        reason: str,
        _key=Depends(require_dev_key),
        _sub=Depends(require_active_subscription),
        _owner=Depends(require_scopes("owner")),
        _rl=rate_limit("cone_set", max_requests=10, window_seconds=60),
    ):
        return set_cone_state(band=band, reason=reason)
    print("  OK")
    
    print("✅ All done!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
