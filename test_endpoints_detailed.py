import requests
import json

base_url = "https://valhalla-api-ha6a.onrender.com"

# Test action endpoint
print("=== Testing POST /deals/16/action ===")
resp = requests.post(f"{base_url}/deals/16/action", json={"action": "hot"})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")

print("\n=== Testing POST /deals/16/analyze ===")
resp = requests.post(f"{base_url}/deals/16/analyze", json={"notes": "test"})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")

print("\n=== Checking OpenAPI for /deals paths ===")
resp = requests.get(f"{base_url}/openapi.json")
if resp.status_code == 200:
    spec = resp.json()
    deals_paths = {k: list(v.keys()) for k, v in spec.get('paths', {}).items() if '/deals' in k}
    for path in sorted(deals_paths.keys()):
        if 'analyze' in path or 'action' in path:
            print(f"{path}: {deals_paths[path]}")
