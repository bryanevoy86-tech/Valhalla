# WEWEB FIRST BUILD SCOPE: Execution Console v1.0

**Status:** IMPLEMENTATION-READY  
**Target Platform:** WeWeb (low-code)  
**Base API URL:** https://valhalla-api-ha6a.onrender.com  
**Launch Date:** 2026-04-22 (TBD)  
**Scope Freeze:** Yes - No additions without approval  

---

## EXECUTIVE SUMMARY

The first WeWeb build is **ONE PAGE ONLY: The Execution Console**.

This single page must:
1. Accept paste opportunity text
2. Show system analysis
3. Display go/no-go decision
4. Show task checklist
5. Show pipeline stage
6. Show strategy
7. Enable case advancement
8. Show history

This page is sufficient to:
- ✅ Run the business for day-one
- ✅ Close deals without touching APIs
- ✅ Make team assignments (manual UI)
- ✅ Track all deal states
- ✅ Feed all reported decisions

This page is **NOT** for:
- ❌ Dashboards or reporting
-❌ Multi-page navigation
- ❌ Advanced builder controls
- ❌ Procurement workflows
- ❌ Portfolio management
- ❌ Investor portal
- ❌ Admin controls
- ❌ Anything not on this page

---

## PAGE LAYOUT

```
┌──────────────────────────────────────────────────────────────┐
│  🎯 EXECUTION CONSOLE                      [?] [Settings]    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─ STAGE 1: PASTE OPPORTUNITY ────────────────────────────┐ │
│  │                                                          │ │
│  │  [Paste raw opportunity text here...]                  │ │
│  │  ┌──────────────────────────────────┐                  │ │
│  │  │                                  │                  │ │
│  │  │ 3 bed 2 bath house, asking $250k │                  │ │
│  │  │ needs roof, great neighborhood   │                  │ │
│  │  │                                  │                  │ │
│  │  └──────────────────────────────────┘                  │ │
│  │                                                          │ │
│  │                            [PROCESS THIS OPPORTUNITY]    │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─ STAGE 2: DEAL SUMMARY ────────────────────────────────┐  │
│  │                                                         │  │
│  │  Case ID: #3                                           │  │
│  │  Status: 🟡 PENDING REVIEW (awaiting your decision)    │  │
│  │                                                         │  │
│  │  Classification:                                       │  │
│  │  • Type: Real Estate                                   │  │
│  │  • Strategy: Wholesale                                 │  │
│  │  • Market: Residential                                 │  │
│  │                                                         │  │
│  │  Financial Snapshot:                                   │  │
│  │  • Purchase Price: $250,000                            │  │
│  │  • ARV Estimate: $300,000                              │  │
│  │  • Repair Cost: $10,000                                │  │
│  │  • Est. Spread: $40,000  ✓ VIABLE                      │  │
│  │                                                         │  │
│  │  🔴 BLOCKED: Low margin - Manual Review Required       │  │
│  │  Reason: System detected risk - needs operator review  │  │
│  │                                                         │  │
│  │  Zone: [Unassigned - pick from dropdown]               │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─ STAGE 3: NEXT ACTION ─────────────────────────────────┐  │
│  │                                                         │  │
│  │  🔴 ESCALATION REQUIRED                                │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │ This deal needs manual review before proceeding. │   │  │
│  │  │ Margin is lower than our standard threshold.     │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │                                                         │  │
│  │  Make Your Decision:                                   │  │
│  │  [ OK-PROCEED ] [ REQUEST-INFO ] [ PASS ]              │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─ STAGE 4: TASK CHECKLIST ──────────────────────────────┐  │
│  │                                                         │  │
│  │  For You (Operator) - Complete these:                  │  │
│  │                                                         │  │
│  │  [ ] ⭐ PRIORITY 1 - Verify property exists            │  │
│  │      Confirm property and details are real, not spam   │  │
│  │      Due: Today                                        │  │
│  │                                                         │  │
│  │  [ ] 🔵 PRIORITY 2 - Contact seller to confirm motive  │  │
│  │      Reach out and understand why they want to sell    │  │
│  │      Due: Tomorrow                                     │  │
│  │                                                         │  │
│  │  [ ] 🟢 PRIORITY 3 - Calculate spread                  │  │
│  │      Get contractor quotes, verify repair cost         │  │
│  │      Due: Monday                                       │  │
│  │                                                         │  │
│  │  [ ] ⭐ PRIORITY 1 - Decide: Proceed or Pass?          │  │
│  │      Review info and make go/no-go decision            │  │
│  │      Due: 14 days                                      │  │
│  │                                                         │  │
│  │  Notes: [empty text field for your notes]              │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─ STAGE 5: PIPELINE STAGE ──────────────────────────────┐  │
│  │                                                         │  │
│  │  Current Stage: 🟡 INTAKE_PROCESSED                    │  │
│  │                                                         │  │
│  │  Stage Progress:                                       │  │
│  │  INTAKE → [✓ INTAKE_PROCESSED] → Ready For Contact    │  │
│  │           ████░░░░░░░░░░░░░░░░ 20%                     │  │
│  │                                                         │  │
│  │  Actions:                                              │  │
│  │  [APPROVE & PROCEED] [REQUEST CLARIFICATION]           │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─ STAGE 6: EVENT LOG ───────────────────────────────────┐  │
│  │                                                         │  │
│  │  📋 Recent Activity:                                   │  │
│  │                                                         │  │
│  │  20:51:00 case_processed                               │  │
│  │           Type: Real Estate, Strategy: Wholesale       │  │
│  │           System classified, awaiting operator review   │  │
│  │                                                         │  │
│  │  20:50:30 case_created                                 │  │
│  │           From intake #16                              │  │
│  │           System initiated processing                  │  │
│  │                                                         │  │
│  │  20:49:15 intake_recorded                              │  │
│  │           Opportunity text saved: "3 bed 2 bath house" │  │
│  │           Awaiting analysis                            │  │
│  │                                                         │  │
│  │  [SHOW MORE] [DOWNLOAD REPORT]                         │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─ ADDITIONAL UI ────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  Assign Team (When Hiring):                            │   │
│  │  Assigned To: [King - Owner] ▼                         │   │
│  │                                                         │   │
│  │  Notes: [Add internal notes about this deal]           │   │
│  │  [text area]                                           │   │
│  │                                                         │   │
│  │  Links:                                                │   │
│  │  [ Get Contractor Quotes ] [ View Comparables ]        │   │
│  │  [ Pull Contract Template ] [ Open Title Repo ]        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## EXACT FIELDS TO DISPLAY

### Row 1: Current Case Info
```
Case ID: {case_id}
Intake ID: {intake_id}
Created: {created_at} (relative time: "2 hours ago")
Status: {current_status} with icon (🟡 pending, 🟢 active, 🔴 blocked)
```

### Row 2: Classification
```
Type: {case_type}
Strategy: {strategy}
Room for Zone: [selector - blank for now]
Assigned To: {assigned_to_user} [dropdown]
```

### Row 3: Financial (If populated)
```
Purchase Price: ${purchase_price} (or "—" if not set)
ARV: ${arv_estimate}
Repairs: ${repair_estimate}
Margin/Spread: ${margin_amount} ({margin_percent}%) with color:
  - Green if > 20%
  - Yellow if 10-20%
  - Red if < 10%
```

### Row 4: Decision Display
```
IF blocked=true:
  🔴 BLOCKED
  Reason: {blocker_reason}
  [Buttons: OK-PROCEED | REQUEST-INFO | PASS]

IF blocked=false:
  ✅ VIABLE
  Next Action: {next_action}
  [Buttons: APPROVE | PASS]
```

### Row 5: Task List
```
For each task in {tasks_array}:
  [ ] [PRIORITY-BADGE] [TITLE]
      [DESCRIPTION (optional)]
      Due: [DUE DATE] [AssignedTo]
      
Priority coloring:
  Priority 1 = ⭐ Red
  Priority 2 = 🔵 Blue  
  Priority 3 = 🟢 Green
```

### Row 6: Notes & History
```
Case Notes: [text area - editable by operator]
Log [Save]

Event Log: [auto-updated list]
- Shows most recent 3-5 events
- Each shows: timestamp, event_type, description
- [More] link to expand

Links Section (when URLs exist):
- [Get Contractor Quotes]
- [View Comps Report]
- [Pull Offer Letter Template]
```

---

## EXACT ROUTES TO CALL

### On Page Load
```javascript
// Get the case ID from URL parameter: /execution/console?case={case_id}

if case_id provided:
  GET /execution/cases/{case_id}
    → Populate all case fields
    
  GET /execution/cases/{case_id}/tasks
    → Show task checklist
    
  GET /execution/cases/{case_id}/events
    → Show event log

if no case_id (first load):
  Show empty "PASTE OPPORTUNITY" section
  Leave other sections hidden/disabled
```

### When Operator Clicks "PROCESS THIS OPPORTUNITY"
```javascript
const raw_text = document.getElementById("opportunity-text").value

POST /execution/intake
  Body: { "raw_text": raw_text }
  On Success:
    const intake_id = response.intake_id
    → Store intake_id in local state
    → Show loading spinner ("Analyzing...")
    
    // After 2 second delay (system processing):
    POST /execution/intake/{intake_id}/process
      On Success:
        const case_id = response.case_id
        → Redirect to /execution/console?case={case_id}
        → Page reloads with new case visible
```

### When Operator Clicks "APPROVE & PROCEED" or "OK-PROCEED"
```javascript
POST /execution/cases/{case_id}/advance
  Body: {
    "case_id": case_id,
    "action": "owner_review_approved" OR "owner_escalation_approved",
    "notes": notes_from_textarea
  }
  On Success:
    → Refresh case data
      GET /execution/cases/{case_id}
      GET /execution/cases/{case_id}/tasks
      GET /execution/cases/{case_id}/events
    → UI updates to show new stage
    → Task list updates
    → Show success banner: "Case moved to Ready for Contact ✓"
```

### When Operator Clicks Task Checkbox
```javascript
// NOTE: This is MANUAL for day-one
// Do NOT call API yet
// Just show checked state visually
// Operator maintains mental note

[Future Week 2: Add task completion API]
```

### When Operator Adds Task Notes
```javascript
// Text area changes saved automatically (on blur)
// For now, store in localStorage
// Do NOT send to API yet

[Future: Add POST /cases/{id}/add-notes]
```

---

## ERROR HANDLING IN UI

### 422 Unprocessable Entity
**Title:** "Missing Required Information"  
**Message:** "The request is missing required fields. Please check: {field names}"  
**Action:** Show validation errors, let user correct and retry

### 404 Not Found
**Title:** "Case Not Found"  
**Message:** "This case ID doesn't exist. Please go back and try again."  
**Action:** Redirect to empty console

### 500 Internal Server Error
**Title:** "System Error"  
**Message:** "The system encountered an error. Try again in 30 seconds or contact support."  
**Action:** Show error banner, offer retry button

### Network Error (No API Response)
**Title:** "Connection Lost"  
**Message:** "Can't reach the server. Check your internet connection."  
**Action:** Show offline state, offer retry when online

---

## PLACEHOLDER FIELDS (For Future Scale)

Show these fields but mark them as "Future":

```
Zone: [Unassigned - future multi-zone feature]
Team Role: [future - currently all King]
Priority Level: [future - currently all Normal]
SLA Deadline: [future - not yet tracked]
Buyer Profile Match: [future - wholesale buyer matching]
```

Do NOT require these fields.  
Do NOT save them to API.  
Just show as disabled/placeholder UI.

---

## COLOR SCHEME

| Element | Color | Meaning |
|---------|-------|---------|
| 🟢 Green | #22C55E | Viable, Approved, Good |
| 🟡 Yellow | #EAB308 | Pending, Warning, Review |
| 🔴 Red | #EF4444 | Blocked, Error, Review Needed |
| 🔵 Blue | #3B82F6 | Info, Secondary |
| ⭐ Star | #FFD700 | Priority 1 / Important |
| ✓ Checkmark | #22C55E | Done / Complete |

---

## RESPONSIVE DESIGN

### Desktop (1920px+)
```
Full single-column layout
All sections visible at once
Form fields max-width 800px centered
Comfortable spacing
```

### Tablet (768px-1024px)
```
Single column maintained
Slightly reduced padding
Task list cards stacked
Event log scrollable
```

### Mobile (< 768px)
```
Single column, full width
Stacked sections
Large touch targets (tap area ≥ 48px)
Horizontal scroll where needed
Collapse sections to save space
Buttons full width for mobile
```

---

## ACCESSIBILITY

- [ ] All buttons have `aria-label`
- [ ] Form fields have labels
- [ ] Color not only indicator of status (use text + icon)
- [ ] Keyboard navigation works (Tab through form)
- [ ] Focus states visible
- [ ] Mobile friendly (touch targets 48x48px+)
- [ ] Text resizable to 200%
- [ ] Sufficient contrast (WCAG AA minimum)

---

## PERFORMANCE TARGETS

| Metric | Target | Why |
|--------|--------|-----|
| Page Load | < 3s | No more than 3 API calls on load |
| API Response | < 1s | Backend is fast, network is main delay |
| Interactivity | < 500ms | Forms respond immediately to user input |
| Task Chevk | Instant | Checkbox checks immediately (no API wait) |
| Case Advance | < 2s | Show loading status while processing |

---

## WHAT TO BUILD FIRST (Priority Order)

### Phase A: Core Intake (Minimum Viable)
1. ✅ Paste text area
2. ✅ "PROCESS" button
3. ✅ Show case summary once processed
4. ✅ Task checklist (visual, no API)
5. ✅ Decision buttons (OK/PASS)
6. ⏰ Event log (informational)

Sufficient for: Run the business day-one

### Phase B: Polish (Week 1 Post-Launch)
1. ✅ Add zone selector placeholder
2. ✅ Add assigned-to dropdown (will be "King")
3. ✅ Add notes textarea
4. ✅ Better error messaging
5. ✅ Loading states
6. ✅ Success confirmations

### Phase C: Advanced (Week 2+)
1. ⏰ Task API integration (mark complete)
2. ⏰ Notes API persistence
3. ⏰ History API depth (show all events)
4. ⏰ Print capability
5. ⏰ Email case summary

---

## KEYBOARD SHORTCUTS (Nice to Have)

```
Cmd+N / Ctrl+N → New opportunity (focus text area)
Cmd+P / Ctrl+P → Process (click process button)
Cmd+S / Ctrl+S → Save notes
Enter (in paste area) → Focus process button
Tab → Navigate between sections
```

---

## TESTING CHECKLIST

Before handing to WeWeb team or going live:

- [ ] Paste text → System correctly receives it
- [ ] Click Process → Intake created, case generated
- [ ] Case displays → All fields show correct data
- [ ] Tasks show → List shows all tasks
- [ ] Click OK-Proceed → Stage advances, tasks refresh
- [ ] Click PASS → Case marked dead
- [ ] Blocked banner shows → Blocker reason displays
- [ ] Notes save → Textarea persists selection
- [ ] History shows → Event log populates
- [ ] Error case → 404 handled gracefully
- [ ] Mobile → All elements accessible
- [ ] Keyboard nav → Tab works through all fields

---

## NOT INCLUDED IN FIRST SCOPE

❌ Dashboards  
❌ Reporting  
❌ Multi-page navigation  
❌ Team management  
❌ Portfolio views  
❌ Buyer matching UI  
❌ Advanced builder controls  
❌ Financial analysis tools  
❌ Contract generators  
❌ Investor portal  
❌ Admin controls  
❌ Settings  
❌ Help system  
❌ Search/filtering  
❌ Bulk operations  

All of these happen AFTER month 1 post-launch.

---

## SUCCESS METRICS

### Day-One Success (First Week Post-Launch)
- ✅ You can paste opportunities and process them
- ✅ System correctly classifies deals
- ✅ You can make decisions without leaving the page
- ✅ All decisions are logged
- ✅ You close at least 1 deal through the system

### Month-One Success
- ✅ 20+ opportunities processed
- ✅ 5+ deals closed
- ✅ Zero data loss
- ✅ Zero blocking bugs
- ✅ Execution layer stable

### Post-Launch Scaling
- ✅ Execution Console runs the entire business before scaling UI
- ✅ Ready to hand off to first VA
- ✅ Ready to add zone dropdown
- ✅ Ready to add multi-user support

---

## HANDOFF TO WEWEB TEAM

This document is deployment-ready for WeWeb builder.

**Copy-paste from [WEWEB_PROMPT_PACK.md](./WEWEB_PROMPT_PACK.md) when ready to build.**

**Do NOT use AI to guess component structure.** This spec is prescriptive. Follow exactly.

---

**Document Owner:** Product/WeWeb Coordination  
**Status:** SCOPE LOCKED - Ready for build  
**Last Updated:** 2026-04-13  
**Approval:** Required before WeWeb starts  
