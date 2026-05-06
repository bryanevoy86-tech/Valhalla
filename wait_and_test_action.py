#!/usr/bin/env python
"""Wait and test the deal action endpoint."""
import time
import requests

print('Waiting 120 seconds for Render full redeploy...')
for i in range(1, 13):
    time.sleep(10)
    pct = int(i * 100 / 12)
    print(f"  [{pct:3d}%] {i*10}s elapsed")

print("\nTesting endpoint now...")
try:
    resp = requests.post(
        "https://valhalla-api-ha6a.onrender.com/deals/16/action",
        json={"action": "hot"},
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print("✅ SUCCESS!")
        print(f"  Deal ID: {data.get('id')}")
        print(f"  New status: {data.get('status')}")
        print(f"  Headline: {data.get('headline')}")
    elif resp.status_code == 404:
        text = resp.text.lower()
        if 'deal' in text or 'action' not in text:
            print("✅ Got our endpoint 404 (deal-specific error)!")
            print(f"  Response: {resp.json()}")
        else:
            print("❌ Still generic 404 - endpoint not deployed yet")
            print(f"  Response: {resp.json()}")
    else:
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
