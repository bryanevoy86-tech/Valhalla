import requests
resp = requests.get('https://valhalla-api-ha6a.onrender.com/health')
print(f'Health: {resp.status_code}')

resp2 = requests.get('https://valhalla-api-ha6a.onrender.com/api/governance/go-live/state')
print(f'Go-live endpoint: {resp2.status_code}')
if resp2.status_code == 200:
    print(resp2.json())
else:
    print(resp2.text)

resp3 = requests.get('https://valhalla-api-ha6a.onrender.com/api/governance/runbook/status')
print(f'Build timestamp: {resp3.json().get("generated_at")}')
