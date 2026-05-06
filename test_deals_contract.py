import requests
import json

BASE_URL = "http://127.0.0.1:4000"
BUILDER_KEY = "test-builder-key-v0.2-verification"  # From .env

headers = {
    "Content-Type": "application/json",
    "X-API-Key": BUILDER_KEY
}

print("=" * 70)
print("STEP 1: Test minimal payload (headline only)")
print("=" * 70)

minimal_payload = {
    "headline": "Test Deal - Minimal"
}

print(f"\nPayload:\n{json.dumps(minimal_payload, indent=2)}")
print(f"\nPOST {BASE_URL}/deals")
print(f"Headers: X-API-Key: {BUILDER_KEY}")

try:
    response = requests.post(
        f"{BASE_URL}/deals",
        json=minimal_payload,
        headers=headers,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    minimal_success = response.status_code in [200, 201]
except Exception as e:
    print(f"ERROR: {str(e)}")
    minimal_success = False

print("\n" + "=" * 70)
print("STEP 2: Test full recommended payload")
print("=" * 70)

full_payload = {
    "headline": "4BR Bungalow in Downtown Toronto",
    "region": "Toronto, ON",
    "property_type": "SFH",
    "price": 425000.00,
    "beds": 4,
    "baths": 2,
    "notes": "Recently renovated, hardwood floors, 2-car garage, close to transit",
    "status": "active"
}

print(f"\nPayload:\n{json.dumps(full_payload, indent=2)}")
print(f"\nPOST {BASE_URL}/deals")

try:
    response = requests.post(
        f"{BASE_URL}/deals",
        json=full_payload,
        headers=headers,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    full_success = response.status_code in [200, 201]
except Exception as e:
    print(f"ERROR: {str(e)}")
    full_success = False

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Minimal payload (headline only): {'✓ PASS' if minimal_success else '✗ FAIL'}")
print(f"Full payload (all fields): {'✓ PASS' if full_success else '✗ FAIL'}")

if minimal_success or full_success:
    print("\n✓ Contract confirmed. Ready to bulk seed 15 deals.")
else:
    print("\n✗ Both payloads failed. Check backend logs.")
