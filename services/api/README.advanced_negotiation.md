# Pack 32: Advanced Negotiation Techniques

## Overview
Data-driven negotiation strategy optimization using AI and effectiveness scoring. Store, rank, and recommend negotiation techniques based on empirical effectiveness scores (0-100 scale). Supports technique categorization and dynamic score updates based on real-world performance.

## Models (`app/advanced_negotiation/models.py`)
- **NegotiationTechnique**: id, technique_name (indexed), description, effectiveness_score (Float 0-100), technique_type (category), created_at
  - **Technique Types**: Anchoring, Framing, Persuasion, Rapport, Concession, Mirroring, etc.
  - **Effectiveness Score**: Quantifiable metric for technique success rate

## Schemas (`app/advanced_negotiation/schemas.py`)
- **NegotiationTechniqueCreate**: technique_name, description, effectiveness_score (0-100), technique_type (optional)
- **NegotiationTechniqueOut**: id, technique_name, description, effectiveness_score, technique_type, created_at
- **TechniqueRankingRequest**: min_score (default 0.0), technique_type (optional filter)

## Service (`app/advanced_negotiation/service.py`)
- `create_technique(db, technique: NegotiationTechniqueCreate) -> NegotiationTechnique`
- `get_all_techniques(db) -> list[NegotiationTechnique]` — sorted by effectiveness descending
- `get_technique_by_id(db, technique_id: int) -> NegotiationTechnique | None`
- `get_techniques_by_type(db, technique_type: str) -> list[NegotiationTechnique]`
- `get_top_techniques(db, min_score: float = 70.0, limit: int = 10) -> list[NegotiationTechnique]`
- `update_technique_score(db, technique_id: int, new_score: float) -> NegotiationTechnique | None`

## Endpoints (`/api/advanced-negotiation-techniques`)

### Create Technique
```
POST /
Body: {
  "technique_name": "Anchoring Bias",
  "description": "Present an initial high value to anchor expectations",
  "effectiveness_score": 87.5,
  "technique_type": "Anchoring"
}
Response: NegotiationTechniqueOut (201 Created)
```

### List All Techniques (sorted by effectiveness)
```
GET /?technique_type=Persuasion
Response: List[NegotiationTechniqueOut]
```

### Get Top-Ranked Techniques
```
GET /top?min_score=80&limit=5
Response: List[NegotiationTechniqueOut] (top 5 techniques with score >= 80)
```

### Get Specific Technique
```
GET /{technique_id}
Response: NegotiationTechniqueOut or 404
```

### Update Effectiveness Score
```
PUT /{technique_id}/score?new_score=92.0
Response: NegotiationTechniqueOut or 404
```

## Dashboard UI
- **Route**: `/api/ui-dashboard/advanced-negotiation-dashboard-ui`
- **Template**: `advanced_negotiation_dashboard.html`
- **Features**:
  - Add new techniques with effectiveness scoring
  - Filter by technique type or minimum score
  - View ranked technique library with color-coded scores
  - Update effectiveness scores based on real-world results
  - Visual score indicators (high=green, medium=orange, low=red)

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Add technique
$tech = @{
  technique_name="Framing Effect"
  description="Present information in a way that influences decision-making"
  effectiveness_score=82.0
  technique_type="Framing"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/advanced-negotiation-techniques/" -Body $tech -ContentType "application/json"

# Get top 10 techniques
Invoke-RestMethod -Method Get -Uri "$API/api/advanced-negotiation-techniques/top?min_score=70&limit=10"

# List all Persuasion techniques
Invoke-RestMethod -Method Get -Uri "$API/api/advanced-negotiation-techniques/?technique_type=Persuasion"

# Update effectiveness score (e.g., after analyzing negotiation outcomes)
Invoke-RestMethod -Method Put -Uri "$API/api/advanced-negotiation-techniques/1/score?new_score=88.5"

# Get specific technique
Invoke-RestMethod -Method Get -Uri "$API/api/advanced-negotiation-techniques/1"

# Open dashboard
start "$API/api/ui-dashboard/advanced-negotiation-dashboard-ui"
```

## Scoring Methodology
Effectiveness scores (0-100) can be calculated using:
- **Historical success rate**: % of negotiations where technique led to favorable outcomes
- **AI analysis**: Machine learning models analyzing negotiation transcripts
- **Expert ratings**: Weighted average of expert assessments
- **A/B testing**: Controlled experiments comparing technique performance
- **Regression analysis**: Impact on deal closure rate, discount reduction, etc.

## Use Cases
- **Real-time Negotiation Coaching**: AI recommends top techniques during live negotiations
- **Training Programs**: Teach sales teams proven high-effectiveness techniques
- **Performance Optimization**: Continuously refine technique library based on outcomes
- **Personalization**: Recommend techniques based on counterparty profile/industry
- **Competitive Analysis**: Compare technique effectiveness across competitors

## Integration Points
- **Pack 28 (Negotiations)**: Link techniques to specific negotiation sessions and track usage
- **Pack 30 (Adaptive Negotiator)**: Cross-reference strategy suggestions with effectiveness scores
- **Pack 29 (Influence Library)**: Combine psychological principles with proven techniques
- **Analytics Dashboard**: Visualize technique performance trends over time
- **AI Models**: Train LLMs on high-scoring techniques for automated recommendations

## Advanced Features

### Dynamic Score Updates
Update scores automatically based on negotiation outcomes:
```python
# After successful negotiation using technique_id=5
current_score = get_technique_by_id(db, 5).effectiveness_score
new_score = (current_score * 0.9) + (100 * 0.1)  # Weighted average with recent success
update_technique_score(db, 5, new_score)
```

### Technique Clustering
Group similar techniques for multi-technique recommendations:
```sql
SELECT * FROM negotiation_techniques_advanced 
WHERE technique_type IN ('Anchoring', 'Framing') 
AND effectiveness_score >= 75
ORDER BY effectiveness_score DESC
LIMIT 5;
```

## Dependencies
- SQLAlchemy 2.x
- No foreign keys; standalone technique library

## Wiring
- Router guarded import in `services/api/main.py` with `advanced_negotiation_available` flag in `/debug/routes`.

## Future Enhancements
- **ML-powered scoring**: Automated score updates from negotiation outcome analysis
- **Context-aware recommendations**: Factor in industry, deal size, counterparty traits
- **A/B testing framework**: Built-in experimentation for technique validation
- **Natural language technique extraction**: Parse negotiation transcripts to identify techniques used
- **Integration with Pack 28**: Automatic technique-to-negotiation linking
- **Performance dashboards**: Track technique ROI, usage frequency, and win rates
- **Collaborative filtering**: Recommend techniques based on similar negotiators' success
