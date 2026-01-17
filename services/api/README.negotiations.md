# Pack 28: Behavioral Closer Engine (Negotiations)

## Overview
Store and manage negotiation interactions with tone/sentiment scoring and stage tracking. Each negotiation is linked to a user and optionally a deal. Supports creation and updating of negotiation state.

## Models (`app/negotiations/models.py`)
- **Negotiation**: id, user_id (FK→user_profiles.user_id), deal_id (optional), tone_score (Float -1..1), sentiment_score (Float -1..1), negotiation_stage (String), created_at, updated_at

## Schemas (`app/negotiations/schemas.py`)
- **NegotiationCreate**: user_id, deal_id (optional), tone_score, sentiment_score, negotiation_stage (default='initial')
- **NegotiationOut**: id, user_id, deal_id, tone_score, sentiment_score, negotiation_stage, created_at, updated_at

## Service (`app/negotiations/service.py`)
- `start_negotiation(db, negotiation: NegotiationCreate) -> Negotiation`
- `update_negotiation(db, negotiation_id: int, tone_score: float, sentiment_score: float, stage: str) -> Negotiation | None`

## Endpoints (`/api/negotiations`)
- `POST /` — Start a new negotiation
  - Request body: `{"user_id": 1, "tone_score": 0.2, "sentiment_score": 0.1, "negotiation_stage": "initial"}`
  - Returns: `NegotiationOut`
- `PUT /{negotiation_id}` — Update negotiation scores and stage
  - Query params: `tone_score`, `sentiment_score`, `stage`
  - Returns: `NegotiationOut` or 404 if not found

## Dashboard UI
- **Route**: `/api/ui-dashboard/negotiations-dashboard-ui`
- **Template**: `negotiations_dashboard.html`
- **Features**:
  - Start new negotiations with user ID, optional deal ID, and initial scores
  - Update existing negotiations (adjust tone/sentiment scores and stage)
  - Displays last created negotiation ID for easy update

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Start negotiation
$body = @{user_id=1; tone_score=0.2; sentiment_score=0.1; negotiation_stage="initial"} | ConvertTo-Json
$neg = Invoke-RestMethod -Method Post -Uri "$API/api/negotiations/" -Body $body -ContentType "application/json"
Write-Host "Created negotiation #$($neg.id)"

# Update negotiation
$negId = $neg.id
Invoke-RestMethod -Method Put -Uri "$API/api/negotiations/${negId}?tone_score=0.4&sentiment_score=0.3&stage=discussion"

# Open dashboard
start "$API/api/ui-dashboard/negotiations-dashboard-ui"
```

## Dependencies
- SQLAlchemy 2.x
- Foreign key: `user_profiles.user_id` (from Pack 24)
- Optional deal_id (assumes deals table exists)

## Wiring
- Router guarded import in `services/api/main.py` with availability flag in `/debug/routes`.
