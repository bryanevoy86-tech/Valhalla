#!/usr/bin/env python
"""
Clean seed script for Render deployment.
Creates 15 realistic deals using POST /deals endpoint.

Usage:
  python seed_render_deals.py https://valhalla-api-ha6a.onrender.com
"""
import requests
import sys
import time

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://valhalla-api-ha6a.onrender.com"
# Use the existing Render BUILDER_KEY (configured in Render dashboard)
BUILDER_KEY = "a774e90bcc3de95f0513782e41fc454f"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": BUILDER_KEY
}

# 15 realistic deals
deals = [
    {"headline": "4BR Bungalow in Downtown Toronto", "region": "Toronto, ON", "property_type": "SFH", "price": 425000.00, "beds": 4, "baths": 2, "notes": "Recently renovated, hardwood floors, 2-car garage, close to transit", "status": "active"},
    {"headline": "3BR Townhouse in East York", "region": "Toronto, ON", "property_type": "Townhouse", "price": 485000.00, "beds": 3, "baths": 2, "notes": "Corner lot, finished basement, walk to shopping", "status": "active"},
    {"headline": "5BR Victorian Home in Leslieville", "region": "Toronto, ON", "property_type": "SFH", "price": 850000.00, "beds": 5, "baths": 3, "notes": "Character home, original woodwork, deep lot potential", "status": "active"},
    {"headline": "2BR Condo at Bathurst & Bloor", "region": "Toronto, ON", "property_type": "Condo", "price": 425000.00, "beds": 2, "baths": 2, "notes": "High-rise, gym, concierge, investor-friendly", "status": "active"},
    {"headline": "3BR Bungalow in Mississauga", "region": "Mississauga, ON", "property_type": "SFH", "price": 515000.00, "beds": 3, "baths": 2, "notes": "Detached, updated kitchen, close to schools", "status": "active"},
    {"headline": "Duplex in Brampton - Cash Flow Opportunity", "region": "Brampton, ON", "property_type": "Duplex", "price": 535000.00, "beds": 6, "baths": 3, "notes": "Strong rental potential, already tenant-occupied", "status": "active"},
    {"headline": "4BR Home in Markham", "region": "Markham, ON", "property_type": "SFH", "price": 625000.00, "beds": 4, "baths": 2, "notes": "Family neighborhood, updated, 3-car driveway", "status": "active"},
    {"headline": "2BR+Den Loft in King West", "region": "Toronto, ON", "property_type": "Condo", "price": 495000.00, "beds": 2, "baths": 2, "notes": "Historic building conversion, high ceilings, parking included", "status": "active"},
    {"headline": "3BR Detached in Richmond Hill", "region": "Richmond Hill, ON", "property_type": "SFH", "price": 745000.00, "beds": 3, "baths": 2, "notes": "End lot, pool-ready backyard, good for subdivision", "status": "active"},
    {"headline": "4BR Semi in North York", "region": "North York, ON", "property_type": "Semi", "price": 655000.00, "beds": 4, "baths": 3, "notes": "Newly updated, move-in ready, near subway", "status": "active"},
    {"headline": "Vacant Industrial Lot - Development Potential", "region": "Etobicoke, ON", "property_type": "Industrial", "price": 425000.00, "notes": "0.5 acres zoned M1, assembly potential, 30ft frontage", "status": "active"},
    {"headline": "6BR Estate in Oakville", "region": "Oakville, ON", "property_type": "SFH", "price": 1250000.00, "beds": 6, "baths": 4, "notes": "Prestigious area, mature trees, guest house potential", "status": "active"},
    {"headline": "2BR Apartment in Cabbagetown", "region": "Toronto, ON", "property_type": "Condo", "price": 415000.00, "beds": 2, "baths": 1, "notes": "Trendy neighborhood, walkable, vintage charm", "status": "active"},
    {"headline": "3BR Townhouse in Milton", "region": "Milton, ON", "property_type": "Townhouse", "price": 485000.00, "beds": 3, "baths": 3, "notes": "New community, good resale, family-friendly", "status": "active"},
    {"headline": "Multi-Unit Converted Mansion - 5 Units", "region": "Toronto, ON", "property_type": "Multi-Unit", "price": 2450000.00, "notes": "Roncesvalles location, strong rental history, good cash flow", "status": "active"},
]

print("=" * 70)
print(f"SEED RENDER DEPLOYMENT: {len(deals)} deals")
print(f"Target: {BASE_URL}/deals")
print("=" * 70 + "\n")

successful = 0
failed = 0

for i, deal in enumerate(deals, 1):
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
            print(f"✓ Deal #{i:2d} (ID: {deal_id}): {deal['headline'][:50]}")
            successful += 1
        else:
            print(f"✗ Deal #{i:2d}: HTTP {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"✗ Deal #{i:2d}: {str(e)}")
        failed += 1
    
    time.sleep(0.1)

print("\n" + "=" * 70)
print(f"Complete: {successful}/{len(deals)} deals seeded")
print("=" * 70)

if successful == len(deals):
    print("\n✓ ALL DEALS SEEDED!")
    print("\nNext steps:")
    print("1. GET https://valhalla-api-ha6a.onrender.com/deals")
    print("2. Verify all deals are returned")
    print("3. Connect WeWeb to https://valhalla-api-ha6a.onrender.com/deals")
else:
    print(f"\n⚠ {failed} deals failed to seed")
    print("Check Render backend logs for details")
