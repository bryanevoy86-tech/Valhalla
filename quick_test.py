#!/usr/bin/env python
"""Quick test of lead engine API"""
import requests
import json

try:
    response = requests.get("http://localhost:9001/api/v1/lead-sources", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
