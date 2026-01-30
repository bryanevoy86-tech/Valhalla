#!/usr/bin/env python
"""
Test that the test-email endpoint is registered.
"""

import sys
sys.path.insert(0, "services/api")

print("Testing notification endpoint registration...\n")

# Import the app
from app.main import app

# Check routes
routes = [route.path for route in app.router.routes]
notify_routes = [r for r in routes if "notify" in r.lower()]

print("Registered notification routes:")
if notify_routes:
    for route in notify_routes:
        print(f"  ✓ {route}")
else:
    print("  (none found)")

print("\nAll routes containing 'test':")
test_routes = [r for r in routes if "test" in r.lower()]
if test_routes:
    for route in test_routes:
        print(f"  ✓ {route}")
else:
    print("  (none found)")

print("\nSearching for /api/notify/test-email...")
if "/api/notify/test-email" in routes:
    print("✓ /api/notify/test-email is registered!")
else:
    print("✗ /api/notify/test-email NOT found")
    print("\nAll routes:")
    for route in sorted(routes):
        print(f"  {route}")
