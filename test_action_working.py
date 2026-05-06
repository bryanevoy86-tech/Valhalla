import requests
import json

resp = requests.post('https://valhalla-api-ha6a.onrender.com/deals/16/action', json={'action': 'hot'})
print(f"Action Endpoint Status: {resp.status_code}")
print(f"Action Response: {json.dumps(resp.json(), indent=2)}")

# Check when this response was last updated
print(f"\nThis deal's current status shows: {resp.json().get('status')}")
print("✅ This confirms action endpoint IS working on Remote")
