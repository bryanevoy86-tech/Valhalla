#!/usr/bin/env python
"""Test all 5 core API routes with full diagnostics."""

import json
import sys
import os

# Load .env file first
from dotenv import load_dotenv
load_dotenv()

# Ensure required env vars
os.environ.setdefault("DATABASE_URL", "sqlite:///valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "dev-secret-key")
os.environ.setdefault("BUILDER_KEY", "test-builder-key-v0.2-verification")

# Import app
sys.path.insert(0, 'services/api')
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test routes
routes_to_test = [
    {
        "method": "GET",
        "path": "/api/deals",
        "headers": {"X-API-Key": "test-builder-key-v0.2-verification"},
        "description": "List all deals"
    },
    {
        "method": "POST",
        "path": "/api/heimdall/deals/1/analyze",
        "headers": {"X-API-Key": "test-builder-key-v0.2-verification"},
        "description": "Analyze deal 1"
    },
    {
        "method": "POST",
        "path": "/api/heimdall/deals/1/advance-stage",
        "headers": {"X-API-Key": "test-builder-key-v0.2-verification"},
        "json": {"requested_stage": "lead_received", "approved_by": "test", "reason": "test"},
        "description": "Advance deal 1 stage"
    },
    {
        "method": "GET",
        "path": "/api/audit/deals/1",
        "headers": {"X-API-Key": "test-builder-key-v0.2-verification"},
        "description": "Get audit record for deal 1"
    },
    {
        "method": "GET",
        "path": "/api/dashboard/pipeline",
        "headers": {"X-API-Key": "test-builder-key-v0.2-verification"},
        "description": "Get dashboard pipeline view"
    },
]

print("\n" + "=" * 80)
print("COMPREHENSIVE API VERIFICATION - All 5 Core Routes")
print("=" * 80)

for i, route in enumerate(routes_to_test, 1):
    print(f"\n[{i}/5] {route['description']}")
    print(f"      {route['method']} {route['path']}")
    
    try:
        if route["method"] == "GET":
            response = client.get(route["path"], headers=route["headers"])
        else:
            response = client.post(
                route["path"],
                headers=route["headers"],
                json=route.get("json", {})
            )
        
        print(f"      Status: {response.status_code}")
        
        # Show first part of response
        try:
            data = response.json()
            if response.status_code >= 400:
                if "detail" in data:
                    detail = data["detail"]
                    if isinstance(detail, str):
                        # Truncate long errors
                        detail = detail[:120]
                    print(f"      Error: {detail}")
            else:
                print(f"      Response: {json.dumps(data)[:100]}")
        except:
            print(f"      Response: {response.text[:100]}")
    
    except Exception as e:
        print(f"      Exception: {str(e)[:100]}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ If all routes returned 200/404/422 (not 500), model graph is stable")
print("❌ If any returned 500, check error messages above for ORM issues")
print("=" * 80 + "\n")
