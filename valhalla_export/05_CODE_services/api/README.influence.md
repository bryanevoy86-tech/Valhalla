# Pack 29: Influence Library

## Overview
Psychology-driven feature pack storing **Influence Techniques** (persuasion methods) and **Cognitive Biases** (mental shortcuts that affect decision-making). Provides CRUD endpoints to build and query a library of psychological patterns.

## Models (`app/influence/models.py`)
- **InfluenceTechnique**: id, name (String), description (Text), category (String), created_at
- **CognitiveBias**: id, name (String), description (Text), mitigation (Text), created_at

## Schemas (`app/influence/schemas.py`)
- **TechniqueCreate**: name, description (optional), category (optional)
- **TechniqueOut**: id, name, description, category, created_at
- **BiasCreate**: name, description (optional), mitigation (optional)
- **BiasOut**: id, name, description, mitigation, created_at

## Service (`app/influence/service.py`)
- `add_technique(db, data: TechniqueCreate) -> InfluenceTechnique`
- `list_techniques(db) -> list[InfluenceTechnique]`
- `add_bias(db, data: BiasCreate) -> CognitiveBias`
- `list_biases(db) -> list[CognitiveBias]`

## Endpoints (`/api/influence`)
- `POST /techniques` — Add a new influence technique
  - Request body: `{"name": "Reciprocity", "description": "People feel obliged to return favors", "category": "persuasion"}`
  - Returns: `TechniqueOut`
- `GET /techniques` — List all techniques
  - Returns: `List[TechniqueOut]`
- `POST /biases` — Add a new cognitive bias
  - Request body: `{"name": "Anchoring", "description": "Relying heavily on first piece of info", "mitigation": "Consider multiple reference points"}`
  - Returns: `BiasOut`
- `GET /biases` — List all cognitive biases
  - Returns: `List[BiasOut]`

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Add technique
$tech = @{name="Scarcity"; description="Limited availability increases perceived value"; category="urgency"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/influence/techniques" -Body $tech -ContentType "application/json"

# List techniques
Invoke-RestMethod -Method Get -Uri "$API/api/influence/techniques"

# Add bias
$bias = @{name="Confirmation Bias"; description="Favor info that confirms beliefs"; mitigation="Actively seek contradictory evidence"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/influence/biases" -Body $bias -ContentType "application/json"

# List biases
Invoke-RestMethod -Method Get -Uri "$API/api/influence/biases"
```

## Use Cases
- **Sales Training**: Build a reference library of persuasion techniques
- **Negotiation Preparation**: Understand biases that may affect counterparty decisions
- **Strategy Recommendations**: Power AI-driven suggestions for which techniques to apply

## Dependencies
- SQLAlchemy 2.x
- No foreign keys; standalone library tables

## Wiring
- Router guarded import in `services/api/main.py` with `influence_available` flag in `/debug/routes`.
