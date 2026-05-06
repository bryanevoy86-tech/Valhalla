import requests
import json

BASE_URL = "http://127.0.0.1:4000"

endpoints_to_test = [
    ("POST", "/wholesale/leads", {"lead_id": "TEST-001", "source": "backend_test", "property_address": "123 Main St, Toronto"}),
    ("POST", "/intelligence/opportunities/", {"source_type": "deal", "title": "Test Opportunity"}),
    ("POST", "/deals/offers/compute", {"property_price": 400000, "strategy": "flip"}),
]

print(f"Testing alternative deal/opportunity endpoints...\n")

for method, endpoint, payload in endpoints_to_test:
    print(f"{method} {BASE_URL}{endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        if method == "POST":
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 500:
            try:
                resp_data = response.json()
                print(f"Response: {json.dumps(resp_data, indent=2)[:200]}...")
            except:
                print(f"Response: {response.text[:200]}")
            success = response.status_code in [200, 201]
            print(f"Result: {'✓ WORKS' if success else '⚠ RESPONSE RECEIVED'}\n")
        else:
            print(f"Response: {response.text[:100]}")
            print("Result: ✗ SERVER ERROR\n")
            
    except Exception as e:
        print(f"ERROR: {str(e)}\n")
