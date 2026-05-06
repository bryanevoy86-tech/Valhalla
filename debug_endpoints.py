import requests

# Test action endpoint
resp = requests.post('https://valhalla-api-ha6a.onrender.com/deals/16/action', json={'action': 'hot'})
print(f'Action Status: {resp.status_code}')

# Check OpenAPI
resp2 = requests.get('https://valhalla-api-ha6a.onrender.com/openapi.json')
has_analyze = "/deals" in resp2.text and "analyze" in resp2.text
has_action = "/deals" in resp2.text and "action" in resp2.text
print(f'Has analyze: {has_analyze}')
print(f'Has action: {has_action}')

# Show what endpoints ARE there
if "/deals/{" in resp2.text:
    # Extract deals endpoints
    import json
    spec = resp2.json()
    if 'paths' in spec:
        deals_paths = {k: list(v.keys()) for k, v in spec['paths'].items() if '/deals' in k}
        print(f'Available /deals endpoints: {deals_paths}')
