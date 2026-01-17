# Pack 31: Advanced Lead Scraper

## Overview
Automate the process of collecting, storing, and qualifying leads. Track lead status through the sales pipeline from initial contact to qualification. Includes filtering, status updates, and comprehensive lead management.

## Models (`app/leads/models.py`)
- **Lead**: id, name, email (indexed), phone, status, source, created_at, updated_at
  - **Status values**: `new`, `contacted`, `qualified`, `disqualified`
  - **Source examples**: Facebook, LinkedIn, Referral, Website, Cold Outreach

## Schemas (`app/leads/schemas.py`)
- **LeadCreate**: name, email (validated), phone, source, status (optional, default='new')
- **LeadOut**: id, name, email, phone, status, source, created_at, updated_at
- **LeadStatusUpdate**: status (required field for status updates)

## Service (`app/leads/service.py`)
- `create_lead(db, lead: LeadCreate) -> Lead`
- `get_all_leads(db, skip: int = 0, limit: int = 100) -> list[Lead]` — with pagination
- `get_lead_by_id(db, lead_id: int) -> Lead | None`
- `get_leads_by_status(db, status: str) -> list[Lead]` — filter by qualification status
- `update_lead_status(db, lead_id: int, status: str) -> Lead | None`
- `delete_lead(db, lead_id: int) -> bool`

## Endpoints (`/api/leads`)

### Create Lead
```
POST /
Body: {
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0100",
  "source": "LinkedIn",
  "status": "new"
}
Response: LeadOut (201 Created)
```

### List Leads (with filtering & pagination)
```
GET /?skip=0&limit=100&status=qualified
Response: List[LeadOut]
```

### Get Specific Lead
```
GET /{lead_id}
Response: LeadOut or 404
```

### Update Lead Status
```
PUT /{lead_id}/status
Body: {"status": "qualified"}
Response: LeadOut or 404
```

### Delete Lead
```
DELETE /{lead_id}
Response: 204 No Content or 404
```

## Dashboard UI
- **Route**: `/api/ui-dashboard/leads-dashboard-ui`
- **Template**: `leads_dashboard.html`
- **Features**:
  - Create new leads with all required fields
  - Filter leads by status (new, contacted, qualified, disqualified)
  - View all leads in a sortable table with color-coded status badges
  - Update lead status with one-click actions
  - Auto-refresh on create/update

## Example Usage (PowerShell)
```powershell
$API = "http://localhost:8000"

# Create lead
$lead = @{
  name="Jane Smith"
  email="jane@startup.io"
  phone="+1-555-0200"
  source="Facebook Ads"
  status="new"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/leads/" -Body $lead -ContentType "application/json"

# List all qualified leads
Invoke-RestMethod -Method Get -Uri "$API/api/leads/?status=qualified"

# Update lead status
$update = @{status="contacted"} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri "$API/api/leads/1/status" -Body $update -ContentType "application/json"

# Get lead by ID
Invoke-RestMethod -Method Get -Uri "$API/api/leads/1"

# Delete lead
Invoke-RestMethod -Method Delete -Uri "$API/api/leads/1"

# Open dashboard
start "$API/api/ui-dashboard/leads-dashboard-ui"
```

## Use Cases
- **Sales Pipeline Management**: Track leads from first contact to qualification
- **Lead Source Analysis**: Identify which channels generate highest-quality leads
- **Automated Lead Scoring**: Integrate with Pack 32 to automatically qualify leads based on engagement
- **CRM Integration**: Export qualified leads to external CRM systems
- **Marketing Attribution**: Track conversion rates by source

## Integration Points
- **Pack 26 (Messaging)**: Send automated follow-up emails/SMS to new leads
- **Pack 32 (Advanced Negotiation)**: Apply negotiation techniques when contacting leads
- **Pack 24 (User Profiles)**: Link leads to user accounts upon conversion
- **Future AI Scraping**: Auto-populate lead data from social media profiles

## Dependencies
- SQLAlchemy 2.x
- Pydantic email validation
- No foreign keys; standalone lead tracking

## Wiring
- Router guarded import in `services/api/main.py` with `leads_available` flag in `/debug/routes`.

## Future Enhancements
- Lead scoring based on engagement metrics
- Duplicate detection (fuzzy matching on email/phone)
- Integration with LinkedIn/Facebook APIs for automated scraping
- Lead nurturing workflows (drip campaigns)
- Custom fields and tags
- Bulk import from CSV
