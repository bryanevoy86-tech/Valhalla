#!/usr/bin/env python
"""Test cone imports without require_scopes."""
from fastapi import APIRouter, Depends
from backend.app.core_gov.canon.canon import ConeBand
from backend.app.core_gov.cone.models import ConeState
from backend.app.core_gov.cone.service import set_cone_state
from backend.app.core_gov.security.rbac import require_scopes, require_active_subscription
from backend.app.core_gov.security.devkey.deps import require_dev_key
from backend.app.core_gov.rate_limit.deps import rate_limit

router = APIRouter(prefix="/cone", tags=["Core: Cone"])

print("Test 1: Without require_scopes...")
try:
    @router.post("/state1", response_model=ConeState)
    def write_state_1(
        band: ConeBand,
        reason: str,
        _key=Depends(require_dev_key),
        _sub=Depends(require_active_subscription),
        _rl=rate_limit("cone_set", max_requests=10, window_seconds=60),
    ):
        return {"status": "ok"}
    print("  ✅ OK")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\nTest 2: With require_scopes factory...")
try:
    @router.post("/state2", response_model=ConeState)
    def write_state_2(
        band: ConeBand,
        reason: str,
        _owner=Depends(require_scopes("owner")),
    ):
        return {"status": "ok"}
    print("  ✅ OK")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\nTest 3: Both together...")
try:
    @router.post("/state3", response_model=ConeState)
    def write_state_3(
        band: ConeBand,
        reason: str,
        _key=Depends(require_dev_key),
        _owner=Depends(require_scopes("owner")),
    ):
        return {"status": "ok"}
    print("  ✅ OK")
except Exception as e:
    print(f"  ❌ Error: {e}")
