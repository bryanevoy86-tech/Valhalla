import requests
import json

base_url = "https://valhalla-api-ha6a.onrender.com"

# Get OpenAPI spec
resp = requests.get(f"{base_url}/openapi.json")
spec = resp.json()

# Extract JUST the /deals endpoints for clarity
deals_endpoints = spec.get('paths', {})
deals_only = {k: v for k, v in deals_endpoints.items() if '/deals' in k and 'analyze' in k or 'action' in k}

print("=== Deals-related endpoints (analyze/action) ===")
for path, methods in sorted(deals_only.items()):
    print(f"{path}:")
    for method, details in methods.items():
        print(f"  {method.upper()}: {details.get('operationId', 'N/A')}")

# Check if score_deal function is in the spec
print("\n=== Searching for 'score' in operationIds ===")
all_ops = []
for path, methods in spec.get('paths', {}).items():
    for method, details in methods.items():
        op_id = details.get('operationId', '')
        if 'score' in op_id.lower() or 'analyze' in op_id.lower():
            print(f"{path} {method.upper()}: {op_id}")
            all_ops.append(op_id)

if not all_ops:
    print("No operations with 'score' or 'analyze' found")
