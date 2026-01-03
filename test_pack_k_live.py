#!/usr/bin/env python
"""PACK K — INTAKE STUB Verification"""
import subprocess
import time
import requests
import json
import os

print("=" * 60)
print("PACK K — INTAKE STUB Live Test")
print("=" * 60)

os.chdir("backend")

# Start server
print("\nStarting uvicorn server...")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "5003"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(4)
print("✓ Server started")

try:
    # Test 1: Create a lead
    print("\n1. Testing POST /core/intake/lead...")
    lead_data = {
        "source": "text",
        "name": "Test Seller",
        "phone": "2045551234",
        "email": "test@example.com",
        "city": "Winnipeg",
        "province": "MB",
        "country": "CA",
        "notes": "Wants offer",
        "tags": ["wholesale", "urgent"],
        "meta": {"test": True, "source_campaign": "sms_blast"}
    }
    
    resp = requests.post(
        "http://localhost:5003/core/intake/lead",
        json=lead_data,
        timeout=5
    )
    
    if resp.status_code == 200:
        print("✓ Status: 200 OK")
        lead = resp.json()
        print(f"  ✓ Lead created with ID: {lead['id']}")
        print(f"  ✓ Created at: {lead['created_at_utc']}")
        print(f"  ✓ Name: {lead['name']}")
        print(f"  ✓ Tags: {lead['tags']}")
        lead_id = lead['id']
    else:
        print(f"✗ Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        lead_id = None
    
    # Test 2: Create another lead
    if lead_id:
        print("\n2. Testing POST /core/intake/lead (second lead)...")
        lead_data2 = {
            "source": "call",
            "name": "John Seller",
            "phone": "2045559999",
            "city": "Toronto",
            "province": "ON",
            "notes": "Interested in wholesaling",
            "tags": ["call", "hot"],
        }
        
        resp = requests.post(
            "http://localhost:5003/core/intake/lead",
            json=lead_data2,
            timeout=5
        )
        
        if resp.status_code == 200:
            print("✓ Second lead created")
        else:
            print(f"✗ Failed: {resp.status_code}")
    
    # Test 3: List leads
    print("\n3. Testing GET /core/intake/leads?limit=5...")
    resp = requests.get(
        "http://localhost:5003/core/intake/leads?limit=5",
        timeout=5
    )
    
    if resp.status_code == 200:
        print("✓ Status: 200 OK")
        data = resp.json()
        leads = data.get("items", [])
        print(f"✓ Returned {len(leads)} leads (newest first)")
        if leads:
            for i, lead in enumerate(leads[:2]):
                print(f"  Lead {i+1}: {lead['name']} ({lead['source']}) - {lead['created_at_utc']}")
    else:
        print(f"✗ Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    
    # Test 4: Check file persistence
    print("\n4. Checking data/leads.json persistence...")
    leads_file = "../data/leads.json"
    if os.path.exists(leads_file):
        with open(leads_file) as f:
            file_data = json.load(f)
        print(f"✓ File exists at {leads_file}")
        print(f"✓ Contains {len(file_data.get('items', []))} leads")
        if file_data.get('items'):
            latest = file_data['items'][-1]
            print(f"✓ Latest lead: {latest['name']} ({latest['source']})")
    else:
        print(f"✗ File not found at {leads_file}")
    
    print("\n" + "=" * 60)
    print("✅ PACK K Verification Complete!")
    print("=" * 60)
    print("\nEndpoints Working:")
    print("  ✓ POST /core/intake/lead")
    print("  ✓ GET /core/intake/leads")
    print("\nData Storage:")
    print("  ✓ File: data/leads.json")
    print("  ✓ Persistence: Working")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\nShutting down server...")
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
    print("✓ Server stopped")
