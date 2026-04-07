# POST /api/deals Endpoint Implementation

## Summary
Added a new direct deal creation endpoint that allows creating deals without first requiring a lead to exist. The endpoint automatically creates a placeholder/system lead if no `lead_id` is provided.

## Changes Made

### 1. **Schema Updates** ([deals/schemas.py](services/api/app/deals/schemas.py))
- Added `DealCreateDirect` schema that makes `lead_id` optional
- This allows clients to POST deals without providing a lead ID upfront
- All other fields (title, stage, status, arv, score, etc.) are supported

```python
class DealCreateDirect(BaseModel):
    """Schema for creating a standalone deal (auto-creates placeholder lead if needed)."""
    lead_id: Optional[int] = None  # Optional - auto-creates placeholder lead if not provided
    title: str = Field(..., min_length=1, max_length=255)
    stage: str = Field(default="lead_received")
    status: str = Field(default="active")
    arv: Optional[Decimal] = None
    estimated_repair_cost: Optional[Decimal] = None
    max_allowable_offer: Optional[Decimal] = None
    target_assignment_fee: Optional[Decimal] = None
    score: Optional[Decimal] = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None
    disposition_status: Optional[str] = None
```

### 2. **Service Layer** ([deals/service.py](services/api/app/deals/service.py))
- Added `create_deal_direct()` function that:
  - Accepts optional `lead_id`
  - If `lead_id` not provided: auto-creates a placeholder lead with:
    - `lead_name`: Derived from deal title
    - `lead_email`: `system@internal.local`
    - `lead_phone`: `000-000-0000`
    - `lead_status`: `converted`
    - `source`: `api_direct`
  - Then creates the deal linked to that lead
  - Returns the created deal

### 3. **Router Endpoint** ([deals/router.py](services/api/app/deals/router.py))
- Added `POST /` endpoint to the deals router (mounts at `/api/deals`)
- Accepts `DealCreateDirect` request body
- Returns `DealOut` response with:
  - Status code: `201 Created`
  - Deal ID, timestamps, all fields
  - Includes optional audit logging

```python
@router.post("", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal_direct(deal: DealCreateDirect, db: Session = Depends(get_db)):
    """Create a new deal directly (standalone)."""
```

## API Usage

### Without lead_id (auto-creates placeholder lead):
```bash
curl -X POST http://localhost:4000/api/deals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Property",
    "stage": "lead_received",
    "status": "active",
    "arv": 250000,
    "estimated_repair_cost": 20000,
    "max_allowable_offer": 150000,
    "target_assignment_fee": 5000,
    "score": 85,
    "notes": "Test notes for sample property",
    "disposition_status": "pending"
  }'
```

### With existing lead_id:
```bash
curl -X POST http://localhost:4000/api/deals \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 123,
    "title": "Sample Property",
    "stage": "lead_received",
    "status": "active",
    "arv": 250000,
    "estimated_repair_cost": 20000,
    "max_allowable_offer": 150000,
    "target_assignment_fee": 5000,
    "score": 85,
    "notes": "Test notes for sample property",
    "disposition_status": "pending"
  }'
```

## Response Example
```json
{
  "id": 42,
  "created_ts": "2026-04-01T12:34:56.789000",
  "updated_ts": "2026-04-01T12:34:56.789000",
  "lead_id": 99,
  "title": "Sample Property",
  "stage": "lead_received",
  "status": "active",
  "arv": "250000",
  "estimated_repair_cost": "20000",
  "max_allowable_offer": "150000",
  "target_assignment_fee": "5000",
  "score": "85",
  "notes": "Test notes for sample property",
  "disposition_status": "pending"
}
```

## Files Modified
1. [services/api/app/deals/schemas.py](services/api/app/deals/schemas.py) - Added `DealCreateDirect` schema
2. [services/api/app/deals/service.py](services/api/app/deals/service.py) - Added `create_deal_direct()` function
3. [services/api/app/deals/router.py](services/api/app/deals/router.py) - Added POST endpoint + import

## Error Handling
- **400 Bad Request**: If provided `lead_id` doesn't exist
- **201 Created**: On successful deal creation
- **500 Internal Server Error**: If audit logging fails (but deal still created)

## Notes
- Placeholder leads have source=`api_direct` for tracking
- All timestamps use UTC
- Decimal fields are serialized as strings in JSON for precision
- Audit logs record each creation with details
