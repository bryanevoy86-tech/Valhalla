# WeWeb Build Order

**Recommended safe build sequence for Valhalla backend integration**

---

## Overview

Build the WeWeb app in phases to minimize risk and validate each component before moving forward.

**Total phases**: 5  
**Estimated time**: 3-4 days (depending on team size)  
**Risk level**: Low (each phase is independent and can be rolled back)

---

## Phase 1: Foundation (Day 1 - 2 hours)

**Objective**: Establish core infrastructure and auth

### 1.1 Set up backend connection
- [ ] Configure `API_BASE_URL` variable (dev: localhost:8000 or Render production URL)
- [ ] Test health endpoint: GET /health (should return 200)
- [ ] Verify `/openapi.json` is accessible
- [ ] Document actual API host/port in project notes
- **Validation**: Health check responds in <1 second

### 1.2 Create Authentication flow
- [ ] Build Login page with email/password form
- [ ] Implement `workflow_login` (POST credentials, store AUTH_TOKEN)
- [ ] Implement `workflow_logout` (clear token, redirect)
- [ ] Store AUTH_TOKEN in secure storage (WeWeb's secure variable)
- [ ] Create session persistence (check token on app load)
- **Validation**: Can login/logout without errors, token persists on reload

### 1.3 Create header/navigation
- [ ] Add global header with user name, logout button
- [ ] Add notifications bell (initialize with 0 unread)
- [ ] Add main navigation (Dashboard, Lead Intake, Deals, Reports, Go-Live)
- [ ] Implement `workflow_checkGoLiveStatus` (display go-live indicator)
- **Validation**: Navigation works, go-live status displays

### 1.4 Build Dashboard skeleton
- [ ] Create Dashboard view with empty sections
- [ ] Add 4 KPI cards (layout complete, data TBD)
- [ ] Implement `workflow_loadDashboard` to fetch metrics
- [ ] Test metrics display (hard-code test data if API unavailable)
- **Validation**: Dashboard loads without errors, layout is complete

---

## Phase 2: Lead Intake (Day 2 - 3 hours)

**Objective**: Build complete lead intake pipeline

### 2.1 Create Lead Intake view
- [ ] Build Lead List page (table/cards layout)
- [ ] Implement `workflow_loadLeadsDashboard` (GET /api/va-intake/leads)
- [ ] Add pagination (skip/limit controls)
- [ ] Add filters: Status, Stage
- [ ] Add search by name/phone
- **Validation**: Can fetch and display leads, pagination works, filters work

### 2.2 Build Lead Creation form
- [ ] Create form with fields: Name, Phone, Email, Address, Value, Equity
- [ ] Add client-side validation (required fields, email format, phone format)
- [ ] Implement `workflow_submitNewLead` (POST /api/va-intake/lead)
- [ ] Show success/error toasts
- [ ] Clear form on success
- **Validation**: Can create a new lead, form validates, toast shows result

### 2.3 Build Lead Detail view
- [ ] Create detail page showing all lead fields
- [ ] Implement `workflow_openLeadDetail` (GET /api/va-intake/leads/{id})
- [ ] Display lead status badge, timeline
- [ ] Add "Convert to Deal" button (workflow TBD in Phase 3)
- [ ] Display audit trail (read-only list of actions)
- **Validation**: Can click on lead and see full details, back button works

### 2.4 Add bulk import (CSV)
- [ ] Create CSV upload form
- [ ] Parse CSV into array of lead objects
- [ ] Implement `workflow_importLeadsBatch` (POST each lead)
- [ ] Show progress indicator
- [ ] Display import results (X created, Y failed)
- **Validation**: Can import 10+ leads from sample CSV, errors handled gracefully

---

## Phase 3: Approvals & Deal Conversion (Day 2 - 2 hours)

**Objective**: Implement approval workflow and lead-to-deal conversion

### 3.1 Create Approval Queue view
- [ ] Build pending approvals list
- [ ] Implement `workflow_loadApprovalQueue` (GET /api/va-intake/approvals/pending)
- [ ] Show lead details in each row
- [ ] Add pagination
- **Validation**: Can fetch approvals, list displays correctly

### 3.2 Build approval actions
- [ ] Add "Approve" and "Deny" buttons to each row
- [ ] Create Approve workflow (POST /api/va-intake/approvals/{id}/approve)
- [ ] Create Deny workflow with reason modal (POST .../deny with reason)
- [ ] Remove approved/denied items from list on success
- [ ] Show success toasts
- **Validation**: Can approve/deny approvals, items remove from list

### 3.3 Implement lead-to-deal conversion
- [ ] Create modal: Choose deal_type (wholesale/flip/brrrr)
- [ ] Implement `workflow_convertLeadToDeal` (POST /api/va-intake/leads/{id}/convert-to-deal)
- [ ] Show success and navigate to new Deal Detail
- [ ] Handle conflicts (already converted)
- **Validation**: Approved lead converts to deal without errors

---

## Phase 4: Deals Management (Day 3 - 3 hours)

**Objective**: Build deal viewing, analysis, and buyer matching

### 4.1 Create Deals Dashboard
- [ ] Build deals list (table/cards)
- [ ] Implement `workflow_loadDealsDashboard` (GET /api/deals)
- [ ] Add filters: Status, Type, Region
- [ ] Add sorting: By date, status, property value
- [ ] Add "New Deal" button
- **Validation**: Can view all deals, filtering works, pagination works

### 4.2 Build Deal Detail view (part 1 - Info)
- [ ] Create detail page with deal header (address, status, type)
- [ ] Implement `workflow_openDealDetail` (GET /api/deals/{id})
- [ ] Display property details, timeline, status
- [ ] Add "Advance Stage" button (workflow TBD)
- [ ] Link back to parent lead if applicable
- **Validation**: Can click deal and see full details

### 4.3 Add deal analysis
- [ ] Create Analysis section (FLIP, BRRRR, comparables)
- [ ] Implement `workflow_calculateFlipEstimate` (POST /api/flip/estimate)
- [ ] Implement `workflow_calculateBrrrrEstimate` (POST /api/brrrr/estimate)
- [ ] Display results in cards or table
- [ ] Handle errors gracefully (show "unavailable")
- **Validation**: Can see deal analysis, calculations display correctly

### 4.4 Build buyer matching
- [ ] Create Buyer Matching section in Deal Detail
- [ ] Implement `workflow_matchBuyersToDeals` (GET /api/deals/{id}/buyers)
- [ ] Display matched buyers with scores
- [ ] Add "Send to Buyer" button
- **Validation**: Can see matched buyers, matches include scores

### 4.5 Implement buyer outreach
- [ ] Implement `workflow_sendDealToBuyer` (POST /api/deals/{id}/send-to-buyer/{buyer_id})
- [ ] Implement `workflow_createBuyerPacket` (POST /api/messaging/va/create-buyer-packet/{id})
- [ ] Show packet URL, offer download/email options
- [ ] Update deal status to reflect buyer contact
- **Validation**: Can send deal to buyer, packet generates and is accessible

---

## Phase 5: Polish & Advanced Features (Day 3-4 - 2 hours)

**Objective**: Add messaging, reporting, and admin features

### 5.1 Build Messaging section
- [ ] Create Messaging view
- [ ] Implement `workflow_draftSellerMessage` (POST /api/messaging/va/draft-seller-message/{id})
- [ ] Allow choosing tone and urgency
- [ ] Show generated message for review/edit
- [ ] Offer copy/send options
- **Validation**: Can generate messages, UI is polished

### 5.2 Build Reports/EIA view
- [ ] Create Reports page
- [ ] Implement `workflow_loadReports` (GET /api/reports/summary, GET /api/reports/eia-monthly-summary)
- [ ] Display KPI cards (total deals, conversions, revenue)
- [ ] Add date range selector (month, quarter, year)
- [ ] Optional: Export as PDF/CSV
- **Validation**: Can view reports, date filtering works

### 5.3 Build Go-Live Status view (admin only)
- [ ] Create Go-Live view (hidden from non-admins)
- [ ] Display current status and mode
- [ ] Implement `workflow_enableGoLive` (POST /api/go-live/enable)
- [ ] Implement `workflow_disableGoLive` (POST /api/go-live/disable)
- [ ] Show mode choice modal (sandbox/production)
- [ ] Display audit trail of go-live toggles
- **Validation**: Admin can toggle go-live, status updates correctly

### 5.4 Add notifications system
- [ ] Create notifications dropdown in header
- [ ] Implement `workflow_refreshNotifications` (GET /api/notifications)
- [ ] Implement `workflow_markNotificationRead` (POST /api/notifications/{id}/read)
- [ ] Show unread badge on bell icon
- [ ] Optional: Real-time notifications (WebSocket if backend supports)
- **Validation**: Can see notifications, marking as read works, badge updates

### 5.5 Optimize performance
- [ ] Implement loading states (spinners, skeletons)
- [ ] Add error boundaries (fallback UI for errors)
- [ ] Implement request caching where appropriate
- [ ] Add optimistic updates (update UI before server confirms)
- **Validation**: App feels responsive, errors are handled gracefully

---

## Testing Checkpoints

### After Each Phase:

**Phase 1**: 
- [ ] Can login/logout
- [ ] Dashboard header displays user name
- [ ] Navigation is accessible
- [ ] Health endpoint responds

**Phase 2**:
- [ ] Can see list of leads
- [ ] Can create a new lead
- [ ] Can view lead details
- [ ] Can bulk import leads from CSV

**Phase 3**:
- [ ] Can see pending approvals
- [ ] Can approve/deny approvals
- [ ] Can convert approved lead to deal

**Phase 4**:
- [ ] Can see all deals
- [ ] Can view deal details with analysis
- [ ] Can see matched buyers
- [ ] Can send deal to buyer

**Phase 5**:
- [ ] Can draft messages
- [ ] Can view reports
- [ ] Admin can toggle go-live
- [ ] Notifications display and update

---

## Rollback Plan

If any phase fails:
1. Identify which component is broken (use error logs)
2. Revert changes to that component in WeWeb
3. Consult WEWEB_BACKEND_CONTRACT.md endpoint definition
4. Check backend logs: `cd services/api && tail -f app.log`
5. Re-test endpoint in Postman/Insomnia before retrying
6. If backend issue: Contact backend team, do not modify WeWeb code
7. If WeWeb issue: Review workflow/variable setup, compare to documentation

---

## Success Criteria

**App is ready for production when:**
- [ ] All 5 phases complete without critical errors
- [ ] Health check responds within 1 second
- [ ] All 15+ core workflows execute successfully
- [ ] No 500/503 errors from backend
- [ ] No auth failures (401/403) for valid tokens
- [ ] Performance is acceptable (pages load <3 seconds)
- [ ] Error messages are user-friendly and actionable
- [ ] Notifications system is functional

---

## Estimated Effort

| Phase | Hours | Complexity | Risk |
|-------|-------|-----------|------|
| Foundation | 2 | Low | Low |
| Lead Intake | 3 | Low | Low |
| Approvals | 2 | Low | Low |
| Deals | 3 | Medium | Medium |
| Polish | 2 | Low | Low |
| **Total** | **12** | **Low** | **Low** |

---

## Notes

- Each phase builds on previous phases (sequential, not parallel)
- Test each workflow in isolation before moving to next feature
- If backend endpoint is unavailable, mock the API response
- Use environment variables to switch between mock and real API
- Keep git commits clean and granular (one feature per commit)
- Document any deviations from this plan for future reference

---

**Last Updated**: 2026-05-19
