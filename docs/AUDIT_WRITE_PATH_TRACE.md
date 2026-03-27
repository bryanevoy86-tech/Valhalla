# AUDIT WRITE PATH TRACE

## Current Write Implementation

**Location**: `services/api/app/services/heimdall_service.py`

### Write Service Function
```
app.audit.service.log_event(db: Session, payload: AuditEventCreate) -> AuditEvent
```
- Takes `AuditEventCreate` payload
- Converts to `AuditEvent` ORM object
- Adds to session, commits, refreshes
- Returns persisted record

**File**: `services/api/app/audit/service.py`

### Audit Model
```
class AuditEvent(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}
```

**Actual Table**: `audit_logs` (SQLite)

**Schema**:
- id (Integer, PK)
- created_at (DateTime)
- entity_type (String)
- deal_id (Integer) ← **Key for deal-scoped queries**
- action (String)
- previous_value (String)
- new_value (String)
- user_id (String)
- notes (Text)
- actor (String) ← Compatibility field
- target (String) ← Compatibility field  
- result (String) ← Compatibility field
- ip, user_agent, meta (optional)

### Write Contract (Pydantic Schema)
```
class AuditEventCreate(BaseModel):
    actor: str              # e.g., "Heimdall_v0.1"
    action: str             # e.g., "heimdall_analyzed_deal"
    target: Optional[str]   # e.g., "deal_1" (currently passed as string)
    result: str             # "success" | "failure"
    ip: Optional[str]
    user_agent: Optional[str]
    meta: Optional[Dict[str, Any]] → Contains deal_id as nested field
```

### Current Heimdall Write Calls

**Location**: `advance_stage_with_approval()` function

1. **Analysis Event**
   ```python
   log_event(db, AuditEventCreate(
       actor="Heimdall_v0.1",
       action="heimdall_analyzed_deal",
       target=f"deal_{deal_id}",  # String: "deal_1"
       result="success",
       meta={
           "deal_id": deal_id,      # Integer: 1 (nested)
           "current_stage": current_stage,
           "recommended_stage": analysis.recommended_stage,
           "blockers": analysis.blocker_flags,
           "risks": analysis.risk_flags,
       }
   ))
   ```

2. **Recommendation Event**
   ```python
   log_event(db, AuditEventCreate(
       actor="Heimdall_v0.1",
       action="heimdall_recommended_stage",
       target=f"deal_{deal_id}",
       result="success",
       meta={
           "deal_id": deal_id,
           "from_stage": current_stage,
           "to_stage": requested_stage,
           ...
       }
   ))
   ```

3. **Advancement Event** (on success)
   ```python
   log_event(db, AuditEventCreate(
       actor="Heimdall_v0.1",
       action="heimdall_stage_advanced",
       target=f"deal_{deal_id}",
       result="success",
       meta={...}
   ))
   ```

## Key Issues Identified

### Issue 1: deal_id Not Populated in ORM Write
- Heimdall passes `target="deal_1"` (string) and `deal_id` nested in `meta` dict
- AuditEventCreate schema doesn't have a top-level `deal_id` field
- ORM model has `deal_id` column but it's not being populated from the payload
- **Result**: deal_id column stays NULL, making deal-scoped queries impossible

### Issue 2: Read Route Not Querying
- Audit route at `/api/audit/deals/{deal_id}` returns hardcoded empty list
- Comment says "audit_logs table doesn't have a direct deal_id column" (outdated)
- **Result**: Even if deal_id was written, it wouldn't be queried

### Issue 3: Write Path Has Exception Handling
- Heimdall's `log_event()` calls wrapped in try/except with silent print
- If database write fails, error only goes to stdout, not propagated
- **Result**: Silent failures hard to debug

## What Needs to be Fixed

1. ✓ AuditEvent model has deal_id column (already updated)
2. ✗ AuditEventCreate schema needs deal_id field
3. ✗ Heimdall needs to pass deal_id directly to log_event()
4. ✗ Audit route needs to query by deal_id instead of returning empty list
5. ✗ Error handling should be more explicit

## Confirmation

**Trace executed**: 2026-03-27  
**Audit writes**: YES, Heimdall calls log_event() 3+ times per workflow  
**Writes reaching DB**: Likely silently failing due to deal_id mismatch  
**Current visibility**: EMPTY (as observed in seeded workflow test)
