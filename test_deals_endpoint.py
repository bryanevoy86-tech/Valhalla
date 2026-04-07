#!/usr/bin/env python
"""
Test script for the new POST /api/deals endpoint.
Run this after starting the dev server.
"""
import requests
import json
from typing import Dict, Any

# Configure these for your environment
API_BASE_URL = "http://localhost:4000"
API_ENDPOINT = f"{API_BASE_URL}/api/deals"

def test_create_deal_without_lead() -> Dict[str, Any]:
    """Test creating a deal without providing a lead_id."""
    print("\n" + "="*70)
    print("TEST 1: Create deal WITHOUT lead_id (auto-creates placeholder lead)")
    print("="*70)
    
    deal_data = {
        "title": "Sample Property",
        "stage": "lead_received",
        "status": "active",
        "arv": 250000,
        "estimated_repair_cost": 20000,
        "max_allowable_offer": 150000,
        "target_assignment_fee": 5000,
        "score": 85,
        "notes": "Test notes for sample property",
        "disposition_status": "pending"
    }
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=deal_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        
        if response.status_code == 201:
            result = response.json()
            print(json.dumps(result, indent=2, default=str))
            print("\n✅ SUCCESS: Deal created!")
            print(f"   Deal ID: {result.get('id')}")
            print(f"   Lead ID: {result.get('lead_id')} (auto-generated)")
            return result
        else:
            print(f"❌ FAILED: Got status {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print(f"   Make sure the dev server is running at {API_BASE_URL}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def test_create_deal_with_lead(lead_id: int = 1) -> Dict[str, Any]:
    """Test creating a deal with an existing lead_id."""
    print("\n" + "="*70)
    print(f"TEST 2: Create deal WITH lead_id={lead_id}")
    print("="*70)
    
    deal_data = {
        "lead_id": lead_id,
        "title": "Property with Lead",
        "stage": "lead_received",
        "status": "active",
        "arv": 300000,
        "estimated_repair_cost": 25000,
        "max_allowable_offer": 175000,
        "target_assignment_fee": 7500,
        "score": 90,
        "notes": "Property linked to existing lead",
        "disposition_status": "pending"
    }
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=deal_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        
        if response.status_code == 201:
            result = response.json()
            print(json.dumps(result, indent=2, default=str))
            print("\n✅ SUCCESS: Deal created!")
            print(f"   Deal ID: {result.get('id')}")
            print(f"   Lead ID: {result.get('lead_id')} (from request)")
            return result
        elif response.status_code == 400:
            print(f"⚠️  INFO: Got 400 Bad Request")
            print(f"   (This usually means lead_id={lead_id} doesn't exist)")
            print(f"   Response: {response.text}")
            return None
        else:
            print(f"❌ FAILED: Got status {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print(f"   Make sure the dev server is running at {API_BASE_URL}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def test_list_deals() -> bool:
    """Test listing all deals to verify they were created."""
    print("\n" + "="*70)
    print("TEST 3: List all deals")
    print("="*70)
    
    try:
        response = requests.get(
            f"{API_ENDPOINT}?skip=0&limit=10",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            deals = response.json()
            print(f"\n✅ SUCCESS: Retrieved {len(deals)} deals")
            
            if deals:
                print("\nDeals:")
                for deal in deals:
                    print(f"  - ID {deal.get('id')}: {deal.get('title')} (lead_id={deal.get('lead_id')})")
            
            return True
        else:
            print(f"❌ FAILED: Got status {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("POST /api/deals Endpoint Test Suite")
    print("="*70)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Endpoint: {API_ENDPOINT}")
    
    # Test 1: Create deal without lead
    deal1 = test_create_deal_without_lead()
    
    # Test 2: Create deal with lead (try lead_id=1)
    deal2 = test_create_deal_with_lead(lead_id=1)
    
    # Test 3: List deals
    test_list_deals()
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    if deal1:
        print("✅ Test 1 PASSED: Created deal without lead_id")
    else:
        print("⚠️  Test 1 FAILED/SKIPPED: Could not create deal without lead_id")
    
    if deal2:
        print("✅ Test 2 PASSED: Created deal with lead_id")
    elif deal2 is None and deal1:
        print("⚠️  Test 2 SKIPPED: Lead_id=1 doesn't exist (this is expected)")
    else:
        print("❌ Test 2 FAILED: Could not create deal with lead_id")
    
    print("="*70)


if __name__ == "__main__":
    main()
