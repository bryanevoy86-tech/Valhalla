# PHASE 3: Execution Models & Table Names

## Models Currently Referenced by app.routers.execution

### 1. LeadIntake
- **File**: `app/models/lead_intake.py`
- **Class**: `LeadIntake`
- **Table Name**: `lead_intake_exec`
- **Key Columns for /execution/intake**:
  - `id`: Primary key (auto-increment)
  - `raw_text`: The operator-pasted opportunity text (TEXT, required)
  - `source_type`: Where it came from (STRING, default="manual_entry")
  - `status`: Current status (STRING, default="new", indexed)
  - `created_at`: When recorded (DATETIME, default=now, indexed)
  - `created_by`: Who created it (STRING, default="operators")
  - `normalized_at`: When execution layer processed (DATETIME, nullable)

### 2. ExecutionCase
- **File**: `app/models/execution_case.py`
- **Class**: `ExecutionCase`
- **Table Name**: `execution_cases`
- **Key Columns for /execution/intake/{id}/process**:
  - `id`: Primary key (auto-increment)
  - `intake_id`: Foreign key to `lead_intake_exec(id)` (UNIQUE, required)
  - `assessment_id`: Foreign key to `underwriter_assessments(id)` (nullable)
  - `case_type`: Classification (STRING, default="unknown")
  - `route_target`: Where case routes (STRING, default="")
  - `current_stage`: Pipeline stage (STRING, default="intake")
  - `current_status`: Execution status (STRING, default="pending")
  - `safe_mode`: Safety flag (BOOLEAN, default=False)
  - `blocked`: Blocking flag (BOOLEAN, default=False)
  - `blocker_reason`: Why blocked (TEXT, nullable)
  - `next_action`: Guidance for operator (TEXT, required)
  - `created_at`: Timestamp (DATETIME, timezone-aware)
  - `updated_at`: Timestamp (DATETIME, timezone-aware)
  - `created_by`: Who created (STRING, default="system")
  - `updated_by`: Who modified (STRING, default="system")

### 3. Task
- **File**: `app/models/task.py`
- **Class**: `Task`
- **Table Name**: `tasks`
- **Key Columns (Execution-specific)**:
  - `id`: Primary key (auto-increment)
  - `case_id`: Foreign key to `execution_cases(id)` (nullable, indexed)
  - `title`: Task name (STRING, required)
  - `description`: Details (TEXT)
  - `sequence`: Order in task list (INTEGER, nullable)
  - `category`: Task type (STRING, default="general")
  - `assignee`: Who handles it (STRING, default="king")
  - `status`: Task status (STRING, default="pending")
  - `due_at`: Due date (DATETIME)
  - `completed_at`: When done (DATETIME)
  - `created_at`, `updated_at`: Timestamps

### 4. ExecutionEvent
- **File**: `app/models/execution_event.py`
- **Class**: `ExecutionEvent`
- **Table Name**: `execution_events`
- **Key Columns**:
  - `id`: Primary key (auto-increment)
  - `case_id`: Foreign key to `execution_cases(id)` (required, indexed)
  - `event_type`: What happened (STRING, e.g. "classified", "assessed", "routed")
  - `stage_from`: Previous stage (STRING, nullable)
  - `stage_to`: New stage (STRING, nullable)
  - `action_description`: Human description (TEXT, nullable)
  - `payload_json`: Details as JSON (TEXT, default="{}")
  - `created_at`: When it happened (DATETIME, timezone-aware)
  - `actor`: Who caused it (STRING, default="system")

## Required Foreign Keys
- `execution_cases.intake_id` → `lead_intake_exec.id` ✅
- `execution_cases.assessment_id` → `underwriter_assessments.id` ✅
- `execution_events.case_id` → `execution_cases.id` ✅
- `tasks.case_id` → `execution_cases.id` ✅

## Workflow Requirements
1. **POST /execution/intake** needs:
   - `lead_intake_exec` table to exist
   - Ability to INSERT with raw_text, source_type, status
   - Return intake ID

2. **POST /execution/intake/{id}/process** needs:
   - `execution_cases` table to exist
   - `execution_events` table to exist
   - Ability to INSERT into both
   - Foreign key constraints valid
   - Ability to UPDATE execution_cases with stage/status

All models are in current codebase and imported correctly by routers.execution.
