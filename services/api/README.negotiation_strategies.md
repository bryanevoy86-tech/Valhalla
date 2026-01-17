# Pack 30: Adaptive Negotiator (Negotiation Strategies)

## Overview
AI-driven strategy recommendation engine. Stores negotiation strategies categorized by approach (rapport, concession, framing, etc.) and provides a **/suggest** endpoint that recommends strategies based on negotiation tone and sentiment scores.

## Models (`app/negotiation_strategies/models.py`)
- **NegotiationStrategy**: id, name (String), description (Text), category (String), created_at

## Schemas (`app/negotiation_strategies/schemas.py`)
- **StrategyCreate**: name, description (optional), category (optional)
- **StrategyOut**: id, name, description, category, created_at
- **StrategySuggestionRequest**: tone_score (Float -1..1), sentiment_score (Float -1..1)

## Service (`app/negotiation_strategies/service.py`)
- `add_strategy(db, data: StrategyCreate) -> NegotiationStrategy`
- `list_strategies(db) -> list[NegotiationStrategy]`
- `suggest_strategies(db, tone_score: float, sentiment_score: float) -> list[NegotiationStrategy]`
  - **Heuristic**: low sentiment → empathy/rapport strategies; high tone → mirroring/labeling; default → framing/collaborative
  - Returns up to 5 strategies

## Endpoints (`/api/negotiation-strategies`)
- `POST /` — Add a new strategy
  - Request body: `{"name": "Mirroring", "description": "Repeat last few words to build rapport", "category": "rapport"}`
  - Returns: `StrategyOut`
- `GET /` — List all strategies
  - Returns: `List[StrategyOut]`
- `POST /suggest` — Get strategy recommendations for negotiation context
  - Request body: `{"tone_score": 0.2, "sentiment_score": -0.1}`
  - Returns: `List[StrategyOut]` (up to 5 relevant strategies)

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Add strategies
$strat1 = @{name="Labeling"; description="Name the emotion to defuse it"; category="rapport"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/negotiation-strategies/" -Body $strat1 -ContentType "application/json"

$strat2 = @{name="Calibrated Questions"; description="Ask open-ended questions"; category="collaborative"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/negotiation-strategies/" -Body $strat2 -ContentType "application/json"

# List all strategies
Invoke-RestMethod -Method Get -Uri "$API/api/negotiation-strategies/"

# Get suggestions for low sentiment negotiation
$req = @{tone_score=0.1; sentiment_score=-0.3} | ConvertTo-Json
$suggestions = Invoke-RestMethod -Method Post -Uri "$API/api/negotiation-strategies/suggest" -Body $req -ContentType "application/json"
$suggestions | Format-Table name, category
```

## Use Cases
- **Real-time Coaching**: AI assistant suggests strategies mid-negotiation based on current tone/sentiment
- **Training Simulations**: Show best-practice strategies for different scenarios
- **Integration with Pack 28 (Negotiations)**: Read current negotiation scores and recommend next moves

## Suggestion Logic (Current)
- **Sentiment < -0.2**: Favor `empathy` and `rapport` categories
- **Tone > 0.5**: Favor `mirroring` and `labeling` categories
- **Default**: Favor `framing` and `collaborative` categories
- Fallback: Return first 5 strategies if no category matches

## Dependencies
- SQLAlchemy 2.x
- No foreign keys; standalone strategy library

## Wiring
- Router guarded import in `services/api/main.py` with `negotiation_strategies_available` flag in `/debug/routes`.

## Future Enhancements
- ML-based strategy ranking using historical negotiation outcomes
- Multi-factor suggestion (consider stage, user profile, opponent traits)
- A/B testing framework for strategy effectiveness
