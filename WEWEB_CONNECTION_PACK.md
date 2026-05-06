# WeWeb Connection Pack - Phase 2b Frontend Build

**Freeze Date**: 2026-05-06  
**Backend Commit**: 908d481  
**Status**: LOCKED - Backend expansion frozen until WeWeb needs changes  
**Base URL**: `http://127.0.0.1:4000` (dev) or production URL  

---

## 🚀 Quick Start - Copy This Into Copilot

**If tokens are low or budget is tight, copy ONE section at a time into Copilot.**

### Token Budget Strategy
- Each page = 1 prompt + test
- Don't ask for multiple pages in one prompt
- Paste stop rules BEFORE building to prevent scope creep
- Test each page before moving to next

---

## ENDPOINT REFERENCE

### Status & Health
```
GET /api/go-live/status
Returns: { system, mode, checked_at, backend_ready, database_ready, 
           va_intake_ready, approvals_ready, deal_conversion_ready, 
           audit_logging_ready, weweb_ready, ok_to_go_live, blockers, 
           warnings, next_step }
```

### Lead Intake
```
POST /api/va-intake/lead
Body: { source_platform, source_type, address, city, province, seller_name, 
        seller_phone, seller_email, asking_price, raw_text, va_notes, 
        strategy_fit, submitted_by }
Returns: { success, lead_id, lead_status, source_platform, heimdall_score, 
           risk_level, confidence, recommended_action, approval_required, 
           next_pipeline_stage, reasoning_summary }

GET /api/va-intake/leads
Query: ?status=<filter> &limit=50
Returns: { success, count, items[] }

GET /api/va-intake/leads/{lead_id}
Returns: { success, lead, approval }

GET /api/va-intake/leads/{lead_id}/audit
Returns: { success, lead_id, audit_trail[] }

POST /api/va-intake/leads/{lead_id}/convert-to-deal
Returns: { success, deal_id, deal_status }

GET /api/va-intake/leads/{lead_id}/deal
Returns: { success, deal }
```

### Approvals
```
GET /api/va-intake/approvals/pending
Returns: { success, count, items[] }

POST /api/va-intake/approvals/{approval_id}/approve
Body: { approver }
Returns: { success, approval_id, status, approved_at }

POST /api/va-intake/approvals/{approval_id}/deny
Body: { approver, denial_reason }
Returns: { success, approval_id, status, denied_at, denial_reason }
```

### Messaging (Draft Only)
```
POST /messaging/va/draft-seller-message/{lead_id}
Query: ?message_type=initial_contact|follow_up|offer
Returns: { success, lead_id, message_type, draft, requires_bryan_approval, 
           note, instructions[] }

POST /messaging/va/create-buyer-packet/{deal_id}
Returns: { success, deal_id, packet{ property, financials, property_info, 
           risks[], next_steps[] }, note }
```

### Reporting
```
GET /reports/va-leads-summary
Returns: { success, report_type, generated_at, totals{}, by_status{}, 
           by_stage{}, by_source{}, quality{} }

GET /reports/approval-summary
Returns: { success, report_type, generated_at, totals{}, metrics{}, 
           pending_risk_distribution{} }

GET /reports/eia-monthly-summary
Query: ?year=2026&month=5
Returns: { success, report_type, period, generated_at, totals{}, 
           approval_metrics{}, conversion_activity{}, quality_metrics{}, 
           efficiency{} }
```

### Dev/Test (Admin Only)
```
POST /api/dev/seed-va-test-data
Returns: { success, message, created_leads[], errors }
Creates: 5 sample leads (Heimdall 100/100 each)

POST /api/dev/clear-test-data
Returns: { success, message, deleted }

GET /api/dev/duplicate-check
Returns: { success, test, query, result{ duplicate_warning, possible_matches[] } }
```

---

## EXACT FIELD NAMES - Copy This For Form Building

### Lead Submission Form
```
source_platform:    string (facebook|website|referral|etc)
source_type:        string (manual_va)
address:            string (required)
city:               string (default: Winnipeg)
province:           string (default: MB)
seller_name:        string (required)
seller_phone:       string (format: 555-0123)
seller_email:       string (format: email@example.com)
asking_price:       number (integer, e.g., 450000)
raw_text:           string (description of property)
va_notes:           string (optional VA observations)
strategy_fit:       string (default: wholesale)
submitted_by:       string (VA name or ID)
```

### Lead Response Fields
```
lead_id:            integer (database ID)
lead_status:        string (qualified_pending_approval|research_required|parked|approved|denied|converted)
heimdall_score:     integer (0-100)
risk_level:         string (low|medium|high)
confidence:         float (0.0-1.0)
recommended_action: string (action to take)
approval_required:  boolean
next_pipeline_stage: string (intake|research|approval_required|approved|deal_conversion|converted|archived)
```

### Lead List Item Fields
```
id:                 integer
address:            string
seller_name:        string
asking_price:       number
source_platform:    string
heimdall_score:     integer
risk_level:         string
status:             string
stage:              string
deal_id:            integer|null
created_at:         ISO timestamp
```

### Approval Queue Fields
```
id:                 integer
entity_type:        string (lead)
entity_id:          integer
va_lead_id:         integer
status:             string (pending|approved|denied)
recommended_action: string
heimdall_score:     integer
risk_level:         string
assigned_to:        string (usually "bryan")
approved_by:        string|null
approved_at:        ISO timestamp|null
denied_by:          string|null
denied_at:          ISO timestamp|null
denial_reason:      string|null
created_at:         ISO timestamp
updated_at:         ISO timestamp
```

---

## TEST LEAD DATA - Use This For Testing

### Sample Leads (Already in Database)
```
Lead 4: 123 Oak Street, Toronto ON - $450,000 - Score: 100/100
Lead 5: 456 Maple Avenue, Vancouver BC - $750,000 - Score: 100/100
Lead 6: 789 Pine Road, Calgary AB - $350,000 - Score: 100/100
Lead 7: 321 Elm Drive, Montreal QC - $550,000 - Score: 100/100
Lead 8: 654 Cedar Lane, Edmonton AB - $320,000 - Score: 100/100
```

### Create New Test Lead
```json
{
  "source_platform": "weweb-test",
  "source_type": "manual_va",
  "address": "999 Test Avenue",
  "city": "Winnipeg",
  "province": "MB",
  "seller_name": "Test Seller",
  "seller_phone": "555-0001",
  "seller_email": "test@example.com",
  "asking_price": 400000,
  "raw_text": "Estate sale. Needs work. Must sell quickly. Behind on payments.",
  "submitted_by": "weweb-qa"
}
```

---

## PAGE-BY-PAGE BUILD PROMPTS

### Use These One At A Time

---

## PROMPT 1: Lead Submission Form Page

```
Build a WeWeb page called "VA Lead Submission" with these requirements:

FORM FIELDS (in order):
1. Source Platform: dropdown (facebook, website, referral)
2. Address: text input (required)
3. City: text input (default: Winnipeg)
4. Province: dropdown (ON, BC, AB, QC, MB)
5. Seller Name: text input (required)
6. Seller Phone: text input (format: 555-0123)
7. Seller Email: email input
8. Asking Price: number input
9. Raw Text: textarea (description of property)
10. VA Notes: textarea (optional)
11. Strategy: dropdown (wholesale)
12. Submitted By: text input (VA name)

SUBMIT BUTTON:
- POST to http://127.0.0.1:4000/api/va-intake/lead
- Show loading spinner while submitting
- On success: show success message with lead_id, heimdall_score, recommended_action
- On error: show error message

RESPONSE DISPLAY:
- Lead ID: {lead_id}
- Score: {heimdall_score}/100
- Status: {lead_status}
- Action: {recommended_action}
- Button: "View Approval Queue" (link to next page)
- Button: "New Lead" (clear form)

STYLING:
- Form layout: 2 columns on desktop, 1 on mobile
- Submit button: green, prominent
- Success message: green background
- Error message: red background
- Loading indicator: show during submission

TEST WITH:
- Submit the sample lead data above
- Verify response shows correct fields
- Verify lead appears in database
- Check heimdall_score is 100
- Check status is qualified_pending_approval
```

---

## PROMPT 2: Leads List & Filter Page

```
Build a WeWeb page called "Lead List" with these requirements:

DATA TABLE:
- Column 1: Address (text, clickable - links to lead detail)
- Column 2: Seller Name
- Column 3: Price (formatted as currency)
- Column 4: Score (0-100, color-coded: ≥75=green, 55-74=yellow, <55=red)
- Column 5: Status (qualified_pending_approval|approved|etc)
- Column 6: Created (date, recent first)
- Column 7: Action (button: "View Details")

API:
- GET http://127.0.0.1:4000/api/va-intake/leads
- Refresh every 30 seconds or on "Refresh" button
- Show total count at top

FILTERS (optional):
- Status dropdown: all|qualified_pending_approval|approved|denied
- Apply filter: GET /api/va-intake/leads?status=<filter>

PAGINATION:
- Show 10 items per page
- Next/Previous buttons

STYLING:
- Table: sortable columns
- Score column: background color matching status
- Hover effect on rows

TEST WITH:
- GET http://127.0.0.1:4000/api/va-intake/leads
- Verify 9 leads appear (4-8 are seed data)
- Click "View Details" → should show lead detail page
- Filter by status=qualified_pending_approval → should show 7 leads
```

---

## PROMPT 3: Lead Detail Page

```
Build a WeWeb page called "Lead Detail" with these requirements:

URL PARAMETER:
- /lead-detail/:lead_id

DATA SOURCE:
- GET http://127.0.0.1:4000/api/va-intake/leads/{lead_id}

DISPLAY FIELDS (read-only):
LEFT COLUMN:
- Address (heading)
- City, Province
- Seller Name
- Seller Phone (clickable: tel: link)
- Seller Email (clickable: mailto: link)

CENTER COLUMN:
- Asking Price (formatted currency)
- Heimdall Score (0-100 with color)
- Risk Level (low|medium|high)
- Confidence (0-1.0, show as percentage)
- Status (badge with color)
- Stage (current pipeline stage)

RIGHT COLUMN:
- Recommended Action (highlighted box)
- Created: {date}
- Raw Text (quoted box)
- VA Notes (if present)

AUDIT TRAIL (expandable section):
- GET http://127.0.0.1:4000/api/va-intake/leads/{lead_id}/audit
- Show: Date | Action | Actor | Details
- Most recent first

BUTTONS:
- "Back to List" → return to Lead List page
- "Add to Approvals" → POST convert if qualified
- "Draft Message" → link to messaging page with this lead_id
- "View Approval" → if approval exists, show approval detail

STYLING:
- Two-column layout: details on left, audit on right
- Color-code score: 75+=green, 55-74=yellow, <55=red
- Monospace font for contact info
- Audit trail: timeline view

TEST WITH:
- Navigate to /lead-detail/4
- Verify all fields display
- Expand audit trail
- Click "Draft Message"
```

---

## PROMPT 4: Approval Queue Page

```
Build a WeWeb page called "Approval Queue" with these requirements:

DATA TABLE:
- GET http://127.0.0.1:4000/api/va-intake/approvals/pending

COLUMNS:
- Lead Address (link to lead detail)
- Seller Name
- Score (color-coded)
- Risk Level (color-coded)
- Status (pending|approved|denied badge)
- Recommended Action
- Created (date)
- Action Button (Approve or Deny - depending on status)

FILTERS:
- Status dropdown: pending|approved|denied
- Show pending by default

APPROVAL ACTIONS (for pending items only):
APPROVE BUTTON:
- Modal asks: "Approve this lead?"
- Input: Bryan/approver name
- POST http://127.0.0.1:4000/api/va-intake/approvals/{approval_id}/approve
- Body: { approver: "name" }
- On success: refresh table, show "✅ Approved"
- On error: show error message

DENY BUTTON:
- Modal asks: "Deny this lead?"
- Input 1: Approver name
- Input 2: Reason for denial (text)
- POST http://127.0.0.1:4000/api/va-intake/approvals/{approval_id}/deny
- Body: { approver: "name", denial_reason: "reason" }
- On success: refresh table, show "❌ Denied"

SUMMARY:
- At top: "X pending | Y approved | Z denied"

STYLING:
- Pending rows: white/light
- Approved rows: green/light
- Denied rows: red/light
- Approve button: green
- Deny button: red
- Color-code Score and Risk columns

TEST WITH:
- GET http://127.0.0.1:4000/api/va-intake/approvals/pending
- Should show 7 pending
- Click Approve on one → approve as "Bryan Test"
- Verify POST succeeds
- Refresh → should show 6 pending, 1 approved
- Click Deny on another → deny with reason "Over estimate"
- Verify POST succeeds
```

---

## PROMPT 5: Draft Message Page

```
Build a WeWeb page called "Draft Message" with these requirements:

URL PARAMETER:
- /draft-message/:lead_id

DATA SOURCE:
- Load lead data from GET http://127.0.0.1:4000/api/va-intake/leads/{lead_id}
- Display lead: Address, Seller Name, Phone, Email at top

MESSAGE TYPE SELECTOR:
- Radio buttons: 
  - ○ Initial Contact (start convo)
  - ○ Follow-up (second contact)
  - ○ Offer (formal offer)

GENERATE DRAFT BUTTON:
- POST http://127.0.0.1:4000/messaging/va/draft-seller-message/{lead_id}
- Query: ?message_type=initial_contact (or follow_up|offer)

DRAFT DISPLAY (after generation):
- Large text box (read-only or editable copy)
- Show: draft text, requires_bryan_approval flag, note

ACTIONS:
- Copy button (copy draft to clipboard)
- Edit button (make it editable)
- Save button (saves edited version)
- "Send to Seller" button → greyed out with tooltip "Draft only - requires Bryan approval"
- "Back to Lead" button

STYLING:
- Draft box: bordered, monospace font, light background
- "Requires Approval" badge: orange warning
- Copy button: light blue
- Send button: disabled/greyed out

TEST WITH:
- Click to lead detail for lead 4
- Click "Draft Message"
- Select "Initial Contact"
- Click "Generate Draft"
- Verify POST succeeds
- Verify draft text appears
- Click Copy (should copy to clipboard)
```

---

## PROMPT 6: Reports Dashboard Page

```
Build a WeWeb page called "Reports Dashboard" with these requirements:

TOP SECTION: Summary Cards
- Card 1: Total Leads (number large, subtitle "this month")
- Card 2: Avg Score (0-100, color-coded)
- Card 3: Total Value (formatted currency)
- Card 4: Approval Rate (percentage, green if high)

API 1 - Summary (GET /reports/va-leads-summary):
- Total Leads: {totals.total_leads}
- Avg Score: {totals.average_heimdall_score}
- Total Value: {totals.total_property_value}

API 2 - Approvals (GET /reports/approval-summary):
- Pending: {totals.pending}
- Approved: {totals.approved}
- Denied: {totals.denied}
- Approval Rate: {metrics.approval_rate_percent}%

CHARTS:
Chart 1: Lead Status Breakdown (Pie Chart)
- Data: {by_status} from va-leads-summary
- Show: qualified_pending_approval, approved, denied, etc.
- Colors: pending=orange, approved=green, denied=red

Chart 2: Lead Quality Distribution (Bar Chart)
- Data: {quality} from va-leads-summary
- Show: high_quality, medium_quality, low_quality
- Colors: high=green, medium=yellow, low=red

Chart 3: Approval Workflow (Funnel or Status Chart)
- Data: pending → approved, denied
- Show: {totals.pending}, {totals.approved}, {totals.denied}

TABLE: Risk Distribution
- From {pending_risk_distribution}
- Show: Risk Level | Count

STYLING:
- Cards: 4 columns on desktop, 2 on tablet, 1 on mobile
- Charts: responsive, clean design
- Colors: match status (green/yellow/red)
- Numbers: large, readable

TEST WITH:
- Load page
- GET http://127.0.0.1:4000/reports/va-leads-summary
- Verify: 9 leads, score 100, value ~$4.3M
- GET http://127.0.0.1:4000/reports/approval-summary
- Charts populate with data
```

---

## PROMPT 7: Navigation & Shell

```
Build a WeWeb shell/navigation component with these requirements:

HEADER:
- Valhalla Legacy Inc. logo/title on left
- System status on right: GET http://127.0.0.1:4000/api/go-live/status
- Display: ✅ Backend Ready | ✅ Database | ✅ VA Intake | ⚠️ WeWeb Not Connected

NAVIGATION MENU (sidebar or top):
Pages:
1. Dashboard (GET /reports/va-leads-summary)
2. Lead List (GET /api/va-intake/leads)
3. Submit Lead (form)
4. Approval Queue (GET /api/va-intake/approvals/pending)
5. Reports (charts)

USER SECTION:
- Display: Logged in as: [user name]
- Dropdown: Settings | Logout

STYLING:
- Navigation: collapsible on mobile
- Active page: highlighted in menu
- Status indicator: refresh every 30 seconds
- Color scheme: professional (blues/grays)

ROUTING:
- / → Dashboard
- /submit-lead → Lead Submission
- /leads → Lead List
- /approvals → Approval Queue
- /reports → Reports Dashboard
- /lead-detail/:lead_id → Lead Detail
- /draft-message/:lead_id → Draft Message

TEST WITH:
- Navigate between pages
- Status indicator updates
- Verify each page loads correct data
```

---

## STOP RULES - READ BEFORE BUILDING

**STOP and wait for backend changes if:**

1. ❌ API returns different field names than documented above
2. ❌ A field is missing from the response (report it, don't guess)
3. ❌ An endpoint returns 404 or 500 error
4. ❌ A button needs a permission level you don't see in docs
5. ❌ A workflow requires an endpoint that doesn't exist
6. ❌ Database doesn't persist your test data
7. ❌ Heimdall score is not returned for new leads
8. ❌ Approval status doesn't update after approve/deny

**DO NOT:**
- ❌ Create new backend endpoints
- ❌ Modify database schema
- ❌ Change field names to "make sense"
- ❌ Add validation that backend doesn't do
- ❌ Call different endpoints than documented
- ❌ Assume a feature exists if not documented
- ❌ Build pages in wrong order (follow sequence 1-7)

**DO:**
- ✅ Test with provided sample data first
- ✅ Use exact field names from this pack
- ✅ Report errors immediately
- ✅ Check backend commit 908d481 if confused
- ✅ Verify API responses match examples
- ✅ Build pages in order (1-7)
- ✅ Lock scope to this one task
- ✅ Stop and report when blocked

---

## TESTING CHECKLIST

### Before calling it "done", test:

```
[ ] Page 1 - Submit Lead
    [ ] Form validates required fields
    [ ] POST sends correct JSON
    [ ] Response shows lead_id
    [ ] Score shows 100 for test lead
    [ ] "Add to Approvals" button appears

[ ] Page 2 - Lead List
    [ ] GET /leads returns 9 items
    [ ] Leads display in table
    [ ] Click row → navigates to detail
    [ ] Filter by status works
    [ ] Refresh button updates data

[ ] Page 3 - Lead Detail
    [ ] GET /leads/{id} loads detail
    [ ] All fields display
    [ ] Audit trail expands
    [ ] Buttons are functional

[ ] Page 4 - Approval Queue
    [ ] GET /approvals/pending shows 7
    [ ] Approve button works
    [ ] Deny button works
    [ ] Status updates after action
    [ ] Filter works

[ ] Page 5 - Draft Message
    [ ] Load lead data
    [ ] POST drafts message
    [ ] Message displays
    [ ] Copy button works

[ ] Page 6 - Reports
    [ ] GET /reports/va-leads-summary loads
    [ ] Charts display data
    [ ] Numbers are correct

[ ] Page 7 - Navigation
    [ ] All pages accessible via menu
    [ ] Status indicator works
    [ ] Mobile responsive
```

---

## QUICK REFERENCE - API BASE

**Local Dev**: `http://127.0.0.1:4000`  
**Production**: `[set by deployment]`

**Health Check**: `GET /health`  
**API Docs**: `GET /docs` (Swagger UI)  
**OpenAPI**: `GET /openapi.json`

---

## Questions for Blocking Issues

If something doesn't work, **before building a workaround**:

1. Copy the exact error message
2. State which endpoint failed
3. Provide request body if applicable
4. Check PHASE_3_COMPLETION_SUMMARY.md
5. Report: "Backend issue: [description]"

**Do NOT make assumptions.**

---

## End of WeWeb Connection Pack

**Status**: Backend LOCKED (commit 908d481)  
**Next**: Build pages 1-7 in order  
**Tokens**: Use one prompt at a time  
**Stop**: Use stop rules above  
**Questions**: Report and wait
