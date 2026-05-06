# Quick Copy-Paste Prompts for WeWeb Pages

**Instructions**: Each section below is a complete prompt. Copy the section, paste into Copilot, and run it. Do NOT modify.

---

## PROMPT 1: Lead Submission Form

```
I'm building the Lead Submission form for a WeWeb app connected to a FastAPI backend.

FORM FIELDS (in order):
1. Source Platform: dropdown (facebook, website, referral, weweb-test)
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

SUBMIT BUTTON ACTION:
POST to http://127.0.0.1:4000/api/va-intake/lead with form data
Show loading spinner during submit
On success: Display alert with "Lead #<lead_id> created! Score: <score>/100 - Status: <status>"
Include button "View Approval Queue"
On error: Show red error alert with error message

FORM BEHAVIOR:
- Clear form after successful submit (unless user clicks "New Lead" button)
- Validate required fields client-side
- Format phone as 555-0123
- Format price with thousands separator

STYLING:
- Two-column form layout on desktop, one column on mobile
- Submit button: green, 100% width, 12px padding
- Required fields: red asterisk
- Error messages: red text below field
- Success alert: green background, white text
- Use professional clean styling

TEST DATA TO USE:
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

Build this page ONLY. Do not add other pages, navigation, or features.
Test the form submission with the sample data provided.
When done, reply "Page 1 complete".
```

---

## PROMPT 2: Leads List & Filter

```
I'm building the Leads List page for a WeWeb app.

DATA SOURCE:
GET http://127.0.0.1:4000/api/va-intake/leads

DATA TABLE STRUCTURE:
Columns (in order):
1. Address (text, clickable - links to lead detail page)
2. Seller Name (text)
3. Price (number, format as currency)
4. Score (integer 0-100, color: ≥75=green, 55-74=yellow, <55=red)
5. Status (text badge: green=approved, orange=pending, red=denied)
6. Created (date, format as "May 6, 2026")
7. Action (button: "View Details" - links to /lead-detail/{lead_id})

TABLE BEHAVIOR:
- Load data on page mount
- Show "Loading..." while fetching
- Display total count at top: "Total: X leads"
- Sort by Created date (newest first)
- Rows per page: 10
- Pagination: Previous/Next buttons
- On row click, navigate to lead detail page

OPTIONAL FILTER (top of page):
- Status dropdown: "All Statuses" | "qualified_pending_approval" | "approved" | "denied"
- Apply filter: GET /api/va-intake/leads?status=<filter>
- Refresh button to reload data

STYLING:
- Table: clean, bordered
- Score column: background color matching the color scheme
- Status column: colored badge
- Hover effect: slight background color on row hover
- Mobile: stack columns or horizontal scroll
- Header: light gray background, bold text

TEST:
- Load page
- Should display 9 leads (leads 4-8 are seed data)
- Click "View Details" on one lead
- Try filter dropdown

Build this page ONLY.
When done, reply "Page 2 complete".
```

---

## PROMPT 3: Lead Detail Page

```
I'm building the Lead Detail page for a WeWeb app.

ROUTE PARAMETER:
/lead-detail/:lead_id (the lead_id is in the URL)

DATA SOURCE:
GET http://127.0.0.1:4000/api/va-intake/leads/{lead_id}

DISPLAY LAYOUT:

LEFT COLUMN (60%):
Property Details (heading)
- Address (large, bold)
- City, Province (text)
- Seller Name (text)
- Seller Phone (text, make it clickable tel: link)
- Seller Email (text, make it clickable mailto: link)

CENTER COLUMN (40%):
Deal Metrics (heading)
- Asking Price (bold, formatted currency)
- Heimdall Score (0-100, large, color-coded: ≥75=green, 55-74=yellow, <55=red)
- Risk Level (text: low/medium/high, colored badge)
- Confidence (percentage, e.g., "95%")
- Status (badge with color)
- Stage (text)

BOTTOM SECTION (full width):
Actions (heading)
Buttons (inline):
- "Back to List" (blue, links to /leads)
- "Draft Message" (green, links to /draft-message/{lead_id})
- "Add to Approvals" (if not already in queue - POST convert endpoint)

TABS/SECTIONS:

Tab 1: Raw Text
- Quoted box with property description

Tab 2: VA Notes
- If present, display in box

Tab 3: Audit Trail
- GET http://127.0.0.1:4000/api/va-intake/leads/{lead_id}/audit
- Table with: Date | Action | Actor | Details
- Most recent first

STYLING:
- Clean two-column layout
- Color-code all score/risk fields
- Monospace font for phone/email
- Audit trail: timeline format with timestamps
- Responsive: stack columns on mobile

BEHAVIOR:
- Load on page mount
- Show "Loading..." while fetching
- If lead not found, show "Lead not found"

TEST:
- Navigate to /lead-detail/4
- Verify all fields display
- Click phone/email (should open tel: and mailto:)
- Click "Back to List"
- Click "Draft Message"

Build this page ONLY.
When done, reply "Page 3 complete".
```

---

## PROMPT 4: Approval Queue Page

```
I'm building the Approval Queue page for a WeWeb app.

DATA SOURCE:
GET http://127.0.0.1:4000/api/va-intake/approvals/pending

DATA TABLE:
Columns (in order):
1. Address (text, clickable to lead detail)
2. Seller Name (text)
3. Score (0-100, color-coded: ≥75=green, 55-74=yellow, <55=red)
4. Risk Level (text badge: low=blue, medium=orange, high=red)
5. Status (badge: pending=orange, approved=green, denied=red)
6. Recommended Action (text, wrapped)
7. Created (date)
8. Action (button)

ACTION BUTTON LOGIC:
- If status="pending": Show "Approve" (green) and "Deny" (red) buttons
- If status="approved": Show "✅ Approved" (disabled)
- If status="denied": Show "❌ Denied" (disabled)

APPROVE FLOW:
1. User clicks "Approve" button
2. Modal dialog appears:
   - Heading: "Approve this lead?"
   - Input: "Approver name" (text)
   - Buttons: Cancel, Approve (green)
3. On Approve button click:
   - POST http://127.0.0.1:4000/api/va-intake/approvals/{approval_id}/approve
   - Body: { "approver": "<name>" }
   - Show loading spinner
   - On success: Refresh table, show green toast "✅ Lead approved"
   - On error: Show red alert with error message
   - Modal closes

DENY FLOW:
1. User clicks "Deny" button
2. Modal dialog appears:
   - Heading: "Deny this lead?"
   - Input 1: "Approver name" (text)
   - Input 2: "Reason" (textarea, required)
   - Buttons: Cancel, Deny (red)
3. On Deny button click:
   - POST http://127.0.0.1:4000/api/va-intake/approvals/{approval_id}/deny
   - Body: { "approver": "<name>", "denial_reason": "<reason>" }
   - Show loading spinner
   - On success: Refresh table, show red toast "❌ Lead denied"
   - On error: Show red alert with error message
   - Modal closes

PAGE-LEVEL FILTER (optional):
- Status dropdown: "Pending" | "Approved" | "Denied"
- Apply filter: requery with status parameter

SUMMARY AT TOP:
- "X Pending | Y Approved | Z Denied"
- Refresh button

TABLE BEHAVIOR:
- Load on page mount
- Sort by Created (newest first)
- Rows per page: 10
- Pagination: Previous/Next

STYLING:
- Table: clean, bordered
- Pending rows: light orange background
- Approved rows: light green background
- Denied rows: light red background
- Score column: background color
- Action buttons: clear, accessible

INITIAL TEST DATA:
Should show 7 pending approvals from seed leads

Build this page ONLY.
When done, reply "Page 4 complete".
```

---

## PROMPT 5: Draft Message Page

```
I'm building the Draft Message page for a WeWeb app.

ROUTE PARAMETER:
/draft-message/:lead_id

DATA SOURCE:
GET http://127.0.0.1:4000/api/va-intake/leads/{lead_id}

PAGE LAYOUT:

HEADER SECTION:
- Lead info at top: "Drafting message for: <address>, <seller_name>"
- Display: Phone and Email (as clickable links)

MESSAGE TYPE SELECTOR:
- Heading: "Message Type"
- Radio button group (select one):
  ○ Initial Contact - "First outreach to seller"
  ○ Follow-up - "Second contact after no response"
  ○ Offer - "Formal offer message"
- Default selected: "Initial Contact"

GENERATE BUTTON:
- Button: "Generate Draft" (green, 200px wide)
- Shows loading spinner while generating
- On click:
  - POST http://127.0.0.1:4000/messaging/va/draft-seller-message/{lead_id}
  - Query parameter: ?message_type=<selected_type>
  - On success: Display draft section below

DRAFT DISPLAY SECTION (after generation):
- Heading: "Draft Message"
- Text box: Display the draft message (read-only initially, monospace font)
- Badge: "⚠️ Requires Bryan Approval" (orange background)
- Note: "Draft only - review with Bryan before sending"

ACTION BUTTONS (below draft):
- "Copy to Clipboard" (blue button) - copies draft text
- "Edit" (gray button) - makes text box editable (optional feature)
- "Back to Lead" (gray button, links to /lead-detail/{lead_id})
- "Send Message" (red disabled button with tooltip "Feature not available - draft only")

STYLING:
- Draft box: bordered (1px solid gray), light gray background, monospace font
- Warning badge: orange background, white text
- Copy button: light blue background
- Send button: disabled/grayed out (visual feedback)
- Mobile: full-width buttons stacked

ERROR HANDLING:
- If lead not found: "Lead not found"
- If POST fails: Show error message in red

BEHAVIOR:
- Load lead data on mount
- Initial state: "Generate Draft" button visible
- After generation: Draft text displayed, buttons available

TEST:
- Navigate to /draft-message/4
- Select "Initial Contact"
- Click "Generate Draft"
- Verify POST succeeds
- Verify draft text appears
- Click "Copy to Clipboard"
- Back button should go to /lead-detail/4

Build this page ONLY.
When done, reply "Page 5 complete".
```

---

## PROMPT 6: Reports Dashboard

```
I'm building the Reports Dashboard page for a WeWeb app.

DATA SOURCES:
API 1: GET http://127.0.0.1:4000/reports/va-leads-summary
API 2: GET http://127.0.0.1:4000/reports/approval-summary
API 3: GET http://127.0.0.1:4000/reports/eia-monthly-summary

PAGE LAYOUT:

TOP SECTION: Summary Cards (4 columns on desktop, 2 on tablet, 1 on mobile)
Card 1: Total Leads
- Large number: {totals.total_leads}
- Subtitle: "Total leads submitted"
- Icon: 📋

Card 2: Average Score
- Large number: {totals.average_heimdall_score}/100
- Subtitle: "Heimdall Score"
- Background color: green (high score), yellow (medium), red (low)
- Icon: 📊

Card 3: Total Value
- Large currency: {totals.total_property_value}
- Subtitle: "Total property value"
- Icon: 💰

Card 4: Approval Rate
- Large percentage: {metrics.approval_rate_percent}%
- Subtitle: "Approval rate"
- Icon: ✅

CHARTS SECTION (below cards):

Chart 1: Lead Status Distribution (Pie Chart)
- Title: "Leads by Status"
- Data: From {by_status} in va-leads-summary
- Show slices for: qualified_pending_approval, approved, denied, etc.
- Colors: pending=orange, approved=green, denied=red, other=gray
- Legend below chart
- Position: 50% width, left side

Chart 2: Lead Quality Distribution (Bar Chart)
- Title: "Lead Quality"
- Data: From {quality} in va-leads-summary
- Show bars: high_quality, medium_quality, low_quality
- Colors: high=green, medium=yellow, low=red
- X-axis labels: "High", "Medium", "Low"
- Y-axis: Count
- Position: 50% width, right side

BOTTOM SECTION:

Risk Distribution Table
- Title: "Pending Approvals by Risk"
- Data: From {pending_risk_distribution} in approval-summary
- Columns: Risk Level (colored badge) | Count
- Show all risk levels

BEHAVIOR:
- Load all 3 APIs on page mount
- Show loading spinners while loading
- If API fails, show error message but don't break page
- Auto-refresh every 60 seconds (or add manual refresh button)

STYLING:
- Cards: white background, border, shadow, padding
- Numbers: large, bold, readable
- Charts: responsive, clean design
- Table: striped rows, alternating colors
- Colors: match the Valhalla theme (professional)
- Mobile: stack elements vertically

RESPONSIVE DESIGN:
- Desktop: 4 columns for cards, 2 columns for charts
- Tablet: 2 columns for cards, 1 column for charts
- Mobile: 1 column for cards, 1 column for charts, full-width table

TEST:
- Load page
- GET apis return data
- Cards display correct numbers
- Charts render data
- Responsive on mobile

Build this page ONLY.
When done, reply "Page 6 complete".
```

---

## PROMPT 7: Navigation & Shell

```
I'm building the Navigation Shell/Layout for a WeWeb app with 7 pages.

PAGES TO ROUTE:
1. Dashboard → /dashboard (Reports Dashboard)
2. Leads → /leads (Lead List)
3. Submit Lead → /submit-lead (Lead Submission Form)
4. Approvals → /approvals (Approval Queue)
5. Lead Detail → /lead-detail/:lead_id (Lead Detail Page)
6. Draft Message → /draft-message/:lead_id (Draft Message Page)
7. Reports → /reports (Reports Dashboard - same as dashboard)

NAVIGATION STRUCTURE:

TOP HEADER (always visible):
- Left side: "Valhalla Legacy Inc." (heading, clickable to dashboard)
- Right side: System Status Indicator
  - GET http://127.0.0.1:4000/api/go-live/status every 30 seconds
  - Display as inline badges: ✅ Backend | ✅ Database | ✅ VA Intake | ⚠️ WebWeb Not Connected
  - Green for true, orange for false

SIDEBAR NAVIGATION (collapsible on mobile):
Main Menu Items:
- 🏠 Dashboard (link to /dashboard)
- 📋 Leads (link to /leads)
- ➕ Submit Lead (link to /submit-lead)
- ✔️ Approvals (link to /approvals)
- 📊 Reports (link to /reports)

Active page: Highlight in menu

USER SECTION (bottom of sidebar):
- Display: "Logged in as: Admin"
- Dropdown menu: Settings | Logout

MAIN CONTENT AREA:
- Flex layout: Sidebar + Content
- Content area: renders page components based on route
- Breadcrumb (optional): shows current page location

ROUTING:
- / → /dashboard
- /dashboard → Reports Dashboard
- /submit-lead → Lead Submission Form
- /leads → Lead List
- /lead-detail/:lead_id → Lead Detail Page
- /approvals → Approval Queue
- /draft-message/:lead_id → Draft Message Page
- /reports → Reports Dashboard

RESPONSIVE DESIGN:
- Desktop: Sidebar visible, navigation horizontal
- Tablet: Sidebar visible, reduced width
- Mobile: Sidebar collapsible, hamburger menu toggle

STYLING:
- Professional color scheme: blues, grays, whites
- Sidebar: dark background with white text
- Active menu item: highlighted (bold, background color)
- Header: light background, clean layout
- Icons: use emoji or simple SVG
- Responsive: smooth transitions, mobile-friendly

BEHAVIOR:
- On page load: Show dashboard
- On route change: Update active menu item
- Status indicator: refresh every 30 seconds
- Sidebar toggle: smooth animation on mobile

Connect all 6 previous pages through this navigation shell.
Make sure routes work correctly for parameterized pages (:lead_id).
Add loading state for page transitions.

Build this shell/layout ONLY.
When done, reply "Page 7 complete - WeWeb frontend ready for testing".
```

---

## Usage Instructions

### For Each Prompt:

1. **Copy the entire code block** (from ``` to ```)
2. **Paste into Copilot Chat**
3. **Wait for completion**
4. **Test the page**
5. **Reply with "works!" or describe the problem**

### After Each Page:

- ✅ If it works: Copy next prompt
- ❌ If it doesn't work: Report the error, include:
  - Exact error message
  - What you did
  - What you expected
  - DO NOT ask for alternative approaches

### When Done:

All 7 pages built → Reply: "All done! Ready to test end-to-end"

---

## Stop Rules Reminder

**DO NOT build more than what's in the prompt**

**DO NOT:**
- Add features not listed
- Modify endpoints
- Change field names
- Assume features exist
- Build multiple pages in one prompt

**DO STOP if:**
- API returns different fields
- Endpoint returns error
- Field is missing
- Response structure differs
- Unclear requirements

**Then report and wait for clarification**

---

**Total Estimated Time**: 2-3 days (May 6-9)  
**Token Budget**: 75-130K  
**Status**: Ready to build  
**Backend**: Locked (commit 908d481)
