#!/usr/bin/env python3
"""
PHASE 3 BATCH LEAD GENERATOR
Generates 150 realistic real estate leads across 3 CSV files for extended testing.
Safe: reads from file system only, writes to data/inbox/real_leads/, zero network calls.
"""

import os
import csv
from datetime import datetime, timedelta
import random
import json

BATCH_SIZE = 50  # 50 leads per file = 150 total

# Cities and neighborhoods
cities = [
    "Winnipeg", "Brandon", "Selkirk", "Portage la Prairie", "Thompson",
    "Dauphin", "Neepawa", "Virden", "Morden", "Altona"
]

# Real estate segments
segments = [
    "Residential", "Condo", "Commercial", "Investment", "Fixer-Upper",
    "New Construction", "Rural", "Urban", "Suburban", "Development"
]

# Lead sources
sources = [
    "Website", "Referral", "Facebook", "Instagram", "Google Ads",
    "Walk-in", "Phone", "Email", "Event", "Direct Mail"
]

# Property types
property_types = [
    "Single Family", "Multi-Unit", "Townhouse", "Apartment",
    "Land", "Commercial Space", "Mixed-Use", "Mobile Home"
]

# Generate realistic lead data
def generate_lead_batch(batch_num: int, start_id: int = 1) -> list:
    """Generate 50 realistic leads for batch"""
    leads = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(BATCH_SIZE):
        lead_id = f"PHASE3_B{batch_num}_L{start_id + i:03d}"
        
        # Realistic price range: $150k to $800k
        price = random.randint(150000, 800000)
        # Score correlates loosely with price (expensive = slightly higher score)
        score = min(100, 40 + int((price - 150000) / 8000) + random.randint(-15, 15))
        
        lead = {
            "lead_id": lead_id,
            "name": f"Contact {i+1}",
            "phone": f"+1 (204) {random.randint(200,999)}-{random.randint(1000,9999)}",
            "email": f"contact{i+1}@example.com",
            "city": random.choice(cities),
            "property_type": random.choice(property_types),
            "budget": f"${price:,}",
            "segment": random.choice(segments),
            "source": random.choice(sources),
            "score": score,
            "interested_in": random.choice(["buy", "sell", "invest"]),
            "created_at": (base_date + timedelta(days=random.randint(0, 90))).isoformat()
        }
        leads.append(lead)
    
    return leads

def write_batch_csv(batch_num: int, leads: list) -> str:
    """Write batch to CSV"""
    filename = f"data/inbox/real_leads/batch_{batch_num:02d}_leads.csv"
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'lead_id', 'name', 'phone', 'email', 'city', 'property_type',
            'budget', 'segment', 'source', 'score', 'interested_in', 'created_at'
        ])
        writer.writeheader()
        writer.writerows(leads)
    
    return filename

def main():
    # Ensure directory exists
    os.makedirs("data/inbox/real_leads", exist_ok=True)
    
    print("=" * 70)
    print("PHASE 3 BATCH GENERATOR - 150 LEADS ACROSS 3 FILES")
    print("=" * 70)
    print()
    
    all_leads = []
    current_id = 1
    
    for batch_num in range(1, 4):  # 3 batches
        print(f"[{batch_num}/3] Generating batch {batch_num} ({BATCH_SIZE} leads)...")
        leads = generate_lead_batch(batch_num, current_id)
        all_leads.extend(leads)
        
        filename = write_batch_csv(batch_num, leads)
        print(f"  -> Wrote {len(leads)} leads to {filename}")
        scores = [l['score'] for l in leads]
        print(f"     Score range: {min(scores)}-{max(scores)}")
        budgets = [int(l['budget'].replace('$','').replace(',','')) for l in leads]
        print(f"     Budget range: ${min(budgets):,} - ${max(budgets):,}")
        
        current_id += BATCH_SIZE
        print()
    
    print("=" * 70)
    print(f"SUCCESS: Generated 150 leads across 3 CSV files")
    print(f"Location: data/inbox/real_leads/batch_*.csv")
    print("=" * 70)
    print()
    print("NEXT STEPS:")
    print("1. Run: python SANDBOX_ACTIVATION.py")
    print("2. Monitor: tail -f output.log")
    print("3. Check exports: ls -lart ops/exports/*.csv")
    print("4. Verify scoring: head ops/exports/sandbox_leads_*.csv")
    print()

if __name__ == "__main__":
    main()
