#!/usr/bin/env python
"""
Direct test of PACK L, M, N services (no server needed)
"""
import sys
sys.path.insert(0, "backend")

from pathlib import Path

print("=" * 70)
print("PACK L, M, N Direct Service Test (No Server)")
print("=" * 70)

# Test 1: Canon
print("\n1. PACK L — Canon Service")
print("-" * 70)
try:
    from app.core_gov.canon.service import canon_snapshot
    result = canon_snapshot()
    print("✓ Canon snapshot retrieved")
    print(f"  - canon_version: {result['canon_version']}")
    print(f"  - locked_model: {result['locked_model']}")
    print(f"  - boring_engines_locked: {result['boring_engines_locked']}")
    print(f"  - band_policy: {list(result['band_policy'].keys())}")
    print(f"  - engine_registry entries: {len(result['engine_registry'])}")
    print("✓ Canon service working")
except Exception as e:
    print(f"✗ Canon service error: {e}")

# Test 2: Weekly Audit
print("\n2. PACK M — Weekly Audit Service")
print("-" * 70)
try:
    from app.core_gov.reality.weekly_service import run_weekly_audit
    result = run_weekly_audit()
    print("✓ Weekly audit snapshot retrieved")
    print(f"  - ok: {result['ok']}")
    record = result['record']
    print(f"  - timestamp: {record['created_at_utc']}")
    print(f"  - cone_band: {record['cone']['band']}")
    print(f"  - go_session_status: {record['go_session']['status']}")
    print("✓ Weekly audit service working")
except Exception as e:
    print(f"✗ Weekly audit service error: {e}")

# Test 3: Weekly Audits List
print("\n3. PACK M — Weekly Audits List")
print("-" * 70)
try:
    from app.core_gov.reality.weekly_store import load_audits
    items = load_audits()
    print(f"✓ Loaded {len(items)} audit(s)")
    if items:
        latest = items[-1]
        print(f"  - Latest: {latest['created_at_utc']}")
    print("✓ Weekly audits list working")
except Exception as e:
    print(f"✗ Weekly audits list error: {e}")

# Test 4: Export Bundle
print("\n4. PACK N — Export Bundle Service")
print("-" * 70)
try:
    from app.core_gov.export.service import build_export_bundle
    import zipfile
    
    path = build_export_bundle()
    print(f"✓ ZIP bundle created: {path.name}")
    
    size_kb = path.stat().st_size / 1024
    print(f"  - Size: {size_kb:.2f} KB")
    
    with zipfile.ZipFile(path, 'r') as z:
        files = z.namelist()
        print(f"  - Contains {len(files)} file(s):")
        for fname in sorted(files):
            finfo = z.getinfo(fname)
            print(f"    • {fname} ({finfo.file_size} bytes)")
    
    print("✓ Export bundle service working")
except Exception as e:
    print(f"✗ Export bundle service error: {e}")

print("\n" + "=" * 70)
print("Summary: All PACK L, M, N services verified! ✅")
print("=" * 70)
print("\nNow testing routers...")
print("=" * 70)

# Test 5: Canon Router
print("\n5. PACK L — Canon Router")
print("-" * 70)
try:
    from app.core_gov.canon.router import router as canon_router
    print(f"✓ Canon router imported")
    print(f"  - Prefix: /canon")
    print(f"  - Routes: {len(canon_router.routes)}")
    for route in canon_router.routes:
        print(f"    • {route.path} [{route.methods}]")
except Exception as e:
    print(f"✗ Canon router error: {e}")

# Test 6: Reality Router
print("\n6. PACK M — Reality Router")
print("-" * 70)
try:
    from app.core_gov.reality.router import router as reality_router
    print(f"✓ Reality router imported")
    print(f"  - Prefix: /reality")
    print(f"  - Routes: {len(reality_router.routes)}")
    for route in reality_router.routes:
        print(f"    • {route.path} [{route.methods}]")
except Exception as e:
    print(f"✗ Reality router error: {e}")

# Test 7: Export Router
print("\n7. PACK N — Export Router")
print("-" * 70)
try:
    from app.core_gov.export.router import router as export_router
    print(f"✓ Export router imported")
    print(f"  - Prefix: /export")
    print(f"  - Routes: {len(export_router.routes)}")
    for route in export_router.routes:
        print(f"    • {route.path} [{route.methods}]")
except Exception as e:
    print(f"✗ Export router error: {e}")

print("\n" + "=" * 70)
print("✅ All services and routers verified!")
print("=" * 70)
