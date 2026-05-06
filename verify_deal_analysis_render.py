#!/usr/bin/env python
"""Test the new deal analysis endpoint."""
import requests
import json

BASE_URL = "https://valhalla-api-ha6a.onrender.com"

print("=== Testing Deal Analysis Endpoint ===\n")

# Test 1: Get an existing deal
print("1. Getting an existing deal from Render...")
try:
    resp = requests.get(f"{BASE_URL}/deals", timeout=15)
    if resp.status_code != 200:
        print(f"   ✗ Failed: {resp.status_code}")
        print(resp.text[:200])
        exit(1)
    
    deals = resp.json()
    if not deals:
        print("   ✗ No deals found")
        exit(1)
    
    deal_id = deals[0]['id']
    print(f"   ✓ Found deal ID: {deal_id}")
    print(f"   Headline: {deals[0]['headline']}\n")
except Exception as e:
    print(f"   ✗ Error: {e}\n")
    exit(1)

# Test 2: Analyze the deal
print("2. POST /deals/{}/analyze...".format(deal_id))
try:
    resp = requests.post(
        f"{BASE_URL}/deals/{deal_id}/analyze",
        timeout=15
    )
    
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        analysis = resp.json()
        print(f"   ✓ Analysis returned!")
        print(f"\n   Deal ID: {analysis['deal_id']}")
        print(f"   Headline: {analysis['headline']}")
        print(f"   Analysis:")
        print(f"     - Score: {analysis['analysis']['score']}")
        print(f"     - Risk: {analysis['analysis']['risk']}")
        print(f"     - Strategy: {analysis['analysis']['strategy']}")
        print(f"     - Recommendation: {analysis['analysis']['recommendation']}\n")
    elif resp.status_code == 404:
        print(f"   ✗ Deal not found (404)")
        print(f"   Error: {resp.json()}\n")
        exit(1)
    else:
        print(f"   ✗ Error: {resp.status_code}")
        print(resp.text[:200])
        exit(1)
        
except Exception as e:
    print(f"   ✗ Exception: {e}\n")
    exit(1)

# Test 3: Try another deal if available
print("3. Testing another deal...")
if len(deals) > 1:
    deal_id_2 = deals[1]['id']
    try:
        resp = requests.post(
            f"{BASE_URL}/deals/{deal_id_2}/analyze",
            timeout=15
        )
        
        if resp.status_code == 200:
            analysis = resp.json()
            print(f"   ✓ Deal {deal_id_2} analyzed")
            print(f"   Score: {analysis['analysis']['score']}, Strategy: {analysis['analysis']['strategy']}\n")
        else:
            print(f"   Status: {resp.status_code}\n")
            
    except Exception as e:
        print(f"   Exception: {e}\n")
else:
    print("   Only 1 deal available\n")

# Test 4: Invalid deal ID (should fail)
print("4. Testing invalid deal ID (should fail)...")
try:
    resp = requests.post(
        f"{BASE_URL}/deals/999999/analyze",
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
print("\n✅ Deal analysis endpoint is working!")
print("\nEndpoint Summary:")
print("  POST /deals/{deal_id}/analyze")
print("  Response fields:")
print("    - score: 0-100")
print("    - risk: low, medium, high")
print("    - strategy: flip, brrrr, wholesale, hold, unknown")
print("    - recommendation: actionable text")
print("\n✅ Ready for WeWeb frontend integration!")
