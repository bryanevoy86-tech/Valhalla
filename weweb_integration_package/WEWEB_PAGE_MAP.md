# WeWeb Page Map

**Maps backend endpoints to WeWeb views and workflows**

---

## Single Page App Views

### Dashboard View
**Purpose**: Executive overview, KPIs, quick actions  
**URL**: /?view=dashboard  

**Sections**:
1. **Header**: Active user, session status, notifications bell
   - Endpoints: GET /api/notifications
   - Variables: CURRENT_USER, AUTH_TOKEN, unread_count
   
2. **KPI Cards**: Total deals, active approvals, conversions, monthly volume
   - Endpoints: GET /api/reports/summary
   - Variables: DASHBOARD_METRICS, SELECTED_PERIOD
   
3. **Go-Live Status**: Current mode, toggle button (admin only)
   - Endpoints: GET /api/go-live/status, POST /api/go-live/enable, POST /api/go-live/disable
   - Variables: GO_LIVE_STATUS, GO_LIVE_MODE, IS_ADMIN
   
4. **Quick Actions**: New lead, new deal, view approvals, view hot contacts
   - Endpoints: GET /api/jarvis/hot-contacts, GET /api/va-intake/approvals/pending
   - Variables: HOT_CONTACTS, PENDING_APPROVALS_COUNT
   
5. **Jarvis Intelligence Widget**: Top recommendations, hot contacts
   - Endpoints: GET /api/jarvis/dashboard
   - Variables: JARVIS_INSIGHTS, HOT_LEADS

**Workflows Used**:
- refreshDashboardMetrics
- toggleGoLiveMode
- openLeadIntake
- openDealCreation
- viewApprovals

**Buttons**:
- New Lead (opens Lead Intake view)
- New Deal (opens Deal Creation view)
- View Approvals (scrolls to section or modal)
- Enable Go-Live (admin only)
- View Hot Contacts (opens Jarvis Intelligence)

**Loading States**:
- METRICS_LOADING, NOTIFICATIONS_LOADING, JARVIS_LOADING

**Error States**:
- GO_LIVE_STATUS_ERROR, METRICS_ERROR, JARVIS_ERROR

---

### Lead Intake View
**Purpose**: Capture VA leads, import, score, and route to approval  
**URL**: /?view=lead_intake  

**Sections**:
1. **Lead Creation Form**
   - Fields: Name, Phone, Email, Property Address, Estimated Value, Equity
   - Endpoints: POST /api/va-intake/lead
   - Variables: NEW_LEAD_FORM, FORM_ERRORS, CREATING_LEAD
   - Workflow: submitNewLead
   
2. **Lead List (Paginated)**
   - Endpoints: GET /api/va-intake/leads (with skip/limit)
   - Variables: VA_LEADS, VA_LEADS_PAGE, VA_LEADS_TOTAL, LEADS_LOADING
   - Filters: Status, Stage, Created Date Range
   
3. **Bulk Import**
   - Endpoints: POST /api/va-intake/lead (batch via loop)
   - Workflow: importLeadsBatch
   
4. **Lead Filters & Sort**
   - Variables: VA_LEAD_FILTER_STATUS, VA_LEAD_FILTER_STAGE, VA_LEAD_SORT

**Buttons**:
- Create Lead (form submit)
- Import CSV (file upload, then POST batch)
- View Detail (opens Lead Detail view)
- Mark for Approval (flow action)

**Loading States**:
- LEADS_LOADING, CREATING_LEAD, IMPORTING_LEADS

**Error States**:
- LEAD_CREATION_ERROR, IMPORT_ERROR, LEADS_FETCH_ERROR

---

### Lead Detail View
**Purpose**: View single lead details, audit trail, status, actions  
**URL**: /?view=lead_detail&lead_id={id}  

**Sections**:
1. **Lead Header**: Name, phone, status badge, timeline
   - Endpoints: GET /api/va-intake/leads/{lead_id}
   - Variables: SELECTED_VA_LEAD, SELECTED_VA_LEAD_STATUS
   
2. **Property Details**: Address, estimated value, equity, comparables
   - Endpoints: GET /api/va-intake/leads/{lead_id}
   - Variables: SELECTED_VA_LEAD.property
   
3. **Audit Trail**: All actions, notes, timestamps
   - Endpoints: GET /api/va-intake/leads/{lead_id} (audit_trail field)
   - Variables: VA_LEAD_AUDIT_LOG
   
4. **Actions**: Convert to deal, send message, mark approved, move to next stage
   - Endpoints: POST /api/va-intake/leads/{lead_id}/convert-to-deal
   - Workflow: convertLeadToDeal, draftSellerMessage

**Buttons**:
- Convert to Deal (POST convert-to-deal)
- Draft Seller Message (POST draft-seller-message)
- Back to List (navigate to Lead Intake)
- Archive Lead (POST action endpoint if exists)

**Loading States**:
- LEAD_DETAIL_LOADING, CONVERTING_TO_DEAL, SENDING_MESSAGE

**Error States**:
- LEAD_DETAIL_ERROR, CONVERSION_ERROR

---

### Approval Queue View
**Purpose**: Review pending VA lead approvals, approve/deny, track  
**URL**: /?view=approval_queue  

**Sections**:
1. **Pending Approvals List**
   - Endpoints: GET /api/va-intake/approvals/pending
   - Variables: VA_PENDING_APPROVALS, VA_PENDING_APPROVALS_TOTAL
   - Filters: Priority, Date, Lead Name
   
2. **Approval Detail**: Lead info, recommended action, notes field
   - Endpoints: GET /api/va-intake/approvals/pending (or detail endpoint if exists)
   - Variables: SELECTED_APPROVAL
   
3. **Approval Actions**: Approve button, deny button, notes
   - Endpoints: POST /api/va-intake/approvals/{approval_id}/approve, POST .../deny
   - Workflows: approveVaApproval, denyVaApproval
   
4. **Approval History**: Recently approved/denied approvals
   - Endpoints: GET /api/audit-log (filtered to va-intake approvals)
   - Variables: APPROVAL_HISTORY

**Buttons**:
- Approve (POST approve endpoint)
- Deny (POST deny endpoint, show reason modal)
- View Lead Detail (navigate to Lead Detail)
- Refresh Queue (GET pending approvals)

**Loading States**:
- APPROVALS_LOADING, APPROVING, DENYING

**Error States**:
- APPROVALS_FETCH_ERROR, APPROVE_ERROR, DENY_ERROR

---

### Deals Dashboard View
**Purpose**: Overview of all deals, filtering, status tracking  
**URL**: /?view=deals_dashboard  

**Sections**:
1. **Deals List (Paginated, Sortable)**
   - Endpoints: GET /api/deals
   - Variables: DEALS, DEALS_PAGE, DEALS_TOTAL, DEALS_LOADING
   - Filters: Status, Deal Type (wholesale/flip/brrrr), Region, Date Range
   - Sort: By Date, By Status, By Property Value, By Deal Type
   
2. **Deal Status Indicators**: Visual status columns
   - Endpoints: GET /api/deals (status field)
   - Variables: Conveyed via DEALS array
   
3. **Quick Create Deal Button**
   - Endpoints: POST /api/deals (in modal form)
   - Workflow: createNewDeal
   
4. **Search**: Property address, deal ID
   - Client-side search on DEALS variable

**Buttons**:
- New Deal (opens Deal Creation modal)
- View Deal (opens Deal Detail)
- Export List (client-side CSV export)
- Refresh (GET deals)

**Loading States**:
- DEALS_LOADING, CREATING_DEAL

**Error States**:
- DEALS_FETCH_ERROR, DEAL_CREATION_ERROR

---

### Deal Detail View
**Purpose**: Single deal view, timeline, buyers, offers, contracts, analysis  
**URL**: /?view=deal_detail&deal_id={id}  

**Sections**:
1. **Deal Header**: Property address, status, deal type, ARV
   - Endpoints: GET /api/deals/{deal_id}
   - Variables: SELECTED_DEAL, SELECTED_DEAL_STATUS
   
2. **Deal Timeline**: Stages (acquisition, due diligence, closing, disposition)
   - Endpoints: GET /api/deals/{deal_id}
   - Variables: SELECTED_DEAL.timeline
   
3. **Buyers List**: Matched buyers, interest status
   - Endpoints: GET /api/deals/{deal_id}/buyers or GET /api/buyers
   - Variables: DEAL_BUYERS, BUYER_MATCHES
   
4. **Offers & Contracts**: Pending offers, signed contracts
   - Endpoints: GET /api/deals/{deal_id} (offers field)
   - Variables: SELECTED_DEAL.offers, SELECTED_DEAL.contracts
   
5. **Deal Analysis**: Comparables, market trend, FLIP/BRRRR estimates
   - Endpoints: GET /api/reports/deal-analysis, POST /api/flip/estimate, POST /api/brrrr/estimate
   - Variables: DEAL_ANALYSIS, FLIP_ESTIMATE, BRRRR_ESTIMATE
   
6. **Actions**: Advance stage, send to buyer, create buyer packet
   - Endpoints: POST /api/deals/{deal_id}/action, POST /api/deals/{deal_id}/send-to-buyer/{buyer_id}
   - Workflows: advanceDealStage, sendDealToBuyer, createBuyerPacket

**Buttons**:
- Advance Stage (POST action endpoint)
- Send to Buyer (modal, then POST send-to-buyer)
- Create Buyer Packet (POST create-buyer-packet)
- View Analysis (load analysis section)
- Back to Dashboard (navigate)

**Loading States**:
- DEAL_DETAIL_LOADING, ANALYSIS_LOADING, SENDING_TO_BUYER

**Error States**:
- DEAL_DETAIL_ERROR, ANALYSIS_ERROR, SEND_ERROR

---

### Buyer Matching View
**Purpose**: View buyer database, match to deals, send packets  
**URL**: /?view=buyer_matching&deal_id={id}  

**Sections**:
1. **Buyer List (Filtered)**
   - Endpoints: GET /api/buyers, GET /api/deals/{deal_id}/buyers
   - Variables: BUYERS, MATCHED_BUYERS, BUYER_MATCH_SCORES
   - Filters: Region, Deal Type, Min Match Score
   
2. **Match Scoring**: Show why each buyer matches
   - Endpoints: GET /api/deals/{deal_id}/buyers (includes match_score)
   - Variables: BUYER_MATCHES (with reasoning)
   
3. **Send Workflow**: Select buyer, preview packet, send
   - Endpoints: POST /api/deals/{deal_id}/send-to-buyer/{buyer_id}, POST /api/messaging/va/create-buyer-packet
   - Workflows: sendDealToBuyer, createBuyerPacket

**Buttons**:
- Send Deal (POST send-to-buyer)
- Create Packet (POST create-buyer-packet)
- View Buyer Profile (modal or nav)
- Refresh Matches (GET matched buyers)

**Loading States**:
- BUYERS_LOADING, SENDING_DEAL, CREATING_PACKET

**Error States**:
- BUYERS_FETCH_ERROR, SEND_ERROR, PACKET_ERROR

---

### Messaging View
**Purpose**: Draft and send communications  
**URL**: /?view=messaging  

**Sections**:
1. **Draft Seller Message** (for VA leads)
   - Endpoints: POST /api/messaging/va/draft-seller-message/{lead_id}
   - Variables: DRAFT_SELLER_MESSAGE, MESSAGE_TONE, MESSAGE_URGENCY
   - Workflow: draftSellerMessage
   
2. **Buyer Packet Creation**
   - Endpoints: POST /api/messaging/va/create-buyer-packet/{deal_id}
   - Variables: BUYER_PACKET_URL, PACKET_CREATED
   - Workflow: createBuyerPacket
   
3. **Message History**: Sent messages, delivery status
   - Endpoints: GET /api/audit-log (filtered to messaging)
   - Variables: MESSAGE_HISTORY

**Buttons**:
- Draft Message (POST draft-seller-message)
- Create Packet (POST create-buyer-packet)
- Send Message (POST send-message if available)

**Loading States**:
- DRAFTING_MESSAGE, CREATING_PACKET, SENDING_MESSAGE

**Error States**:
- DRAFT_ERROR, PACKET_ERROR, SEND_ERROR

---

### Reports / EIA View
**Purpose**: Monthly reports, KPIs, performance tracking  
**URL**: /?view=reports_eia  

**Sections**:
1. **Dashboard Summary**
   - Endpoints: GET /api/reports/summary
   - Variables: REPORT_SUMMARY, SELECTED_PERIOD
   
2. **Monthly EIA Report**
   - Endpoints: GET /api/reports/eia-monthly-summary
   - Variables: EIA_REPORT, EIA_METRICS
   
3. **Deal Analysis**: Average deal size, cycle time, profitability
   - Endpoints: GET /api/reports/deal-analysis
   - Variables: DEAL_STATS

**Buttons**:
- Export Report (client-side PDF/CSV)
- Change Period (date picker)
- Refresh (GET reports)

**Loading States**:
- REPORT_LOADING, EIA_LOADING

**Error States**:
- REPORT_ERROR, EIA_ERROR

---

### Go-Live Status View
**Purpose**: Monitor activation status, enable/disable, timeline  
**URL**: /?view=go_live_status  

**Sections**:
1. **Status Indicator**: Current mode (active/inactive), timestamp
   - Endpoints: GET /api/go-live/status
   - Variables: GO_LIVE_STATUS, GO_LIVE_MODE, GO_LIVE_TIMESTAMP
   
2. **Enable/Disable Controls** (admin only)
   - Endpoints: POST /api/go-live/enable, POST /api/go-live/disable
   - Workflows: enableGoLive, disableGoLive
   - Variables: GO_LIVE_MODE_CHOICE (sandbox/production)
   
3. **Timeline**: Activation history
   - Endpoints: GET /api/audit-log (filtered to go-live events)
   - Variables: GO_LIVE_HISTORY

**Buttons**:
- Enable Go-Live (POST enable, modal to choose mode)
- Disable Go-Live (POST disable)
- Refresh Status (GET status)

**Loading States**:
- STATUS_LOADING, ENABLING, DISABLING

**Error States**:
- STATUS_ERROR, ENABLE_ERROR, DISABLE_ERROR

---

## View Navigation Map

```
Dashboard (home)
├── → Lead Intake
│   └── → Lead Detail (for specific lead)
│       └── → Deal Detail (if converted)
├── → Approval Queue
│   └── → Lead Detail
│       └── → Deal Detail
├── → Deals Dashboard
│   └── → Deal Detail
│       ├── → Buyer Matching
│       └── → Reports (deal-specific)
├── → Buyer Matching (direct)
├── → Messaging
├── → Reports / EIA
└── → Go-Live Status (admin only)
```

---

## Cross-Page Variables

| Variable | Type | Usage | Set By |
|----------|------|-------|--------|
| AUTH_TOKEN | string | All requests | Login / Session store |
| CURRENT_USER | object | Display, permissions | Backend auth |
| CURRENT_VIEW | string | Navigation control | URL query param |
| IS_ADMIN | boolean | Permission gates | Backend auth |
| DASHBOARD_METRICS | object | Dashboard KPIs | GET /api/reports/summary |
| VA_LEADS | array | Lead Intake list | GET /api/va-intake/leads |
| SELECTED_VA_LEAD | object | Lead Detail view | GET /api/va-intake/leads/{id} |
| VA_LEAD_AUDIT_LOG | array | Audit display | GET /api/va-intake/leads/{id} |
| VA_PENDING_APPROVALS | array | Approval Queue | GET /api/va-intake/approvals/pending |
| SELECTED_APPROVAL | object | Approval detail | Selected from list |
| DEALS | array | Deals Dashboard | GET /api/deals |
| SELECTED_DEAL | object | Deal Detail view | GET /api/deals/{id} |
| DEAL_BUYERS | array | Buyer section | GET /api/deals/{id}/buyers |
| BUYER_MATCHES | array | Matching scores | GET /api/deals/{id}/buyers |
| HOT_CONTACTS | array | Jarvis widget | GET /api/jarvis/hot-contacts |
| GO_LIVE_STATUS | string | Status indicator | GET /api/go-live/status |
| GO_LIVE_MODE | string | active/inactive | GET /api/go-live/status |
| REPORT_SUMMARY | object | Report view | GET /api/reports/summary |
| EIA_REPORT | object | EIA view | GET /api/reports/eia-monthly-summary |

---

**Last Updated**: 2026-05-19
