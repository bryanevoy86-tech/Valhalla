# Pack 33: AI Behavioral Profiling

## Overview
Analyze user and lead behavior to create custom engagement strategies. Track behavioral scores, interests, and engagement levels to power personalized marketing and sales approaches. Includes AI-driven strategy recommendations based on user activity patterns.

## Models (`app/behavioral_profiling/models.py`)
- **BehavioralProfile**: id, user_id (FK→user_profiles.user_id), lead_id (FK→leads.id, optional), behavioral_score (0-100), interests, engagement_level (low/medium/high), last_engaged_at, created_at, updated_at

## Schemas (`app/behavioral_profiling/schemas.py`)
- **BehavioralProfileCreate**: user_id, lead_id (optional), behavioral_score (0-100), interests, engagement_level, last_engaged_at (optional)
- **BehavioralProfileOut**: All fields including timestamps
- **BehavioralProfileUpdate**: Partial update schema for score, interests, level, last_engaged_at
- **EngagementRecommendation**: AI-generated strategy with confidence score and reasoning

## Service (`app/behavioral_profiling/service.py`)
- `create_behavioral_profile(db, profile: BehavioralProfileCreate) -> BehavioralProfile`
- `get_all_profiles(db, skip: int = 0, limit: int = 100) -> list[BehavioralProfile]`
- `get_profile_by_user(db, user_id: int) -> BehavioralProfile | None`
- `get_profiles_by_engagement(db, engagement_level: str) -> list[BehavioralProfile]`
- `update_profile(db, profile_id: int, update_data: BehavioralProfileUpdate) -> BehavioralProfile | None`
- `generate_engagement_strategy(db, user_id: int) -> EngagementRecommendation | None` — **AI-powered recommendation**

## Endpoints (`/api/behavioral-profiles`)

### Create Profile
```
POST /
Body: {
  "user_id": 1,
  "lead_id": 42,
  "behavioral_score": 65.0,
  "interests": "real estate, investing, negotiation",
  "engagement_level": "medium"
}
Response: BehavioralProfileOut (201 Created)
```

### List Profiles (with filtering & pagination)
```
GET /?skip=0&limit=100&engagement_level=high
Response: List[BehavioralProfileOut]
```

### Get User's Profile
```
GET /user/{user_id}
Response: BehavioralProfileOut or 404
```

### Update Profile
```
PUT /{profile_id}
Body: {
  "behavioral_score": 75.0,
  "engagement_level": "high"
}
Response: BehavioralProfileOut or 404
```

### Get AI Engagement Strategy 🤖
```
GET /strategy/{user_id}
Response: {
  "user_id": 1,
  "recommended_strategy": "Maintain engagement with premium content and exclusive offers",
  "confidence_score": 0.9,
  "reasoning": "High engagement score (75) indicates strong interest. Focus on retention."
}
```

## Dashboard UI
- **Route**: `/api/ui-dashboard/behavioral-profiling-dashboard-ui`
- **Template**: `behavioral_profiling_dashboard.html`
- **Features**:
  - Create behavioral profiles with score and interests
  - Filter profiles by engagement level (low/medium/high)
  - View all profiles with color-coded engagement badges
  - Generate AI-driven engagement strategies
  - Display strategy recommendations with confidence scores

## AI Strategy Logic

### Engagement Levels (Auto-calculated)
- **High (score ≥ 70)**: Frequent engagement, high interest
- **Medium (score 40-69)**: Moderate engagement, needs nurturing
- **Low (score < 40)**: Minimal engagement, requires re-activation

### Strategy Recommendations
- **High Engagement**: "Maintain with premium content and exclusive offers" (confidence: 90%)
- **Medium Engagement**: "Re-engage with personalized content based on interests" (confidence: 75%)
- **Low Engagement**: "Win-back campaign with special incentives" (confidence: 60%)

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Create behavioral profile
$profile = @{
  user_id=1
  behavioral_score=72.0
  interests="real estate, wholesaling, fix-and-flip"
  engagement_level="high"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/behavioral-profiles/" -Body $profile -ContentType "application/json"

# Get user's profile
Invoke-RestMethod -Method Get -Uri "$API/api/behavioral-profiles/user/1"

# Get AI engagement strategy
$strategy = Invoke-RestMethod -Method Get -Uri "$API/api/behavioral-profiles/strategy/1"
Write-Host "Strategy: $($strategy.recommended_strategy)"
Write-Host "Confidence: $($strategy.confidence_score * 100)%"

# List high-engagement profiles
Invoke-RestMethod -Method Get -Uri "$API/api/behavioral-profiles/?engagement_level=high"

# Update profile
$update = @{behavioral_score=85.0; engagement_level="high"} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri "$API/api/behavioral-profiles/1" -Body $update -ContentType "application/json"

# Open dashboard
start "$API/api/ui-dashboard/behavioral-profiling-dashboard-ui"
```

## Use Cases
- **Personalized Marketing**: Tailor campaigns based on behavioral scores and interests
- **Lead Nurturing**: Identify low-engagement leads for win-back campaigns
- **Retention Strategies**: Keep high-value users engaged with premium content
- **Sales Prioritization**: Focus on users with highest engagement scores
- **A/B Testing**: Measure impact of different engagement strategies on behavioral scores

## Integration Points
- **Pack 31 (Leads)**: Link behavioral profiles to lead records for comprehensive tracking
- **Pack 26 (Messaging)**: Trigger automated emails/SMS based on engagement level
- **Pack 30 (Adaptive Negotiator)**: Combine behavioral insights with negotiation strategies
- **Pack 24 (User Profiles)**: Enrich user data with behavioral analytics
- **Future ML**: Train models to predict churn risk, optimal contact timing, conversion probability

## AI Enhancement Opportunities
- **Predictive Scoring**: Use ML to forecast future engagement based on historical patterns
- **Sentiment Analysis**: Analyze user communication to auto-update behavioral scores
- **Interest Extraction**: NLP-based extraction of interests from user interactions
- **Optimal Timing**: Recommend best times to contact based on engagement patterns
- **Churn Prediction**: Identify users at risk of disengagement before it happens

## Dependencies
- SQLAlchemy 2.x
- Foreign keys: `user_profiles.user_id`, `leads.id` (optional)

## Wiring
- Router guarded import in `services/api/main.py` with `behavioral_profiling_available` flag in `/debug/routes`.
