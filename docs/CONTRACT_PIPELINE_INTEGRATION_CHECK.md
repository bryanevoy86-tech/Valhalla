# CONTRACT PIPELINE INTEGRATION CHECK - Sprint 2

**Status**: ✅ **READY FOR WIRING (Contracts 95% complete, needs deal/offer linking)**

---

## Current Contract Implementation State

### What's Complete
- ✅ Contract model exists: `services/api/app/models/contracts.py`
  - Fields: id, created_at, updated_at, deal_id, offer_id, status, template_id, content, pdf_url, signing_status, docusign_id
  - Note: deal_id and offer_id already in model (future-proof)
  
- ✅ Contract router: `services/api/app/routers/contracts_lifecycle.py`
  - Endpoints exist for contract management
  - Proven working (95% complete per previous assessment)

- ✅ Contract state machine: Contract lifecycle fully implemented
  - E-signature and audit trail present

### What Needs Wiring for Sprint 2

#### 1. Deal-Contract Linking
When a deal progresses to `contract_pending` stage:
- Verify contract router can create contract with `deal_id` 
- Verify contract router can create contract with `offer_id`
- Ensure contract inherits deal/offer properties (amount, terms, etc.)

**Action**: Check if contract router has endpoints like:
```
POST /api/contracts/for-deal/{deal_id}
POST /api/contracts/for-offer/{offer_id}
```

If not, add minimal endpoint:
```python
@router.post("/from-deal/{deal_id}", ...)
async def create_contract_from_deal(deal_id: int, ...):
    deal = get_deal(db, deal_id)
    # Create contract with deal_id FK
```

#### 2. Contract Status in Dashboard
Dashboard `/api/dashboard/pipeline` must include contract status:

```python
GET /api/dashboard/pipeline
Response:
[
  {
    "id": 1,
    "title": "123 Main St",
    "stage": "contract_pending",
    "contract_status": "draft",  # ← Must fetch from contracts table
    ...
  }
]
```

**Action**: Query contracts table when fetching deals, join on deal_id

#### 3. Contract Status Changes → Audit Trail
When contract status changes (draft → signed → executed), must log to audit_logs:

```python
# In contract service/router
INSERT INTO audit_logs (entity_type, entity_id, action, new_value)  
VALUES ('contract', {contract_id}, 'status_changed', '{"status": "signed"}')
```

**Action**: Add audit logging to contract status update endpoint

#### 4. Smoke Test Integration
Test contract creation in smoke flow:

```python
# In test_smoke_core_pipeline.py

# 1. Create deal (already working)
deal = create_deal(...)

# 2. Progress to contract_pending stage
update_deal_stage(deal, "contract_pending")

# 3. Create contract for deal (THIS STEP)
contract = create_contract(deal_id=deal.id)
assert contract.deal_id == deal.id

# 4. Verify contract appears in dashboard
dashboard = get_dashboard_pipeline()
deal_view = dashboard[0]
assert deal_view["contract_status"] == "draft"

# 5. Sign contract, verify audit trail
update_contract_status(contract, "signed")
audit_trail = get_deal_audit_trail(deal.id)
assert any(log["action"] == "status_changed" for log in audit_trail)
```

---

## Integration Checklist

- [ ] Contract model has deal_id FK constraint
- [ ] Contract model has offer_id FK constraint
- [ ] Contract router accepts deal_id in create endpoint
- [ ] Contract router accepts offer_id in create endpoint
- [ ] Contract status changes write audit log entries
- [ ] Dashboard pipeline fetch includes contract_status
- [ ] Smoke test covers: create deal → create contract → check dashboard

---

## Estimated Effort

**Discovery**: 10 minutes (find contract router, verify FK fields)  
**Wiring**: 20 minutes (add audit logging, fix FK constraints if needed)  
**Testing**: 15 minutes (run smoke test subset)

**Total**: ~45 minutes

---

## Handoff Notes

Contracts are the strongest entity in the system. They don't need rebuilding.
Just ensure:
1. New Deal/Offer tables can be linked via FK (already designed in db_bootstrap schema)
2. Audit trail captures status changes (add logging if missing)
3. Dashboard can query contracts by deal_id (simple join query)

No major refactoring needed—just plumbing between layers.
