#!/usr/bin/env python3
import time
import urllib.request
import urllib.error
import json

print('Waiting 25 more seconds for full deployment...')
for i in range(25):
    time.sleep(1)
    if (i+1) % 5 == 0:
        print(f'  {i+1}s elapsed...')

print('\nTesting endpoint...')
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/api/deals?limit=1', timeout=15)
    print(f'✅ Status: {resp.status}')
    data = json.loads(resp.read())
    print(f'✅ Response received: {len(str(data))} chars')
    print(f'Response: {json.dumps(data, default=str, indent=2)[:500]}')
    print("\n🎉 BLOCKER FIXED - GET /api/deals is now working!")
except urllib.error.HTTPError as e:
    print(f'❌ HTTP {e.code}')
    try:
        err = json.loads(e.read())
        print(f'Correlation ID: {err.get("correlation_id")}')
        print(f'Detail: {err.get("detail")}')
    except:
        print('Error response could not be parsed')
except Exception as e:
    print(f'❌ {type(e).__name__}: {e}')
