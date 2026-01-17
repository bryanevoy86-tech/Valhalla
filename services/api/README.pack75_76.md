# Pack 75 & 76: Heimdall↔Loki Sync Engine + Human Specialist Bridge

## Overview

**Pack 75** and **Pack 76** complete your three-actor decision-making system:

1. **Heimdall** generates proposals
2. **Loki** analyzes and critiques
3. **Human experts** provide specialized input
4. **You** make final decisions

All tracked, all synced, all logged in your God Review Case system.

---

## Pack 75: Heimdall↔Loki Sync Engine

### Purpose
Automatically detects when Heimdall and Loki disagree on key metrics, creates a conflict case, and escalates for human review.

### Architecture

```
┌─────────────┐         ┌─────────────┐
│  Heimdall   │         │    Loki     │
│  Proposal   │         │   Review    │
└──────┬──────┘         └──────┬──────┘
       │                       │
       └───────────┬───────────┘
                   │
            ┌──────▼──────┐
            │ Sync Engine │
            │  Compares   │
            └──────┬──────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼────┐         ┌────▼────────┐
    │  CLEAN  │         │  CONFLICT   │
    │  (logs) │         │ (escalate)  │
    └─────────┘         └──────┬──────┘
                               │
                        ┌──────▼──────────┐
                        │ God Review Case │
                        │  (human input)  │
                        └─────────────────┘
```

### Database Schema

**Table: `god_sync_records`**
```sql
id                  UUID PRIMARY KEY
created_at          TIMESTAMP WITH TIME ZONE
subject_type        VARCHAR(100)          -- "deal", "contract", "tax_plan"
subject_reference   VARCHAR(200)          -- "deal_123"
heimdall_payload    JSONB                 -- Heimdall's numbers
loki_payload        JSONB                 -- Loki's numbers
sync_status         VARCHAR(20)           -- "clean" | "conflict" | "resolved"
conflict_summary    TEXT                  -- Detailed diff
forwarded_case_id   UUID                  -- Link to God review case if conflict
```

### API Endpoints

#### POST `/god-sync`
**Purpose:** Compare Heimdall and Loki payloads, detect conflicts

**Request:**
```json
{
  "subject_type": "deal",
  "subject_reference": "deal_789",
  "heimdall_payload": {
    "arv": 400000,
    "purchase_price": 250000,
    "cap_rate": 0.08
  },
  "loki_payload": {
    "arv": 350000,
    "purchase_price": 250000,
    "cap_rate": 0.08
  }
}
```

**Response (CONFLICT):**
```json
{
  "id": "uuid",
  "created_at": "2025-11-20T12:00:00Z",
  "subject_type": "deal",
  "subject_reference": "deal_789",
  "heimdall_payload": {...},
  "loki_payload": {...},
  "sync_status": "conflict",
  "conflict_summary": "arv: Heimdall=400000 | Loki=350000",
  "forwarded_case_id": "case-uuid"
}
```

**Response (CLEAN):**
```json
{
  "id": "uuid",
  "sync_status": "clean",
  "conflict_summary": null,
  "forwarded_case_id": null
}
```

#### GET `/god-sync/{record_id}`
**Purpose:** Retrieve sync record by ID

**Response:**
```json
{
  "id": "uuid",
  "created_at": "2025-11-20T12:00:00Z",
  "sync_status": "conflict",
  "conflict_summary": "arv: Heimdall=400000 | Loki=350000",
  "forwarded_case_id": "case-uuid"
}
```

### How It Works

1. **Both gods process a subject** (deal, contract, tax plan)
2. **POST to `/god-sync`** with both payloads
3. **Engine compares** all matching keys
4. **If conflict detected:**
   - Sets `sync_status = "conflict"`
   - Generates `conflict_summary` showing differences
   - **Auto-creates God Review Case** with:
     - Title: "Conflict detected: {subject_reference}"
     - Description: Conflict summary
     - Heimdall's summary and payload
     - Status: "open"
   - **Adds initial event** to case timeline
   - Returns `forwarded_case_id` for tracking
5. **If clean:**
   - Sets `sync_status = "clean"`
   - No case created
   - Just logs the sync

### Example Usage

```powershell
# Conflict: Heimdall says ARV=400k, Loki says ARV=350k
$body = @{
    subject_type = "deal"
    subject_reference = "deal_789"
    heimdall_payload = @{
        arv = 400000
        purchase_price = 250000
        cap_rate = 0.08
    }
    loki_payload = @{
        arv = 350000  # Disagrees with Heimdall
        purchase_price = 250000
        cap_rate = 0.08
    }
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:4000/god-sync" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Result:
# sync_status: "conflict"
# conflict_summary: "arv: Heimdall=400000 | Loki=350000"
# forwarded_case_id: "uuid-of-new-case"
```

---

## Pack 76: Human Specialist Bridge

### Purpose
Connect real-world experts (lawyers, accountants, advisors) to your God Review Case system. Their comments automatically sync to case timelines.

### Architecture

```
┌──────────────────┐
│ Human Specialist │
│   (Lawyer)       │
└────────┬─────────┘
         │
         │ comments on case
         ▼
┌────────────────────┐
│ SpecialistComment  │
│   (stored)         │
└────────┬───────────┘
         │
         │ auto-creates
         ▼
┌────────────────────┐
│ GodReviewEvent     │
│  (case timeline)   │
└────────────────────┘
```

### Database Schema

**Table: `human_specialists`**
```sql
id          UUID PRIMARY KEY
created_at  TIMESTAMP WITH TIME ZONE
name        VARCHAR(120)          -- "Sarah Chen"
role        VARCHAR(60)           -- "lawyer" | "accountant" | "advisor"
email       VARCHAR(200)
phone       VARCHAR(40)
notes       TEXT
expertise   JSONB                 -- {"areas": [...], "years": 12}
```

**Table: `specialist_case_comments`**
```sql
id              UUID PRIMARY KEY
created_at      TIMESTAMP WITH TIME ZONE
specialist_id   UUID FK -> human_specialists.id
case_id         UUID FK -> god_review_cases.id (CASCADE DELETE)
comment         TEXT
payload         JSONB
```

### API Endpoints

#### POST `/specialists`
**Purpose:** Register a new human specialist

**Request:**
```json
{
  "name": "Sarah Chen",
  "role": "lawyer",
  "email": "sarah.chen@lawfirm.com",
  "phone": "+1-555-0123",
  "notes": "Real estate and contract specialist",
  "expertise": {
    "areas": ["real estate law", "contracts", "compliance"],
    "years": 12
  }
}
```

**Response:**
```json
{
  "id": "specialist-uuid",
  "created_at": "2025-11-20T12:00:00Z",
  "name": "Sarah Chen",
  "role": "lawyer",
  "email": "sarah.chen@lawfirm.com",
  "expertise": {...}
}
```

#### GET `/specialists/{specialist_id}`
**Purpose:** Retrieve specialist details

**Response:**
```json
{
  "id": "uuid",
  "name": "Sarah Chen",
  "role": "lawyer",
  "expertise": {...}
}
```

#### POST `/specialists/{specialist_id}/comment/{case_id}`
**Purpose:** Specialist adds comment to a God review case

**Request:**
```json
{
  "comment": "I've reviewed the comps and agree with Loki's lower ARV estimate.",
  "payload": {
    "recommendation": "use_conservative_arv",
    "confidence": 0.85,
    "supporting_comps": ["123 Main St", "456 Oak Ave"]
  }
}
```

**Response:**
```json
{
  "id": "comment-uuid",
  "created_at": "2025-11-20T12:30:00Z",
  "specialist_id": "specialist-uuid",
  "case_id": "case-uuid",
  "comment": "I've reviewed the comps...",
  "payload": {...}
}
```

**Side Effect:** Automatically creates `GodReviewEvent`:
```json
{
  "case_id": "case-uuid",
  "actor": "human",
  "event_type": "comment",
  "message": "I've reviewed the comps...",
  "payload": {...}
}
```

### Complete Workflow Example

```powershell
# Step 1: Heimdall and Loki disagree on ARV
$sync = @{
    subject_type = "deal"
    subject_reference = "deal_789"
    heimdall_payload = @{ arv = 400000; purchase_price = 250000 }
    loki_payload = @{ arv = 350000; purchase_price = 250000 }
} | ConvertTo-Json

$syncResult = Invoke-RestMethod -Uri "http://localhost:4000/god-sync" -Method Post -Body $sync
# Result: conflict detected, case created
$caseId = $syncResult.forwarded_case_id

# Step 2: Register your lawyer
$lawyer = @{
    name = "Sarah Chen"
    role = "lawyer"
    email = "sarah@lawfirm.com"
} | ConvertTo-Json

$lawyerResult = Invoke-RestMethod -Uri "http://localhost:4000/specialists" -Method Post -Body $lawyer
$specialistId = $lawyerResult.id

# Step 3: Lawyer reviews conflict and adds expert opinion
$comment = @{
    comment = "Reviewed comps. Market has softened. Recommend Loki's conservative ARV."
    payload = @{
        recommendation = "use_conservative_arv"
        confidence = 0.85
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:4000/specialists/$specialistId/comment/$caseId" -Method Post -Body $comment

# Step 4: Check case timeline - lawyer's comment now appears
$events = Invoke-RestMethod -Uri "http://localhost:4000/god-cases/$caseId/events" -Method Get
# Shows:
# - system event: "Sync conflict detected"
# - human event: "Reviewed comps. Market has softened..."

# Step 5: You review the case and make final decision
$update = @{
    human_summary = "Agree with Sarah and Loki. Use $350k ARV."
    final_outcome = "approved"
    status = "closed"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:4000/god-cases/$caseId" -Method Patch -Body $update
```

---

## Integration Points

### Pack 75 integrates with:
- **God Review Cases** (Pack 74): Auto-creates cases on conflict
- **GodReviewEvent**: Adds initial "sync" event to timeline
- **Heimdall/Loki systems**: Consumes their output payloads

### Pack 76 integrates with:
- **God Review Cases** (Pack 74): Links specialists to cases
- **GodReviewEvent**: Auto-creates "human" events for comments
- **Your team**: Real lawyers, accountants, advisors join the workflow

---

## Files Created

### Pack 75 Files
```
services/api/app/sync/
├── __init__.py
├── models.py          # GodSyncRecord
└── schemas.py         # GodSyncRecordCreate/Read

services/api/app/routers/
└── sync_engine.py     # POST /god-sync, GET /god-sync/{id}

services/api/alembic/versions/
└── fa9eb99ebae2_add_god_sync_records_table.py
```

### Pack 76 Files
```
services/api/app/specialists/
├── __init__.py
├── models.py          # HumanSpecialist, SpecialistCaseComment
└── schemas.py         # HumanSpecialistCreate/Read, SpecialistCommentCreate/Read

services/api/app/routers/
└── specialists.py     # POST /specialists, GET /specialists/{id}, POST comment

services/api/alembic/versions/
└── f8dc20521d28_add_human_specialists_and_case_comments.py
```

---

## Testing

Run the test script:
```powershell
cd services/api
.\test_pack75_76.ps1
```

**Test Coverage:**
1. Clean sync (gods agree)
2. Conflict sync (gods disagree) → auto-creates case
3. Create human specialist
4. Specialist comments on conflict case
5. Verify comment appears in case timeline

---

## Key Features

### Pack 75
✅ **Automatic conflict detection** - compares all payload keys  
✅ **Auto-escalation** - creates God review case on conflict  
✅ **Audit trail** - logs every sync attempt  
✅ **Flexible subjects** - deals, contracts, tax plans, automation changes  

### Pack 76
✅ **Specialist registry** - track all external experts  
✅ **Expertise tracking** - JSONB field for skills/experience  
✅ **Automatic event sync** - comments become timeline events  
✅ **Foreign key CASCADE** - delete comments when case deleted  

---

## Production Considerations

### Indexing
```sql
-- Pack 75
CREATE INDEX idx_sync_status ON god_sync_records(sync_status);
CREATE INDEX idx_sync_subject ON god_sync_records(subject_type, subject_reference);

-- Pack 76
CREATE INDEX idx_specialist_role ON human_specialists(role);
CREATE INDEX idx_comment_case ON specialist_case_comments(case_id);
CREATE INDEX idx_comment_specialist ON specialist_case_comments(specialist_id);
```

### Security
- **Specialist emails** - consider encryption for PII
- **Payloads** - may contain sensitive financial data
- **Access control** - restrict specialist comment endpoint to authenticated specialists

### Notifications
Consider adding:
- Email notification when conflict detected
- Slack message when specialist comments
- Dashboard widget showing pending conflicts

---

## Migration Chain

```
... → 3e8296b25e8b (God review cases)
    → fa9eb99ebae2 (God sync records)      ← Pack 75
    → f8dc20521d28 (Human specialists)     ← Pack 76
```

All migrations applied and pushed to main branch.

---

## Summary

**Pack 75 + Pack 76 = Complete Three-Actor Decision System**

1. **Heimdall** proposes a deal with ARV=$400k
2. **Loki** analyzes and says ARV=$350k
3. **Sync Engine** detects conflict, creates God review case
4. **Lawyer** (Pack 76) reviews comps, agrees with Loki
5. **You** review all inputs, make final decision
6. **Full audit trail** in case timeline

All actors tracked. All decisions logged. All encrypted. All synced.

🎯 **Your decision-making system is now complete.**
