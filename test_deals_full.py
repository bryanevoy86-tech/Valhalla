#!/usr/bin/env python
"""Test with full error details."""
import urllib.request
import json

url = "https://valhalla-api-ha6a.onrender.com/api/deals"
req = urllib.request.Request(url, method="GET")

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        body = response.read().decode('utf-8')
        print(body)
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    body = e.read().decode('utf-8')
    print(body)
    try:
        data = json.loads(body)
        print("\nParsed JSON:")
        print(json.dumps(data, indent=2))
    except:
        pass
