#!/usr/bin/env python
"""Wait and test the deal analysis endpoint."""
import time
import requests

print('Waiting 90 seconds for Render to redeploy...')
for i in range(1, 10):
    time.sleep(10)
    pct = int(i * 100 / 9)
    print(f"  [{pct:3d}%] {i*10}s elapsed")

print("\nTesting endpoint...")
try:
    resp = requests.post(
        "https://valhalla-api-ha6a.onrender.com/deals/16/analyze",
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("✅ SUCCESS!")
        print(f"  Deal: {data.get('headline')}")
        print(f"  Score: {data['analysis']['score']}")
        print(f"  Risk: {data['analysis']['risk']}")
        print(f"  Strategy: {data['analysis']['strategy']}")
        print(f"  Recommendation: {data['analysis']['recommendation']}")
    else:
        print(f"Response: {resp.status_code} - {resp.text[:100]}")
except Exception as e:
    print(f"Error: {e}")
