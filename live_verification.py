#!/usr/bin/env python3
"""Live endpoint verification - final test."""

import urllib.request
import urllib.error
import json

print("="*70)
print("LIVE ENDPOINT VERIFICATION")
print("="*70)

# Test 1: Health
print("\n1. GET /health")
print("-"*70)
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/health', timeout=15)
    print(f"Status: {resp.status}")
    print(f"Headers:")
    for header, value in resp.headers.items():
        print(f"  {header}: {value}")
    body = resp.read().decode()
    print(f"Body: {body}")
    health_status = "✅ PASS"
except Exception as e:
    print(f"❌ Error: {e}")
    health_status = "❌ FAIL"

# Test 2: Deals
print("\n2. GET /api/deals")
print("-"*70)
deals_status = None
deals_body = None
try:
    resp = urllib.request.urlopen('https://valhalla-api-ha6a.onrender.com/api/deals', timeout=15)
    status_code = resp.status
    body = resp.read().decode()
    
    print(f"Status: {status_code}")
    print(f"Headers:")
    for header, value in resp.headers.items():
        print(f"  {header}: {value}")
    print(f"Body: {body[:500]}" + ("..." if len(body) > 500 else ""))
    
    deals_status = f"✅ PASS ({status_code})"
    deals_body = body
except urllib.error.HTTPError as e:
    status_code = e.code
    body = e.read().decode()
    
    print(f"Status: {status_code}")
    print(f"Error body: {body[:500]}" + ("..." if len(body) > 500 else ""))
    
    deals_status = f"❌ FAIL ({status_code})"
    deals_body = body

# Summary
print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70)
print(f"/health:      {health_status}")
print(f"/api/deals:   {deals_status}")

if "200" in str(deals_status):
    print("\n🎉 BLOCKER FIXED - GET /api/deals returns 200")
else:
    print("\n⚠️  GET /api/deals still not 200 - check logs")

print("="*70)
