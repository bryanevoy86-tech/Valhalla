#!/usr/bin/env python3
"""
Capture FIRST ORM failure chain for each route - get full stack traces
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
builder_key = "test-builder-key-v0.2-verification"
headers = {"X-API-Key": builder_key}

routes = [
    ("GET", "/api/deals", None, "deals_list"),
    ("POST", "/api/heimdall/deals/1/analyze", None, "heimdall_analyze"),
    ("POST", "/api/heimdall/deals/1/advance-stage", {"requested_stage": "lead_received", "approved_by": "test", "reason": "test"}, "heimdall_advance"),
    ("GET", "/api/audit/deals/1", None, "audit_deals"),
    ("GET", "/api/dashboard/pipeline", None, "dashboard_pipeline"),
]

for method, path, body, name in routes:
    print(f"\n{'='*80}")
    print(f"ROUTE: {method} {path}")
    print('='*80)
    
    try:
        if method == "GET":
            resp = client.get(path, headers=headers)
        else:
            resp = client.post(path, json=body or {}, headers=headers)
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code >= 500:
            try:
                import json
                data = json.loads(resp.text)
                if "detail" in data:
                    print(f"\nFirst Error Detail:")
                    print(data["detail"][:500])
            except:
                pass
                
    except Exception as e:
        print(f"Exception: {type(e).__name__}")
        print(f"\nFirst Real Traceback:")
        tb_lines = traceback.format_exc().split('\n')
        # Find first mention of model/mapper/relationship
        for i, line in enumerate(tb_lines):
            if any(x in line.lower() for x in ['mapper', 'relationship', 'model', '__init__', 'sqlalchemy']):
                # Print from this point
                print('\n'.join(tb_lines[max(0, i-3):min(len(tb_lines), i+10)]))
                break
        else:
            # If no model-related line found, print last part
            print('\n'.join(tb_lines[-20:]))
