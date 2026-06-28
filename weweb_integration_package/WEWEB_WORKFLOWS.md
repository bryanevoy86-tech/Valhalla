# WeWeb Workflows

**Recommended reusable workflows for Valhalla backend integration**

---

## Authentication Workflows

### workflow_login
**Purpose**: Authenticate user and set global session  
**Triggers**: Login button, page load (auto-login if token exists)

**Steps**:
1. Collect email/password from login form
2. POST /api/auth/login (if endpoint exists) or validate existing AUTH_TOKEN
3. Store returned JWT/session token in localStorage
4. Set AUTH_TOKEN variable globally
5. Fetch CURRENT_USER via API
6. Set IS_ADMIN based on CURRENT_USER.role
7. Navigate to dashboard
8. On error: Display login error message, clear AUTH_TOKEN

**Error Handling**:
- 401: "Invalid credentials"
- 400: "Missing email or password"
- 503: "Backend unavailable - try again later"

---

### workflow_logout
**Purpose**: Clear session and redirect to login  
**Triggers**: Logout button, session timeout

**Steps**:
1. Clear AUTH_TOKEN from localStorage
2. Clear CURRENT_USER variable
3. Clear all page-specific variables
4. Navigate to login page
5. On error: Force redirect to login anyway

---

### workflow_refreshAuth
**Purpose**: Check if current session is still valid  
**Triggers**: Periodically (every 5 minutes), or when 401 received

**Steps**:
1. Check AUTH_TOKEN exists
2. GET /health to verify backend is up
3. If 401: Call workflow_logout
4. If 503: Show "Backend temporarily unavailable" message
5. If 200: Continue normally

---

## Lead Intake Workflows

### workflow_submitNewLead
**Purpose**: Create a new VA lead from form  
**Triggers**: "Create Lead" button in Lead Intake form

**Steps**:
1. Validate form: name, phone, email, property_address required
2. Set CREATING_LEAD = true
3. POST /api/va-intake/lead with form data
4. On success:
   - Add new lead to VA_LEADS array (prepend for fresh view)
   - Clear NEW_LEAD_FORM
   - Show success toast: "Lead created successfully"
   - Set CREATING_LEAD = false
5. On error:
   - Populate FORM_ERRORS with validation messages
   - Show error toast: error.detail
   - Set CREATING_LEAD = false
   - Highlight invalid fields in form

---

### workflow_importLeadsBatch
**Purpose**: Bulk import leads from CSV file  
**Triggers**: "Import CSV" button → file upload → confirm

**Steps**:
1. Validate CSV format (headers: Name, Phone, Email, Address, Value, Equity)
2. Parse CSV rows into array of lead objects
3. Set IMPORTING_LEADS = true
4. For each lead object:
   - POST /api/va-intake/lead with lead data
   - On error: Log to import_errors array, continue (don't stop)
5. After all POST calls complete:
   - Count successes and failures
   - Show toast: "Imported 45 leads, 2 failed"
   - Refresh VA_LEADS via GET /api/va-intake/leads
   - Set IMPORTING_LEADS = false
6. On critical error (parse failed):
   - Show error modal with details
   - Set IMPORTING_LEADS = false

---

### workflow_openLeadDetail
**Purpose**: Load and display single lead details  
**Triggers**: Click on lead row in list, "View Lead" button

**Steps**:
1. Extract lead_id from clicked row or button context
2. Set LEAD_DETAIL_LOADING = true
3. GET /api/va-intake/leads/{lead_id}
4. On success:
   - Set SELECTED_VA_LEAD = response
   - Set SELECTED_VA_LEAD_STATUS = response.status
   - Set VA_LEAD_AUDIT_LOG = response.audit_trail
   - Set LEAD_DETAIL_LOADING = false
   - Navigate to Lead Detail view
5. On error (404):
   - Show error: "Lead not found"
   - Navigate back to Lead Intake
6. On error (401):
   - Call workflow_refreshAuth

---

### workflow_convertLeadToDeal
**Purpose**: Convert approved VA lead to active deal  
**Triggers**: "Convert to Deal" button in Lead Detail

**Steps**:
1. Check SELECTED_VA_LEAD.status == "approved"
2. Open modal: Choose deal_type (wholesale/flip/brrrr)
3. Collect deal_type from modal, optional: estimated_arv, notes
4. Set CONVERTING_TO_DEAL = true
5. POST /api/va-intake/leads/{lead_id}/convert-to-deal with deal_type
6. On success:
   - Show success toast: "Lead converted to deal #{deal_id}"
   - Fetch updated SELECTED_VA_LEAD (now shows status: converted, deal_id link)
   - Auto-navigate to new Deal Detail view after 2 seconds
   - Set CONVERTING_TO_DEAL = false
7. On error (409 - already converted):
   - Show warning: "This lead is already converted"
   - Offer "View Existing Deal" button → navigate to deal
   - Set CONVERTING_TO_DEAL = false
8. On error (validation):
   - Show error modal with details
   - Set CONVERTING_TO_DEAL = false

---

## Approval Queue Workflows

### workflow_loadApprovalQueue
**Purpose**: Fetch and display pending approvals  
**Triggers**: Navigate to Approval Queue view, "Refresh" button

**Steps**:
1. Set APPROVALS_LOADING = true
2. GET /api/va-intake/approvals/pending (with pagination: skip=0, limit=50)
3. On success:
   - Set VA_PENDING_APPROVALS = response.approvals
   - Set VA_PENDING_APPROVALS_TOTAL = response.total
   - Sort by priority desc, then date asc
   - Set APPROVALS_LOADING = false
4. On error:
   - Show error toast: error.detail
   - Set APPROVALS_LOADING = false

---

### workflow_approveVaApproval
**Purpose**: Approve a pending VA lead  
**Triggers**: "Approve" button in Approval Queue

**Steps**:
1. Extract approval_id from current row
2. Optionally collect approval notes from textarea
3. Set APPROVING = true
4. POST /api/va-intake/approvals/{approval_id}/approve with notes
5. On success:
   - Remove approval from VA_PENDING_APPROVALS array
   - Decrement VA_PENDING_APPROVALS_TOTAL
   - Show success toast: "Approval granted"
   - Update NOTIFICATIONS_UNREAD (decrement)
   - Set APPROVING = false
6. On error (409 - already approved):
   - Show warning: "This approval was already processed"
   - Refresh queue
   - Set APPROVING = false
7. On error (validation):
   - Show error modal
   - Set APPROVING = false

---

### workflow_denyVaApproval
**Purpose**: Deny a pending VA lead  
**Triggers**: "Deny" button in Approval Queue

**Steps**:
1. Extract approval_id
2. Open modal: Collect reason for denial (dropdown + textarea)
3. Set DENYING = true
4. POST /api/va-intake/approvals/{approval_id}/deny with reason
5. On success:
   - Remove approval from VA_PENDING_APPROVALS
   - Decrement VA_PENDING_APPROVALS_TOTAL
   - Show success toast: "Approval denied"
   - Update NOTIFICATIONS_UNREAD (decrement)
   - Set DENYING = false
6. On error:
   - Show error modal
   - Set DENYING = false

---

## Deal Management Workflows

### workflow_loadDealsDashboard
**Purpose**: Fetch and display all deals  
**Triggers**: Navigate to Deals Dashboard, "Refresh" button

**Steps**:
1. Set DEALS_LOADING = true
2. Build query params from filter variables (status, type, region, etc.)
3. GET /api/deals (with skip, limit, filters)
4. On success:
   - Set DEALS = response.deals
   - Set DEALS_TOTAL = response.total
   - Sort by DEAL_FILTER_SORT (date desc, status, etc.)
   - Set DEALS_LOADING = false
5. On error:
   - Show error toast
   - Set DEALS_LOADING = false

---

### workflow_createNewDeal
**Purpose**: Create a new deal  
**Triggers**: "New Deal" button

**Steps**:
1. Open Deal Creation modal
2. Collect form: property_address, property_value, deal_type, estimated_arv
3. Validate required fields
4. Set CREATING_DEAL = true
5. POST /api/deals with form data
6. On success:
   - Add new deal to DEALS array (prepend)
   - Increment DEALS_TOTAL
   - Show success toast: "Deal created: {address}"
   - Navigate to Deal Detail view for new deal
   - Set CREATING_DEAL = false
7. On error:
   - Show validation errors in modal
   - Set CREATING_DEAL = false

---

### workflow_openDealDetail
**Purpose**: Load and display single deal  
**Triggers**: Click on deal row, "View Deal" button

**Steps**:
1. Extract deal_id
2. Set DEAL_DETAIL_LOADING = true
3. Parallel requests:
   - GET /api/deals/{deal_id}
   - GET /api/deals/{deal_id}/buyers
   - GET /api/reports/deal-analysis?deal_id={deal_id}
4. On success:
   - Set SELECTED_DEAL = main response
   - Set SELECTED_DEAL_STATUS = main response.status
   - Set DEAL_BUYERS = buyers response
   - Set DEAL_ANALYSIS = analysis response
   - Set DEAL_DETAIL_LOADING = false
   - Navigate to Deal Detail view
5. On error (404):
   - Show error: "Deal not found"
   - Navigate back to Deals Dashboard
6. On error (partial - analysis fails but deal loads):
   - Load deal normally, show "Analysis unavailable" message

---

### workflow_advanceDealStage
**Purpose**: Move deal to next stage (acquire → due dil → closing → disp)  
**Triggers**: "Advance Stage" button

**Steps**:
1. Check deal can advance (not already at final stage)
2. Optional: Collect notes/reason for advancement
3. Set ADVANCING_DEAL = true (if flag exists)
4. POST /api/deals/{deal_id}/action with action="advance" and notes
5. On success:
   - Update SELECTED_DEAL.status to new stage
   - Update SELECTED_DEAL.timeline to reflect new position
   - Show success toast: "Deal advanced to {stage}"
   - Refresh dashboard (DEALS array)
6. On error (409 - invalid state):
   - Show error: "Cannot advance deal from current stage"
7. On error:
   - Show error modal with details

---

### workflow_calculateFlipEstimate
**Purpose**: Calculate FLIP deal profitability  
**Triggers**: User opens FLIP section in Deal Detail, or manually refreshes

**Steps**:
1. Extract purchase_price, arv, holding_cost_months, rehab_cost from SELECTED_DEAL
2. Set ANALYSIS_LOADING = true
3. POST /api/flip/estimate with above parameters
4. On success:
   - Set FLIP_ESTIMATE = response
   - Show FLIP_ESTIMATE in UI (gross_profit, roi, holding_cost)
   - Set ANALYSIS_LOADING = false
5. On error:
   - Show "FLIP analysis unavailable"
   - Set ANALYSIS_LOADING = false

---

### workflow_calculateBrrrrEstimate
**Purpose**: Calculate BRRRR deal financing and cash flow  
**Triggers**: User opens BRRRR section in Deal Detail

**Steps**:
1. Extract purchase_price, arv, rehab_cost, desired_ltv, desired_rent
2. Set ANALYSIS_LOADING = true
3. POST /api/brrrr/estimate with parameters
4. On success:
   - Set BRRRR_ESTIMATE = response
   - Show BRRRR_ESTIMATE in UI (max_loan, monthly_rent, cash_flow)
   - Set ANALYSIS_LOADING = false
5. On error:
   - Show "BRRRR analysis unavailable"

---

## Buyer & Messaging Workflows

### workflow_matchBuyersToDeals
**Purpose**: Get list of matched buyers for current deal  
**Triggers**: Navigate to Buyer Matching section or "Find Buyers" button

**Steps**:
1. Set BUYERS_LOADING = true
2. GET /api/deals/{deal_id}/buyers (includes match_score)
3. On success:
   - Set BUYER_MATCHES = response (sorted by match_score desc)
   - Set BUYERS_LOADING = false
4. On error:
   - Show error: "No buyers available"
   - Set BUYERS_LOADING = false

---

### workflow_sendDealToBuyer
**Purpose**: Send deal packet to specific buyer  
**Triggers**: "Send Deal" button in Buyer Matching

**Steps**:
1. Open modal: Select buyer from BUYER_MATCHES
2. Optional: Include analysis (checkbox), set deadline_days
3. Set SENDING_TO_BUYER = true
4. POST /api/deals/{deal_id}/send-to-buyer/{buyer_id} with options
5. On success:
   - Show success toast: "Deal sent to {buyer_name}"
   - Record in DEAL_BUYERS that deal was sent (add sent_at timestamp)
   - Set SENDING_TO_BUYER = false
6. On error (404 - buyer not found):
   - Show error: "Buyer not found"
7. On error:
   - Show error modal

---

### workflow_createBuyerPacket
**Purpose**: Generate buyer information packet (PDF, email format)  
**Triggers**: "Create Packet" button in Messaging or Deal Detail

**Steps**:
1. Open modal: Choose options (include_analysis, include_comps, format: pdf/email)
2. Set CREATING_PACKET = true
3. POST /api/messaging/va/create-buyer-packet/{deal_id} with options
4. On success:
   - Set BUYER_PACKET_URL = response.url
   - Set BUYER_PACKET_GENERATED = true
   - Show success toast: "Packet created"
   - Offer "Download" or "Send" button
   - Set CREATING_PACKET = false
5. On error:
   - Show error modal
   - Set CREATING_PACKET = false

---

### workflow_draftSellerMessage
**Purpose**: AI-draft initial outreach message to seller  
**Triggers**: "Draft Message" button in Lead Detail

**Steps**:
1. Open modal: Choose message tone (professional/friendly/formal)
2. Choose urgency (high/normal/low)
3. Set DRAFTING_MESSAGE = true
4. POST /api/messaging/va/draft-seller-message/{lead_id} with tone, urgency
5. On success:
   - Set DRAFT_SELLER_MESSAGE = response.message
   - Show draft in modal for review/edit
   - Offer "Copy to Clipboard", "Send as Email", "Edit" buttons
   - Set DRAFTING_MESSAGE = false
6. On error:
   - Show "Message generation failed"
   - Set DRAFTING_MESSAGE = false

---

## Go-Live Management Workflows

### workflow_checkGoLiveStatus
**Purpose**: Check current go-live status  
**Triggers**: App load, Dashboard refresh, Go-Live Status view

**Steps**:
1. GET /api/go-live/status
2. On success:
   - Set GO_LIVE_STATUS = response.status
   - Set GO_LIVE_MODE = response.mode
   - Set GO_LIVE_TIMESTAMP = response.timestamp
   - Update UI status badge
3. On error (403):
   - Hide go-live controls (not authorized)
4. On error:
   - Show "Status unavailable"

---

### workflow_enableGoLive
**Purpose**: Activate go-live (admin only)  
**Triggers**: "Enable Go-Live" button (admin view only)

**Steps**:
1. Check IS_ADMIN == true
2. Open modal: Choose mode (sandbox/production)
3. Show warning message appropriate to mode
4. Set ENABLING_GO_LIVE = true
5. POST /api/go-live/enable with mode choice
6. On success:
   - Set GO_LIVE_STATUS = "active"
   - Set GO_LIVE_MODE = chosen mode
   - Update CURRENT_USER.can_modify (may change)
   - Show success toast: "Go-live enabled: {mode}"
   - Refresh dashboard
   - Set ENABLING_GO_LIVE = false
7. On error (403):
   - Show "You are not authorized"
8. On error:
   - Show error modal
   - Set ENABLING_GO_LIVE = false

---

### workflow_disableGoLive
**Purpose**: Disable go-live (admin only, emergency stop)  
**Triggers**: "Disable Go-Live" button

**Steps**:
1. Check IS_ADMIN == true
2. Show warning modal: "This will disable all automation"
3. Require confirmation
4. Set DISABLING_GO_LIVE = true
5. POST /api/go-live/disable
6. On success:
   - Set GO_LIVE_STATUS = "inactive"
   - Set GO_LIVE_MODE = null
   - Show success toast: "Go-live disabled"
   - Refresh dashboard
   - Set DISABLING_GO_LIVE = false
7. On error:
   - Show error modal
   - Set DISABLING_GO_LIVE = false

---

## Data Refresh Workflows

### workflow_refreshNotifications
**Purpose**: Periodically fetch latest notifications  
**Triggers**: App load, every 30 seconds (background), after actions

**Steps**:
1. GET /api/notifications (skip=0, limit=20)
2. On success:
   - Set NOTIFICATIONS = response.notifications
   - Set UNREAD_COUNT = response.unread_count
   - Update bell badge in header
3. On error: Continue normally (non-blocking)

---

### workflow_markNotificationRead
**Purpose**: Mark single notification as read  
**Triggers**: Click on notification

**Steps**:
1. Extract notification_id
2. POST /api/notifications/{notification_id}/read
3. On success:
   - Remove from NOTIFICATIONS array or mark as read
   - Decrement UNREAD_COUNT
   - Update bell badge
4. On error: Continue normally

---

## Notes

- Each workflow should have clear entry points (what triggers it)
- All async operations should have loading flags (_LOADING variables)
- All workflows should include error handling (toast messages, error modals)
- Parallel requests should be used where safe (e.g., loading deal + buyers + analysis)
- Sensitive operations (go-live, denying approvals) should require confirmation
- Destructive operations should show warnings before executing
- After all mutations (POST/PUT), refresh relevant data structures

---

**Last Updated**: 2026-05-19
