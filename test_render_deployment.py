import requests
import json

RENDER_URL = 'https://valhalla-api-ha6a.onrender.com'

print('=' * 70)
print('RENDER VERIFICATION TEST')
print('=' * 70)

# Test 1: Health endpoint
print('\n1. Testing GET /health')
try:
    r = requests.get(f'{RENDER_URL}/health', timeout=10)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        print(f'   ✓ Backend is alive')
except Exception as e:
    print(f'   ✗ Error: {str(e)}')

# Test 2: GET /deals without auth
print('\n2. Testing GET /deals (no X-API-Key)')
try:
    r = requests.get(f'{RENDER_URL}/deals', timeout=10)
    print(f'   Status: {r.status_code}')
    if r.status_code == 200:
        deals = r.json()
        print(f'   ✓ Success - Retrieved {len(deals)} deals')
        if deals:
            deal = deals[0]
            headline = deal.get('headline', 'N/A')[:50]
            print(f'   Sample: {headline}...')
    else:
        print(f'   Response: {r.json()}')
except Exception as e:
    print(f'   ✗ Error: {str(e)}')

# Test 3: Check token endpoint
print('\n3. Testing POST /ops/token')
try:
    payload = {'username': 'admin', 'password': 'admin'}
    r = requests.post(f'{RENDER_URL}/ops/token', json=payload, timeout=10)
    print(f'   Status: {r.status_code}')
    if r.status_code in [200, 401, 422]:
        print(f'   ✓ Endpoint responds (auth may require valid creds)')
    else:
        print(f'   Response: {r.text}')
except Exception as e:
    print(f'   ✗ Error: {str(e)}')

print('\n' + '=' * 70)
