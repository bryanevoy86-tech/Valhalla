#!/usr/bin/env python
"""Quick demo of the governance orchestrator."""

from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

# Test 1: Clean deal - all gods approve
print("=" * 60)
print("TEST 1: Clean deal - all five gods should approve")
print("=" * 60)
payload = {
    'context_type': 'deal',
    'data': {
        'purchase_price': '200000',
        'repairs': '20000',
        'roi': '0.25',
        'hours_per_week': '40',
        'stress_level': '5',
        'active_verticals': '2',
        'distraction_score': '3',
        'capital_at_risk': '80000',
        'worst_case_loss': '60000',
        'probability_of_ruin': '0.02',
        'tax_evasion': 'False',
    },
    'gods': None
}

resp = client.post('/api/governance/evaluate_all', json=payload)
result = resp.json()
print(f"\nOverall Allowed: {result['overall_allowed']}")
print(f"Worst Severity: {result['worst_severity']}")
print(f"Number of Gods Checked: {len(result['checks'])}")
print(f"Summary: {result['summary']}\n")

# Test 2: Tax evasion - Tyr hard-stops
print("=" * 60)
print("TEST 2: Tax evasion violation - Tyr hard-stops")
print("=" * 60)
payload['data']['tax_evasion'] = 'True'

resp = client.post('/api/governance/evaluate_all', json=payload)
result = resp.json()
print(f"\nOverall Allowed: {result['overall_allowed']}")
print(f"Worst Severity: {result['worst_severity']}")
print(f"Blocked By: {result['blocked_by']}")
print(f"Summary: {result['summary']}\n")

# Test 3: Subset - only Odin
print("=" * 60)
print("TEST 3: Subset evaluation - only Odin")
print("=" * 60)
payload = {
    'context_type': 'new_vertical',
    'data': {
        'active_verticals': '3',
        'new_verticals': '1',
        'distraction_score': '8',
    },
    'gods': ['odin']
}

resp = client.post('/api/governance/evaluate_all', json=payload)
result = resp.json()
print(f"\nNumber of Gods Checked: {len(result['checks'])}")
print(f"Gods: {[c['god'] for c in result['checks']]}")
print(f"Overall Allowed: {result['overall_allowed']}")
print(f"Worst Severity: {result['worst_severity']}\n")

print("✓ All orchestrator demos completed successfully!")
