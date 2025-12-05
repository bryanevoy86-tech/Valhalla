# FunFunds Personal Finance Planner

A stateless monthly budgeting calculator that allocates income across five categories: bills, safety reserve, play money (FunFunds), debt paydown, and reinvestment.

## Features

- **Stateless calculation** - No database changes, pure computation
- **Decimal precision** - ROUND_HALF_UP for accurate money calculations
- **Proportional scaling** - Automatically adjusts when requested allocations exceed available funds
- **Policy flags** - Warns when safety minimums are breached
- **Preset modes** - Quick access to lean (conservative) and growth (aggressive) budgeting

## Endpoints

### Main Planner

**POST** `/api/flow/funfunds_plan`

Full control over all percentage dials.

```json
{
  "month_label": "2025-01",
  "gross_income": 20000,
  "fixed_bills": [
    {"name": "Rent", "amount": 1800, "category": "housing"},
    {"name": "Utilities", "amount": 300, "category": "utilities"}
  ],
  "min_safety_reserve_percent": 0.10,
  "funfunds_percent": 0.15,
  "debt_paydown_percent": 0.15,
  "reinvest_percent": 0.40
}
```

**Response:**
```json
{
  "month_label": "2025-01",
  "gross_income": 20000,
  "bills_total": 2100,
  "net_after_bills": 17900,
  "allocation": {
    "bills_total": 2100,
    "safety_reserve": 1790,
    "funfunds_amount": 2685,
    "debt_paydown_amount": 2685,
    "reinvest_amount": 7160,
    "leftover_amount": 1580
  },
  "policy_flags": {
    "breach_safety_minimum": false,
    "notes": null
  },
  "debug": {
    "mode": "custom",
    "gross_income": "20000",
    "bills_total": "2100",
    "net_after_bills": "17900",
    "min_safety_reserve_percent": "0.10",
    "funfunds_percent": "0.15",
    "debt_paydown_percent": "0.15",
    "reinvest_percent": "0.40"
  }
}
```

### Lean Preset

**POST** `/api/flow/funfunds_plan/lean`

Conservative budgeting (safety + debt priority):
- **20%** safety reserve
- **10%** FunFunds
- **30%** debt paydown
- **30%** reinvestment

```json
{
  "month_label": "2025-01",
  "gross_income": 10000,
  "fixed_bills": [
    {"name": "Rent", "amount": 2000, "category": "housing"}
  ]
}
```

### Growth Preset

**POST** `/api/flow/funfunds_plan/growth`

Aggressive budgeting (machine + play priority):
- **10%** safety reserve
- **20%** FunFunds
- **15%** debt paydown
- **45%** reinvestment

```json
{
  "month_label": "2025-01",
  "gross_income": 10000,
  "fixed_bills": [
    {"name": "Rent", "amount": 2000, "category": "housing"}
  ]
}
```

## Algorithm

1. **Calculate bills total** - Sum all fixed monthly bills
2. **Calculate net after bills** - `gross_income - bills_total`
3. **Protect safety reserve** - `net_after_bills × min_safety_reserve_percent`
4. **Calculate available for dials** - `net_after_bills - safety_reserve`
5. **Apply percentage dials** - Calculate raw amounts for FunFunds, debt, reinvest
6. **Proportional scaling** - If requested > available, scale down proportionally
7. **Handle leftover** - Remaining funds after rounding corrections

### Edge Cases

- **Zero/negative net after bills** → All allocations set to zero, breach flag raised
- **Over-allocation** → Proportional scaling applied to fit within available funds
- **Rounding corrections** → Leftover amount captures rounding differences

## Testing

Run the full test suite:

```powershell
python -m pytest tests/test_flow_funfunds_planner.py tests/test_flow_funfunds_presets.py -v
```

**Test Coverage:**
- ✅ Basic allocation with positive leftover
- ✅ Zero/negative income breach handling
- ✅ Over-allocation proportional scaling
- ✅ Lean preset percentage verification
- ✅ Growth preset percentage verification
- ✅ Preset over-allocation handling

## Files

**Schemas:**
- `services/api/app/schemas/funfunds_planner.py` - Pydantic models (122 lines)

**Routers:**
- `services/api/app/routers/flow_funfunds_planner.py` - Main planner (157 lines)
- `services/api/app/routers/flow_funfunds_presets.py` - Lean/growth presets (133 lines)

**Tests:**
- `services/api/tests/test_flow_funfunds_planner.py` - Main planner tests (122 lines, 3 tests)
- `services/api/tests/test_flow_funfunds_presets.py` - Preset tests (141 lines, 3 tests)

**Router Registration:**
- `services/api/app/main.py` - Both routers registered at lines 217-231

## Philosophy

FunFunds follows the Valhalla principle of **capital allocation discipline**:

- **Bills** (survival) - Non-negotiable fixed costs
- **Safety** (buffer) - Protection against volatility
- **FunFunds** (play) - Fuel for creativity and quality of life
- **Debt** (freedom) - Path to independence
- **Reinvest** (machine) - Growth engine

The tool is **stateless** by design - it calculates what *should* happen, not what *did* happen. For tracking actual vs budget, persist the plan outputs to your database separately.

## Future Enhancements

- [ ] Additional preset modes (balanced, emergency, retirement)
- [ ] Historical tracking (budget vs actual)
- [ ] Database persistence layer
- [ ] Multi-month planning
- [ ] Goal-based allocation (save for X by date Y)
- [ ] Integration with actual transaction data
