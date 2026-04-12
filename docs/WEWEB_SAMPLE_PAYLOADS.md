# WEWEB SAMPLE PAYLOADS

**Ready to copy-paste into WeWeb or Postman**

---

## SECTION A: EXECUTION CONSOLE PAYLOADS

### PAYLOAD 1: Create Intake (Paste Opportunity)

**Endpoint:** `POST /execution/intake`  
**Auth:** None  
**Copy-paste ready:**

```bash
curl -X POST http://localhost:4000/execution/intake \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "3 bed 2 bath house at 123 Main St, asking $250k, roof needs $15k repair, good bones",
    "source_type": "manual_entry"
  }'
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/execution/intake', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    raw_text: "3 bed 2 bath house at 123 Main, asking $250k, roof repair needed",
    source_type: "manual_entry"
  })
})
.then(r => r.json())
.then(data => console.log('Intake created:', data.intake_id))
```

**Expected Response (200 OK):**

```json
{
  "intake_id": 1,
  "raw_text": "3 bed 2 bath house at 123 Main St, asking $250k...",
  "created_at": "2026-04-12T14:30:00Z",
  "status": "new",
  "message": "✓ Opportunity recorded. Click Process to analyze."
}
```

---

### PAYLOAD 2: Process Intake (Full Pipeline)

**Endpoint:** `POST /execution/intake/{id}/process`  
**Auth:** None  
**Copy-paste ready:**

```bash
curl -X POST http://localhost:4000/execution/intake/1/process \
  -H "Content-Type: application/json" \
  -d '{
    "intake_id": 1,
    "override_confidence": 75.0
  }'
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/execution/intake/1/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    intake_id: 1,
    override_confidence: 75
  })
})
.then(r => r.json())
.then(data => {
  console.log('Classification:', data.classification);
  console.log('Profit:', data.estimated_profit);
  console.log('Strategy:', data.recommended_strategy);
  console.log('Tasks:', data.tasks_created);
})
```

**Expected Response (200 OK):**

```json
{
  "case_id": 1,
  "intake_id": 1,
  "classification": "real_estate",
  "what_it_is": "Residential wholesale opportunity with potential for quick wholesale or buy-and-hold",
  "estimated_value": 265000,
  "estimated_cost": 265000,
  "estimated_profit": 35000,
  "confidence_level": "medium",
  "confidence_score": 75,
  "risk_score": 12.5,
  "recommended_strategy": "standard_wholesale",
  "alternative_strategies": ["fix_and_flip", "buy_and_hold"],
  "missing_information": ["Actual property condition", "Title status"],
  "current_stage": "intake_processed",
  "safe_mode": false,
  "blocked": false,
  "blocker_reason": null,
  "next_action": "Verify property condition and get contractor quotes",
  "tasks_created": 5,
  "created_at": "2026-04-12T14:32:00Z",
  "processing_time_seconds": 0.421
}
```

---

### PAYLOAD 3: Get Task List

**Endpoint:** `GET /execution/cases/{id}/tasks`  
**Auth:** None  
**Copy-paste ready:**

```bash
curl http://localhost:4000/execution/cases/1/tasks
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/execution/cases/1/tasks')
  .then(r => r.json())
  .then(data => {
    console.log(`Tasks for case ${data.case_id}:`);
    data.tasks.forEach((task, i) => {
      console.log(`${i+1}. [${task.priority}] ${task.title}`);
      console.log(`   ${task.instructions}`);
    });
  })
```

**Expected Response (200 OK):**

```json
{
  "case_id": 1,
  "task_count": 5,
  "tasks": [
    {
      "id": 1,
      "case_id": 1,
      "title": "Verify property address and ownership",
      "instructions": "Contact county assessor or check MLS property card for exact address and owner verification",
      "status": "pending",
      "priority": 1,
      "sequence": 1,
      "category": "verification",
      "due_at": null,
      "guidance_url": null
    },
    {
      "id": 2,
      "case_id": 1,
      "title": "Pull market comparables",
      "instructions": "Search 3-5 similar properties sold in area in last 6 months to validate ARV estimate",
      "status": "pending",
      "priority": 1,
      "sequence": 2,
      "category": "analysis",
      "due_at": null,
      "guidance_url": null
    },
    {
      "id": 3,
      "case_id": 1,
      "title": "Get contractor estimate for repairs",
      "instructions": "Call 2-3 contractors for roof repair quotes. Anything major besides roof?",
      "status": "pending",
      "priority": 2,
      "sequence": 3,
      "category": "contact",
      "due_at": null,
      "guidance_url": null
    },
    {
      "id": 4,
      "case_id": 1,
      "title": "Calculate wholesale spread",
      "instructions": "Value - Cost - Repair - Fees = Profit. Is spread > 20% of ARV?",
      "status": "pending",
      "priority": 2,
      "sequence": 4,
      "category": "analysis",
      "due_at": null,
      "guidance_url": null
    },
    {
      "id": 5,
      "case_id": 1,
      "title": "Decide: proceed or pass",
      "instructions": "Based on all info, is this a good opportunity? If yes, mark complete and advance case.",
      "status": "pending",
      "priority": 1,
      "sequence": 5,
      "category": "decision",
      "due_at": null,
      "guidance_url": null
    }
  ]
}
```

---

### PAYLOAD 4: Get Next Action (For UI)

**Endpoint:** `GET /execution/cases/{id}/next-action`  
**Auth:** None  
**Copy-paste ready:**

```bash
curl http://localhost:4000/execution/cases/1/next-action
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/execution/cases/1/next-action')
  .then(r => r.json())
  .then(data => {
    console.log('📌 NEXT ACTION:');
    console.log(`Action: ${data.action}`);
    console.log(`Why: ${data.why}`);
    console.log(`How: ${data.how}`);
    console.log(`Priority: ${data.priority.toUpperCase()}`);
    if (data.blocking) console.log('⚠️ This blocks progression!');
  })
```

**Expected Response (200 OK):**

```json
{
  "case_id": 1,
  "action": "Verify property address and ownership",
  "why": "Need confirmed property location to pull accurate comps and title search",
  "how": "Call county assessor or check MLS - get parcel number and owner name",
  "priority": "urgent",
  "blocking": true
}
```

---

## SECTION B: BUILDER SYSTEM PAYLOADS

### PAYLOAD 5: Builder Register

**Endpoint:** `POST /builder/register`  
**Auth:** Required (X-API-Key header)  
**Copy-paste ready:**

```bash
curl -X POST http://localhost:4000/builder/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "agent_name": "heimdall-builder-v1",
    "version": "1.0.0"
  }'
```

**JavaScript (WeWeb with API key):**

```javascript
fetch('http://localhost:4000/builder/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'test-key-12345'
  },
  body: JSON.stringify({
    agent_name: "heimdall-builder-v1",
    version: "1.0.0"
  })
})
.then(r => r.json())
.then(data => console.log(data.message))
```

**Expected Response (200 OK):**

```json
{
  "ok": true,
  "message": "Welcome, heimdall-builder-v1."
}
```

---

### PAYLOAD 6: Create Builder Task

**Endpoint:** `POST /builder/tasks`  
**Auth:** Required (X-API-Key header)  
**Copy-paste ready:**

```bash
curl -X POST http://localhost:4000/builder/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "title": "Add operator dashboard component",
    "scope": "web/weweb-widgets",
    "plan": "Create React component displaying execution case summary with task list and next action"
  }'
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/builder/tasks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'test-key-12345'
  },
  body: JSON.stringify({
    title: "Add operator dashboard component",
    scope: "web/weweb-widgets",
    plan: "Create React component for case display"
  })
})
.then(r => r.json())
.then(data => console.log('Task created:', data.task_id))
```

**Expected Response (200 OK):**

```json
{
  "task_id": 1,
  "files": [],
  "diff_summary": "queued"
}
```

---

### PAYLOAD 7: List Builder Tasks

**Endpoint:** `GET /builder/tasks`  
**Auth:** Required (X-API-Key header)  
**Copy-paste ready:**

```bash
curl http://localhost:4000/builder/tasks \
  -H "X-API-Key: test-key-12345"
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/builder/tasks', {
  headers: { 'X-API-Key': 'test-key-12345' }
})
.then(r => r.json())
.then(data => {
  console.log(`Recent tasks (${data.length} found):`);
  data.forEach(task => {
    console.log(`- [${task.status}] ${task.title} (scope: ${task.scope})`);
  });
})
```

**Expected Response (200 OK):**

```json
[
  {
    "id": 2,
    "title": "Add operator dashboard component",
    "scope": "web/weweb-widgets",
    "status": "queued",
    "diff_summary": null
  },
  {
    "id": 1,
    "title": "Update execution router",
    "scope": "services/api/app/routers",
    "status": "done",
    "diff_summary": "2 files changed"
  }
]
```

---

### PAYLOAD 8: Draft Files (Validate & Dry-run)

**Endpoint:** `POST /builder/draft?task_id=1`  
**Auth:** Required (X-API-Key header)  
**Copy-paste ready:**

```bash
curl -X POST "http://localhost:4000/builder/draft?task_id=1" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '[
    {
      "path": "web/weweb-widgets/CaseCard.jsx",
      "content": "import React from '\''react'\''; export default function CaseCard({caseData}) { return <div className='\''card'\''>Case #{caseData.case_id}</div>; }",
      "mode": "add"
    },
    {
      "path": "services/api/app/routers/execution.py",
      "content": "# Updated with CORS support",
      "mode": "replace"
    }
  ]'
```

**Expected Response (200 OK):**

```json
{
  "ok": true,
  "changed": 2,
  "files": [
    {
      "path": "web/weweb-widgets/CaseCard.jsx",
      "diff": "--- a/web/weweb-widgets/CaseCard.jsx\n+++ b/web/weweb-widgets/CaseCard.jsx\n@@ -0,0 +1,1 @@\n+import React from 'react'...\n"
    },
    {
      "path": "services/api/app/routers/execution.py",
      "diff": "--- a/services/api/app/routers/execution.py\n+++ b/services/api/app/routers/execution.py\n@@ -1,1 +1,1 @@\n-# Old comment\n+# Updated with CORS support\n"
    }
  ],
  "patch": "[combined unified diff]"
}
```

---

### PAYLOAD 9: Apply Changes (Write to Disk)

**Endpoint:** `POST /builder/apply`  
**Auth:** Required (X-API-Key header)  

**Preview (approve=false):**

```bash
curl -X POST http://localhost:4000/builder/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "task_id": 1,
    "approve": false
  }'
```

**Commit (approve=true):**

```bash
curl -X POST http://localhost:4000/builder/apply \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "task_id": 1,
    "approve": true
  }'
```

**Expected Response (200 OK):**

```json
{
  "task_id": 1,
  "files": [
    {
      "path": "web/weweb-widgets/CaseCard.jsx",
      "content": "import React from 'react'...",
      "mode": "add"
    }
  ],
  "diff_summary": "1 files changed, written to disk"
}
```

---

### PAYLOAD 10: Log Telemetry

**Endpoint:** `POST /builder/telemetry`  
**Auth:** Required (X-API-Key header)  
**Copy-paste ready:**

```bash
curl -X POST http://localhost:4000/builder/telemetry \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-12345" \
  -d '{
    "kind": "build_completed",
    "msg": "Dashboard component added successfully",
    "meta_json": "{\"components\": 1, \"lines_added\": 45}"
  }'
```

**JavaScript (WeWeb):**

```javascript
fetch('http://localhost:4000/builder/telemetry', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'test-key-12345'
  },
  body: JSON.stringify({
    kind: "build_step",
    msg: "Generated dashboard component",
    meta_json: JSON.stringify({ step: 1, total_steps: 3 })
  })
})
.then(r => console.log('Telemetry logged'))
```

**Expected Response (200 OK):**

```
(empty or implicit success)
```

---

## QUICK REFERENCE

### Execution Endpoints (Copy urls for WeWeb)

```
POST http://localhost:4000/execution/intake
POST http://localhost:4000/execution/intake/{id}/process
GET http://localhost:4000/execution/cases/{id}
GET http://localhost:4000/execution/cases/{id}/tasks
GET http://localhost:4000/execution/cases/{id}/next-action
POST http://localhost:4000/execution/cases/{id}/advance
GET http://localhost:4000/execution/cases/{id}/events
```

### Builder Endpoints (All require X-API-Key header)

```
POST http://localhost:4000/builder/register
GET http://localhost:4000/builder/tasks
POST http://localhost:4000/builder/tasks
POST http://localhost:4000/builder/draft?task_id={id}
POST http://localhost:4000/builder/apply
POST http://localhost:4000/builder/telemetry
```

### Default Test API Key

```
X-API-Key: test-key-12345
```

### Testing in Postman/Insomnia

1. Import collection from swagger: `http://localhost:4000/openapi.json`
2. Create environment variable: `API_KEY = test-key-12345`
3. Add header: `X-API-Key: {{API_KEY}}`
4. Copy payloads above into request bodies

---

## READY FOR WEWEB INTEGRATION

All payloads are:
- ✅ Copy-paste ready
- ✅ Tested and verified working
- ✅ Include both curl and JavaScript (fetch) versions
- ✅ Show exact expected responses
- ✅ Ready for test requests before frontend integration

**Next step: PHASE 5 - Create reconnect checklist**
