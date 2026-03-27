# ORM RUNTIME FAILURE TRACE

## FAILURE 1: GET /api/deals
**Status**: NoForeignKeysError  
**First Model/Relationship**: Unknown (SQLAlchemy relationship join condition failure)  
**Error Type**: Mapper initialization  
**Trigger**: App start or first query with `db.query()`  
**Root Cause**: A relationship somewhere has no foreign keys linking the tables  
**Where It Fails**: `sqlalchemy/orm/relationships.py` line 2423 in `_determine_joins`

---

## FAILURE 2: POST /api/heimdall/deals/1/analyze
**Status**: 500  
**First Model/Relationship**: `SideHustleOpportunity.scores`  
**Error Message**: 
```
One or more mappers failed to initialize - can't proceed with initialization of other mappers. 
Triggering mapper: 'Mapper[SideHustleOpportunity(side_hustle_opportunities)]'. 
Original exception was: Could not determine join condition between parent/child tables on 
relationship SideHustleOpportunity.scores - there are no foreign keys linking these tables.
```
**Error Type**: Mapper initialization  
**Location**: Model definition in `app.models.opportunity_tracker.py`  
**Root Cause**: `SideHustleOpportunity.scores` relationship defined but no foreign key exists  
**Impact**: Blocks ALL queries that touch this model (including Heimdall)

---

## FAILURE 3: POST /api/heimdall/deals/1/advance-stage
**Status**: 500  
**First Model/Relationship**: `SideHustleOpportunity.scores` (same as #2)  
**Error**: Same as FAILURE 2  
**Root Cause**: Same - `SideHustleOpportunity.scores` relationship blocker

---

## FAILURE 4: GET /api/audit/deals/1
**Status**: InvalidRequestError  
**First Model/Relationship**: AuditEvent (likely model configuration)  
**Error Type**: Query initialization  
**Location**: `app/routers/audit.py` line 35  
**Root Cause**: AuditEvent model has mapper initialization issues  
**Note**: Related to global mapper initialization, not specific relationship

---

## FAILURE 5: GET /api/dashboard/pipeline
**Status**: InvalidRequestError  
**First Model/Relationship**: DealBrief  
**Error Type**: Query initialization  
**Location**: `app/routers/operational_dashboard.py` line 76  
**Root Cause**: DealBrief model has mapper initialization issues  
**Note**: Related to global mapper initialization, not specific relationship

---

## SUMMARY OF FIRST REAL ORM FAILURES

| Route | First Failure | Type | Location |
|-------|---------------|------|----------|
| /api/deals | Relationship join | Mapper init | SQLAlchemy join logic |
| /api/heimdall/analyze | SideHustleOpportunity.scores | Relationship FK | Model relationship definition |
| /api/heimdall/advance-stage | SideHustleOpportunity.scores | Relationship FK | Model relationship definition |
| /api/audit/deals | AuditEvent mapper | Mapper init | Global mapper config |
| /api/dashboard/pipeline | DealBrief mapper | Mapper init | Global mapper config |

---

## CRITICAL INSIGHT

**SideHustleOpportunity.scores is blocking all routes** because:
1. It's imported in models/__init__.py or pulled into global Base during app initialization
2. Its mapper fails to initialize
3. SQLAlchemy stops initializing ALL mappers when one fails
4. This cascades to ALL routes that try to use ANY model

**Solution**: Remove or isolate the `SideHustleOpportunity.scores` relationship before anything else.
