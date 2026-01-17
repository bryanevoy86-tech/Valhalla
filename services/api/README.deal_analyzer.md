# Pack 34: Automated Deal Analyzer

## Overview
AI-driven real estate deal analysis for ROI, ARV, profitability, risk scoring, and investment recommendation. Calculates key metrics and provides an AI recommendation (pass, review, reject), with notes for decision-making.

## Models (`app/deal_analyzer/models.py`)
- **DealAnalysis**: id, property_address, purchase_price, rehab_cost, arv, expected_profit, roi, cash_on_cash_return, is_profitable, risk_score, ai_recommendation, analysis_notes, created_at, updated_at

## Schemas (`app/deal_analyzer/schemas.py`)
- **DealAnalysisCreate**: property_address, purchase_price, rehab_cost, arv
- **DealAnalysisOut**: all computed fields and timestamps
- **DealMetrics**: internal computation structure for total investment, ROI, margin, etc.

## Service (`app/deal_analyzer/service.py`)
- `analyze_and_create_deal(db, deal: DealAnalysisCreate) -> DealAnalysis`
- `get_all_analyses(db, skip: int = 0, limit: int = 100) -> list[DealAnalysis]`
- `get_analysis_by_id(db, analysis_id: int) -> DealAnalysis | None`
- `get_profitable_deals(db, min_roi: float = 0.0) -> list[DealAnalysis]`
- `get_deals_by_recommendation(db, recommendation: str) -> list[DealAnalysis]`
- `calculate_deal_metrics(purchase_price: float, rehab_cost: float, arv: float) -> DealMetrics`
- `calculate_risk_score(roi: float, margin: float, investment: float, arv: float) -> float`
- `generate_ai_recommendation(metrics: DealMetrics) -> str`

## Endpoints (`/api/deal-analyzer`)

### Analyze Deal
```
POST /analyze
Body: {
  "property_address": "123 Main St, Springfield",
  "purchase_price": 150000,
  "rehab_cost": 30000,
  "arv": 220000
}
Response: DealAnalysisOut (201 Created)
```

### List Analyses (with filtering)
```
GET /?recommendation=pass
GET /?min_roi=20
Response: List[DealAnalysisOut]
```

### Get Specific Analysis
```
GET /{analysis_id}
Response: DealAnalysisOut or 404
```

### Top Profitable Deals
```
GET /profitable/top?min_roi=25
Response: List[DealAnalysisOut]
```

## Dashboard UI
- **Route**: `/api/ui-dashboard/deal-analyzer-dashboard-ui`
- **Template**: `deal_analyzer_dashboard.html`
- **Features**:
  - Analyze new deals with purchase, rehab, ARV inputs
  - Filter by AI recommendation (pass/review/reject) or ROI threshold
  - Table view with ROI, profit, risk score, and recommendation badges

## Calculation Details
- **Total Investment**: purchase + rehab
- **Expected Profit**: ARV − investment
- **ROI %**: (profit ÷ investment) × 100
- **Profit Margin %**: (profit ÷ ARV) × 100
- **Cash-on-Cash Return**: profit ÷ (down payment + rehab) × 100 (assumes 20% down)
- **Risk Score**: Derived from ROI, margin, investment size, and purchase-to-ARV ratio
- **AI Recommendation**:
  - pass: ROI ≥ 25% and risk < 30
  - review: ROI ≥ 15% and risk < 50
  - reject: otherwise

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Analyze a deal
$deal = @{property_address="123 Main St"; purchase_price=150000; rehab_cost=30000; arv=220000} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/deal-analyzer/analyze" -Body $deal -ContentType "application/json"

# List all analyses
Invoke-RestMethod -Method Get -Uri "$API/api/deal-analyzer/"

# List by recommendation
Invoke-RestMethod -Method Get -Uri "$API/api/deal-analyzer/?recommendation=pass"

# Get by ID
Invoke-RestMethod -Method Get -Uri "$API/api/deal-analyzer/1"

# Top profitable deals
Invoke-RestMethod -Method Get -Uri "$API/api/deal-analyzer/profitable/top?min_roi=25"

# Open dashboard
start "$API/api/ui-dashboard/deal-analyzer-dashboard-ui"
```

## Integration Points
- **Pack 27 (Payments)**: Assess affordability and payment impact on ROI
- **Pack 28 (Negotiations)**: Use analysis to guide negotiation strategy and offer terms
- **Pack 30 (Adaptive Negotiator)**: Recommend negotiation techniques based on analysis outcomes
- **Analytics/Reports**: Feed analysis results into dashboards and PDF reports

## Future Enhancements
- Market comparables integration (comps) to improve ARV accuracy
- Sensitivity analysis and Monte Carlo simulations
- Loan terms integration (interest rates, points, monthly payments)
- Location scoring using external datasets
- Auto-import from MLS or property APIs
