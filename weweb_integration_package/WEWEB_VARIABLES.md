# WeWeb Variables

**Recommended variable structure and naming for Valhalla backend integration**

---

## Global Variables (Persistent Across Views)

### Authentication & Session

| Variable | Type | Default | Purpose | Scope | Notes |
|----------|------|---------|---------|-------|-------|
| **AUTH_TOKEN** | string | null | JWT or Session token for all API requests | Global | Store securely; send in Authorization header |
| **CURRENT_USER** | object | {} | Current logged-in user info | Global | Contains id, email, role, permissions |
| **IS_ADMIN** | boolean | false | Whether current user is admin | Global | Controls visibility of admin buttons |
| **SESSION_CREATED** | datetime | null | When session was created | Global | For session timeout tracking |
| **SESSION_EXPIRES** | datetime | null | When session expires | Global | For logout countdown timer |

### Dashboard State

| Variable | Type | Default | Purpose | Scope | Global | Notes |
|----------|------|---------|---------|-------|-------|-------|
| **CURRENT_VIEW** | string | "dashboard" | Which page/view is active | Global | Controls navigation, URL query param |
| **API_BASE_URL** | string | "http://localhost:8000" (dev) or "https://api.valhalla.com" (prod) | Backend API root URL | Global | Set at app initialization |
| **DATABASE_READY** | boolean | false | Whether backend database initialized | Global | Check on /health endpoint |

### Go-Live State

| Variable | Type | Default | Purpose | Scope | Global | Notes |
|----------|------|---------|---------|-------|-------|-------|
| **GO_LIVE_STATUS** | string | "inactive" | Current go-live mode | Global | Values: "active" or "inactive" |
| **GO_LIVE_MODE** | string | null | Sandbox vs production | Global | Set when enabling go-live |
| **GO_LIVE_TIMESTAMP** | datetime | null | When go-live was last toggled | Global | For audit trail |
| **CAN_ENABLE_GO_LIVE** | boolean | false | Whether current user can enable | Global | Derived from IS_ADMIN and system readiness |

---

## Page-Specific Variables

### Dashboard Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **DASHBOARD_METRICS** | object | {} | KPI summary data | Dashboard | {total_deals: 42, active_leads: 8, conversions_month: 5, pending_approvals: 3} |
| **SELECTED_PERIOD** | string | "month" | Date range for metrics | Dashboard | "week", "month", "quarter", "year", "custom" |
| **METRICS_LOADING** | boolean | false | Show loading spinner | Dashboard | true while GET /api/reports/summary pending |
| **HOTBAR_NOTIFICATIONS** | array | [] | Top 3 pending approvals or alerts | Dashboard | Limited array for hot bar display |
| **NOTIFICATIONS_UNREAD** | number | 0 | Count of unread notifications | Dashboard | Shown as bell badge |

### Lead Intake Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **VA_LEADS** | array | [] | All VA leads (paginated) | Lead Intake | Array of lead objects |
| **VA_LEADS_PAGE** | number | 1 | Current page number | Lead Intake | Used with skip/limit |
| **VA_LEADS_TOTAL** | number | 0 | Total lead count (unfiltered) | Lead Intake | For pagination UI |
| **VA_LEAD_FILTER_STATUS** | string | "all" | Filter by lead status | Lead Intake | "pending", "approved", "denied", "converted", "all" |
| **VA_LEAD_FILTER_STAGE** | string | "all" | Filter by stage | Lead Intake | "intake", "review", "approval", "conversion", "all" |
| **VA_LEADS_LOADING** | boolean | false | Show loading state | Lead Intake | true while fetching |
| **NEW_LEAD_FORM** | object | {} | Form data for new lead | Lead Intake | {name: "", phone: "", email: "", property_address: "", estimated_value: 0, equity: 0} |
| **FORM_ERRORS** | object | {} | Validation errors | Lead Intake | {phone: "Invalid format", email: "Required"} |
| **CREATING_LEAD** | boolean | false | Show submit button loading | Lead Intake | true while POST pending |
| **IMPORTING_LEADS** | boolean | false | Show import progress | Lead Intake | true while batch import pending |
| **LEAD_IMPORT_FILE** | file | null | Selected CSV for bulk import | Lead Intake | File object from input |

### Lead Detail Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **SELECTED_VA_LEAD** | object | {} | Current lead being viewed | Lead Detail | Full lead object with all fields |
| **SELECTED_VA_LEAD_STATUS** | string | "" | Short status for badge | Lead Detail | "pending", "approved", "denied", "converted" |
| **VA_LEAD_AUDIT_LOG** | array | [] | All actions on this lead | Lead Detail | Array of audit events |
| **LEAD_DETAIL_LOADING** | boolean | false | Show loading skeleton | Lead Detail | true while GET pending |
| **CONVERTING_TO_DEAL** | boolean | false | Show convert button loading | Lead Detail | true while POST pending |
| **CONVERSION_ERROR** | string | "" | Error message if conversion failed | Lead Detail | "Lead already converted" |

### Approval Queue Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **VA_PENDING_APPROVALS** | array | [] | All pending approvals | Approval Queue | Array of approval objects |
| **VA_PENDING_APPROVALS_TOTAL** | number | 0 | Total pending (for pagination) | Approval Queue | Numeric count |
| **SELECTED_APPROVAL** | object | {} | Current approval being reviewed | Approval Queue | Full approval object |
| **APPROVALS_LOADING** | boolean | false | Show loading | Approval Queue | true while fetching |
| **APPROVING** | boolean | false | Show approve button loading | Approval Queue | true while POST approve pending |
| **DENYING** | boolean | false | Show deny button loading | Approval Queue | true while POST deny pending |
| **DENIAL_REASON** | string | "" | Why approval was denied | Approval Queue | Used in POST deny body |
| **APPROVAL_HISTORY** | array | [] | Recently approved/denied | Approval Queue | Optional, for reference |

### Deals Dashboard Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **DEALS** | array | [] | All deals (paginated) | Deals Dashboard | Array of deal objects |
| **DEALS_PAGE** | number | 1 | Current page | Deals Dashboard | For pagination |
| **DEALS_TOTAL** | number | 0 | Total deal count | Deals Dashboard | For pagination UI |
| **DEAL_FILTER_STATUS** | string | "all" | Filter by status | Deals Dashboard | "draft", "active", "closed", "archived", "all" |
| **DEAL_FILTER_TYPE** | string | "all" | Filter by deal type | Deals Dashboard | "wholesale", "flip", "brrrr", "all" |
| **DEAL_FILTER_REGION** | string | "" | Filter by region | Deals Dashboard | Zip code or region name |
| **DEALS_LOADING** | boolean | false | Show loading | Deals Dashboard | true while fetching |
| **CREATING_DEAL** | boolean | false | Show create button loading | Deals Dashboard | true while POST pending |
| **DEALS_SEARCH** | string | "" | Search by address or ID | Deals Dashboard | Client-side search term |

### Deal Detail Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **SELECTED_DEAL** | object | {} | Current deal being viewed | Deal Detail | Full deal object with all fields |
| **SELECTED_DEAL_STATUS** | string | "" | Deal status badge | Deal Detail | "draft", "active", "closed", "archived" |
| **DEAL_DETAIL_LOADING** | boolean | false | Show loading skeleton | Deal Detail | true while fetching |
| **DEAL_ANALYSIS** | object | {} | Comparables, market data | Deal Detail | {comps: [], market_trend: "", roi: 0} |
| **FLIP_ESTIMATE** | object | {} | FLIP deal profit estimate | Deal Detail | {gross_profit: 0, roi: 0.25, holding_months: 6} |
| **BRRRR_ESTIMATE** | object | {} | BRRRR deal financing | Deal Detail | {monthly_rent: 0, cash_flow: 0, ltv: 0.7} |
| **ANALYSIS_LOADING** | boolean | false | Show analysis loading | Deal Detail | true while fetching |
| **DEAL_BUYERS** | array | [] | Buyers matched to this deal | Deal Detail | Array of buyer objects with match_score |
| **SENDING_TO_BUYER** | boolean | false | Show send button loading | Deal Detail | true while POST pending |
| **BUYER_PACKET_URL** | string | "" | URL to generated packet | Deal Detail | PDF or document link |
| **CREATING_PACKET** | boolean | false | Show packet creation loading | Deal Detail | true while creating |

### Buyer Matching Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **BUYERS** | array | [] | All buyers in database | Buyer Matching | Array of buyer objects |
| **BUYER_MATCHES** | array | [] | Matched buyers for deal | Buyer Matching | Subset of BUYERS with match_score |
| **BUYER_MATCH_SCORES** | object | {} | Scoring explanation | Buyer Matching | {buyer_id: {score: 0.95, reason: ""}} |
| **BUYERS_LOADING** | boolean | false | Show loading | Buyer Matching | true while fetching |
| **SELECTED_BUYER** | object | {} | Buyer being sent a deal | Buyer Matching | Single buyer object |

### Messaging Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **DRAFT_SELLER_MESSAGE** | string | "" | AI-generated message draft | Messaging | Template message text |
| **MESSAGE_TONE** | string | "professional" | Message tone choice | Messaging | "professional", "friendly", "formal" |
| **MESSAGE_URGENCY** | string | "normal" | Urgency level | Messaging | "high", "normal", "low" |
| **DRAFTING_MESSAGE** | boolean | false | Show loading | Messaging | true while generating draft |
| **BUYER_PACKET_GENERATED** | boolean | false | Whether packet created | Messaging | true if POST successful |
| **MESSAGE_HISTORY** | array | [] | Previously sent messages | Messaging | Array of message objects |

### Reports/EIA Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **REPORT_SUMMARY** | object | {} | Monthly summary report | Reports | {deals: 0, conversions: 0, revenue: 0, metrics: {}} |
| **EIA_REPORT** | object | {} | Engagement, Impact, Analysis | Reports | {period: "2026-05", metrics: {}, top_performers: []} |
| **REPORT_LOADING** | boolean | false | Show loading | Reports | true while fetching |
| **EIA_LOADING** | boolean | false | Show EIA loading | Reports | true while fetching |
| **REPORT_PERIOD** | string | "current_month" | Which month to report | Reports | "current_month", "current_quarter", "custom" |
| **CUSTOM_REPORT_START** | date | null | Start date for custom report | Reports | ISO8601 date |
| **CUSTOM_REPORT_END** | date | null | End date for custom report | Reports | ISO8601 date |

### Go-Live Status Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **GO_LIVE_HISTORY** | array | [] | Activation audit trail | Go-Live | Array of go-live toggle events |
| **GO_LIVE_MODE_CHOICE** | string | "" | Mode being set | Go-Live | "sandbox" or "production" |
| **ENABLING_GO_LIVE** | boolean | false | Show enable button loading | Go-Live | true while POST pending |
| **DISABLING_GO_LIVE** | boolean | false | Show disable button loading | Go-Live | true while POST pending |

### Notifications Variables

| Variable | Type | Default | Purpose | Page Scope | Typical Value |
|----------|------|---------|---------|------------|--------------|
| **NOTIFICATIONS** | array | [] | All user notifications | Global | Array of notification objects |
| **NOTIFICATIONS_LOADING** | boolean | false | Show loading | Global | true while fetching |
| **UNREAD_COUNT** | number | 0 | Unread notification count | Global | For bell badge |
| **NOTIFICATION_FILTER** | string | "all" | Filter notifications | Global | "all", "approvals", "deals", "unread" |

---

## Local Variables (Within Buttons/Components)

| Variable | Type | Purpose | Used In |
|----------|------|---------|---------|
| is_expanded | boolean | Accordion state | Details sections |
| show_modal | boolean | Modal visibility | Modals |
| selected_tab | string | Tab navigation | Tabbed interfaces |
| sort_by | string | Current sort field | Tables |
| sort_ascending | boolean | Sort direction | Tables |
| hover_item | string | Item being hovered | Lists (for highlighting) |

---

## Variable Initialization (App Load)

**On app start, initialize these globally:**

```
AUTH_TOKEN = localStorage.get("auth_token")  // or null if not logged in
CURRENT_USER = API GET /current-user (if AUTH_TOKEN exists)
IS_ADMIN = CURRENT_USER?.role === "admin"
CURRENT_VIEW = URL.getQueryParam("view") || "dashboard"
API_BASE_URL = environment.API_BASE_URL
DATABASE_READY = API GET /health (check 200 response)
GO_LIVE_STATUS = API GET /api/go-live/status
NOTIFICATIONS = API GET /api/notifications (async, non-blocking)
```

---

## Notes

- **Global variables** persist across page navigations (within same app session)
- **Page-specific variables** reset/refresh when entering a new view
- **Local variables** are scoped to individual components and reset on unmount
- **AUTH_TOKEN** must be included in Authorization header for all authenticated endpoints
- **Variable naming** uses SCREAMING_SNAKE_CASE for clarity and consistency
- **Boolean flags** ending in `_LOADING` indicate pending async operations (show spinners)
- **Object variables** like `SELECTED_DEAL` can have nested properties accessed via dot notation

---

**Last Updated**: 2026-05-19
