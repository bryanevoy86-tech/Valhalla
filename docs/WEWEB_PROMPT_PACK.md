# WEWEB PROMPT PACK: Copy-Paste Building Instructions

**Status:** READY TO USE  
**Purpose:** Give to WeWeb team as copy-paste prompts - save your tokens  
**Base URL:** https://valhalla-api-ha6a.onrender.com  
**Authorization:** None required (open API for now)  
**Last Updated:** 2026-04-13  

---

## HOW TO USE THIS DOCUMENT

1. Copy each prompt exactly as written
2. Paste into your WeWeb builder or AI assistant
3. Follow the implementation order
4. Test each step before moving to next
5. Do NOT deviate from prompts without approval

---

## PROMPT #1: VERIFICATION ONLY

**Purpose:** Verify WeWeb can reach the backend before building anything

**Use This First:**

```
TASK: Verify Backend API Connectivity

Backend Base URL: https://valhalla-api-ha6a.onrender.com

Test these 3 routes to confirm connectivity:

1. GET https://valhalla-api-ha6a.onrender.com/execution/cases
   Expected: HTTP 200, JSON array of case objects

2. POST https://valhalla-api-ha6a.onrender.com/execution/intake
   Body: { "raw_text": "Test property - 3 bed house" }
   Expected: HTTP 200, Response includes "intake_id"

3. GET https://valhalla-api-ha6a.onrender.com/execution/cases/{case_id}
   (Replace {case_id} with the case_id you got from step 2)
   Expected: HTTP 200, Full case object with fields

If all three return HTTP 200 with valid data, backend is working.
If you get 500 errors or empty responses, DO NOT PROCEED - notify team.

Report back: "Backend verification: ✓ PASS" or "✗ FAIL"
```

---

## PROMPT #2: BUILD EXECUTION CONSOLE PAGE

**Purpose:** Build the single landing page that runs the business

**Use This After:** Backend verification passes

```
TASK: Build WeWeb Page - "Execution Console"

Requirements:
- Page URL: /execution-console or /?case={case_id}
- Single page, no navigation (for now)
- Responsive design (desktop, tablet, mobile)

BASE URL: https://valhalla-api-ha6a.onrender.com

================== SECTION 1: PASTE OPPORTUNITY ==================

Component: Textarea input + Button

Label: "Paste raw opportunity text"
Placeholder: "Paste opportunity description here... e.g., 3 bed 2 bath house, asking $250k, needs roof"
Submit Button: "PROCESS THIS OPPORTUNITY"

On button click:
1. Read textarea value → ${opportunity_text}
2. POST to: /execution/intake
   Headers: { "Content-Type": "application/json" }
   Body: { "raw_text": "${opportunity_text}" }
3. On success (HTTP 200):
   - Extract response.intake_id
   - Show loading message: "Analyzing opportunity..."
   - Wait 2 seconds
   - Call: POST /execution/intake/{intake_id}/process
   - Body: {"intake_id": {intake_id}}
   - On success: Extract response.case_id
   - Call: GET /execution/cases/{case_id}
   - Populate all sections below with response data
   - Clear textarea
4. On error (HTTP 422 or 500):
   - Show error message in red banner
   - Message: "Error: " + response.error_message
   - Keep textarea content
   - Offer [RETRY] button

================== SECTION 2: DEAL SUMMARY ==================

Display these fields from GET /execution/cases/{case_id} response:

Required Fields (must display):
- case_id
- case_type (Real Estate / Commercial / etc)
- strategy (Wholesale / Hold / Flip / Partnership)
- purchase_price_estimate (if available, with $ formatting)
- arv_estimate (if available)
- repair_estimate (if available)
- current_stage (with color: yellow for pending, green for active)
- current_status

If blocked = true:
- Show red alert box with blocker_reason text
- Display prominently at top of summary
- Example: "🔴 BLOCKED: Profit margin 2.0% - below 5% threshold"

Formatting:
- All currency values with $ and comma separators ($250,000)
- Create color badges for stage (yellow=pending, green=active, red=blocked)
- Show strategy as uppercase badge (WHOLESALE, HOLD, etc)

================== SECTION 3: NEXT ACTION ==================

From response.next_action, display:
- Show in prominent box/card
- Font: Larger than normal text
- Color: Red if blocked, Yellow if needs review, Green if approved

Display action buttons based on blocked status:

If blocked:
  [OK-PROCEED] [REQUEST-CLARIFICATION] [PASS]

If not blocked:
  [APPROVE & PROCEED] [PASS]

On button click:
- POST to: /execution/cases/{case_id}/advance
- Headers: { "Content-Type": "application/json" }
- Body for proceed buttons:
  {
    "case_id": {case_id},
    "action": "owner_review_approved",
    "notes": "" (or read from notes textarea if present)
  }
- Body for pass buttons:
  {
    "case_id": {case_id},
    "action": "owner_rejected",
    "notes": ""
  }
- On success: Show green banner "Case advanced to next stage ✓"
- On success: Refresh page data by calling:
  GET /execution/cases/{case_id}
  GET /execution/cases/{case_id}/tasks
  Update all display sections

================== SECTION 4: TASK CHECKLIST ==================

From GET /execution/cases/{case_id}/tasks response:

For each task object in response.tasks array:
- Display as a checkbox item (unchecked initially)
- Show fields:
  - task.title
  - task.priority (1-10, color code: 1-3=red star, 4-6=blue, 7-10=green)
  - task.category (verification, contact, analysis, decision)
  - task.due_days (relative: "Due in 1 day", "Overdue")
  - task.description (optional, can collapse/expand)
  - task.assignee

IMPORTANT: Checkboxes are visual ONLY for day-one
- Do NOT call any API when user clicks checkbox
- Just toggle checked state locally
- This is manual operator tracking

Display notes area:
- Label: "Case Notes"
- Textarea, allow freeform operator notes
- For now: store in browser localStorage (key: "case_${case_id}_notes")
- In future (week 2): POST to /execution/cases/{case_id}/add-notes

================== SECTION 5: EVENT LOG ==================

From GET /execution/cases/{case_id}/events response:

Show as timeline/list (most recent first):
- For each event in response.events array:
  - Show: event.created_at (formatted: "2026-04-13 20:51")
  - Show: event.description (full text)
  - Show: event.event_type as label (case_created, case_processed, etc)
  - Show: event.actor (who did it, e.g., "system", "operator")

Optional: [MORE EVENTS] link at bottom if > 3 events

================== STYLING GUIDE ==================

Color Scheme:
- Viable/Good: #22C55E (green)
- Pending/Warning: #EAB308 (yellow)
- Blocked/Error: #EF4444 (red)
- Info: #3B82F6 (blue)

Typography:
- Headings: 20px, bold
- Body text: 14px, regular
- Labels: 12px, gray
- Urgency text: 16px, bold

Spacing:
- Between sections: 20px margin
- Between fields: 10px margin
- Button padding: 8px 16px

Buttons:
- Primary (PROCESS, APPROVE): Green background, white text, 12px bold
- Secondary (PASS): Red background, white text
- Size: 48px height minimum (mobile touch target)

================== RESPONSIVE DESIGN ==================

Desktop (1920px+):
- Max content width: 900px
- Centered on page
- Full spacing

Tablet (768px-1024px):
- Full width with 20px padding
- Sections stack vertically
- Buttons full width

Mobile (< 768px):
- Full width
- All buttons full width
- Textareas full width
- Touch targets > 48x48px

================== ERROR HANDLING ==================

Display errors in red banner at top of page:

HTTP 422 (Missing field):
Message: "Validation error: {field_name} is required"
Action: Keep form data, let user fix and retry

HTTP 404 (Case not found):
Message: "Case not found. Please paste a new opportunity."
Action: Clear form, show empty state

HTTP 500 (Server error):
Message: "System error. Try again in 30 seconds."
Action: Show [RETRY] button

Network error (no response):
Message: "Connection lost. Check internet."
Action: Show [RETRY] button

Clear errors after 5 seconds unless user interacts.

================== LOCAL STORAGE PERSISTENCE ==================

Save to localStorage (for day-one MVP):
- localStorage.setItem("current_case_id", case_id)
- localStorage.setItem("case_${case_id}_notes", notes_textarea_value)

On page load:
- If localStorage has current_case_id, fetch and display that case
- Otherwise show empty paste-opportunity section

================== TESTING CHECKLIST ==================

Test these scenarios:

1. Paste → Process → Display Works
   [ ] Textarea accepts text
   [ ] Process button calls API
   [ ] Case displays after 2s
   [ ] All fields populate

2. Blocked Case Display
   [ ] Red blocked banner shows
   [ ] Blocker reason displays
   [ ] Decision buttons show

3. Task Checklist
   [ ] Tasks display in list
   [ ] Checkboxes toggle (no API call)
   [ ] Notes persist in localStorage

4. Button Actions
   [ ] [OK-PROCEED] calls advance API
   [ ] [PASS] calls reject API
   [ ] Success banner shows
   [ ] Page refreshes with new stage

5. Mobile Responsive
   [ ] All text readable at 14px
   [ ] All buttons > 48x48px touch targets
   [ ] No horizontal scroll
   [ ] Inputs full width

6. Error Cases
   [ ] Paste nothing → error on process
   [ ] Invalid case_id → 404 handled
   [ ] Network down → connection error shown

REPORT: "Execution Console build complete - All tests passing ✓"
```

---

## PROMPT #3: POLISH & REFINEMENT (Week 1 Post-Launch)

**Purpose:** Make the page production-ready

**Use This After:** First build is live and you're running cases through it

```
TASK: Polish Execution Console for Production

Improvements to implement:

1. LOADING STATES
   - When processing opportunity: Show spinner + "Analyzing..." text
   - When loading case: Show skeleton placeholders
   - When submitting decision: Disable buttons + show "Saving..."

2. VISUAL POLISH
   - Add icons to section headers (paste icon, checkmark icon, etc)
   - Highlight blocked/urgent items in red background
   - Add subtle shadows to cards
   - Make margins consistent throughout

3. USER FEEDBACK
   - Toast notification when opportunity pasted: "Opportunity saved. Analyzing..."
   - Toast when case advanced: "Case moved to next stage ✓"
   - Toast on error: Red toast with "Error: {reason}"
   - Success banner: Green background, stays 3 seconds then fades

4. MOBILE OPTIMIZATION
   - Stack all button groups to full width on mobile
   - Make task list scrollable on mobile if > 5 tasks
   - Textarea minimum height 100px
   - Increase font sizes on mobile (14px → 16px)

5. ACCESSIBILITY
   - Add alt text to all icons
   - Add aria-labels to buttons
   - Ensure color contrast > 4.5:1
   - Make form keyboard navigable (Tab through fields)
   - Add focus indicators (blue outline on focus)

6. PERFORMANCE
   - Cache case data so refreshing doesn't cause flicker
   - Debounce manual textarea saves (500ms)
   - Lazy load event log (show 3, load more on demand)

DONE: "Execution Console v1.0 production-ready ✓"
```

---

## PROMPT #4: SECOND BUILD - PIPELINE BOARD

**Purpose:** After first build stable, build team collaboration page

**Use This After:** Minimum 1 week post-Execution Console launch

```
TASK: Build WeWeb Page - "Pipeline Board"

When ready: (Only after Execution Console is proven and team is live with it)

Page URL: /pipeline-board
Navigation: Add link to Execution Console for quick switching

This is a multi-stage Kanban-like table view for team coordination.

See WEWEB_SECOND_BUILD_SCOPE.md for complete specification.

Key routes:
- GET /execution/cases?stage=X&assigned_to=Y (filter by stage and assignee)
- POST /execution/cases/{id}/assign (reassign case)
- POST /execution/cases/{id}/advance (stage movement)

This build should NOT start until first build is 100% stable
and you've closed at least 3 deals through it without issues.

TIMELINE: Week 2-3 post-launch (not day one)
```

---

## PROMPT #5: WIRING FOR VA ROLE ACCESS

**Purpose:** After hiring first VA, restrict their view

**Use This After:** You have actual team members to assign cases to

```
TASK: Implement Role-Based View Restrictions

When you add team members:
- Store their role: INTAKE_VA, QUAL_VA, FOLLOWUP_VA, CLOSER, OWNER
- On page load, check logged-in user's role
- Filter case list based on role:

  OWNER can see: All cases
  INTAKE_VA can see: Cases with stage=intake_processed, assigned to them
  QUAL_VA can see: Cases with stage=intake_processed or ready_for_contact
  FOLLOWUP_VA can see: Cases with stage=ready_for_contact or contacted
  CLOSER can see: Cases with stage=negotiating or under_contract

Implementation:
- Add role check before showing case list
- If not authorized for case: Show "Access Denied"
- If VA can only see their assigned cases: Filter by "assigned_to_user_id = current_user"

This is optional for day-one (you're the only user initially)
But implement on landing so it's ready when you hire.
```

---

## PROMPT #6: INTEGRATION CHECKLIST

**Purpose:** Ensure all connections are working before launch

**Use This:** Before going live

```
TASK: Final Integration Verification

Before launching to users, verify:

[✓] Backend connectivity
   - GET /execution/cases returns data
   - POST /execution/intake creates records
   - POST /execution/intake/{id}/process generates case

[✓] Page functionality
   - Paste text → Process → Case display
   - Display all fields from API response
   - Buttons trigger correct API calls
   - Errors handled gracefully

[✓] Responsive design
   - Desktop: Works at 1920px
   - Tablet: Works at 1024px
   - Mobile: Works at 375px
   - No horizontal scroll

[✓] Performance
   - Page load: < 3 seconds
   - API calls: < 1 second response
   - No UI lag when clicking buttons

[✓] Data persistence
   - Notes saved to localStorage
   - Case data reflects API response
   - Refresh page: Case still visible

[✓] Error handling
   - Invalid input: Error message shown
   - Network error: Graceful fallback
   - API error: User-friendly message

[✓] Mobile-specific
   - All buttons > 48px height
   - Textareas full width
   - No horizontal scroll
   - Portrait orientation works

SIGN-OFF: "Integration verification complete - Ready for production ✓"

When all boxes ticked: Deploy to production
```

---

## WHAT TO AVOID

❌ Do NOT add pages beyond Execution Console (first build only)
❌ Do NOT add dashboards or charts
❌ Do NOT add user authentication (treat all users as "OWNER")
❌ Do NOT cache data longer than 30 seconds
❌ Do NOT make API calls on every keystroke (batch/debounce)
❌ Do NOT require user registration
❌ Do NOT store API keys in client-side code
❌ Do NOT expose full API errors to users (sanitize them)
❌ Do NOT implement real-time updates yet (poll every 30s instead)
❌ Do NOT build team management (manual for now)

---

## API RESPONSE FORMATS

### POST /execution/intake Response
```json
{
  "intake_id": 16,
  "raw_text": "3 bed 2 bath house...",
  "created_at": "2026-04-13T20:49:14.473666",
  "status": "new",
  "message": "Opportunity recorded..."
}
```

### POST /execution/intake/{id}/process Response
```json
{
  "case_id": 3,
  "intake_id": 16,
  "case_type": "real_estate",
  "route_target": "blocked",
  "current_stage": "intake_processed",
  "current_status": "pending_review",
  "safe_mode": true,
  "blocked": true,
  "blocker_reason": "Profit margin only 2.0% - below 5% threshold",
  "next_action": "Manual review required - potential high-risk deal",
  "created_at": "2026-04-13T20:50:00.000000",
  "updated_at": "2026-04-13T20:50:00.000000"
}
```

### GET /execution/cases/{id} Response
```json
{
  "case_id": 3,
  "intake_id": 16,
  "case_type": "real_estate",
  "route_target": "blocked",
  "current_stage": "intake_processed",
  "current_status": "pending_review",
  "safe_mode": true,
  "blocked": true,
  "blocker_reason": "...",
  "next_action": "...",
  "created_at": "2026-04-13T20:50:00.000000",
  "updated_at": "2026-04-13T20:50:00.000000"
}
```

### GET /execution/cases/{id}/tasks Response
```json
{
  "case_id": 3,
  "tasks": [
    {
      "id": 1,
      "title": "Verify property...",
      "description": "...",
      "category": "verification",
      "priority": 1,
      "status": "pending",
      "sequence": 1,
      "assignee": "king",
      "due_days": 1,
      "created_at": "2026-04-13T20:50:00.000000"
    },
    ...
  ]
}
```

### GET /execution/cases/{id}/events Response
```json
{
  "case_id": 3,
  "events": [
    {
      "id": 1,
      "event_type": "case_created",
      "description": "Case created from intake ID 16",
      "actor": "system",
      "created_at": "2026-04-13T20:50:00.000000"
    },
    ...
  ]
}
```

---

## SUPPORT CONTACTS

If API errors occur:
1. Check that URL is exactly: https://valhalla-api-ha6a.onrender.com
2. Verify request body matches schema above
3. Check response HTTP status code
4. If 500 error: Backend may be down, wait 1 minute and retry
5. If persistent issues: Report with exact error message + request body

---

## SUMMARY

**Execution Order:**
1. Prompt #1: Verify backend
2. Prompt #2: Build Execution Console
3. Prompt #3: Polish (week 1 post-launch)
4. Prompt #4: Pipeline Board (week 2+ post-launch)
5. Prompt #5: Role restrictions (when hiring VAs)
6. Prompt #6: Final verification before launch

**Target Timeline:**
- Week 1: Prompts #1-2 (launch Execution Console)
- Week 2: Prompt #3 (polish based on real usage)
- Week 3: Prompt #4 (build Pipeline Board)
- Month 1+: Prompts #5-6 (team features)

**Do NOT deviate from these prompts without architecture approval.**

---

**Document Owner:** WeWeb Coordination / Product  
**Status:** READY TO DISTRIBUTE  
**Last Updated:** 2026-04-13  
**Revision:** 1.0  
