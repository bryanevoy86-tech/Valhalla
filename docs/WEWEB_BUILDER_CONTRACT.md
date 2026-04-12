# WEWEB BUILDER SYSTEM CONTRACT

**Version**: 1.0  
**Base URL**: `http://localhost:4000` (dev) or configured production URL  
**Protocol**: HTTP/JSON  
**Content-Type**: `application/json`  
**Auth**: Required (`X-API-Key` header)  

---

## AUTHENTICATION

All builder endpoints require the `X-API-Key` header:

```http
X-API-Key: <value-of-BUILDER_KEY-environment-variable>
```

**Implementation:**
- Key source: Environment variable `BUILDER_KEY`
- Validation: Exact string match
- Failure: Returns `401 Unauthorized` if missing or incorrect
- Status service: Returns `503 Service Unavailable` if `BUILDER_KEY` not configured

**Setup for WeWeb:**
```bash
# Before boot
export BUILDER_KEY="your-secure-api-key-here"

# Pass to all requests
-H "X-API-Key: your-secure-api-key-here"
```

---

## ENDPOINT 1: Register Agent/Builder

### Request

```http
POST /builder/register
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "agent_name": "heimdall-builder-v1",
  "version": "1.0.0"
}
```

### Body: `RegisterIn`

| Field | Type | Required | Max Length | Example | Notes |
|-------|------|----------|-----------|---------|-------|
| `agent_name` | string | Yes | 64 | "heimdall-builder-v1" | Agent/builder identifier |
| `version` | string | No | - | "1.0.0" | Agent version (for tracking) |

### Response: 200 OK

```json
{
  "ok": true,
  "message": "Welcome, heimdall-builder-v1."
}
```

### Response Model: `RegisterOut`

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `ok` | boolean | Yes | true |
| `message` | string | Yes | "Welcome, heimdall-builder-v1." |

### Database Effect

Creates a `BuilderEvent` record:
- `kind` = "register"
- `msg` = agent_name
- `meta_json` = version

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 401 | "Invalid X-API-Key" | Missing or wrong key |
| 503 | "Builder key not configured" | BUILDER_KEY env var not set |
| 500 | "Failed to register: {error}" | Database error |

### Example cURL

```bash
curl -X POST http://localhost:4000/builder/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "agent_name": "heimdall-v1",
    "version": "1.0.0"
  }'
```

---

## ENDPOINT 2: List Recent Builder Tasks

### Request

```http
GET /builder/tasks
X-API-Key: <BUILDER_KEY>
```

### Parameters

None (returns 50 most recent tasks)

### Response: 200 OK

```json
[
  {
    "id": 3,
    "title": "Add landing page component",
    "scope": "web/weweb-widgets",
    "status": "done",
    "diff_summary": "3 files changed"
  },
  {
    "id": 2,
    "title": "Fix execution router",
    "scope": "services/api/app/routers",
    "status": "done",
    "diff_summary": "1 files changed"
  },
  {
    "id": 1,
    "title": "Add intake model",
    "scope": "services/api/app/models",
    "status": "queued",
    "diff_summary": null
  }
]
```

### Response Model: `List[TaskOut]`

Each item is a `TaskOut`:

| Field | Type | Required | Example | Notes |
|-------|------|----------|---------|-------|
| `id` | integer | Yes | 3 | Task ID |
| `title` | string | Yes | "Add landing page" | Task description |
| `scope` | string | Yes | "web/weweb-widgets" | Affected directory |
| `status` | string | Yes | "done" | queued, working, done, error |
| `diff_summary` | string or null | No | "3 files changed" | What changed |

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 401 | "Invalid X-API-Key" | Missing or wrong key |
| 500 | "Failed to list tasks: {error}" | Database error |

### Example cURL

```bash
curl http://localhost:4000/builder/tasks \
  -H "X-API-Key: test-key-12345"
```

---

## ENDPOINT 3: Create New Builder Task

### Request

```http
POST /builder/tasks
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "title": "Add dashboard widget",
  "scope": "web/weweb-widgets",
  "plan": "Optional: Description of what to build"
}
```

### Body: `TaskIn`

| Field | Type | Required | Max Length | Example | Notes |
|-------|------|----------|-----------|---------|-------|
| `title` | string | Yes | - | "Add dashboard widget" | Task name (verb phrase) |
| `scope` | string | Yes | - | "web/weweb-widgets" | Which directory to modify |
| `plan` | string | No | - | "Create React component for..." | Detailed instructions |

### Response: 200 OK

```json
{
  "task_id": 4,
  "files": [],
  "diff_summary": "queued"
}
```

### Response Model: `DraftOut`

| Field | Type | Required | Example | Notes |
|-------|------|----------|---------|-------|
| `task_id` | integer | Yes | 4 | New task ID |
| `files` | array | Yes | [] | Empty initially |
| `diff_summary` | string | Yes | "queued" | Status message |

### Database Effect

Creates `BuilderTask` record:
- `status` = "queued"
- `title`, `scope`, `plan` populated
- `payload_json` = null (filled by /draft later)

### Workflow

1. `/builder/tasks` POST → Creates queued task
2. `/builder/draft` POST → Populates task.payload_json with files
3. `/builder/apply` POST → Applies queued files to disk

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 401 | "Invalid X-API-Key" | Missing or wrong key |
| 400 | "Invalid scope" | Scope not in BUILDER_ALLOWED_DIRS |
| 500 | "Failed to create task: {error}" | Database error |

### Example cURL

```bash
curl -X POST http://localhost:4000/builder/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "title": "Add dashboard widget",
    "scope": "web/weweb-widgets",
    "plan": "Create React component for opportunity summary"
  }'
```

---

## ENDPOINT 4: Validate & Dry-Run File Changes

### Request

```http
POST /builder/draft?task_id=4
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

[
  {
    "path": "web/weweb-widgets/Dashboard.jsx",
    "content": "import React from 'react'; export default function Dashboard() { ... }",
    "mode": "add"
  },
  {
    "path": "services/api/app/models/execution_case.py",
    "content": "from sqlalchemy import ...\n\nclass ExecutionCase(Base):\n    ...",
    "mode": "replace"
  }
]
```

### Query Parameters

| Param | Type | Required | Example | Notes |
|-------|------|----------|---------|-------|
| `task_id` | integer | Yes | 4 | Task to attach draft to |

### Body: `List[FileSpec]`

Each item is a `FileSpec`:

| Field | Type | Required | Example | Notes |
|-------|------|----------|---------|-------|
| `path` | string | Yes | "web/weweb-widgets/Dashboard.jsx" | Relative to repo root |
| `content` | string | Yes | "import React from ..." | New file content (UTF-8) |
| `mode` | string | Yes | "add" | add or replace |

### Validation

- **Path whitelist**: Checked against BUILDER_ALLOWED_DIRS
  - Allowed: `services/api/app/routers`, `services/api/app/models`, `services/api/app/schemas`, `services/api/jobs`, `services/api/alembic/versions`, `web/weweb-datasources`, `web/weweb-widgets`
  - Denied: Any path outside these directories
- **File size**: Max 200KB per file (BUILDER_MAX_FILE_BYTES)

### Response: 200 OK

```json
{
  "ok": true,
  "changed": 2,
  "files": [
    {
      "path": "web/weweb-widgets/Dashboard.jsx",
      "diff": "--- a/web/weweb-widgets/Dashboard.jsx\n+++ b/web/weweb-widgets/Dashboard.jsx\n@@ -1,0 +1,5 @@\n+import React from 'react';\n+export default function Dashboard() {\n+  return <div>Dashboard</div>;\n+}\n"
    },
    {
      "path": "services/api/app/models/execution_case.py",
      "diff": "--- a/services/api/app/models/execution_case.py\n+++ b/services/api/app/models/execution_case.py\n@@ -5,3 +5,5 @@\n class ExecutionCase(Base):\n     __tablename__ = 'execution_cases'\n+    # new fields here\n"
    }
  ],
  "patch": "[unified diff of all files combined]"
}
```

### Response Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `ok` | boolean | true | Success indicator |
| `changed` | integer | 2 | Number of files with changes |
| `files` | array | [...] | Per-file diffs in unified format |
| `patch` | string | "..." | Combined unified diff (all files) |

### Database Effect

Updates `BuilderTask` record:
- `payload_json` = JSON array of FileSpec objects
- `diff_summary` = "N files changed"
- `status` remains "queued"

### Important: No Side Effects

- ✅ Does NOT write to disk
- ✅ Does NOT commit to Git
- ✅ Safe to call multiple times
- ✅ Computes diffs from current disk state

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 400 | "path not allowed: {path}" | Path outside whitelist |
| 413 | "file too large: {path}" | File > 200KB |
| 404 | "task not found" | task_id doesn't exist |
| 401 | "Invalid X-API-Key" | Missing or wrong key |
| 500 | "Failed to draft: {error}" | Database error |

### Example cURL

```bash
curl -X POST "http://localhost:4000/builder/draft?task_id=4" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '[
    {
      "path": "web/weweb-widgets/Dashboard.jsx",
      "content": "import React from '\''react'\''; export default function Dashboard() { return <div>Hello</div>; }",
      "mode": "add"
    }
  ]'
```

---

## ENDPOINT 5: Apply or Preview File Changes

### Request (Apply - Write to Disk)

```http
POST /builder/apply
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "task_id": 4,
  "approve": true
}
```

### Request (Preview - Dry-run)

```http
POST /builder/apply
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "task_id": 4,
  "approve": false
}
```

### Body: `ApplyIn`

| Field | Type | Required | Values | Example | Notes |
|-------|------|----------|--------|---------|-------|
| `task_id` | integer | Yes | - | 4 | Task to apply |
| `approve` | boolean | Yes | true/false | true | true=write, false=dry-run |

### Response: 200 OK (approve=true)

```json
{
  "task_id": 4,
  "files": [
    {
      "path": "web/weweb-widgets/Dashboard.jsx",
      "content": "import React from 'react'; ...",
      "mode": "add"
    }
  ],
  "diff_summary": "1 files changed, written to disk"
}
```

### Response: 200 OK (approve=false)

```json
{
  "task_id": 4,
  "files": [
    {
      "path": "web/weweb-widgets/Dashboard.jsx",
      "content": "import React from 'react'; ...",
      "mode": "add"
    }
  ],
  "diff_summary": "Preview mode - not written"
}
```

### Response Model: `DraftOut`

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `task_id` | integer | 4 | Task ID |
| `files` | array | [...] | List of FileSpec objects |
| `diff_summary` | string | "1 files changed" | Status message |

### Side Effects (when approve=true)

- ✅ Writes files to disk
- ✅ Updates BuilderTask status to "done"
- ✅ If GIT_ENABLE_AUTOCOMMIT=true: Auto-commits to Git
  - Commit message: `"Builder task: <title>"`
  - Push: To configured remote (default: origin/main)
- ✅ Creates BuilderEvent: kind="applied"

### Side Effects (when approve=false)

- ❌ No disk writes
- ❌ No Git commit
- ✅ Task remains "queued"
- Used for review/preview before commit

### Workflow Pattern

**Safe approach:**
1. POST /builder/tasks → Create task
2. POST /builder/draft → Stage files (3-4 times to refine)
3. POST /builder/apply with approve=false → Final review
4. POST /builder/apply with approve=true → Commit

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 404 | "task not found" | task_id doesn't exist |
| 400 | "no files staged" | payload_json is empty |
| 401 | "Invalid X-API-Key" | Missing or wrong key |
| 500 | "Failed to apply: {error}" | Disk write error, Git error |

### Example cURL (Dry-run)

```bash
curl -X POST http://localhost:4000/builder/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "task_id": 4,
    "approve": false
  }'
```

### Example cURL (Commit)

```bash
curl -X POST http://localhost:4000/builder/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "task_id": 4,
    "approve": true
  }'
```

---

## ENDPOINT 6: Log Telemetry Events

### Request

```http
POST /builder/telemetry
Content-Type: application/json
X-API-Key: <BUILDER_KEY>

{
  "kind": "build_started",
  "msg": "Starting WeWeb integration build",
  "meta_json": "{\"user\": \"operator1\", \"session\": \"abc123\"}"
}
```

### Body: `TelemetryIn`

| Field | Type | Required | Example | Notes |
|-------|------|----------|---------|-------|
| `kind` | string | Yes | "build_started" | Event type (any string) |
| `msg` | string | No | "Starting build" | Human-readable message |
| `meta_json` | string | No | "{...}" | JSON metadata string |

### Response: 200 OK

```
(no response body, implicit success)
```

### Database Effect

Creates `BuilderEvent` record:
- `kind` = value from request
- `msg` = value from request
- `meta_json` = value from request
- `created_at` = now

### Common Telemetry Events

| kind | msg Example | Use Case |
|------|-------------|----------|
| `build_started` | "Starting execution layer build" | Mark build beginning |
| `build_step` | "Generated 4 task endpoints" | Track progress |
| `build_error` | "Failed to write Dashboard.jsx" | Log errors |
| `build_completed` | "Execution layer complete" | Mark completion |
| `debug` | "Parsed 45 execution cases" | Debug data |

### Error Responses

| Status | Error | When |
|--------|-------|------|
| 401 | "Invalid X-API-Key" | Missing or wrong key |
| 500 | "Failed to log telemetry: {error}" | Database error |

### Example cURL

```bash
curl -X POST http://localhost:4000/builder/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "kind": "build_started",
    "msg": "Starting WeWeb dashboard build",
    "meta_json": "{\"components\": 1, \"services\": 0}"
  }'
```

---

## BUILDER WORKFLOW EXAMPLE

**Scenario**: Heimdall needs to add a new dashboard page

```bash
# 1. Register
curl -X POST http://localhost:4000/builder/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{"agent_name": "heimdall-v1", "version": "1.0"}'

# Response: {"ok": true, "message": "Welcome, heimdall-v1."}

# 2. Create task
curl -X POST http://localhost:4000/builder/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "title": "Add operator dashboard widget",
    "scope": "web/weweb-widgets",
    "plan": "Create React component for execution case summary"
  }'

# Response: {"task_id": 10, "files": [], "diff_summary": "queued"}

# 3. Stage files via draft (can do multiple times)
curl -X POST "http://localhost:4000/builder/draft?task_id=10" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '[
    {
      "path": "web/weweb-widgets/CaseCard.jsx",
      "content": "import React from '\''react'\''; export default function CaseCard({caseData}) { ... }",
      "mode": "add"
    }
  ]'

# Response: {"ok": true, "changed": 1, "files": [...diffs...]}

# 4. Preview (dry-run)
curl -X POST http://localhost:4000/builder/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{"task_id": 10, "approve": false}'

# Response: {"task_id": 10, "files": [...], "diff_summary": "Preview mode..."}

# 5. Commit
curl -X POST http://localhost:4000/builder/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{"task_id": 10, "approve": true}'

# Response: {"task_id": 10, "files": [...], "diff_summary": "1 files changed, written to disk"}

# 6. Log completion
curl -X POST http://localhost:4000/builder/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "kind": "build_completed",
    "msg": "Dashboard widget added successfully"
  }'
```

---

## DATABASE TABLES

### BuilderTask

```sql
CREATE TABLE builder_tasks (
  id INTEGER PRIMARY KEY,
  title VARCHAR(140) NOT NULL,
  scope VARCHAR(200) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'queued',  -- queued|working|done|error
  plan TEXT,
  diff_summary TEXT,
  payload_json TEXT,  -- JSON array of FileSpec
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME
);
```

### BuilderEvent

```sql
CREATE TABLE builder_events (
  id INTEGER PRIMARY KEY,
  kind VARCHAR(40) NOT NULL,  -- register|task_created|applied|error|telemetry|etc
  msg TEXT,
  meta_json TEXT,
  created_at DATETIME DEFAULT NOW()
);
```

---

## CONFIGURATION

### Environment Variables

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `BUILDER_KEY` | Yes | "" (empty) | "your-secure-key-12345" |
| `BUILDER_ALLOWED_DIRS` | No | See settings.py | [pre-configured] |
| `BUILDER_MAX_FILE_BYTES` | No | 200000 | 200000 |
| `GIT_ENABLE_AUTOCOMMIT` | No | false | true |
| `GIT_REPO_DIR` | No | "" | "/path/to/repo" |
| `GIT_BRANCH` | No | "main" | "main" |

### Setup for WeWeb Builder Phase

```bash
# Before using builder endpoints
export BUILDER_KEY="secure-key-generated-by-ops"
export GIT_ENABLE_AUTOCOMMIT="false"  # Only enable with careful review

# Allowed directories are pre-configured, do NOT change during runtime
```

---

## STATUS CODES SUMMARY

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid path, file too large) |
| 401 | Unauthorized (invalid API key) |
| 404 | Not found (task not found) |
| 503 | Service unavailable (BUILDER_KEY not configured) |
| 500 | Server error (database, file I/O, Git error) |

---

## CURRENT STATUS

- ✅ All 6 endpoints implemented
- ✅ Database schema ready (BuilderTask, BuilderEvent)
- ✅ Authentication middleware configured
- ⏳ Not yet integration-tested with sample requests
- ⏳ BUILDER_KEY not yet set in environment

**Next**: PHASE 3 - Test builder routes with sample requests
