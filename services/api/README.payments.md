# Pack 27: Billing & Payment Integration

## Overview
Track user payments with simple creation and retrieval endpoints. Payments are associated with user profiles via `user_id` foreign key and store amount, status, and timestamps.

## Models (`app/payments/models.py`)
- **Payment**: id, user_id (FK→user_profiles.user_id), amount (Decimal), status (String, default='pending'), created_at, updated_at

## Schemas (`app/payments/schemas.py`)
- **PaymentCreate**: user_id, amount
- **PaymentOut**: id, user_id, amount, status, created_at, updated_at

## Service (`app/payments/service.py`)
- `create_payment(db, payment: PaymentCreate) -> Payment`
- `get_payment_by_user(db, user_id: int) -> list[Payment]`

## Endpoints (`/api/payments`)
- `POST /` — Create a new payment
  - Request body: `{"user_id": 1, "amount": 49.99}`
  - Returns: `PaymentOut`
- `GET /user/{user_id}` — Retrieve all payments for a user
  - Returns: `List[PaymentOut]`

## Dashboard UI
- **Route**: `/api/ui-dashboard/payments-dashboard-ui`
- **Template**: `payments_dashboard.html`
- **Features**:
  - Create new payments
  - List payments by user ID
  - Displays payment amount, status, and creation timestamp

## Example Usage (PowerShell)
```powershell
# Create payment
$API = "http://localhost:8000"
$body = @{user_id=1; amount=49.99} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$API/api/payments/" -Body $body -ContentType "application/json"

# Get user payments
Invoke-RestMethod -Method Get -Uri "$API/api/payments/user/1"

# Open dashboard
start "$API/api/ui-dashboard/payments-dashboard-ui"
```

## Dependencies
- SQLAlchemy 2.x
- Foreign key: `user_profiles.user_id` (from Pack 24)

## Wiring
- Router guarded import in `services/api/main.py` with availability flag in `/debug/routes`.
