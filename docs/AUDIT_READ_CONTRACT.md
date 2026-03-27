# AUDIT READ CONTRACT

## Current Read Implementation

**Route**: `GET /api/audit/deals/{deal_id}`

**Location**: `services/api/app/routers/audit.py` line 25-35

### Current Implementation
```python
@router.get("/deals/{deal_id}", response_model=List[AuditEventResponse])
def get_deal_audit_trail(deal_id: int, db: Session = Depends(get_db)):
    """Get complete audit trail for a specific deal."""
    # NOTE: audit_logs table doesn't have a direct deal_id column
    # Return empty list since there are no deal-specific audit events stored yet
    # TODO: Implement deal-specific audit event tracking
    return []
```

**Status**: HARDCODED EMPTY RETURN
**Reason**: Comment claims audit_logs has no deal_id column (OUTDATED/FALSE)

## Expected Read Behavior

### What the Route Should Return
- List of `AuditEventResponse` objects
- Filtered to only records for the specified `deal_id`
- Sorted newest first (descending by created_at)
- All fields from AuditEventResponse

### Read Contract Specification

**Input**: `deal_id: int` (from URL path)

**Filter Logic** (not yet implemented):
```sql
SELECT * FROM audit_logs WHERE deal_id = ? ORDER BY created_at DESC
```

**Expected Output Format** (Pydantic):
```python
class AuditEventResponse(BaseModel):
    id: int
    created_at: datetime
    actor: str
    action: str
    target: Optional[str]
    result: str
    ip: Optional[str]
    user_agent: Optional[str]
    meta: Optional[Dict[str, Any]]
```

**Plus extended fields** (from base AuditEvent model):
- entity_type
- deal_id
- action
- user_id
- notes

## Mismatch Analysis

### Write-Read Mismatch

**What Heimdall Writes:**
- actor="Heimdall_v0.1"
- action="heimdall_analyzed_deal"
- target="deal_1"
- result="success"
- meta={deal_id: 1, ...}
- **deal_id column**: NOT POPULATED

**What Read Route Needs:**
- Queries on deal_id = {deal_id} 
- But deal_id is NULL (never written)
- **Result**: Query returns 0 rows even though events exist

### Field Mapping Issue

| Write Source | ORM Column | Read Expectation |
|--------------|-----------|------------------|
| meta.deal_id (nested) | deal_id (NULL) | WHERE deal_id = ? |
| target (string) | target | Part of response |
| actor | actor | Part of response |
| action | action | Part of response |
| result | result | Part of response |
| meta | meta (JSON) | Part of response |

**Critical Gap**: Nested meta.deal_id never propagates to deal_id column

## Timeline Route (if exists)

**Route**: `GET /api/dashboard/deals/{deal_id}/timeline` (if exists)

Need to verify:
- Does it exist?
- Does it query audit_logs?
- Does it use same deal_id filter?
- Should it use result=success only or all results?

## Fix Required

1. ✓ AuditEvent model has deal_id column (confirmed in models.py)
2. ✗ AuditEventCreate needs explicit deal_id field
3. ✗ Heimdall needs to pass deal_id as top-level field
4. ✗ Audit route needs to query: `db.query(AuditEvent).filter(AuditEvent.deal_id == deal_id).order_by(AuditEvent.created_at.desc()).all()`
5. ? Check if timeline route exists and needs same fix

**Priority**: High - This is the direct cause of empty audit response observed in seeded workflow test
