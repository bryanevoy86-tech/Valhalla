#!/usr/bin/env python
"""Quick test for PACK E implementation."""
import sys

try:
    print("Testing Settings module...")
    from backend.app.core_gov.settings.config import load_settings
    s = load_settings()
    print(f"  ✓ Settings loaded. Dev key configured: {s.VALHALLA_DEV_KEY is not None}")
    
    print("Testing Identity model...")
    from backend.app.core_gov.security.models import Identity
    print("  ✓ Identity model imported")
    
    print("Testing Identity hook...")
    from backend.app.core_gov.security.identity import get_identity
    print("  ✓ Identity hook imported")
    
    print("Testing DevKey requirement...")
    from backend.app.core_gov.security.devkey.deps import require_dev_key
    print("  ✓ DevKey requirement imported")
    
    print("Testing RBAC with new Identity...")
    from backend.app.core_gov.security.rbac import require_active_subscription, require_scopes
    print("  ✓ RBAC functions imported")
    
    print("Testing routers with dev_key_dep...")
    from backend.app.core_gov.cone.router import router as cone_router
    print("  ✓ Cone router imported")
    
    from backend.app.core_gov.capital.router import router as capital_router
    print("  ✓ Capital router imported")
    
    from backend.app.core_gov.config.router import router as config_router
    print("  ✓ Config router imported")
    
    from backend.app.core_gov.notify.router import router as notify_router
    print("  ✓ Notify router imported")
    
    from backend.app.core_gov.jobs.router import router as jobs_router
    print("  ✓ Jobs router imported")
    
    print("\n✅ All PACK E imports successful!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
