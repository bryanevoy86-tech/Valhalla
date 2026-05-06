import requests

RENDER_URL = 'https://valhalla-api-ha6a.onrender.com'
BUILDER_KEY = 'a774e90bcc3de95f0513782e41fc454f'

print('Testing one POST /deals with Render BUILDER_KEY')
print('=' * 70)

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': BUILDER_KEY
}

payload = {
    'headline': 'Test Deal - Render Verification'
}

try:
    r = requests.post(
        f'{RENDER_URL}/deals',
        json=payload,
        headers=headers,
        timeout=10
    )
    
    print(f'Status: {r.status_code}')
    
    if r.status_code in [200, 201]:
        deal = r.json()
        print('✓ SUCCESS - Deal created')
        print(f'  Deal ID: {deal.get("id")}')
        print(f'  Headline: {deal.get("headline")}')
    else:
        print('✗ FAILED')
        print(f'  Response: {r.json()}')
        
except Exception as e:
    print(f'✗ ERROR: {str(e)}')
