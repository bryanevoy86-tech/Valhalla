import requests
import json

BASE_URL = 'http://127.0.0.1:4000'

# Test WITHOUT X-API-Key header
print("=" * 70)
print("GET /deals (NO X-API-Key header)")
print("=" * 70)

try:
    response = requests.get(
        f'{BASE_URL}/deals',
        timeout=5
    )
    
    print(f'\nStatus: HTTP {response.status_code}')
    
    if response.status_code == 200:
        deals = response.json()
        print(f'✓ Success! Retrieved {len(deals)} deals')
        
        if deals:
            print(f'\nFirst 3 deals:')
            for i, deal in enumerate(deals[:3], 1):
                print(f'\n  Deal #{i}:')
                print(f'    ID: {deal.get("id")}')
                print(f'    Headline: {deal.get("headline")}')
                print(f'    Region: {deal.get("region")}')
                print(f'    Type: {deal.get("property_type")}')
                print(f'    Price: ${deal.get("price")}')
    else:
        print(f'Error: {response.json()}')
        
except Exception as e:
    print(f'✗ Exception: {str(e)}')
