# FRONTEND PHASE 1 — MINIMAL VALIDATION BUILD

**Backend V1 is Frozen. Do not modify backend unless a real blocker is discovered.**

---

## CONTEXT

- Backend V1 freeze is official.
- 0 MUST FIX NOW items.
- API contract is locked (see V1_API_CONTRACT.md).
- Production backend is live and stable (https://valhalla-api-ha6a.onrender.com).
- This phase is ONLY to prove frontend ↔ backend connection cleanly.
- We are NOT rebuilding the full app yet.
- We are NOT importing old WeWeb mess.
- We are NOT expanding scope.

---

## OBJECTIVE

Build the smallest possible frontend validation layer that proves the frozen backend works cleanly with the UI.

---

## SUCCESS CONDITION

All of the following must be true:

1. ✅ Frontend connects to backend cleanly
2. ✅ /health works from frontend
3. ✅ Deals list loads successfully
4. ✅ Deal detail loads successfully
5. ✅ One backend action can be triggered from UI
6. ✅ No console errors
7. ✅ No backend contract changes required (unless a real blocker is found)

---

## PHASE 1 — CREATE CLEAN FRONTEND FOUNDATION

### 1. Start a NEW clean frontend / WeWeb project

- Do NOT reuse old project
- Do NOT import old layouts
- Do NOT bring forward broken bindings
- Keep structure minimal and clean

### 2. Define environment/config clearly

- `API_BASE_URL` = production backend URL
- Auth/header strategy = current backend contract only
- No alternate URLs
- No ngrok
- No dev hacks unless explicitly needed for local testing

### 3. Create a tiny frontend structure with only

- Login/Auth handling if required
- Dashboard page
- Deals List page
- Deal Detail page

---

## PHASE 2 — API CONNECTION VALIDATION

### 1. Add backend data source / API connector

### 2. Validate: GET /health

**Expected:**
- 200 OK
- valid JSON
- no CORS error
- no auth mismatch

### 3. Log and document

- actual base URL used
- actual auth header used
- whether the request succeeded first try
- any mismatch found

**OUTPUT REQUIRED:**

Create: `docs/FRONTEND_PHASE1_CONNECTION.md`

Include:
- base URL
- auth/header strategy
- test endpoint used
- result
- issues found
- whether backend changes were required

---

## PHASE 3 — BUILD ONLY 3 CORE SCREENS

### SCREEN 1 — DASHBOARD

**Purpose:** Prove frontend can read backend state

**Display only:**
- system health
- go-live state or governance status if available
- simple counts if already exposed

No fancy layout needed.

### SCREEN 2 — DEALS LIST

**Purpose:** Prove list retrieval works

**Behavior:**
- `GET /deals`
- render a clean simple list/table/cards
- show basic fields only:
  - id
  - address/name if present
  - status
  - created date if present

No filtering, sorting, or advanced controls yet unless already trivial.

### SCREEN 3 — DEAL DETAIL

**Purpose:** Prove detail retrieval + one action works

**Behavior:**
- `GET /deals/{id}`
- show core deal fields only
- add ONE action button:
  - Heimdall Analyze
  - OR the equivalent frozen backend action already in contract

**Button behavior:**
- trigger existing backend route only
- report success/failure clearly
- do NOT invent new routes

---

## PHASE 4 — STRICT SCOPE CONTROL

### DO NOT BUILD

- advanced dashboards
- trust pages
- expansion modules
- vault pages
- story/media modules
- settings screens
- design polish
- animation
- role systems beyond what already exists
- extra widgets
- old frontend migration work

### DO ONLY

- connect
- read data
- open detail
- trigger one action
- verify clean behavior

---

## PHASE 5 — ERROR HANDLING / BLOCKER RULE

If something fails, classify it into exactly one bucket:

### A. FRONTEND ISSUE

**Examples:**
- bad binding
- wrong page param
- UI state bug
- bad header wiring
- bad response parsing

**Action:** Fix in frontend only

### B. REAL BACKEND BLOCKER

**Examples:**
- contract mismatch with frozen API
- endpoint returns wrong shape
- production 500
- auth requirement contradicts frozen contract
- missing field required for basic screen to function

**Action:**
- document exact blocker
- change ONLY the minimum backend code required
- return immediately to frontend

### C. OUT-OF-SCOPE WISH

**Examples:**
- "would be nice to also add…"
- "while we're here…"
- "this page could also…"

**Action:** Do nothing. Defer to Phase 2 or later.

**OUTPUT REQUIRED:**

Create: `docs/FRONTEND_PHASE1_BLOCKERS.md`

Format each blocker as:
- page
- endpoint
- issue
- classification (frontend / backend / deferred)
- action taken

---

## PHASE 6 — FINAL VALIDATION REPORT

After completion, create: `docs/FRONTEND_PHASE1_VALIDATION.md`

This report must state:

1. Did /health work?
2. Did the dashboard load?
3. Did the deals list load?
4. Did deal detail load?
5. Did the single action button work?
6. Any console errors?
7. Any backend blockers discovered?
8. Is the system approved to move to full frontend build?

---

## OPERATING RULES

- **Backend remains frozen** unless a real blocker is proven
- **No scope expansion**
- **No rebuilding the old frontend**
- **No architecture changes**
- **No polish-first behavior**
- **This phase is proof, not perfection**

---

## START NOW WITH

**STEP 1:** Connect frontend to production backend and verify `GET /health`

---

## REFERENCE MATERIALS

For API details, see:
- [V1_API_CONTRACT.md](V1_API_CONTRACT.md) — Complete frozen API specification
- [V1_BACKEND_FREEZE_CHECKLIST.md](V1_BACKEND_FREEZE_CHECKLIST.md) — Readiness assessment

For backend status, see:
- [BACKEND_SPINE_AUDIT.md](BACKEND_SPINE_AUDIT.md) — Infrastructure map
- [ROUTER_LIVE_VS_DEAD_AUDIT.md](ROUTER_LIVE_VS_DEAD_AUDIT.md) — Live routes inventory
- [MIGRATION_AND_STARTUP_INTEGRITY.md](MIGRATION_AND_STARTUP_INTEGRITY.md) — Startup sequences

---

## KEY ENDPOINTS FOR THIS PHASE

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/health` | GET | Connection validation | None |
| `/docs` | GET | API documentation | None |
| `/api/deals` | GET | List all deals | Optional |
| `/api/deals/{id}` | GET | Get single deal | Optional |
| `/api/governance/go-live/state` | GET | Gov status (dashboard) | Optional |
| `/api/heimdall/deals/{id}/analyze` | POST | Trigger analysis | Optional |

---

## PRODUCTION BACKEND URL

```
https://valhalla-api-ha6a.onrender.com
```

---

**Status:** Frontend Phase 1 ready to execute.  
**Backend:** Frozen. Observer mode only.  
**Timeline:** Complete validation within 3-5 days.  
**Next:** Report blockers here for classification and action.
