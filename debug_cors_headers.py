#!/usr/bin/env python
"""Debug script to see all headers from Render."""
import requests

resp = requests.get("https://valhalla-api-ha6a.onrender.com/health")
print("Status:", resp.status_code)
print("\nAll headers:")
for key, value in resp.headers.items():
    print(f"  {key}: {value}")

print("\n" + "="*50)
print("Checking access-control-* headers:")
for key in resp.headers:
    if "access-control" in key.lower():
        print(f"  FOUND: {key}={resp.headers[key]}")
        
if not any("access-control" in k.lower() for k in resp.headers):
    print("  NONE FOUND - CORS not working")
