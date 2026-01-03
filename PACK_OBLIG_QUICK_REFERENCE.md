# Obligations Registry — Quick Reference

**5-Minute Getting Started Guide**

---

## What Is It?

The Obligations Registry tracks recurring payments (bills, subscriptions, etc.), calculates when they're due, and determines if you have enough cash reserve to cover them.

**3 Packs:**
- **PACK 1:** Create/manage obligations
- **PACK 2:** Generate upcoming payment schedule
- **PACK 3:** Calculate required cash reserve and check coverage

---

## Installation

Already installed at: `backend/app/core_gov/obligations/`

Endpoints available at: `GET/POST /core/obligations/*`

---

## Quick Start: 5 Steps

### Step 1: Create an Obligation
```bash
curl -X POST http://localhost:8000/core/obligations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rent",
    "amount": 1500,
    "currency": "CAD",
    "frequency": "monthly",
    "due_day": 1,
    "category": "housing",
    "priority": "A"
  }'
```

**Response includes:** obligation ID (e.g., `ob_6038e7c40571`)

### Step 2: Get Upcoming 30 Days
```bash
curl http://localhost:8000/core/obligations/upcoming_30
```

**Shows:** All scheduled payments for next 30 days

### Step 3: Verify Autopay (Optional)
```bash
curl -X POST http://localhost:8000/core/obligations/{ID}/verify_autopay \
  -H "Content-Type: application/json" \
  -d '{
    "verified": true,
    "method": "bank_autopay",
    "payee": "LANDLORD INC",
    "reference": "UNIT 12"
  }'
```

### Step 4: Check Coverage
```bash
curl http://localhost:8000/core/obligations/status
```

**Shows:**
- Monthly required amount
- Buffer required (with 1.25x multiplier)
- Coverage: Yes or No

### Step 5: Get Setup Guide
```bash
curl http://localhost:8000/core/obligations/{ID}/autopay_guide
```

**Shows:** 8-step instructions to set up autopay in your bank

---

## Supported Frequencies

| Frequency | Example | Calculation |
|-----------|---------|-------------|
| `weekly` | Every Monday | Repeats every 7 days |
| `biweekly` | Every 2 weeks | Repeats every 14 days |
| `monthly` | 1st of month | Repeats monthly on same day |
| `quarterly` | Every 3 months | Repeats every quarter |
| `annually` | January 15 | Repeats every year |

---

## Data Model at a Glance

### Obligation
```json
{
  "id": "ob_xxxxx",
  "name": "Rent",
  "amount": 1500,
  "frequency": "monthly",
  "due_day": 1,
  "category": "housing",
  "priority": "A",
  "status": "active",
  "autopay": {
    "enabled": true,
    "verified": true,
    "method": "bank_autopay"
  }
}
```

### Reserve State
```json
{
  "monthly_required": 1500,
  "buffer_required": 1875,         // 1500 × 1.25
  "coverage": {
    "available_cash": 2500,
    "covered": true                 // 2500 >= 1875
  }
}
```

---

## Common Tasks

### Task: Add Multiple Bills
```bash
# Rent
curl -X POST http://localhost:8000/core/obligations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rent",
    "amount": 1500,
    "currency": "CAD",
    "frequency": "monthly",
    "due_day": 1,
    "category": "housing"
  }'

# Internet
curl -X POST http://localhost:8000/core/obligations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Internet",
    "amount": 79.99,
    "currency": "CAD",
    "frequency": "monthly",
    "due_day": 15,
    "category": "utilities"
  }'

# Gym (quarterly)
curl -X POST http://localhost:8000/core/obligations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gym",
    "amount": 120,
    "currency": "CAD",
    "frequency": "quarterly",
    "due_day": 1,
    "category": "subscriptions"
  }'
```

### Task: List All Active Bills
```bash
curl "http://localhost:8000/core/obligations?status=active"
```

### Task: Pause an Obligation
```bash
curl -X PATCH http://localhost:8000/core/obligations/ob_xxxxx \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'
```

### Task: Update Amount (e.g., Rent Increase)
```bash
curl -X PATCH http://localhost:8000/core/obligations/ob_xxxxx \
  -H "Content-Type: application/json" \
  -d '{"amount": 1600}'
```

### Task: Check Next 60 Days
```bash
curl -X POST "http://localhost:8000/core/obligations/runs/generate?start_date=2026-01-02&end_date=2026-03-02"
```

### Task: Use Conservative Buffer (2x)
```bash
curl "http://localhost:8000/core/obligations/status?buffer_multiplier=2.0"
```

---

## Key Concepts

### Buffer Multiplier
- **Default:** 1.25x (25% safety margin)
- **Conservative:** 2.0x (100% safety margin)
- **Formula:** `buffer_required = monthly_required × multiplier`

### Monthly Equivalent
- Weekly is converted: × 52/12 ≈ 4.33 months
- Biweekly: × 26/12 ≈ 2.17 months
- Quarterly: ÷ 3
- Annually: ÷ 12

### Coverage Check
- Looks for available cash in capital module
- If not found, note says "capital module required"
- Best-effort integration (doesn't fail if unavailable)

### Edge Cases Handled
- 31st in months with 30 days → Moves to 30th
- Feb 30th → Moves to 28th (or 29th in leap year)
- Timezone-aware calculations (default: America/Toronto)

---

## Autopay Methods

| Method | Description |
|--------|-------------|
| `bank_autopay` | Set up in your bank's online portal |
| `credit_card` | Automatic monthly/periodic charge |
| `e_transfer` | Scheduled e-transfer payment |
| `manual` | Manual reminder (no autopay) |

**Setup Guide:** Use endpoint `/core/obligations/{id}/autopay_guide` for step-by-step instructions.

---

## Data Persistence

All data stored as JSON:
- `backend/data/obligations/obligations.json` - Your bills
- `backend/data/obligations/runs.json` - Scheduled payments
- `backend/data/obligations/reserves.json` - Reserve calculations

Auto-created on first use. Atomic writes prevent corruption.

---

## Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Validation error (check your input) |
| `404` | Not found (check ID) |
| `500` | Server error (check logs) |

---

## Troubleshooting

### "Obligation not found"
- Check obligation ID is correct
- Use `GET /core/obligations` to list all

### "Validation error: amount must be >= 0"
- Amount must be positive (> 0)

### "Coverage requires capital module"
- This is a note, not an error
- Coverage check attempted but capital module unavailable
- You can still see monthly_required and buffer_required

### "Invalid due_day"
- Must be 1-31
- 31st works but auto-adjusts for shorter months

---

## Performance Notes

- Max 120 runs generated per request (prevents timeout)
- Max 500 runs returned per list request
- Recalculate reserves periodically (e.g., daily)
- Autopay verification is manual (secure by design)

---

## API Endpoints Cheat Sheet

### Create/Read/Update (PACK 1)
```
POST   /core/obligations                    Create
GET    /core/obligations                    List all
GET    /core/obligations/{id}               Get one
PATCH  /core/obligations/{id}               Update
POST   /core/obligations/{id}/verify_autopay Verify autopay
```

### Schedule Generation (PACK 2)
```
POST   /core/obligations/runs/generate      Generate runs
GET    /core/obligations/runs               List runs
GET    /core/obligations/upcoming_30        Next 30 days
```

### Coverage & Reserves (PACK 3)
```
POST   /core/obligations/reserves/recalculate Recalculate
GET    /core/obligations/reserves           Get state
GET    /core/obligations/status             Status summary
GET    /core/obligations/{id}/autopay_guide Setup guide
```

---

## Example Response: Full Obligation

```json
{
  "id": "ob_6038e7c40571",
  "name": "Rent",
  "amount": 1500.0,
  "currency": "CAD",
  "frequency": "monthly",
  "due_day": 1,
  "category": "housing",
  "priority": "A",
  "status": "active",
  "pay_from": "personal",
  "autopay": {
    "enabled": true,
    "verified": true,
    "method": "bank_autopay",
    "payee": "LANDLORD INC",
    "reference": "UNIT 12",
    "notes": "Set up through TD online"
  },
  "recurrence": {
    "frequency": "monthly",
    "interval": 1,
    "day_of_month": 1,
    "day_of_week": null,
    "start_date": "2026-01-02",
    "next_due_date": "2026-02-01",
    "timezone": "America/Toronto"
  },
  "tags": ["essential", "housing"],
  "meta": {
    "landlord_contact": "john@example.com",
    "lease_end": "2027-01-01"
  },
  "created_at": "2026-01-02T14:30:45Z",
  "updated_at": "2026-01-02T14:30:45Z"
}
```

---

## Next Steps

1. **Create 3-5 obligations** covering your main expenses
2. **Enable autopay** for recurring bills
3. **Check coverage** with `GET /core/obligations/status`
4. **Generate 30-day** schedule with `GET /core/obligations/upcoming_30`
5. **Monitor** with dashboard integration

---

**Documentation:** See [PACK_OBLIG_API_REFERENCE.md](PACK_OBLIG_API_REFERENCE.md) for full API details

**Implementation:** See [PACK_OBLIG_1_2_3_IMPLEMENTATION.md](PACK_OBLIG_1_2_3_IMPLEMENTATION.md) for technical details
