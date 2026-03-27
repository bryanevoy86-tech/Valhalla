# WeWeb Phase 1 — Foundation Setup Guide

**Date:** March 27, 2026  
**Status:** Ready for WeWeb Integration  
**Backend:** Proven + Stable ✅  

---

## 📋 STEP 1: API CONFIGURATION

### Base URL
```
http://localhost:4000/api
```

### Authentication
```
Header: X-API-Key
Value: test-builder-key-v0.2-verification
```

### Global API Setup (WeWeb)

In WeWeb API config:

```javascript
// Base configuration
baseURL: "http://localhost:4000/api"

// Default headers
headers: {
  "Content-Type": "application/json",
  "X-API-Key": "test-builder-key-v0.2-verification"
}

// Error handling
onError: (error) => {
  console.error(`[API Error] ${error.status}: ${error.statusText}`)
  console.error(`Response: ${JSON.stringify(error.data)}`)
  return error
}
```

### Content-Type
Always: `application/json`

---

## 🏥 STEP 2: HEALTH CHECK CONNECTION

### Endpoint to Test
```
GET /api/deals (simplest working endpoint)
```

### Request Format
```javascript
GET http://localhost:4000/api/deals
Headers: {
  "X-API-Key": "test-builder-key-v0.2-verification",
  "Content-Type": "application/json"
}
```

### Expected Response (200 OK)
```json
[
  {
    "id": 1,
    "created_at": "2026-03-27T15:07:26.210996Z",
    "updated_at": "2026-03-27T15:07:26.211020Z",
    "lead_id": 1,
    "title": "Test Deal - Workflow Verification",
    "stage": "draft",
    "status": "active",
    "arv": "350000.00",
    "estimated_repair_cost": "50000.00",
    "max_allowable_offer": "280000.00",
    "target_assignment_fee": "7000.00",
    "score": "75.50",
    "notes": "Seeded for workflow verification",
    "disposition_status": "active"
  },
  ...more deals...
]
```

### What to Watch For
- ✅ Status code: 200 (not 404, 500, 503)
- ✅ Auth header accepted (no 401)
- ✅ JSON response parses cleanly
- ✅ Array of objects returned
- ✅ Each object has same fields

### Success Indicators
- Request completes < 500ms
- No CORS errors in console
- Response is valid JSON
- At least 1 deal returned

---

## 📊 STEP 3: DEALS LIST (FIRST REAL DATA)

### Endpoint
```
GET /api/deals?skip=0&limit=100
```

### Request (WeWeb)
```javascript
// Create data query in WeWeb
const dealsQuery = {
  url: "http://localhost:4000/api/deals",
  method: "GET",
  headers: {
    "X-API-Key": "test-builder-key-v0.2-verification"
  },
  params: {
    skip: 0,
    limit: 100
  }
}
```

### Response Data Shape
```javascript
// Each deal object will have:
{
  id: number,
  created_at: ISO8601 datetime string,
  updated_at: ISO8601 datetime string,
  lead_id: number (foreign key to lead),
  title: string (deal name/description),
  stage: string (draft | lead_received | preliminary_analysis | offer_ready | under_contract | closed),
  status: string (active | **reserved** for future use),
  arv: decimal string (after-repair value),
  estimated_repair_cost: decimal string,
  max_allowable_offer: decimal string,
  target_assignment_fee: decimal string,
  score: decimal string (0-100),
  notes: string | null,
  disposition_status: string | null
}
```

### UI Component: Deals List View

**Build a simple table/list with:**

```
┌─────┬────────────────────────┬─────────────┬──────────┬────────────┐
│ ID  │ TITLE                  │ STAGE       │ SCORE    │ ARV        │
├─────┼────────────────────────┼─────────────┼──────────┼────────────┤
│ 1   │ Test Deal - Workflow   │ draft       │ 75.50    │ $350,000   │
│ 2   │ Lead A - Analysis      │ lead_recvd  │ 82.00    │ $420,000   │
│ 3   │ Lead B - Preliminary   │ preliminary │ 68.50    │ $280,000   │
└─────┴────────────────────────┴─────────────┴──────────┴────────────┘
```

**Display columns (in order):**
1. **id** - Deal identifier (small, left-aligned)
2. **title** - Deal name (full-width, clickable later)
3. **stage** - Pipeline stage (badge, color-coded)
4. **score** - Deal quality (right-aligned numeric)
5. **arv** - Property value (right-aligned currency)

**Stage Badge Colors** (suggestion):
- `draft` - Gray
- `lead_received` - Blue
- `preliminary_analysis` - Yellow
- `offer_ready` - Orange
- `under_contract` - Green
- `closed` - Dark green

### Include States

**Loading State:**
```
Fetching deals...
(show spinner)
```

**Empty State:**
```
No deals found
(can appear if skip/limit filtered all deals)
```

**Error State:**
```
Failed to load deals
Error: [error message from API]
[Retry button]
```

---

## ✅ STEP 4: SUCCESS CRITERIA

All of these must pass:

1. ✅ **API connection stable**
   - Request returns within 500ms
   - No connection refused errors
   - No CORS errors

2. ✅ **Auth header works**
   - No 401 Unauthorized errors
   - Request accepted by backend
   - Header passed correctly to API

3. ✅ **Deals load without errors**
   - GET /api/deals returns 200
   - Response not empty (at least 1 deal)
   - No 500 errors from backend
   - No parse errors on response JSON

4. ✅ **Data matches backend exactly**
   - Field names match (id, title, stage, etc)
   - Field types correct (numbers are numbers, dates are ISO strings)
   - No missing fields in response
   - Decimal values formatted as strings (e.g., "350000.00")

5. ✅ **No console errors**
   - Browser console is clean
   - No JS errors when loading data
   - No warnings about missing elements

6. ✅ **Refresh does not break state**
   - F5 refresh reloads data correctly
   - List re-renders without issues
   - No duplicate entries on refresh
   - Loading state clears properly

---

## 🧱 STEP 5: REPORT BACK FORMAT

After building Phase 1, return this format:

```
API STATUS: connected ✅ / failed ❌
  └─ Response time: __ms
  └─ Auth header: accepted ✅ / rejected ❌

DEALS LIST: loaded ✅ / not loaded ❌
  └─ Number of deals shown: __
  └─ Column display: OK ✅ / broken ❌

ERRORS: none ✅ / see below ❌
  └─ [If any errors occurred, describe here]

FIELD MATCH: exact ✅ / mismatched ❌
  └─ [If fields don't match, list which ones differ]

CONSOLE: clean ✅ / has warnings ⚠️
  └─ [If warnings exist, describe them]

NOTES:
  [Any other observations about the integration]
```

---

## 🚫 DO NOT BUILD YET

**Do not add:**
- Filters
- Sorting
- Pagination UI
- Action buttons
- Navigation links
- Detail views
- Heimdall integration
- Dashboard
- Lead intake form

**Build only:**
- API config
- Data fetching
- Simple list display
- Error/loading states

---

## 🔄 What Comes After (Don't build yet)

### Phase 2: Detail View
- Click deal → see full details
- Show all fields
- Audit timeline

### Phase 3: Heimdall Integration
- Show stage recommendations
- Advancement buttons (once Heimdall builder key configured)
- Block invalid transitions

### Phase 4: Dashboard
- Stage breakdown view
- KPIs and metrics
- Filtering by stage/score

### Phase 5: Lead Intake
- Lead form
- Auto-convert to deal
- Audit trail

---

## 📡 Endpoint Reference (For Phase 1)

**What we're using:**
```
GET /api/deals
```

**Available later (don't use yet):**
```
POST /api/leads (create lead)
POST /api/deals/from-lead/{lead_id} (convert lead to deal)
GET /api/audit/deals/{deal_id} (see transaction log)
POST /api/heimdall/deals/{deal_id}/analyze (get recommendations)
```

---

## 💡 WeWeb Configuration Template

```javascript
// In WeWeb plugins/API section

API_CONFIG = {
  baseURL: "http://localhost:4000/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "test-builder-key-v0.2-verification"
  }
}

// Query for deals list
QUERY_DEALS = {
  name: "Get Deals List",
  method: "GET",
  url: `${API_CONFIG.baseURL}/deals`,
  headers: API_CONFIG.headers,
  params: {
    skip: 0,
    limit: 100
  },
  onSuccess: (data) => {
    console.log(`Loaded ${data.length} deals`)
    return data
  },
  onError: (error) => {
    console.error(`Failed to load deals: ${error.status}`)
    return null
  }
}
```

---

## 🎯 Success = You See This on Screen

```
Deals Dashboard

▶ Loading deals...

[After load]

Deals

┌────┬───────────────────────┬─────────────┬────────┬──────────┐
│ ID │ Title                 │ Stage       │ Score  │ ARV      │
├────┼───────────────────────┼─────────────┼────────┼──────────┤
│ 1  │ Test Deal - Workflow  │ draft       │ 75.50  │ $350K    │
│ 2  │ Lead A - Analysis     │ lead_recvd  │ 82.00  │ $420K    │
│ 3  │ Lead B - Preliminary  │ preliminary │ 68.50  │ $280K    │
└────┴───────────────────────┴─────────────┴────────┴──────────┘
```

---

## 📌 Troubleshooting Phase 1

### "Request blocked / CORS error"
- Check base URL is exactly `http://localhost:4000/api`
- Verify X-API-Key header is in requests
- Backend should allow cross-origin

### "401 Unauthorized"
- Check X-API-Key header value
- Should be: `test-builder-key-v0.2-verification`
- Make sure header is being sent

### "Empty array returned"
- That's actually OK - means connection works
- Just shows no deals are loaded yet
- Build empty state UI

### "Data fields missing"
- Check field names exactly (case-sensitive)
- All fields should match the schema above
- If `arv` shows as `null` in some, that's OK - it's nullable

### "Decimal formatting wrong"
- ARV, repair_cost, etc. come as strings like "350000.00"
- Format in UI with: `parseFloat(value).toLocaleString('en-US', {style: 'currency', currency: 'USD'})`

---

## ✅ You're Ready

Backend is stable ✅  
Endpoints verified ✅  
Data shape documented ✅  
Error handling defined ✅  

Now go build the foundation in WeWeb.

Report back what loads and what breaks.

