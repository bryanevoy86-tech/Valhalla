import requests, json
resp = requests.get('https://valhalla-api-ha6a.onrender.com/api/engines/states')
data = resp.json()
print('=' * 78)
print('ENGINE STATES AFTER PHASE 2')
print('=' * 78)
print()
for engine in data.get('engines', []):
    print(f"{engine['engine_name'].upper()}:")
    print(f"  state: {engine['state']}")
    print(f"  allowed_next: {engine['allowed_next']}")
    print(f"  changed_by: {engine['changed_by']}")
    print()
print('=' * 78)
