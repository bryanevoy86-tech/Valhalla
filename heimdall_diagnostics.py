#!/usr/bin/env python3
"""
Get detailed error for Heimdall endpoints
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
builder_key = "test-builder-key-v0.2-verification"
headers = {"X-API-Key": builder_key}

print("Testing Heimdall endpoints with detailed error capture...\n")

# Test analyze endpoint
print("="*80)
print("POST /api/heimdall/deals/1/analyze")
print("="*80)

resp = client.post(
    "/api/heimdall/deals/1/analyze",
    headers=headers,
    json={}
)

print(f"Status: {resp.status_code}")
try:
    data = json.loads(resp.text)
    print(f"Detail: {data.get('detail', 'N/A')}")
except:
    print(f"Body: {resp.text[:500]}")

print("\n" + "="*80)
print("POST /api/heimdall/deals/1/advance-stage")
print("="*80)

resp = client.post(
    "/api/heimdall/deals/1/advance-stage",
    headers=headers,
    json={"requested_stage": "lead_received", "approved_by": "test", "reason": "test"}
)

print(f"Status: {resp.status_code}")
try:
    data = json.loads(resp.text)
    print(f"Detail: {data.get('detail', 'N/A')}")
except:
    print(f"Body: {resp.text[:500]}")
