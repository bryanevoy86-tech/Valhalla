#!/usr/bin/env python
"""Quick test to check if execution router loads"""
import sys
import os
os.chdir("services/api")
sys.path.insert(0, ".")

import importlib
import pkgutil
from pathlib import Path

routers_pkg = "app.routers"
package = importlib.import_module(routers_pkg)
package_path = Path(package.__file__).resolve().parent

print(f"Routers package path: {package_path}")
print(f"\nFiles in routers directory:")
exec_files = [item.name for item in sorted(package_path.glob("*.py")) if "execution" in item.name]
for fname in exec_files:
    print(f"  ✓ {fname}")

print("\n--- Attempting to load execution router ---")
full_name = "app.routers.execution"
try:
    mod = importlib.import_module(full_name)
    router = getattr(mod, "router", None)
    if router is not None:
        print(f"✅ SUCCESS: Loaded {full_name}")
        print(f"  - Prefix: {router.prefix}")
        print(f"  - Routes: {len(router.routes)}")
        for r in router.routes:
            print(f"    • {r.path}")
    else:
        print(f"❌ FAILED: Module loaded but no 'router' attribute found")
except Exception as e:
    print(f"❌ FAILED: Exception during import")
    import traceback
    traceback.print_exc()
