# MULTI-DEAL SEED MAP

**Created**: 2026-03-27

## Seeded Canonical Deals

All deals seeded in realistic states to test operator workflows across multiple states and conditions.

| Deal | ID | State | Lead | Title | ARV | Repairs | Offer | Contract | Buyer Match | Test Purpose |
|------|-----|-------|-------|---------|-----------|---------|--------|----------|----------|---|
| A | 10 | draft | 1 | Minimal Draft | $250k | ✗ | ✗ | ✗ | ✗ | Minimal data blocker |
| B | 11 | lead_received | 102 | Analysis Ready | $350k | $50k | ✗ | ✗ | ✗ | Full data but no offer |
| C | 12 | offer_presented | 103 | Offer State | $425k | $75k | ✓ | ✗ | ✗ | Has live offer |
| D | 13 | under_contract | 104 | Contract State | $520k | $120k | ✓ | ✓ | ✗ | Full contract flow |
| E | 14 | lead_received | 105 | Blocked Problem | $300k | ✗ | ✗ | ✗ | ✗ | Missing repairs (blocker) |

## Verification Scenarios

### Deal A — Minimal Data
- **Purpose**: Test dashboard/Heimdall with incomplete deal
- **Expected Behavior**: 
  - Heimdall should identify missing repairs as blocker
  - Cannot advance without repairs data
  - No false advancement

### Deal B — Analysis Ready
- **Purpose**: Test Heimdall across complete base data
- **Expected Behavior**:
  - Heimdall should analyze without errors
  - Identify valid next stages
  - Support advancement if allowed by rules

### Deal C — Offer State
- **Purpose**: Test offer relationship integrity
- **Expected Behavior**:
  - Dashboard shows offer exists
  - Audit can track offer state changes
  - Contract prerequisite validations work

### Deal D — Under Contract
- **Purpose**: Test full offer→contract flow
- **Expected Behavior**:
  - Relationships: 1 offer + 1 contract linked correctly
  - Audit shows both documents exist
  - Dashboard reflects contract state

### Deal E — Blocked Problem
- **Purpose**: Test rejection handling
- **Expected Behavior**:
  - Heimdall correctly identifies blocker (missing repairs)
  - Advancement rejected cleanly
  - Override path available if needed

## Database State

All deals persisted to: `valhalla_local.db`

### Tables Affected
- `leads` - 5 records (IDs: 1, 102-105)
- `deals` - 6 records (IDs: 1, 10-14)
- `offers` - 2 records (linked to deals 12, 13)
- `contracts` - 1 record (linked to deal 13)
- `audit_logs` - Events recorded per action

## Known Issues (To Hardening Pass)

1. **Dashboard Query Issue**
   - Not showing newly seeded deals 10-14
   - May be filtering by stage or status incorrectly
   - Needs verification: `GET /api/dashboard/pipeline` query logic

2. **Heimdall Stage Mapping**
   - Returns `current_stage: "active"` instead of actual deal.stage value
   - Affects stage transition recommendations
   - Needs verification: `POST /api/heimdall/deals/{deal_id}/analyze` stage reading

3. **Lead Foreign Key Mismatch**
   - Database schema uses `lead_name`, `lead_email` not `name`, `email`
   - Lead model in ORM doesn't match seed table
   - Seeded using raw SQL to bypass model mismatch

## Next Actions

1. Fix Heimdall stage reading (critical for advancement logic)
2. Fix dashboard querying (blocks operator visibility)
3. Verify audit completeness across all actions
4. Test advancement success path (all rejection shown, need success)
