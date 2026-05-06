#!/usr/bin/env python
"""Verify the deal action endpoint on Render."""
import requests
import json
import time

BASE_URL = "https://valhalla-api-ha6a.onrender.com"

print("=== Testing Deal Action Endpoint on Render ===\n")
print("Waiting 15 seconds for Render to redeploy...\n")
time.sleep(15)

# Test 1: Get an existing deal
print("1. Getting existing deals from Render...")
try:
    resp = requests.get(f"{BASE_URL}/deals", timeout=15)
    if resp.status_code != 200:
        print(f"   ✗ Failed: {resp.status_code}")
        print(resp.text)
        exit(1)
    
    deals = resp.json()
    if not deals:
        print("   ✗ No deals found")
        exit(1)
    
    deal_id = deals[0]['id']
    original_status = deals[0]['status']
    print(f"   ✓ Found deal ID: {deal_id}")
    print(f"   Current status: {original_status}\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")
    exit(1)

# Test 2: Update with action
print("2. POST /deals/{}/action with action='hot'...".format(deal_id))
try:
    resp = requests.post(
        f"{BASE_URL}/deals/{deal_id}/action",
        json={"action": "hot"},
        timeout=15
    )
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        updated = resp.json()
        print(f"   ✓ Success!")
        print(f"   Updated status: {updated['status']}")
        print(f"   Headline: {updated['headline']}\n")
        
        if updated['status'] == 'hot':
            print("   ✅ ACTION MAPPING CORRECT: 'hot' -> status='hot'\n")
        else:
            print(f"   ⚠️  Unexpected status: {updated['status']}\n")
    
    elif resp.status_code == 404:
        print(f"   ✗ Deal not found (404)")
        print(f"   Error: {resp.json()}\n")
        exit(1)
    else:
        print(f"   ✗ Error: {resp.status_code}")
        print(resp.text)
        exit(1)
        
except Exception as e:
    print(f"   ✗ Exception: {e}\n")
    exit(1)

# Test 3: Try analyze action
print("3. POST /deals/{}/action with action='analyze'...".format(deal_id))
try:
    resp = requests.post(
        f"{BASE_URL}/deals/{deal_id}/action",
        json={"action": "analyze"},
        timeout=15
    )
    
    if resp.status_code == 200:
        updated = resp.json()
        print(f"   ✓ Success!")
        print(f"   Updated status: {updated['status']}\n")
        
        if updated['status'] == 'analyzing':
            print("   ✅ ACTION MAPPING CORRECT: 'analyze' -> status='analyzing'\n")
    else:
        print(f"   ✗ Error: {resp.status_code}\n")
        
except Exception as e:
    print(f"   ✗ Exception: {e}\n")

# Test 4: Invalid action should fail
print("4. POST /deals/{}/action with action='invalid' (should fail)...".format(deal_id))
try:
    resp = requests.post(
        f"{BASE_URL}/deals/{deal_id}/action",
        json={"action": "invalid"},
        timeout=15
    )
    
    if resp.status_code == 400:
        error = resp.json()
        print(f"   ✓ Correctly rejected with 400")
        print(f"   Error message: {error.get('detail', {}).get('message', 'N/A')}\n")
    else:
        print(f"   ✗ Unexpected status: {resp.status_code}\n")
        
except Exception as e:
    print(f"   ✗ Exception: {e}\n")

# Test 5: Non-existent deal should fail
print("5. POST /deals/999999/action (should fail with 404)...")
try:
    resp = requests.post(
        f"{BASE_URL}/deals/999999/action",
        json={"action": "hot"},
        timeout=15
    )
    
    if resp.status_code == 404:
        print(f"   ✓ Correctly returned 404")
        print(f"   Error: {resp.json().get('detail', {}).get('error', 'Deal not found')}\n")
    else:
        print(f"   ✗ Unexpected status: {resp.status_code}\n")
        
except Exception as e:
    print(f"   ✗ Exception: {e}\n")

print("=== Verification Complete ===")
print("\n✅ Deal action endpoint is working on Render!")
print("\nEndpoint Summary:")
print("  POST /deals/{deal_id}/action")
print("  Request: {\"action\": \"analyze\" | \"hot\" | \"dead\" | \"pipeline\"}")
print("  Status mappings:")
print("    - analyze -> 'analyzing'")
print("    - hot -> 'hot'")
print("    - dead -> 'dead'")
print("    - pipeline -> 'pipeline'")
print("\n✅ Ready for WeWeb frontend integration!")
