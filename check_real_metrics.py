import sys
sys.path.insert(0, 'services/api')
from app.deal_analyzer.service import calculate_deal_metrics

test_cases = [
    {'name': 'Low ($90k)', 'assessed_value': 90000},
    {'name': 'Mid ($180k)', 'assessed_value': 180000},
    {'name': 'High ($320k)', 'assessed_value': 320000},
]

print("=== Direct calculate_deal_metrics Output ===\n")
for tc in test_cases:
    assessed = tc['assessed_value']
    purchase_price = assessed * 0.70
    rehab_cost = max(8000, min(90000, assessed * 0.12))
    arv = assessed * 1.10
    
    metrics = calculate_deal_metrics(
        purchase_price=purchase_price,
        rehab_cost=rehab_cost,
        arv=arv,
    )
    
    print(f"{tc['name']}")
    print(f"  inputs: purchase={purchase_price:,.0f}, rehab={rehab_cost:,.0f}, arv={arv:,.0f}")
    print(f"  metrics.recommendation: {metrics.recommendation}")
    print(f"  metrics.risk_score: {metrics.risk_score}")
    print(f"  metrics.roi_percentage: {metrics.roi_percentage}")
    print(f"  metrics.expected_profit: {metrics.expected_profit:,.0f}\n")
