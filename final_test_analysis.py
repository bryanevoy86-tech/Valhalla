#!/usr/bin/env python
"""Final wait and test."""
import requests
import time

print("Waiting 180 seconds for complete Render deployment...")
for i in range(18):
    time.sleep(10)
    print(f"  {(i+1)*10}s elapsed...")

print("\nTesting endpoint directly...")
try:
    resp = requests.post(
        "https://valhalla-api-ha6a.onrender.com/deals/16/analyze",
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("✅ SUCCESS!")
        print(f"\nAnalysis Result:")
        print(f"  Headline: {data['headline']}")
        print(f"  Score: {data['analysis']['score']}")
        print(f"  Risk: {data['analysis']['risk']}")
        print(f"  Strategy: {data['analysis']['strategy']}")
        print(f"  Recommendation: {data['analysis']['recommendation']}")
    else:
        print(f"Response: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

print("\nChecking OpenAPI...")
try:
    resp = requests.get("https://valhalla-api-ha6a.onrender.com/openapi.json")
    spec = resp.json()
    
    if "/deals/{deal_id}/analyze" in spec.get("paths", {}):
        print("✅ Endpoint IN OpenAPI spec")
    else:
        print("❌ Endpoint NOT in OpenAPI spec yet")
except Exception as e:
    print(f"Error checking OpenAPI: {e}")
