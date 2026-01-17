#!/usr/bin/env python
"""Test PACK I - Go Session implementation."""
import sys

print("=" * 60)
print("PACK I — Go Session Verification")
print("=" * 60)

try:
    print("\n1. Testing Go Session module imports...")
    from backend.app.core_gov.go.session_models import GoSession
    print("   ✓ GoSession model imported")
    
    from backend.app.core_gov.go.session_store import load_session, save_session
    print("   ✓ Session store imported")
    
    from backend.app.core_gov.go.session_service import get_session, start_session, end_session
    print("   ✓ Session service imported")
    
    from backend.app.core_gov.go.session_router import router as go_session_router
    print("   ✓ Session router imported")
    
    print("\n2. Testing GoSession model...")
    sess = GoSession(
        active=False,
        started_at_utc=None,
        ended_at_utc=None,
        cone_band="B",
        status="green",
        notes="Test session",
        snapshot=None
    )
    print(f"   ✓ GoSession created: active={sess.active}, status={sess.status}")
    
    print("\n3. Testing session functions...")
    # Test get_session (should return inactive if no file)
    current = get_session()
    print(f"   ✓ get_session() works: active={current.active}")
    
    print("\n4. Checking Session routes in core_router...")
    from backend.app.core_gov.core_router import core
    routes = [r.path for r in core.routes]
    session_routes = [r for r in routes if 'session' in r or 'start' in r or 'end' in r]
    
    if "/core/go/session" in routes:
        print(f"   ✓ /core/go/session endpoint registered")
    else:
        print(f"   ✗ /core/go/session endpoint not found")
        sys.exit(1)
    
    if "/core/go/start_session" in routes:
        print(f"   ✓ /core/go/start_session endpoint registered")
    else:
        print(f"   ✗ /core/go/start_session endpoint not found")
        sys.exit(1)
    
    if "/core/go/end_session" in routes:
        print(f"   ✓ /core/go/end_session endpoint registered")
    else:
        print(f"   ✗ /core/go/end_session endpoint not found")
        sys.exit(1)
    
    print("\n5. Checking coexistence with PACK H playbook...")
    from backend.app.core_gov.go.router import router as go_router
    playbook_routes = [r.path for r in go_router.routes]
    print(f"   ✓ Playbook routes exist ({len(playbook_routes)} routes)")
    
    all_go_routes = sorted(set([r for r in routes if '/go' in r]))
    print(f"   ✓ Total Go endpoints: {len(all_go_routes)}")
    for route in all_go_routes:
        print(f"     - {route}")
    
    print("\n" + "=" * 60)
    print("✅ PACK I Verification Complete!")
    print("=" * 60)
    print("\nPACK I Components Ready:")
    print("  • GoSession model with timestamps and snapshot")
    print("  • Session store (file-based in data/go_session.json)")
    print("  • Session service (start, end, get operations)")
    print("  • Endpoints:")
    print("    - GET  /core/go/session (check current session)")
    print("    - POST /core/go/start_session (begin session)")
    print("    - POST /core/go/end_session (close session)")
    print("\nCoexists with PACK H playbook endpoints:")
    print("    - GET  /core/go/checklist")
    print("    - GET  /core/go/next_step")
    print("    - POST /core/go/complete")
    print("\nNext: Start uvicorn and test full session workflow")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
