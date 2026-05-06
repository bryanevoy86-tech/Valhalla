import requests

BASE_URL = 'http://127.0.0.1:4000'
BUILDER_KEY = 'test-builder-key-v0.2-verification'

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': BUILDER_KEY
}

payload = {
    'headline': 'Test Deal - Single Insert'
}

try:
    response = requests.post(
        f'{BASE_URL}/deals',
        json=payload,
        headers=headers,
        timeout=5
    )
    
    print(f'Status: HTTP {response.status_code}')
    result = response.json()
    
    if response.status_code in [200, 201]:
        print('✓ Deal created successfully')
        print(f'  Deal ID: {result.get("id")}')
        print(f'  Headline: {result.get("headline")}')
    else:
        print(f'✗ Error: {result}')
except Exception as e:
    print(f'✗ Exception: {str(e)}')
