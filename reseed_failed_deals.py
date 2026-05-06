"""
Reseed failed deals with corrected schema (integer baths).
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:4000"
BUILDER_KEY = "test-builder-key-v0.2-verification"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": BUILDER_KEY
}

# Failed deals with integer baths (corrected)
failed_deals = [
    {
        "headline": "3BR Bungalow in Mississauga",
        "region": "Mississauga, ON",
        "property_type": "SFH",
        "price": 515000.00,
        "beds": 3,
        "baths": 2,  # Fixed from 1.5
        "notes": "Detached, updated kitchen, close to schools",
        "status": "active"
    },
    {
        "headline": "4BR Semi in North York",
        "region": "North York, ON",
        "property_type": "Semi",
        "price": 655000.00,
        "beds": 4,
        "baths": 3,  # Fixed from 2.5
        "notes": "Newly updated, move-in ready, near subway",
        "status": "active"
    },
    {
        "headline": "3BR Townhouse in Milton",
        "region": "Milton, ON",
        "property_type": "Townhouse",
        "price": 485000.00,
        "beds": 3,
        "baths": 3,  # Fixed from 2.5
        "notes": "New community, good resale, family-friendly",
        "status": "active"
    },
    {
        "headline": "2BR Freehold Townhouse in Chinatown",
        "region": "Toronto, ON",
        "property_type": "Townhouse",
        "price": 445000.00,
        "beds": 2,
        "baths": 2,  # Fixed from 1.5
        "notes": "Freehold gives flexibility, gentrifying area, development potential",
        "status": "active"
    },
]

print("=" * 70)
print("RESEED: Failed Deals (Corrected Schema)")
print("=" * 70)
print(f"\nReseeding {len(failed_deals)} corrected deals...\n")

successful = 0
failed = 0
deal_ids = []

for i, deal in enumerate(failed_deals, 1):
    clean_deal = {k: v for k, v in deal.items() if v is not None}
    
    try:
        response = requests.post(
            f"{BASE_URL}/deals",
            json=clean_deal,
            headers=headers,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            deal_id = result.get("id")
            deal_ids.append(deal_id)
            print(f"✓ Deal #{i} (ID: {deal_id}): {deal['headline'][:50]}")
            successful += 1
        else:
            print(f"✗ Deal #{i}: HTTP {response.status_code} - {deal['headline'][:50]}")
            print(f"  Response: {response.json()}")
            failed += 1
    except Exception as e:
        print(f"✗ Deal #{i}: Error - {str(e)}")
        failed += 1
    
    time.sleep(0.1)

print("\n" + "=" * 70)
print(f"Reseed complete: {successful}/{len(failed_deals)} deals created")
if deal_ids:
    print(f"New deal IDs: {deal_ids}")
