import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:4000"

deals_template = [
    {"title": "Fixer Upper 1", "stage": "lead_received", "status": "active", "arv": 220000, "estimated_repair_cost": 30000, "max_allowable_offer": 140000, "target_assignment_fee": 10000, "score": 78},
    {"title": "Rental Flip 2", "stage": "analysis", "status": "active", "arv": 180000, "estimated_repair_cost": 20000, "max_allowable_offer": 120000, "target_assignment_fee": 8000, "score": 72},
    {"title": "Wholesale Deal 3", "stage": "lead_received", "status": "active", "arv": 250000, "estimated_repair_cost": 35000, "max_allowable_offer": 160000, "target_assignment_fee": 12000, "score": 85},
    {"title": "Distressed Property 4", "stage": "analysis", "status": "active", "arv": 200000, "estimated_repair_cost": 40000, "max_allowable_offer": 130000, "target_assignment_fee": 9000, "score": 68},
    {"title": "Quick Flip 5", "stage": "offer", "status": "active", "arv": 300000, "estimated_repair_cost": 50000, "max_allowable_offer": 190000, "target_assignment_fee": 15000, "score": 88},
    {"title": "Off Market 6", "stage": "lead_received", "status": "active", "arv": 175000, "estimated_repair_cost": 15000, "max_allowable_offer": 115000, "target_assignment_fee": 7000, "score": 74},
    {"title": "Investor Special 7", "stage": "analysis", "status": "active", "arv": 260000, "estimated_repair_cost": 60000, "max_allowable_offer": 150000, "target_assignment_fee": 13000, "score": 81},
    {"title": "Rehab Project 8", "stage": "offer", "status": "active", "arv": 280000, "estimated_repair_cost": 55000, "max_allowable_offer": 170000, "target_assignment_fee": 14000, "score": 83},
    {"title": "Fix & Hold 9", "stage": "lead_received", "status": "active", "arv": 190000, "estimated_repair_cost": 25000, "max_allowable_offer": 125000, "target_assignment_fee": 7500, "score": 70},
    {"title": "Flip Candidate 10", "stage": "analysis", "status": "active", "arv": 310000, "estimated_repair_cost": 65000, "max_allowable_offer": 200000, "target_assignment_fee": 16000, "score": 90},
    {"title": "Underpriced Deal 11", "stage": "offer", "status": "active", "arv": 240000, "estimated_repair_cost": 30000, "max_allowable_offer": 155000, "target_assignment_fee": 11000, "score": 82},
    {"title": "Fire Sale 12", "stage": "lead_received", "status": "active", "arv": 160000, "estimated_repair_cost": 20000, "max_allowable_offer": 100000, "target_assignment_fee": 6000, "score": 69},
    {"title": "Auction Lead 13", "stage": "analysis", "status": "active", "arv": 270000, "estimated_repair_cost": 50000, "max_allowable_offer": 165000, "target_assignment_fee": 12500, "score": 84},
    {"title": "Hidden Gem 14", "stage": "offer", "status": "active", "arv": 320000, "estimated_repair_cost": 45000, "max_allowable_offer": 210000, "target_assignment_fee": 17000, "score": 91},
    {"title": "Wholesale Special 15", "stage": "lead_received", "status": "active", "arv": 210000, "estimated_repair_cost": 35000, "max_allowable_offer": 135000, "target_assignment_fee": 9500, "score": 76}
]

addresses = [
    "123 Oak Street, Springfield IL 62701",
    "456 Maple Avenue, Chicago IL 60601",
    "789 Pine Road, Peoria IL 61601",
    "321 Elm Court, Indianapolis IN 46201",
    "654 Birch Lane, Columbus OH 43215",
    "987 Cedar Drive, Cleveland OH 44114",
    "147 Spruce Way, Austin TX 78701",
    "258 Willow Street, Dallas TX 75201",
    "369 Ash Avenue, Houston TX 77001",
    "741 Poplar Court, Phoenix AZ 85001",
    "852 Hickory Drive, Philadelphia PA 19101",
    "963 Sycamore Lane, San Antonio TX 78201",
    "159 Juniper Road, San Diego CA 92101",
    "264 Magnolia Street, San Francisco CA 94102",
    "375 Dogwood Avenue, Seattle WA 98101"
]

# Transform template deals to include required fields
deals = []
for i, template in enumerate(deals_template):
    deal = {
        "deal_id": str(uuid.uuid4()),
        "address": addresses[i],
        "purchase_price": template["max_allowable_offer"],
        "reno_budget": template["estimated_repair_cost"],
        "title": template["title"],
        "arv": template["arv"],
        "stage": template["stage"],
        "status": template["status"],
        "score": template["score"],
    }
    deals.append(deal)

print(f"Inserting {len(deals)} deals to /brrrr/deals...")
success = 0
failed = 0

for deal in deals:
    try:
        response = requests.post(
            f"{BASE_URL}/brrrr/deals",
            json=deal,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code in [200, 201]:
            print(f"✓ {deal['title']}")
            success += 1
        else:
            print(f"✗ {deal['title']} - HTTP {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"✗ {deal['title']} - {str(e)}")
        failed += 1

print("\n" + "="*50)
print(f"SUCCESS: {success} deals inserted")
print(f"FAILED:  {failed} deals")
