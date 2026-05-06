import requests

r = requests.get('https://valhalla-api-ha6a.onrender.com/deals', timeout=10)
deals = r.json() if r.status_code == 200 else []

print(f'GET /deals response: HTTP {r.status_code}')
print(f'Total deals: {len(deals)}')

if len(deals) > 0:
    print('\nLatest 3 deals:')
    for i, d in enumerate(deals[:3], 1):
        headline = d.get('headline', 'N/A')[:50]
        print(f'  {i}. {headline}')
