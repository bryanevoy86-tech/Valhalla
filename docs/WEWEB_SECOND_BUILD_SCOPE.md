# WEWEB SECOND BUILD SCOPE: Deal Pipeline & Team Coordination v2.0

**Status:** DESIGN FOR MONTH 2+  
**Timeline:** After Execution Console stable (Week 2-3 post-launch)  
**Dependency:** First build must be complete and running live    
**Scope:** Multi-page application with navigation  

---

## OVERVIEW

Once the Execution Console is proven and you're closing deals, the second WeWeb build adds team collaboration and deal lifecycle visibility.

**Goals:**
1. ✅ Give VAs their own workflows (intake → qualification → followup tasks)
2. ✅ Show deal pipeline visually (board view of stages)
3. ✅ Enable task assignment to team members
4. ✅ Track team member workload
5. ✅ Route deals to zone leads
6. ✅ Support strategy filtering

**What It Allows:**
- You delegate intake to VA #1
- You delegate qualification to VA #2
- Each VA sees only their work
- You see the full board
- Cases automatically flow to right person

---

## PAGES TO BUILD (In Order)

### Page 1: PIPELINE BOARD (Primary Navigation)

**URL:** `/pipeline-board`

**Purpose:** Table-view of all cases organized by current stage

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  📊 PIPELINE BOARD                          [Filter] [View: 📋]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Filter: [All Cases] ▼  [Strategy: All] ▼  [Zone: All] ▼       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ INTAKE_PROCESSED (5)    │ READY_FOR_CONTACT (3)        │   │
│  ├─────────────────────────┼──────────────────────────────┤   │
│  │ #3: Property A          │ #7: Property D               │   │
│  │ Wholesale, $40k margin  │ Wholesale, $25k margin       │   │
│  │ Assigned: King          │ Assigned: VA2_Followup       │   │
│  │ Due: Today              │ Due: Tomorrow                │   │
│  │ 🔴 BLOCKEDR: Low margin │ Status: Active ✓             │   │
│  │                         │ Contact: Pending             │   │
│  │ ──────────────────────  │                              │   │
│  │ #5: Property B          │ #9: Property E               │   │
│  │ FLIP, $35k margin       │ HOLD, $800mo cashflow        │   │
│  │ Assigned: King          │ Assigned: VA2_Followup       │   │
│  │ Due: Tomorrow           │ Due: Next week               │   │
│  │ Status: Pending review  │ Status: Awaiting seller call │   │
│  │                         │                              │   │
│  │ ──────────────────────  │                              │   │
│  │ #8: Property C          │ #12: Property F              │   │
│  │ Wholesale, $15k margin  │ Partnership, 25% equity      │   │
│  │ Assigned: VA1_Intake    │ Assigned: King               │   │
│  │ Due: Soon               │ Due: 3 days                  │   │
│  │ Status: Researching     │ Status: Partner review       │   │
│  │                         │                              │   │
│  └──────────────────────────┴──────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ NEGOTIATING (2)         │ UNDER_CONTRACT (1)           │   │
│  ├─────────────────────────┼──────────────────────────────┤   │
│  │ #10: Property G         │ #11: Property H              │   │
│  │ Wholesale, $50k spread  │ FLIP, $80k profit            │   │
│  │ Assigned: Closer_John   │ Assigned: Acq_Sarah          │   │
│  │ Due: 2 days             │ Due: Inside 14 days          │   │
│  │ Status: Seller agrees   │ Status: Closing in progress  │   │
│  │ Profit: $50k            │ Profit: $80k                 │   │
│  │                         │                              │   │
│  └──────────────────────────┴──────────────────────────────┘   │
│                                                                  │
│  Summary Stats:
│  Total Cases: 12 | Active: 8 | Blocked: 1 | This Month Sales: $150k
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Kanban-style board (but table view for now)
- Each column = one stage
- Each card = one case
- Show:
  - Case ID
  - Property type / Strategy
  - Estimated profit
  - Assigned to (team member name)
  - Due date
  - Current status
  - Block indicators (🔴 if blocked)
- Click card → Opens case detail in sidebar or modal
- Drag-drop to advanced stage (optional, Phase B)

**Filters:**
- By Stage (show/hide individual stages)
- By Strategy (Wholesale | Hold | Flip | Partnership)
- By Assigned To (show my cases only / all)
- By Zone (filter by geographic area)

**Routes Needed:**
```
GET /execution/cases?stage=intake_processed&sort=due_date
  → Returns paginated list of cases in each stage
  → Limit: 50 per page (load more available)
```

---

### Page 2: CASE DETAIL SIDEBAR

**URL:** `/pipeline-board?case={case_id}`  (modal overlay)

**Purpose:** Full case detail without leaving board view

**Similar to:** First build's Execution Console, but formatted as sidebar

**Key Difference:** Read-only by default (can edit if you're assigned or owner)

**Actions Available:**
- [APPROVE & ADVANCE] - if you're owner
- [ASSIGN TO TEAM MEMBER] - if you're owner
- [ADD COMMENT] - everyone
- [MARK COMPLETE] - if you're assigned
- [ESCALATE] - everyone

---

### Page 3: MY WORK QUEUE

**URL:** `/my-work`

**Purpose:** Filter for logged-in user's assigned cases and tasks

**Who Sees:**
- VA #1 sees: Only intake_processed cases assigned to them
- VA #2 sees: Only ready_for_contact & contacted cases assigned to them
- Closer sees: Only negotiating cases assigned to them
- You (King) see: All cases (or can filter to "my cases")

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│  📋 MY WORK QUEUE                          [Done: 8/20]    │
├────────────────────────────────────────────────────────────┤
│ Logged in as: VA2_Followup                                 │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🔴 PRIORITY: Contact Seller (3 OVERDUE)               │ │
│ │                                                        │ │
│ │  □ #3: Property A - Contact by 04-13   OVERDUE       │ │
│ │    Assigned 3 days ago, seller very responsive        │ │
│ │    [CONTACT NOW] [RESCHEDULE] [MARK DONE]            │ │
│ │                                                        │ │
│ │  □ #5: Property B - Contact by 04-13   OVERDUE       │ │
│ │    Great deal, need to move fast                       │ │
│ │    [CONTACT NOW] [RESCHEDULE] [MARK DONE]            │ │
│ │                                                        │ │
│ │  □ #8: Property C - Contact by 04-13   OVERDUE       │ │
│ │    Standard opportunity, less urgent                  │ │
│ │    [CONTACT NOW] [RESCHEDULE] [MARK DONE]            │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟡 SCHEDULED: Contact Due Tomorrow (2)                │ │
│ │                                                        │ │
│ │  □ #7: Property D - Contact by 04-14    📅 READY     │ │
│ │    Scheduled for: Tomorrow at 2 PM                     │ │
│ │    [MARK DONE] [RESCHEDULE]                           │ │
│ │                                                        │ │
│ │  □ #9: Property E - Contact by 04-14    📅 READY     │ │
│ │    Flexible seller, no preferred time                  │ │
│ │    [MAKE CALL NOW] [SEND EMAIL] [RESCHEDULE]          │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🟢 COMPLETED TODAY (8 ✓)                              │ │
│ │                                                        │ │
│ │  ✓ #1: Property A - Contacted, seller very interested │ │
│ │  ✓ #2: Property B - Left voicemail, will follow up    │ │
│ │  ✓ #4: Property C - Email sent, awaiting response     │ │
│ │  ... [+ 5 more] [SHOW ALL]                            │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Shows only YOUR assigned cases
- Grouped by priority and due date
- Shows overdue tasks prominently
- One-click actions (mark done, contact now, reschedule)
- Progress tracker (8/20 done this week)

**Routes Needed:**
```
GET /execution/cases?assigned_to={user_id}&sort=priority,due_date
  → Returns user's work queue
```

---

### Page 4: TEAM DIRECTORY

**URL:** `/team`

**Purpose:** Manage team member workload and assignments

**Who Can Access:** Owner only

**Sections:**
```
┌──────────────────────────────────────────────────────┐
│  👥 TEAM DIRECTORY                                   │
├──────────────────────────────────────────────────────┤
│ Filter: [All Roles] ▼  [Status: Active] ▼            │
│                                                      │
│ ┌──────────────────────────────────────────────────┐ │
│ │ 👤 KING (You)                                   │ │
│ │ Role: Owner                                      │ │
│ │ Cases: 8 assigned (3 overdue, 2 blocked)        │ │
│ │ Monthly Closes: 12                               │ │
│ │ Team Lead                                        │ │
│ │                                                  │ │
│ ├──────────────────────────────────────────────────┤ │
│ │ 👤 VA1 (Sarah)                                  │ │
│ │ Role: Intake VA                                 │ │
│ │ Cases: 4 assigned (all on time)                 │ │
│ │ Performance: 95% accuracy                       │ │
│ │ Action: [VIEW CASES] [REASSIGN]                 │ │
│ │                                                  │ │
│ ├──────────────────────────────────────────────────┤ │
│ │ 👤 VA2 (Mark)                                   │ │
│ │ Role: Qualification VA                          │ │
│ │ Cases: 6 assigned (3 OVERDUE)                   │ │
│ │ Performance: 87% accuracy                       │ │
│ │ ⚠️  OVERDUE ALERT: 3 cases pending analysis     │ │
│ │ Action: [VIEW CASES] [REASSIGN] [SUPPORT]      │ │
│ │                                                  │ │
│ ├──────────────────────────────────────────────────┤ │
│ │ 👤 JOHN (Closer)                                │ │
│ │ Role: Deal Closer                               │ │
│ │ Cases: 2 assigned (active negotiations)         │ │
│ │ Closed This Month: 3 deals, $150k revenue       │ │
│ │ Action: [VIEW CASES] [REASSIGN]                 │ │
│ │                                                  │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [ADD TEAM MEMBER] [REMOVE MEMBER]                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Features:**
- List all team members
- Show role, caseload, performance
- Show overdue/blocked cases
- Quick reassign action
- Add/remove team members (future: integration with user management)

---

### Page 5: STRATEGY & ZONE FILTERS (Dashboard)

**URL:** `/dashboard/filters`

**Purpose:** Strategic filtering and organization

**Sections:**

#### Strategy Breakdown
```
Wholesale: 8 cases, $320k profit potential
Hold: 3 cases, $28.8k annual projected
Flip: 1 case, $80k profit potential
Partnership: 0 cases
```

#### Zone Breakdown (When Multi-Zone Active)
```
Florida - Miami: 5 cases, $150k profit
Florida - Tampa: 3 cases, $120k profit
Texas - Austin: 2 cases, $80k profit
(Unassigned): 2 cases - [ASSIGN TO ZONE]
```

---

## SECOND BUILD FEATURES (Prioritized)

### WEEK 1 Post-Execution Console Launch
- [ ] Pipeline board (kanban-table view)
- [ ] Case detail sidebar
- [ ] Basic filtering (stage, strategy)

### WEEK 2
- [ ] "My Work" queue for VAs
- [ ] Task assignment UI
- [ ] Due date management
- [ ] Team member overview (read-only)

### WEEK 3+
- [ ] Drag-drop stage movement (kanban advanced)
- [ ] Team directory management
- [ ] Ad-hoc case notes
- [ ] Bulk reassign actions

---

## ROUTES NEEDED FOR SECOND BUILD

```
// Get all cases (paginated, filterable)
GET /execution/cases?stage=X&strategy=Y&assigned_to=Z&sort=due_date

// Get case detail (for sidebar)
GET /execution/cases/{case_id}

// Update assignment
POST /execution/cases/{case_id}/assign
  Body: { "assigned_to_user_id": UUID }

// Advance case on board drag
POST /execution/cases/{case_id}/advance
  Body: { "action": "drag_to_stage" }

// Get user's work queue
GET /execution/cases?assigned_to={current_user_id}

// Get team members
GET /users (or /team)

// Log work item (optional)
POST /execution/cases/{case_id}/log-work
  Body: { "action": "contacted_seller", "notes": "..." }
```

---

## NOT INCLUDED IN SECOND BUILD

❌ Analytics / dashboards  
❌ Advanced reporting  
❌ Multi-zone switching  
❌ Custom team roles (beyond basic assignment)  
❌ Buyer matching interface  
❌ Contract generation  
❌ Portfolio management  
❌ Investor portal  
❌ Advanced automation rules  

These happen in phases 3-5 (months 3-6 post-launch).

---

## SUCCESS METRICS FOR SECOND BUILD

### Technical
- ✅ All pipeline board loads < 2s
- ✅ Filters update without page reload
- ✅ Case reassignment saves instantly
- ✅ No data loss on updates

### Functional
- ✅ You can delegate work to VAs
- ✅ VAs see only their assigned cases
- ✅ Cases flow visually through pipeline
- ✅ Team workload is visible
- ✅ Overdue tasks highlighted

### Business
- ✅ Deal processing time reduced 20%
- ✅ VA productivity tracked
- ✅ Bottlenecks visible (stage with most cases)
- ✅ Revenue tracking per team member

---

## HANDOFF TO WEWEB TEAM

This scope document is ready for planning once first build is complete.

**Timeline:** Week 1-2 Post-Launch (after Execution Console is proven)

**Do NOT start building this until first page is live and team is using it daily.**

---

**Document Owner:** Product  
**Status:** DESIGN PHASE - Ready for development after Week 1 validation  
**Last Updated:** 2026-04-13  
**Next Review:** One week post-Execution Console launch  
