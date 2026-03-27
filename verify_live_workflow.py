#!/usr/bin/env python
"""Live seeded workflow verification against the canonical API."""

import json
import sys
import os
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("DATABASE_URL", "sqlite:///valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "dev-secret-key")
os.environ.setdefault("BUILDER_KEY", "test-builder-key-v0.2-verification")

# Import app
sys.path.insert(0, 'services/api')
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

DEAL_ID = 1
AUTH_HEADER = {"X-API-Key": "test-builder-key-v0.2-verification"}

print("\n" + "=" * 80)
print("SEEDED WORKFLOW VERIFICATION")
print("=" * 80)
print(f"\nTesting deal_id={DEAL_ID} through complete workflow\n")

results = {}

# STEP 1: List deals (should see our seeded deal)
print("[STEP 1] GET /api/deals")
print("-" * 80)
response = client.get("/api/deals", headers=AUTH_HEADER)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)[:500]}")
results['list_deals'] = {
    'status': response.status_code,
    'count': len(data) if isinstance(data, list) else 0,
    'has_deal_1': any(d.get('id') == DEAL_ID for d in data) if isinstance(data, list) else False,
    'data': data
}

# STEP 2: Heimdall analyze
print("\n[STEP 2] POST /api/heimdall/deals/1/analyze")
print("-" * 80)
response = client.post(f"/api/heimdall/deals/{DEAL_ID}/analyze", headers=AUTH_HEADER)
print(f"Status: {response.status_code}")
try:
    data = response.json()
    analysis_snippet = {
        'deal_id': data.get('deal_id'),
        'current_stage': data.get('current_stage'),
        'blocker_flags': data.get('blocker_flags'),
        'risk_flags': data.get('risk_flags'),
        'recommendations': data.get('recommendations')
    }
    print(f"Response: {json.dumps(analysis_snippet, indent=2)}")
    results['heimdall_analyze'] = {
        'status': response.status_code,
        'deal_id': data.get('deal_id'),
        'current_stage': data.get('current_stage'),
        'blockers': data.get('blocker_flags'),
        'recommendations': data.get('recommendations'),
        'full_response': data
    }
except Exception as e:
    print(f"Error: {str(e)[:200]}")
    results['heimdall_analyze'] = {'status': response.status_code, 'error': str(e)[:100]}

# STEP 3: Heimdall advance stage
print("\n[STEP 3] POST /api/heimdall/deals/1/advance-stage")
print("-" * 80)
response = client.post(
    f"/api/heimdall/deals/{DEAL_ID}/advance-stage",
    json={"requested_stage": "lead_received", "approved_by": "test-workflow", "reason": "Stage advancement test"},
    headers=AUTH_HEADER
)
print(f"Status: {response.status_code}")
try:
    data = response.json()
    advance_snippet = {
        'deal_id': data.get('deal_id'),
        'action': data.get('action'),
        'previous_stage': data.get('previous_stage'),
        'new_stage': data.get('new_stage'),
        'result': data.get('result')
    }
    print(f"Response: {json.dumps(advance_snippet, indent=2)}")
    results['heimdall_advance'] = {
        'status': response.status_code,
        'deal_id': data.get('deal_id'),
        'action': data.get('action'),
        'previous_stage': data.get('previous_stage'),
        'new_stage': data.get('new_stage'),
        'result': data.get('result'),
        'full_response': data
    }
except Exception as e:
    print(f"Error: {str(e)[:200]}")
    results['heimdall_advance'] = {'status': response.status_code, 'error': str(e)[:100]}

# STEP 4: Audit trail
print("\n[STEP 4] GET /api/audit/deals/1")
print("-" * 80)
response = client.get(f"/api/audit/deals/{DEAL_ID}", headers=AUTH_HEADER)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2) if data else '[]'}")
results['audit_trail'] = {
    'status': response.status_code,
    'event_count': len(data) if isinstance(data, list) else 0,
    'data': data
}

# STEP 5: Dashboard pipeline
print("\n[STEP 5] GET /api/dashboard/pipeline")
print("-" * 80)
response = client.get("/api/dashboard/pipeline", headers=AUTH_HEADER)
print(f"Status: {response.status_code}")
try:
    data = response.json()
    pipeline_snippet = {
        'total_deals': data.get('total_deals'),
        'deals_in_pipeline': len(data.get('deals', [])) if isinstance(data.get('deals'), list) else 0,
        'has_deal_1': any(d.get('deal_id') == DEAL_ID for d in data.get('deals', [])) if isinstance(data.get('deals'), list) else False
    }
    print(f"Response: {json.dumps(pipeline_snippet, indent=2)}")
    results['dashboard_pipeline'] = {
        'status': response.status_code,
        'total_deals': data.get('total_deals'),
        'deals_count': len(data.get('deals', [])) if isinstance(data.get('deals'), list) else 0,
        'has_deal_1': any(d.get('deal_id') == DEAL_ID for d in data.get('deals', [])) if isinstance(data.get('deals'), list) else False,
        'full_response': data
    }
except Exception as e:
    print(f"Error: {str(e)[:200]}")
    results['dashboard_pipeline'] = {'status': response.status_code, 'error': str(e)[:100]}

# SUMMARY
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

summary = {
    'timestamp': datetime.now().isoformat(),
    'deal_id': DEAL_ID,
    'results': results,
    'success_criteria': {
        'step1_list_shows_deal': results['list_deals'].get('has_deal_1', False),
        'step2_analyze_returns_200_or_200range': 200 <= results['heimdall_analyze'].get('status', 0) < 300,
        'step3_advance_returns_200_or_200range': 200 <= results['heimdall_advance'].get('status', 0) < 300,
        'step4_audit_returns_200': results['audit_trail'].get('status', 0) == 200,
        'step5_dashboard_shows_deal': results['dashboard_pipeline'].get('has_deal_1', False),
        'no_500_errors': all(
            results[k].get('status', 0) < 500 
            for k in ['list_deals', 'heimdall_analyze', 'heimdall_advance', 'audit_trail', 'dashboard_pipeline']
        )
    }
}

print("\nCriteria:")
for crit, value in summary['success_criteria'].items():
    status = "✓" if value else "✗"
    print(f"  {status} {crit}")

all_pass = all(summary['success_criteria'].values())
print(f"\n{'✓ ALL CRITERIA MET' if all_pass else '✗ SOME CRITERIA FAILED'}")

# Write detailed report
with open('workflow_verification_results.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n✓ Detailed results saved to: workflow_verification_results.json")
