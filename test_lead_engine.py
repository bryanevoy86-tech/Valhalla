#!/usr/bin/env python
"""
Comprehensive test suite for Lead Acquisition Engine API.

Tests all CRUD operations and ingestion functionality.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:9001/api/v1"

print("=" * 80)
print("LEAD ACQUISITION ENGINE - COMPREHENSIVE TEST SUITE")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print(f"Test Time: {datetime.now().isoformat()}\n")

# Track results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "endpoints": []
}

def test_endpoint(method, endpoint, data=None, expected_status=200, description=""):
    """Helper function to test an endpoint"""
    results["total"] += 1
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        passed = response.status_code == expected_status
        status_icon = "✅" if passed else "❌"
        
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        print(f"{status_icon} {method:6} {endpoint:50} {response.status_code}")
        if description:
            print(f"    Description: {description}")
        
        results["endpoints"].append({
            "method": method,
            "endpoint": endpoint,
            "status": response.status_code,
            "expected": expected_status,
            "passed": passed,
            "description": description
        })
        
        return response
    
    except Exception as e:
        print(f"❌ {method:6} {endpoint:50} ERROR")
        print(f"    Error: {str(e)}")
        results["failed"] += 1
        results["endpoints"].append({
            "method": method,
            "endpoint": endpoint,
            "status": "ERROR",
            "expected": expected_status,
            "passed": False,
            "description": description,
            "error": str(e)
        })
        return None


print("\n" + "=" * 80)
print("TEST 1: LEAD SOURCE CRUD OPERATIONS")
print("=" * 80)

# Create a lead source
print("\n1a. Create Lead Source")
source_data = {
    "name": "Zillow API",
    "source_type": "api",
    "sector": "real_estate",
    "base_url": "https://api.zillow.com",
    "scrape_frequency": 24,
    "auth_type": "api_key",
    "parser_type": "json",
    "notes": "Test lead source from Zillow API"
}
response = test_endpoint("POST", "/lead-sources", source_data, 201, "Create new lead source")
source_id = None
if response and response.status_code == 201:
    source_id = response.json().get("id")
    print(f"    Created source with ID: {source_id}\n")

# List lead sources
print("1b. List Lead Sources")
test_endpoint("GET", "/lead-sources?skip=0&limit=10", None, 200, "List all lead sources")

# Get specific lead source
if source_id:
    print(f"\n1c. Get Lead Source {source_id}")
    response = test_endpoint("GET", f"/lead-sources/{source_id}", None, 200, f"Get source ID {source_id}")
    if response:
        print(f"    Response: {json.dumps(response.json(), indent=6)}\n")

# Update lead source
if source_id:
    print(f"1d. Update Lead Source {source_id}")
    update_data = {
        "status": "ok",
        "notes": "Updated notes"
    }
    response = test_endpoint("PUT", f"/lead-sources/{source_id}", update_data, 200, "Update source status")
    if response:
        print(f"    Updated source\n")


print("\n" + "=" * 80)
print("TEST 2: INGESTION TEST ENDPOINT")
print("=" * 80)

if source_id:
    print(f"\n2a. Test Ingestion for Source {source_id}")
    response = test_endpoint(
        "POST", 
        f"/lead-sources/{source_id}/ingest/test", 
        None, 
        200, 
        "Test ingestion with sample data"
    )
    if response:
        result = response.json()
        print(f"\n    Ingestion Result:")
        print(f"    - Raw leads imported: {result.get('raw_leads_imported')}")
        print(f"    - Normalized leads created: {result.get('normalized_leads_created')}")
        print(f"    - Status: {result.get('status')}")
        print(f"    - Message: {result.get('message')}\n")


print("\n" + "=" * 80)
print("TEST 3: NORMALIZED LEADS OPERATIONS")
print("=" * 80)

# List leads
print("\n3a. List Normalized Leads")
response = test_endpoint("GET", "/leads?skip=0&limit=10", None, 200, "List all normalized leads")
if response:
    leads = response.json()
    print(f"    Found {len(leads)} leads\n")
    if leads:
        first_lead = leads[0]
        lead_id = first_lead.get("id")
        
        # Get specific lead
        print(f"3b. Get Normalized Lead {lead_id}")
        response = test_endpoint("GET", f"/leads/{lead_id}", None, 200, f"Get lead ID {lead_id}")
        if response:
            print(f"    Lead: {first_lead.get('company_name')} ({first_lead.get('lead_type')})\n")
        
        # Update lead
        print(f"3c. Update Lead {lead_id}")
        lead_update = {
            "status": "review",
            "assigned_to": "john_operator",
            "tags": ["hot", "wholesaler"]
        }
        response = test_endpoint("PUT", f"/leads/{lead_id}", lead_update, 200, "Update lead status and assignment")
        if response:
            print(f"    Lead updated\n")


print("\n" + "=" * 80)
print("TEST 4: CREATE ADDITIONAL SOURCES AND LEADS")
print("=" * 80)

# Create another source
print("\n4a. Create Second Lead Source")
source_data_2 = {
    "name": "Real Estate Listing Service",
    "source_type": "scraper",
    "sector": "wholesaling",
    "base_url": "https://mls.example.com",
    "scrape_frequency": 12,
    "auth_type": "oauth",
    "parser_type": "html",
    "notes": "MLS scraper for wholesale leads"
}
response = test_endpoint("POST", "/lead-sources", source_data_2, 201, "Create second source")
source_id_2 = None
if response and response.status_code == 201:
    source_id_2 = response.json().get("id")
    print(f"    Created source with ID: {source_id_2}\n")

# Test ingestion on second source
if source_id_2:
    print(f"4b. Test Ingestion for Second Source")
    test_endpoint(
        "POST", 
        f"/lead-sources/{source_id_2}/ingest/test", 
        None, 
        200, 
        "Test second source ingestion"
    )


print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Tests: {results['total']}")
print(f"Passed:      {results['passed']} ✅")
print(f"Failed:      {results['failed']} ❌")
print(f"Pass Rate:   {(results['passed']/results['total']*100):.1f}%\n")

# Print failed tests
if results['failed'] > 0:
    print("Failed Tests:")
    for ep in results['endpoints']:
        if not ep['passed']:
            print(f"  ❌ {ep['method']:6} {ep['endpoint']}")
            if 'error' in ep:
                print(f"     Error: {ep['error']}")
    print()

print("=" * 80)
print("✅ LEAD ACQUISITION ENGINE READY FOR OPERATIONS")
print("=" * 80)
