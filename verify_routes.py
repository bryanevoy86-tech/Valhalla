#!/usr/bin/env python3
"""Verify Phase 1 route count"""
import os
import sys

os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/valhalla'
os.environ['VALHALLA_JWT_SECRET'] = 'test-secret'

try:
    from services.api.main import app
    print("✓ App loaded successfully")
    print(f"  Total routes: {len(app.routes)}")
    routes_with_path = [r for r in app.routes if hasattr(r, 'path')]
    print(f"  Routes with path: {len(routes_with_path)}")
    unique_paths = len(set(r.path for r in routes_with_path))
    print(f"  Unique paths: {unique_paths}")
except Exception as e:
    print(f"✗ Error loading app: {e}")
    sys.exit(1)
