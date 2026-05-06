# MILLION-PATH: Team Operating Model & Roles

**Status:** ORGANIZATIONAL DESIGN  
**Purpose:** Define the team structure that scales from 1 person to multi-zone operator  
**Timeline:** Day-one (lean) through enterprise scale (delegated)  
**Last Updated:** 2026-04-13  

---

## PHILOSOPHY

We're building a system that starts with one operator and scales to many roles, many zones.

**Day-One:** One "king" operator does everything (intake, qualification, negotiation, closing)

**Month 1:** Add VA (virtual assistant) for intake/qualification

**Month 3:** Add closer, dispo specialist, zone lead

**Month 6:** Add multi-zone lead team, scale to 5 zones

**Year 1:** Add commercial team, development team, investor relations

**Year 2:** Add procurement, capital team, arbitrage specialists, partnership managers

This document defines the roles we'll need and what system screens/routes each one uses.

---

## DAY-ONE LEAN OPERATING MODEL

### Role 1: OWNER / KING

**Who:** Usually founder/operator (you)

**Responsibilities:**
- Final decision authority on all deals
- High-level strategy direction
- Capital allocation
- Team hiring/management
- Revenue/P&L accountability
- Escalation point for complex deals

**Routes They Use:**
- ✅ POST /execution/intake (paste opportunity)
- ✅ POST /execution/intake/{id}/process (analyze)
- ✅ GET /execution/cases/{id} (view full case)
- ✅ POST /execution/cases/{id}/advance (approve or reject)
- ⏰ GET /empire/dashboard (year 1: portfolio summary)
- ⏰ GET /portfolio/summary (year 1: holdings dashboard)

**Screens They Interact With:**
- Execution Console (primary)
- Decision Dashboard (review cases queued for approval)
- Portfolio Overview (later)

**Data They Own:**
- Final decision on every case
- Strategy for each zone
- Budget allocation

**Day-One:** Basically all the work. Welcome to startup.

---

### Role 2: OPERATOR / "YOU" (Today)

**Who:** You (doing most execution work)

**Responsibilities:**
- All day-to-day operations (before VA hired)
- Intake text parsing
- Initial filtering
- Seller contact
- Negotiation
- Process management
- Closing coordination

**Routes They Use:**
- ✅ POST /execution/intake (paste opportunity)
- ✅ POST /execution/intake/{id}/process (analyze it)
- ✅ GET /execution/cases/{id} (pull full details)
- ✅ GET /execution/cases/{id}/tasks (view to-do list)
- ✅ GET /execution/cases/{id}/next-action (what's important?)
- ✅ POST /execution/cases/{id}/advance (move case forward)
- ✅ GET /execution/cases/{id}/events (audit trail)

**Screens They Interact With:**
- Execution Console (90% of work)
- Task Board (manual checklist)
- History/Events Tab (compliance)

**Data They Own:**
- All case notes and decisions (for now)
- Contact information and conversations
- Financial quotes and estimates

**Limit:** This role is sustainable for ~20-30 deals/month. Beyond that, must hire VA.

---

## MONTH 1+ ADDING VIRTUAL ASSISTANT

### Role 3: INTAKE VA (Virtual Assistant - Intake)

**When to Hire:** After you have 20+ opportunities/month and 10+ active cases

**Who:** Remote or part-time contractor doing initial intake work

**Responsibilities:**
- Parse opportunity text details
- Validate property exists (basic research)
- Create initial lead notes
- Categorize by opportunity type
- Flag disqualifiers (already sold, too expensive, etc.)
- Escalate to you for decision
- Organize intake pipeline

**Routes They Use:**
- ✅ GET /execution/cases (see intake queue)
- ✅ GET /execution/cases/{id} (read full details)
- ✅ POST /execution/cases/{id}/add-notes (log research)
- ⏰ GET /lead/source (research tool - later)

**Screens They Interact With:**
- Intake Queue (list of new opportunities)
- Detailed View (research notes)
- Task Checklist (verification tasks)

**Data They Own:**
- Intake research notes
- Property verification details
- Initial risk assessment

**Bottleneck Removed:** You no longer read and parse every raw text. VA filters.

---

### Role 4: QUALIFICATION VA (Virtual Assistant - Deal Qualification)

**When to Hire:** After 30+ opportunities/month, existing VA is overloaded

**Who:** Remote contractor doing financial analysis and viability checks

**Responsibilities:**
- Run detailed financial analysis (after system classifies)
- Verify comparable sales (comps research)
- Get repair estimates
- Calculate accurate profits/margins
- Competition analysis
- Risk assessment update
- Prepare summary for closer

**Routes They Use:**
- ✅ GET /execution/cases (see cases needing analysis)
- ✅ GET /execution/cases/{id} (detail view)
- ✅ POST /execution/cases/{id}/add-financial-analysis (log analysis)
- ⏰ GET /research/comparables (comp research tool)

**Screens They Interact With:**
- Analysis Queue (cases needing financial work)
- Financial Analysis Form (comps, repairs, margin)
- Decision Support Dashboard

**Data They Own:**
- All financial analysis
- Comparable sales research
- Repair estimates and quotes

**Bottleneck Removed:** You don't do the research. VA does, hands you decision memo.

---

### Role 5: FOLLOWUP VA (Virtual Assistant - Deal Pursuit)

**When to Hire:** After 10+ viable cases, too many sellers to contact

**Who:** Remote contractor doing persistent seller contact and negotiation prep

**Responsibilities:**
- Initial seller phone/text/email outreach
- Qualification questions to seller
- Relationship building
- Calendar management (followup timing)
- Document assembly (intro letter, offer framework)
- Seller motivation assessment
- Negotiation prep (ranges, terms to present)

**Routes They Use:**
- ✅ GET /execution/cases (see contacted/contacted queue)
- ✅ GET /execution/cases/{id} (case detail)
- ✅ POST /execution/cases/{id}/log-contact (record seller conversation)
- ✅ POST /execution/cases/{id}/add-seller-profile (seller notes)
- ⏰ GET /contracts/ (offer templates)

**Screens They Interact With:**
- Followup Queue (cases needing seller contact)
- Contact Log (track all interactions)
- Seller Profile (motivation, budget, timeline)
- Offer Template Builder

**Data They Own:**
- All seller communication logs
- Seller profiles and motivation assessment
- Timeline and constraint tracking

**Bottleneck Removed:** You don't do low-level contact work. VA builds the relationship, hands you motivated sellers.

---

### Role 6: CLOSER (Negotiator / Dealmaker)

**When to Hire:** After 5+ cases in simultaneous negotiation, you're context-switching too much

**Who:** Experienced negotiator with deal-closure track record

**Responsibilities:**
- Seller negotiation (live calls and meetings)
- Term refinement
- Contract preparation
- Contingency management
- Inspection coordination
- Appraisal management
- Buyer/investor communication (for wholesales)
- Deal structure optimization

**Routes They Use:**
- ✅ GET /execution/cases?stage=negotiating (my cases)
- ✅ GET /execution/cases/{id} (full case detail)
- ✅ POST /execution/cases/{id}/update-negotiation-status (status)
- ✅ GET /execution/cases/{id}/tasks (action items)
- ⏰ GET /contracts (finalize agreements)
- ⏰ POST /execution/cases/{id}/advance (move to under_contract)

**Screens They Interact With:**
- My Negotiations (active negotiating cases)
- Seller Notes & History (context)
- Contract Status Dashboard
- Inspection & Appraisal Tracking

**Data They Own:**
- Negotiation progress
- Final terms agreed
- Contingency status

**Bottleneck Removed:** You don't do each seller call. Closer does, you only step in for final approval.

---

### Role 7: ACQUISITIONS MANAGER

**When to Hire:** After 5+ closes/month, closing coordination is manual chaos

**Who:** Detail-oriented operations person managing closing logistics

**Responsibilities:**
- Closing timeline management
- Funding coordination
- Title company coordination
- Inspection scheduling
- Appraisal ordering
- Insurance coordination
- Closing document prep
- Walkthrough scheduling

**Routes They Use:**
- ✅ GET /execution/cases?stage=under_contract (my closes)
- ✅ GET /execution/cases/{id} (case detail)
- ✅ POST /execution/cases/{id}/update-closing-status (status)
- ✅ GET /execution/cases/{id}/tasks (checklist)
- ⏰ POST /execution/cases/{id}/advance (move to closed)
- ⏰ GET /contracts/closing-docs (docs to sign)

**Screens They Interact With:**
- Active Closings (cases in closing process)
- Closing Timeline (deadline tracker)
- Document Checklist
- Lender/Title Company Portal Integration

**Data They Own:**
- Closing timeline
- Document status
- Funding ready/not ready

**Bottleneck Removed:** You don't manage every title company phone call. Acq Manager does.

---

### Role 8: DISPO SPECIALIST (Disposition Manager)

**When to Hire:** After 10+ closed properties, managing exit strategy is full-time job

**Who:** Specialist in matching properties with buyers/strategies

**Responsibilities:**
- Wholesaler buyer matching
- Cash buyer identification
- Rental tenant matching
- Contractor recommendations
- Portfolio planning (hold vs sell)
- Exit strategy optimization
- Buyer/tenant placement
- Transaction coordination

**Routes They Use:**
- ✅ GET /execution/cases?stage=closed (my dispositions)
- ✅ GET /execution/cases/{id} (case detail)
- ⏰ GET /buyer (buyer registry search)
- ⏰ POST /dispo/match (match property to buyer)
- ⏰ GET /portfolio/hold-analysis (what should we hold?)
- ⏰ POST /portfolio/add (add to holdings)

**Screens They Interact With:**
- Closed Deals (ready for exit)
- Buyer Registry Search
- Exit Strategy Dashboard
- Cash vs Hold Decision Board

**Data They Own:**
- Buyer/tenant matches
- Exit strategy decisions
- Portfolio composition

**Bottleneck Removed:** You don't find every buyer. Dispo does, handles the placement.

---

### Role 9: ZONE LEAD (Geographic Manager)

**When to Hire:** After 3+ zones active, you can't be everywhere

**Who:** Regional operator managing one geographic zone

**Responsibilities:**
- All operations for assigned zone
- Local market knowledge
- Team coordination in zone
- Lead generation strategy for zone
- Market reporting
- Relationship building with local wholesalers/contractors
- Decision authority delegated to zone (up to policy limits)

**Routes They Use:**
- ✅ GET /execution/cases?zone=florida_miami (my zone's cases)
- ✅ All execution routes limited to their zone
- ⏰ GET /zone/{zone_id}/performance (zone dashboard)
- ⏰ POST /zone/{zone_id}/settings (zone strategy)
- ⏰ GET /zone/{zone_id}/team (my team)

**Screens They Interact With:**
- Zone Dashboard (all zone cases)
- My Team Management
- Zone Performance Metrics
- Zone Strategy Settings
- Local Market Data

**Data They Own:**
- All zone case decisions (delegated)
- Zone strategy and targeting
- Local relationship inventory

**Bottleneck Removed:** You're multi-zone empowered. Each zone has semi-autonomous leader.

---

## MONTH 6+ ADDING SPECIALIZED ROLES

### Role 10: OPERATOR ADMIN (System Administrator)

**When to Hire:** When you have 10+ team members

**Who:** Technical or operations person managing system access and compliance

**Responsibilities:**
- User access management
- Report generation
- Audit compliance
- Data integrity monitoring
- System troubleshooting

**Routes They Use:**
- ✅ GET /governance/audit-log (all activity)
- ✅ GET /users (team member list)
- ✅ POST /users (add team member)
- ✅ GET /system/health (system status)

**Screens They Interact With:**
- User Management Dashboard
- Audit Log (detailed)
- System Health
- Access Control Panel

**Data They Own:**
- User access policies
- Audit trail
- System configuration

---

## YEAR 1+ ADDING STRATEGIC ROLES

> These roles are future capability, not for day-one launch

### Role 11: CAPITAL MANAGER (Funding Strategy)

Strategies: Manage investor relationships, capital deployment, returns distribution

### Role 12: PARTNERSHIP MANAGER (Joint Ventures)

Strategies: Partnership deal coordination, equity management, partner reporting

### Role 13: COMMERCIAL SPECIALIST (Commercial Real Estate)

Strategies: Complex commercial deals, multi-tenant, triple-net analysis

### Role 14: DEVELOPMENT MANAGER (Land Development)

Strategies: Development projects, construction management, entitlements

### Role 15: ARBITRAGE SPECIALIST (Multi-Zone Pricing)

Strategies: Cross-zone opportunities, market inefficiency exploitation

---

## ROLE MATRIX: Who Uses What Routes

| Route | OWNER | INTAKE_VA | QUAL_VA | FOLLOWUP_VA | CLOSER | ACQ | DISPO | ZONE_LEAD | ADMIN |
|-------|-------|-----------|---------|-------------|--------|-----|-------|-----------|-------|
| POST /execution/intake | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| POST /process | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| GET /cases | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅(zone) | ✅ |
| GET /cases/{id} | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅(zone) | ✅ |
| GET /cases/{id}/tasks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅(zone) | ❌ |
| POST /cases/{id}/advance | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅(delegated) | ❌ |
| POST /buyer_match | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| GET /portfolio | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅(zone) | ✅ |
| GET /zone/{id}/dashboard | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| GET /governance/audit | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| POST /users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

✅ = Yes, this role needs this route  
❌ = No, shouldn't access this  
⏰ = Later (after WeWeb launch)

---

## ROLE ACTIVATION TIMELINE

### WEEK 1 (You launch execution console)
```
Active: OWNER (you)
        OPERATOR (you wearing operator hat)
        + manual VA support if hired (ad-hoc notes)
```

### MONTH 1 (After 20+ deals)
```
Active: OWNER
        INTAKE_VA
        QUALIFICATION_VA
Bottleneck Solved: Raw opportunity processing
```

### MONTH 3 (After 30+ opportunities, 10+ active cases)
```
Active: OWNER
        INTAKE_VA
        QUALIFICATION_VA
        FOLLOWUP_VA
        CLOSER
Bottleneck Solved: Seller contact and negotiation
```

### MONTH 6 (After 50+ deals, multi-zone ready)
```
Active: OWNER
        + ZONE_LEADs (one per zone)
        Each zone has: intake, qual, followup, closer, acq
```

### YEAR 1 (After 200+ closed deals)
```
Active: OWNER
        Multiple ZONE_LEADs
        Specialized roles: DISPO, CAPITAL_MANAGER, PARTNERSHIP_MANAGER
```

---

## ROLE PERMISSIONS IN SYSTEM

**Safe to Add Now (Constants Only):**

Create `app/constants/roles.py`:

```python
ROLES = {
    "OWNER": {
        "title": "Owner",
        "can_read": ["all_cases", "all_zones", "all_team", "all_reports"],
        "can_write": ["all_cases", "team_settings", "zone_settings"],
        "can_delete": ["cases"],  # archive only
        "owns_decisions": ["final_approval", "strategy", "team_hiring"],
    },
    "OPERATOR": {
        "title": "Operator",
        "can_read": ["own_cases", "own_zone"],
        "can_write": ["own_cases", "own_case_notes"],
        "can_delete": [],
        "owns_decisions": ["case_day_to_day"],
    },
    "INTAKE_VA": {
        "title": "Intake Assistant",
        "can_read": ["new_intakes"],
        "can_write": ["intake_notes"],
        "can_delete": [],
        "owns_decisions": ["filter_disqualifiers"],
    },
    "CLOSER": {
        "title": "Deal Closer",
        "can_read": ["negotiating_cases"],
        "can_write": ["negotiating_case_terms"],
        "can_delete": [],
        "owns_decisions": ["advance_to_contract"],
    },
    "DISPO": {
        "title": "Disposition Manager",
        "can_read": ["closed_cases", "buyer_registry"],
        "can_write": ["closed_case_disposition"],
        "can_delete": [],
        "owns_decisions": ["buyer_matching", "exit_strategy"],
    },
    # etc.
}
```

**Risk Level:** ZERO (constants only)

---

## SAFE TO APPLY NOW

✅ **Create roles.py constants file** (zero risk)  
❌ **Do NOT apply RBAC to routes yet** (too risky pre-WeWeb)  
⏰ **Apply role-based filtering post-WeWeb when stable** (week 2 post-launch)

---

## SYSTEM NOTES

**Current State (Today):**
- All cases assigned to hardcoded "king" user
- No role separation
- No team management

**Day-One WeWeb Launch:**
- You (OWNER) use execution console
- Possible single VA for intake notes
- Still mostly manual

**Month 1+ Post-Launch:**
- Roles come online as you hire
- System routes cases to assigned role
- Role-specific screens appear

**Security Note:**
- Roles define what data you CAN see, not what you SHOULD see
- Owners still see everything for audit purposes
- Team members see only their assigned cases (post-launch)

---

## NEXT STEPS

1. ✅ Review this role model with team
2. ✅ Create roles.py constants file
3. ⏳ Deploy to code (no breaking changes)
4. ⏳ Integrate into WeWeb build (role-aware screens)
5. ⏳ Post-launch: Apply role-based filtering to routes

---

**Document Owner:** Organizational Design Team  
**Status:** CANONICAL - Ready for resource planning  
**Last Updated:** 2026-04-13  
**Next Review:** Before hiring first VA  
