#!/usr/bin/env python
"""Test the new deal action endpoint."""
import requests
import json

BASE_URL = "http://127.0.0.1:4000"

print("=== Testing Deal Action Endpoint ===\n")

# Test 1: Get an existing deal
print("1. Getting an existing deal...")
resp = requests.get(f"{BASE_URL}/deals?limit=1")
if resp.status_code != 200:
    print(f"   ✗ Failed to get deals: {resp.status_code}")
    print(resp.text)
    exit(1)

deals = resp.json()
if not deals:
    print("   ✗ No deals found. Please seed some deals first.")
    exit(1)

deal_id = deals[0]['id']
print(f"   ✓ Found deal ID: {deal_id}")
print(f"   Current status: {deals[0]['status']}\n")

# Test 2: Update deal with action
print("2. Testing POST /deals/{id}/action with action='hot'...")
action_payload = {"action": "hot"}
resp = requests.post(
    f"{BASE_URL}/deals/{deal_id}/action",
    json=action_payload
)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    updated = resp.json()
    print(f"   ✓ Deal updated")
    print(f"   New status: {updated['status']}")
    print(f"   Headline: {updated['headline']}\n")
else:
    print(f"   ✗ Error: {resp.text}\n")

# Test 3: Try another action
print("3. Testing action='analyzing'...")
action_payload = {"action": "analyze"}
resp = requests.post(
    f"{BASE_URL}/deals/{deal_id}/action",
    json=action_payload
)
if resp.status_code == 200:
    updated = resp.json()
    print(f"   ✓ Deal updated to status: {updated['status']}\n")
else:
    print(f"   ✗ Error: {resp.text}\n")

# Test 4: Invalid action
print("4. Testing invalid action (should fail)...")
action_payload = {"action": "invalid"}
resp = requests.post(
    f"{BASE_URL}/deals/{deal_id}/action",
    json=action_payload
)
if resp.status_code == 400:
    print(f"   ✓ Correctly rejected with 400")
    print(f"   Error: {resp.json()}\n")
else:
    print(f"   ✗ Unexpected status: {resp.status_code}\n")

# Test 5: Invalid deal ID (should fail)
print("5. Testing with invalid deal ID (should fail)...")
action_payload = {"action": "hot"}
resp = requests.post(
    f"{BASE_URL}/deals/99999/action",
    json=action_payload
)
if resp.status_code == 404:
    print(f"   ✓ Correctly returned 404")
    print(f"   Error: {resp.json()}\n")
else:
    print(f"   ✗ Unexpected status: {resp.status_code}\n")

# Test 6: Verify final state
print("6. Verifying final state with GET /deals...")
resp = requests.get(f"{BASE_URL}/deals?limit=1")
if resp.status_code == 200:
    deals = resp.json()
    if deals:
        final_deal = deals[0]
        if final_deal['id'] == deal_id:
            print(f"   ✓ Deal {deal_id} final status: {final_deal['status']}\n")
        else:
            print(f"   Note: Different deal returned (ID mismatch)\n")

print("=== All tests complete ===")
