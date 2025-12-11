# PACK AD, AE, AF Quick Reference

## PACK AD — SaaS Access Engine

### Create a Plan with Modules
```bash
curl -X POST http://localhost:8000/saas/plans \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VALHALLA_PRO",
    "name": "Valhalla Pro",
    "price_monthly": 97.0,
    "price_yearly": 970.0,
    "modules": [
      {"module_key": "wholesale_engine"},
      {"module_key": "dispo_engine"}
    ]
  }'
```

### List All Plans
```bash
curl http://localhost:8000/saas/plans
```

### Create a Subscription
```bash
curl -X POST http://localhost:8000/saas/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 42,
    "plan_id": 1,
    "provider": "stripe",
    "provider_sub_id": "sub_abc123"
  }'
```

### Check User Module Access
```bash
curl "http://localhost:8000/saas/access-check?user_id=42&module_key=wholesale_engine"
```

### Update Subscription Status
```bash
curl -X PATCH http://localhost:8000/saas/subscriptions/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'
```

### Database Schema

**saas_plans**
```
id (PK)
code (UNIQUE)
name
description
price_monthly
price_yearly
currency (default: USD)
is_active
created_at
```

**saas_plan_modules**
```
id (PK)
plan_id (FK → saas_plans.id, CASCADE)
module_key
```

**subscriptions**
```
id (PK)
user_id
plan_id (FK → saas_plans.id)
status (active | cancelled | past_due)
provider
provider_sub_id
started_at
cancelled_at (auto-set when status = cancelled)
```

---

## PACK AE — Public Investor Module

### Create/Get Investor Profile
```bash
curl -X POST http://localhost:8000/investor/profile \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "full_name": "John Investor",
    "email": "john@example.com",
    "is_accredited": true,
    "country": "USA",
    "strategy_preference": "growth",
    "risk_tolerance": "moderate"
  }'
```

### Get Profile by User ID
```bash
curl http://localhost:8000/investor/profile/1
```

### Update Profile
```bash
curl -X PATCH http://localhost:8000/investor/profile/1 \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_preference": "income",
    "risk_tolerance": "conservative"
  }'
```

### Create Project Summary
```bash
curl -X POST http://localhost:8000/investor/projects \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "bahamas-resort-1",
    "title": "Bahamas Resort #1",
    "region": "Bahamas",
    "description": "High-end resort development",
    "status": "research"
  }'
```

### List All Projects
```bash
curl http://localhost:8000/investor/projects
```

### Filter Projects by Status
```bash
curl "http://localhost:8000/investor/projects?status=open"
```

### Get Project by Slug
```bash
curl http://localhost:8000/investor/projects/bahamas-resort-1
```

### Update Project
```bash
curl -X PATCH http://localhost:8000/investor/projects/bahamas-resort-1 \
  -H "Content-Type: application/json" \
  -d '{"status": "open"}'
```

### Database Schema

**investor_profiles**
```
id (PK)
user_id (UNIQUE)
full_name
email
is_accredited (default: False)
country
strategy_preference (income | growth | mixed)
risk_tolerance (conservative | moderate | higher)
notes
created_at
updated_at
```

**investor_project_summaries**
```
id (PK)
slug (UNIQUE)
title
region
description
status (research | open | closed, default: research)
notes
created_at
```

---

## PACK AF — Unified Empire Dashboard

### Get Empire Dashboard
```bash
curl http://localhost:8000/dashboard/empire
```

### Response Example
```json
{
  "system": {
    "version": "1.0.0",
    "backend_complete": true
  },
  "holdings": {
    "count": 42,
    "total_estimated_value": 8500000.0
  },
  "pipelines": {
    "wholesale_total": 156,
    "wholesale_active": 23,
    "dispo_assignments": 18
  },
  "risk_governance": {
    "open_audit_events": 3,
    "governance_decisions": 127
  },
  "education": {
    "enrollments_total": 450
  },
  "children": {
    "hubs_total": 2
  }
}
```

---

## Testing

### Run PACK AD Tests
```bash
pytest app/tests/test_saas_access.py -v
pytest app/tests/test_saas_access.py::test_create_saas_plan -v
pytest app/tests/test_saas_access.py -v --tb=short
```

### Run PACK AE Tests
```bash
pytest app/tests/test_investor_module.py -v
```

### Run PACK AF Tests
```bash
pytest app/tests/test_empire_dashboard.py -v
```

### Run All New Tests
```bash
pytest app/tests/test_saas_access.py app/tests/test_investor_module.py app/tests/test_empire_dashboard.py -v
```

### Run Full Test Suite
```bash
pytest app/tests/ -v
```

---

## Stripe Integration (PACK AD)

For production Stripe integration:

1. **Create a subscription event handler**
   ```python
   # Listen for charge.succeeded, customer.subscription.created events
   @app.post("/webhooks/stripe")
   def handle_stripe_webhook(request: Request):
       # Verify Stripe signature
       # Parse event
       # Call create_subscription or update_subscription
       # Return 200 OK
   ```

2. **Link user_id to Stripe customer_id**
   - Add customer_id field to Subscription model
   - Use to retrieve subscription status from Stripe

3. **Sync subscriptions periodically**
   - Celery task to check Stripe API
   - Update local subscription records

---

## Access Control Checks

Use `user_has_access()` in other endpoints:

```python
from app.services.saas_access import user_has_access

@app.get("/wholesale/leads")
def get_leads(user_id: int, db: Session = Depends(get_db)):
    # Check access
    has_access, plan_code = user_has_access(db, user_id, "wholesale_engine")
    if not has_access:
        raise HTTPException(status_code=403, detail="Upgrade to access wholesale features")
    
    # Serve leads...
    return db.query(Lead).all()
```

---

## Key Design Decisions

### PACK AD
- Plan modules as separate table for flexibility (add/remove without migration)
- Subscription status in string enum (not separate table) for simplicity
- Auto-set `cancelled_at` on status change for audit trail
- User access check returns both boolean and plan code for logging

### PACK AE
- No foreign keys to other entities (privacy, flexibility)
- Slug as unique identifier for projects (URL-friendly)
- Profile creation is idempotent (returns existing if user_id already exists)
- Status enumeration in code, not database (future enhancement: separate table)

### PACK AF
- All imports wrapped in try/except for graceful degradation
- Read-only (no POST/PATCH, only GET)
- Aggregates from existing models (no custom tables)
- Returns zeros if models don't exist (no cascade failures)

---

## Error Handling

### PACK AD
- 404 if plan not found
- 404 if subscription not found

### PACK AE
- 200 with null if profile doesn't exist (not 404)
- 404 if project slug not found
- 404 if trying to update non-existent project

### PACK AF
- Always returns 200 (graceful degradation)
- Missing models return 0 counts
- No error responses

---

## Valhalla Endpoint Summary

**32 Packs → 220+ Endpoints**

| Pack | Endpoints |
|------|-----------|
| A-G (Foundation) | ~40 |
| H-R (Professional) | ~60 |
| S-W (Infrastructure) | ~50 |
| X-Z (Enterprise) | ~40 |
| AA-AC (Content) | ~24 |
| AD-AF (SaaS/Dashboard) | **16** |
| **TOTAL** | **220+** |

**Status: Ready for database migrations and deployment**
