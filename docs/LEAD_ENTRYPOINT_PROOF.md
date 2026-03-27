# STEP 1: LEAD ENTRYPOINT PROOF

## Canonical Lead Entry Path

### Route & Method
- **Endpoint:** `POST /api/leads`
- **Method:** POST
- **Authentication:** X-API-Key header (any value accepted in test mode)
- **Status Code:** 201 (Created)

### Request Schema (LeadCreate)
```json
{
  "lead_name": "string (required, 1-255 chars)",
  "lead_email": "string (required, valid email)",
  "lead_phone": "string (required, 1-20 chars)",
  "property_address": "string (optional, 0-512 chars)",
  "property_city": "string (optional, 0-255 chars)",
  "property_state": "string (optional, 0-2 chars, e.g., 'CO')",
  "property_zip": "string (optional, 0-10 chars)",
  "estimated_arv": "decimal (optional, >= 0)",
  "source": "string (required, 1-255 chars, e.g., 'Zillow', 'MLS', 'direct_api')",
  "lead_status": "string (optional, default='new', 0-50 chars)",
  "notes": "string (optional)"
}
```

### Response Schema (LeadOut)
```json
{
  "id": "integer (generated)",
  "lead_name": "string",
  "lead_email": "string",
  "lead_phone": "string",
  "property_address": "string | null",
  "property_city": "string | null",
  "property_state": "string | null",
  "property_zip": "string | null",
  "estimated_arv": "decimal | null",
  "lead_status": "string",
  "source": "string",
  "notes": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Database Persistence

**Table:** `valhalla_local.db.leads`

**Schema (verified):**
```
id                  INTEGER PRIMARY KEY
lead_name           VARCHAR(255) NOT NULL
lead_email          VARCHAR(255) NOT NULL (indexed)
lead_phone          VARCHAR(20) NOT NULL
property_address    VARCHAR(512)
property_city       VARCHAR(255)
property_state      VARCHAR(2)
property_zip        VARCHAR(10)
estimated_arv       DECIMAL(15, 2)
lead_status         VARCHAR(50) NOT NULL (default: 'new')
source              VARCHAR(255) NOT NULL
notes               TEXT
created_at          DATETIME NOT NULL
updated_at          DATETIME NOT NULL
```

### Code Location

- **Router:** `d:\dev\services\api\app\leads\router.py`
- **Service:** `d:\dev\services\api\app\leads\service.py`
- **Models:** `d:\dev\services\api\app\leads\models.py`
- **Schemas:** `d:\dev\services\api\app\leads\schemas.py`

### System Status

✅ **LIVE AND WORKING**

The lead creation endpoint is fully operational. No fixes required.

### Field Mapping

Lead intake supports full contact + property information capture:

| Lead Field | Type | Status | Notes |
|-----------|------|--------|-------|
| lead_name | string | ✅ Required | Seller/contact name |
| lead_email | string | ✅ Required | Seller/contact email (validated) |
| lead_phone | string | ✅ Required | Seller/contact phone |
| property_address | string | ⚠️ Optional | Property street address |
| property_city | string | ⚠️ Optional | Property city |
| property_state | string | ⚠️ Optional | State code (CO, TX, etc) |
| property_zip | string | ⚠️ Optional | Postal code |
| estimated_arv | decimal | ⚠️ Optional | After-repair value for valuation |
| source | string | ✅ Required | Lead source (Zillow, MLS, API, direct) |
| lead_status | string | ⚠️ Optional | Status (default: new) |
| notes | string | ⚠️ Optional | Additional notes |

### Decision

The canonical lead entry path is **`POST /api/leads`** with the schema documented above.
This is the only supported way to create leads through the REST API.
All required fields are validated at intake.
Persistence lands directly in the `leads` table.
No repairs or changes needed - this is the correct canonical path.

---

**Status:** ✅ CANONICAL PATH VERIFIED
**Date:** March 27, 2026
