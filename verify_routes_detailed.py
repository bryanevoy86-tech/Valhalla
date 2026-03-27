#!/usr/bin/env python3
"""
Detailed verification - capture full error stacktraces
"""
import sys
import os
import traceback
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Now import app
print("Loading app...", file=sys.stderr)
try:
    from app.main import app
    from fastapi.testclient import TestClient
except Exception as e:
    print(f"FAILED TO LOAD APP: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("App loaded successfully", file=sys.stderr)

client = TestClient(app)

routes_to_check = [
    ("GET", "/health", None, "System health check"),
    ("POST", "/api/heimdall/deals/1/analyze", None, "Heimdall analyze endpoint"),
    ("POST", "/api/heimdall/deals/1/advance-stage", {"requested_stage": "lead_received", "approved_by": "test", "reason": "test"}, "Heimdall advance-stage endpoint"),
    ("GET", "/api/audit/deals/1", None, "Audit deals endpoint"),
    ("GET", "/api/dashboard/pipeline", None, "Dashboard pipeline endpoint"),
]

for method, path, body, description in routes_to_check:
    print(f"\n{'='*80}")
    print(f"Testing: {method} {path}")
    print(f"Description: {description}")
    print('='*80)
    
    try:
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json=body or {})
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code >= 400:
            print(f"Response Body: {resp.text[:1000]}")
            if resp.status_code == 500:
                print("\n[ERROR DETAILS FROM RESPONSE]")
                try:
                    import json
                    data = json.loads(resp.text)
                    if "detail" in data:
                        print(f"Detail: {data['detail']}")
                    if "traceback" in data:
                        print(f"Traceback:\n{data['traceback']}")
                except:
                    pass
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        traceback.print_exc()
