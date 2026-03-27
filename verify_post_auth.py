#!/usr/bin/env python3
"""
Post-auth live verification - test routes with builder key in headers
"""
import sys
import os
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

# Load .env with VALHALLA_BUILDER_KEY now set
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Import app
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Get builder key from env
builder_key = os.getenv("VALHALLA_BUILDER_KEY", "test-default")

print("="*80)
print("POST-AUTH LIVE VERIFICATION")
print(f"Builder Key: {builder_key[:20]}...")
print("="*80)

# Test routes WITH builder key header
routes_to_test = [
    ("GET", "/api/deals", None, "List deals"),
    ("POST", "/api/heimdall/deals/1/analyze", None, "Heimdall analyze"),
    ("POST", "/api/heimdall/deals/1/advance-stage", {"requested_stage": "lead_received", "approved_by": "test", "reason": "test"}, "Heimdall advance-stage"),
    ("GET", "/api/audit/deals/1", None, "Audit deals"),
    ("GET", "/api/dashboard/pipeline", None, "Dashboard pipeline"),
]

headers = {"X-API-Key": builder_key}
results = {}

for method, path, body, desc in routes_to_test:
    try:
        if method == "GET":
            resp = client.get(path, headers=headers)
        elif method == "POST":
            resp = client.post(path, json=body or {}, headers=headers)
        
        status = resp.status_code
        result_key = desc.lower().replace(" ", "_").replace("-", "_")
        results[result_key] = status
        
        print(f"{method:4} {path:40} → {status:3}")
        if status >= 400:
            try:
                import json
                data = json.loads(resp.text)
                detail = data.get("detail", resp.text[:100])
                print(f"      Detail: {detail}")
            except:
                print(f"      Body: {resp.text[:100]}")
    except Exception as e:
        result_key = desc.lower().replace(" ", "_").replace("-", "_")
        results[result_key] = f"ERROR: {str(e)[:50]}"
        print(f"{method:4} {path:40} → ERROR: {str(e)[:50]}")

print("="*80)
print("RESULTS SUMMARY")
print("="*80)
for key, val in results.items():
    print(f"{key:25} → {val}")

# Return as JSON for parsing
import json
print("\nJSON OUTPUT:")
print(json.dumps(results, indent=2))
