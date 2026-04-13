#!/usr/bin/env python
import urllib.request
import json
import sys

url = "https://valhalla-api-ha6a.onrender.com/execution/intake"
data = {"raw_text": "3 bed 2 bath house, 250k asking, needs roof and foundation work"}
payload = json.dumps(data).encode('utf-8')

req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
        print("✅ SUCCESS 200 OK")
        print(json.dumps(result, indent=2))
        sys.exit(0)
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}")
    try:
        body = e.read().decode()
        print("Response Body:")
        print(body)
    except:
        pass
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
