import time
import requests

time.sleep(120)

resp = requests.post('https://valhalla-api-ha6a.onrender.com/deals/16/analyze', json={'notes': 'test property'})
print(f'Analyze Status: {resp.status_code}')

if resp.status_code == 200:
    print("✅ SUCCESS - Endpoint is now available!")
    print(f"Response: {resp.json()}")
else:
    print(f"Response: {resp.text[:300]}")

# Also check OpenAPI
resp2 = requests.get('https://valhalla-api-ha6a.onrender.com/openapi.json')
spec = resp2.json()
paths = spec.get('paths', {})
has_analyze = '/deals/{deal_id}/analyze' in paths
print(f"\n/deals/{{deal_id}}/analyze in OpenAPI: {has_analyze}")
