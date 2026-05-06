"""
Bulk seed script for universal deals.
Creates 15-20 realistic property opportunities using POST /deals endpoint.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:4000"
BUILDER_KEY = "test-builder-key-v0.2-verification"  # From .env

headers = {
    "Content-Type": "application/json",
    "X-API-Key": BUILDER_KEY
}

# 15 realistic deals across multiple regions and property types
deals = [
    {
        "headline": "4BR Bungalow in Downtown Toronto",
        "region": "Toronto, ON",
        "property_type": "SFH",
        "price": 425000.00,
        "beds": 4,
        "baths": 2,
        "notes": "Recently renovated, hardwood floors, 2-car garage, close to transit",
        "status": "active"
    },
    {
        "headline": "3BR Townhouse in East York",
        "region": "Toronto, ON",
        "property_type": "Townhouse",
        "price": 485000.00,
        "beds": 3,
        "baths": 2,
        "notes": "Corner lot, finished basement, walk to shopping",
        "status": "active"
    },
    {
        "headline": "5BR Victorian Home in Leslieville",
        "region": "Toronto, ON",
        "property_type": "SFH",
        "price": 850000.00,
        "beds": 5,
        "baths": 3,
        "notes": "Character home, original woodwork, deep lot potential",
        "status": "active"
    },
    {
        "headline": "2BR Condo at Bathurst & Bloor",
        "region": "Toronto, ON",
        "property_type": "Condo",
        "price": 425000.00,
        "beds": 2,
        "baths": 2,
        "notes": "High-rise, gym, concierge, investor-friendly",
        "status": "active"
    },
    {
        "headline": "3BR Bungalow in Mississauga",
        "region": "Mississauga, ON",
        "property_type": "SFH",
        "price": 515000.00,
        "beds": 3,
        "baths": 1.5,
        "notes": "Detached, updated kitchen, close to schools",
        "status": "active"
    },
    {
        "headline": "Duplex in Brampton - Cash Flow Opportunity",
        "region": "Brampton, ON",
        "property_type": "Duplex",
        "price": 535000.00,
        "beds": 6,
        "baths": 3,
        "notes": "Strong rental potential, already tenant-occupied, renovations done",
        "status": "active"
    },
    {
        "headline": "4BR Home in Markham",
        "region": "Markham, ON",
        "property_type": "SFH",
        "price": 625000.00,
        "beds": 4,
        "baths": 2,
        "notes": "Family neighborhood, updated, 3-car driveway",
        "status": "active"
    },
    {
        "headline": "2BR+Den Loft in King West",
        "region": "Toronto, ON",
        "property_type": "Condo",
        "price": 495000.00,
        "beds": 2,
        "baths": 2,
        "notes": "Historic building conversion, high ceilings, parking included",
        "status": "active"
    },
    {
        "headline": "3BR Detached in Richmond Hill",
        "region": "Richmond Hill, ON",
        "property_type": "SFH",
        "price": 745000.00,
        "beds": 3,
        "baths": 2,
        "notes": "End lot, pool-ready backyard, good for subdivision",
        "status": "active"
    },
    {
        "headline": "4BR Semi in North York",
        "region": "North York, ON",
        "property_type": "Semi",
        "price": 655000.00,
        "beds": 4,
        "baths": 2.5,
        "notes": "Newly updated, move-in ready, near subway",
        "status": "active"
    },
    {
        "headline": "Vacant Industrial Lot - Development Potential",
        "region": "Etobicoke, ON",
        "property_type": "Industrial",
        "price": 425000.00,
        "beds": None,
        "baths": None,
        "notes": "0.5 acres zoned M1, assembly potential, 30ft frontage",
        "status": "active"
    },
    {
        "headline": "6BR Estate in Oakville",
        "region": "Oakville, ON",
        "property_type": "SFH",
        "price": 1250000.00,
        "beds": 6,
        "baths": 4,
        "notes": "Prestigious area, mature trees, guest house potential",
        "status": "active"
    },
    {
        "headline": "2BR Apartment in Cabbagetown",
        "region": "Toronto, ON",
        "property_type": "Condo",
        "price": 415000.00,
        "beds": 2,
        "baths": 1,
        "notes": "Trendy neighborhood, walkable, vintage charm",
        "status": "active"
    },
    {
        "headline": "3BR Townhouse in Milton",
        "region": "Milton, ON",
        "property_type": "Townhouse",
        "price": 485000.00,
        "beds": 3,
        "baths": 2.5,
        "notes": "New community, good resale, family-friendly",
        "status": "active"
    },
    {
        "headline": "Multi-Unit Converted Mansion - 5 Units",
        "region": "Toronto, ON",
        "property_type": "Multi-Unit",
        "price": 2450000.00,
        "beds": None,
        "baths": None,
        "notes": "Roncesvalles location, strong rental history, good cash flow",
        "status": "active"
    },
    {
        "headline": "2BR Freehold Townhouse in Chinatown",
        "region": "Toronto, ON",
        "property_type": "Townhouse",
        "price": 445000.00,
        "beds": 2,
        "baths": 1.5,
        "notes": "Freehold gives flexibility, gentrifying area, development potential",
        "status": "active"
    },
    {
        "headline": "4BR Home with Laneway House - Rosedale",
        "region": "Toronto, ON",
        "property_type": "SFH",
        "price": 1850000.00,
        "beds": 4,
        "baths": 3,
        "notes": "Established area, laneway component adds value, mature landscaping",
        "status": "active"
    },
    {
        "headline": "3BR + Office in Old Toronto",
        "region": "Toronto, ON",
        "property_type": "SFH",
        "price": 545000.00,
        "beds": 3,
        "baths": 2,
        "notes": "Home office setup, updated, excellent walkability score",
        "status": "active"
    },
    {
        "headline": "1BR Condo Studio in Entertainment District",
        "region": "Toronto, ON",
        "property_type": "Condo",
        "price": 325000.00,
        "beds": 1,
        "baths": 1,
        "notes": "Core location, entertainment district, investor flip potential",
        "status": "active"
    },
    {
        "headline": "Stacked Townhouse in Regent Park",
        "region": "Toronto, ON",
        "property_type": "Townhouse",
        "price": 595000.00,
        "beds": 3,
        "baths": 2,
        "notes": "Modern design, new neighborhood transformation, strong appreciation potential",
        "status": "active"
    },
]

print("=" * 70)
print("BULK SEED: Universal Deals")
print("=" * 70)
print(f"\nSeeding {len(deals)} deals via POST {BASE_URL}/deals")
print(f"Headers: X-API-Key: {BUILDER_KEY}\n")

successful = 0
failed = 0
deal_ids = []

for i, deal in enumerate(deals, 1):
    # Filter out None values for cleaner payload
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
            print(f"✓ Deal #{i:2d} (ID: {deal_id:3d}): {deal['headline'][:50]}")
            successful += 1
        else:
            print(f"✗ Deal #{i:2d}: HTTP {response.status_code} - {deal['headline'][:50]}")
            print(f"  Response: {response.json()}")
            failed += 1
    except Exception as e:
        print(f"✗ Deal #{i:2d}: Error - {str(e)}")
        failed += 1
    
    # Small delay to avoid overwhelming the server
    time.sleep(0.1)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total deals processed: {len(deals)}")
print(f"✓ Successfully created: {successful}")
print(f"✗ Failed: {failed}")

if deal_ids:
    print(f"\n✓ Created deal IDs: {deal_ids}")
    print(f"\n✓ BULK SEED COMPLETE! {successful}/{len(deals)} deals inserted.")
    print(f"\nNext steps:")
    print(f"1. Verify deals appear in WeWeb dashboard")
    print(f"2. Test bulk GET /deals endpoint")
    print(f"3. Test filtering by region: GET /deals?status=active")
else:
    print(f"\n✗ No deals were created. Check backend logs.")
