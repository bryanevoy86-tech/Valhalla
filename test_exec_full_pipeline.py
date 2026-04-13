#!/usr/bin/env python
import urllib.request
import json
import sys

# First, test intake endpoint
url = "https://valhalla-api-ha6a.onrender.com/execution/intake"
data = {"raw_text": "3 bed 2 bath house, 250k asking, needs roof and foundation work"}
payload = json.dumps(data).encode('utf-8')

req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
        intake_id = result.get('intake_id')
        print("✅ POST /execution/intake - 200 OK")
        print(f"   Intake ID: {intake_id}")
        print()
        
        # Now test the process endpoint with the intake_id
        if intake_id:
            process_url = f"https://valhalla-api-ha6a.onrender.com/execution/intake/{intake_id}/process"
            process_data = {"intake_id": intake_id}
            process_payload = json.dumps(process_data).encode('utf-8')
            process_req = urllib.request.Request(process_url, data=process_payload, method='POST', headers={'Content-Type': 'application/json'})
            
            try:
                with urllib.request.urlopen(process_req, timeout=60) as process_response:
                    process_result = json.load(process_response)
                    print("✅ POST /execution/intake/{id}/process - 200 OK")
                    print(json.dumps(process_result, indent=2))
            except urllib.error.HTTPError as e:
                print(f"❌ Process endpoint error {e.code}")
                body = e.read().decode()
                print(body)
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}")
    try:
        body = e.read().decode()
        print("Response Body:")
        print(body)
    except:
        pass
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

