import time
import requests

print("Waiting 90 seconds for Render rebuild...")
time.sleep(90)

print("\n=== Test 1: POST /deals/ui-create (NEW) ===")
deal_payload = {
    "headline": "WeWeb Created Deal - Test Property",
    "region": "Toronto, ON",
    "property_type": "Single Family",
    "price": 450000,
    "beds": 3,
    "baths": 2,
    "notes": "Created via WeWeb UI without BUILDER_KEY"
}

try:
    r = requests.post(
        "https://valhalla-api-ha6a.onrender.com/deals/ui-create",
        json=deal_payload
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"✅ Success - Created deal ID: {result['id']}")
        print(f"   Headline: {result['headline']}")
        print(f"   Status: {result['status']}")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Failed: {e}")

print("\n=== Test 2: GET /deals (verify new record appears) ===")
try:
    r = requests.get("https://valhalla-api-ha6a.onrender.com/deals")
    if r.status_code == 200:
        deals = r.json()
        print(f"Total deals: {len(deals)}")
        # Find our test deal
        for deal in deals:
            if "WeWeb Created Deal" in deal.get("headline", ""):
                print(f"✅ Found our test deal!")
                print(f"   ID: {deal['id']}")
                print(f"   Headline: {deal['headline']}")
                break
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Failed: {e}")

print("\n=== Test 3: POST /deals/ui-create with minimal data ===")
minimal_payload = {
    "headline": "Minimal Deal - Only headline"
}

try:
    r = requests.post(
        "https://valhalla-api-ha6a.onrender.com/deals/ui-create",
        json=minimal_payload
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"✅ Success - Created deal with minimal data")
        print(f"   ID: {result['id']}")
        print(f"   Status: {result['status']} (defaulted to active)")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Failed: {e}")

print("\n=== Test 4: POST /deals/ui-create missing headline (should fail) ===")
invalid_payload = {
    "region": "Toronto, ON"
}

try:
    r = requests.post(
        "https://valhalla-api-ha6a.onrender.com/deals/ui-create",
        json=invalid_payload
    )
    print(f"Status: {r.status_code}")
    if r.status_code >= 400:
        print(f"✅ Correctly rejected - {r.json()['detail']}")
    else:
        print(f"❌ Should have rejected but got: {r.text[:200]}")
except Exception as e:
    print(f"Failed: {e}")
