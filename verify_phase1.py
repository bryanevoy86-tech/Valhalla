import requests, json

# Get go-live state
resp1 = requests.get('https://valhalla-api-ha6a.onrender.com/api/governance/go-live/state')
state = resp1.json()

# Get runbook status
resp2 = requests.get('https://valhalla-api-ha6a.onrender.com/api/governance/runbook/status')
runbook = resp2.json()

print('=' * 78)
print('PHASE 1 VERIFICATION')
print('=' * 78)
print()
print('✓ Go-Live State:')
print(f'  go_live_enabled: {state["go_live_enabled"]}')
print(f'  kill_switch_engaged: {state["kill_switch_engaged"]}')
print(f'  changed_by: {state["changed_by"]}')
print()
print('✓ Runbook Status:')
print(f'  go_live.enabled: {runbook["go_live"]["enabled"]}')
print(f'  kill_switch: {runbook["go_live"]["kill_switch_engaged"]}')
print(f'  Checklist OK: {runbook.get("ok", False)}')
print()
print('✓ Engine States:')
for engine in runbook.get('engines', []):
    print(f'  {engine["engine_name"]}: {engine["state"]} (allowed_next: {engine["allowed_next"]})')
print()
print('=' * 78)
