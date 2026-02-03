import sys
sys.path.insert(0, 'services/api')
from services.api.tools.public_training.replay_wholesaling import run_wholesaling_pipeline

test_cases = [
    {'name': 'Low ($90k)', 'assessed_value': 90000},
    {'name': 'Mid ($180k)', 'assessed_value': 180000},
    {'name': 'High ($320k)', 'assessed_value': 320000},
]

print("=== Real Adapter Output ===\n")
for tc in test_cases:
    lead = {
        'source': 'test',
        'external_id': tc['name'],
        'province': 'AB',
        'city': 'Calgary',
        'address': 'Test',
        'assessed_value': tc['assessed_value']
    }
    result = run_wholesaling_pipeline(lead)
    print(f"{tc['name']}")
    print(f"  pursue={result['should_pursue']} review={result['human_review_required']}")
    print(f"  offers: ${result['offer_low']:,.0f} - ${result['offer_high']:,.0f}\n")
