# MILLION-PATH: Existing Route Inventory & Mapping

**Status:** AUDIT & MAPPING  
**Purpose:** Document all existing routes and their relevance to million-path scaling  
**Timeline:** Reference only (no changes to routes)  
**Last Updated:** 2026-04-13  

---

## OVERVIEW

The backend has a massive route inventory accumulated over time. This document categorizes which routes are:
- **LAUNCH-ESSENTIAL:** Must work perfectly for day-one
- **ALREADY USEFUL:** Ready to use post-launch without changes
- **USEFUL LATER:** Good foundation for future scaling
- **NOISY/ARCHIVE:** Not relevant to million-path focus

---

## SECTION 1: EXECUTION ROUTES - LAUNCH ESSENTIAL ✅

These routes are **LIVE NOW** and form the day-one foundation.

### Execution Intake & Processing
```
POST /execution/intake                        LIVE ✅  Launch Essential
POST /execution/intake/{intake_id}/process    LIVE ✅  Launch Essential
GET  /execution/cases                         LIVE ✅  Already Useful (list all)
GET  /execution/cases/{case_id}               LIVE ✅  Launch Essential
GET  /execution/cases/{case_id}/tasks         LIVE ✅  Launch Essential
GET  /execution/cases/{case_id}/next-action   LIVE ✅  Launch Essential
POST /execution/cases/{case_id}/advance       STUBBED   Need to Verify
GET  /execution/cases/{case_id}/events        LIVE ✅  Already Useful
```

**Status:** Core execution layer.  
**WeWeb Dependency:** All 7 routes must be tested before WeWeb first build.  
**Data Flow Diagram:**
```
User Types Opportunity → POST /intake
                            ↓
                     Record Created
                            ↓
                   User Clicks Process → POST /process
                            ↓
                     System Analyzes
                            ↓
                   GET /cases/{id} View Results
                            ↓
                   GET /cases/{id}/tasks See To-Do List
                            ↓
                   User Completes Tasks
                            ↓
               POST /cases/{id}/advance → Next Stage
```

---

## SECTION 2: BUYER/MATCHING ROUTES - ALREADY USEFUL (Partial)

These routes support wholesale buyer matching and deployment strategies.

### Buyer Discovery & Matching
```
GET  /buyer                                   EXISTS    Already Useful
GET  /buyer/{buyer_id}                        EXISTS    Already Useful
POST /buyer                                   EXISTS    Later (buyer registration)
GET  /buyers                                  EXISTS    Already Useful
POST /buyer_match                             STUBBED   Useful Later
GET  /buyer_profile                           EXISTS    Useful Later
```

**Status:** Buyer registry exists but matching logic to wholesale deals not wired yet.  
**Post-Launch Use Case:** After closing wholesale deal, POST /buyer_match to find buyer.  
**Not Required Day-One:** But useful in week 2.

**Sample Workflow (Later):**
```
User closed deal for $250k, want $290k wholesaler markup
→ POST /buyer_match {"purchase_price": 250000, "target_price": 290000}
← API returns list of registered wholesale buyers matching criteria
→ User selects buyer and initiates transaction
```

---

## SECTION 3: PORTFOLIO & HOLDINGS - ALREADY USEFUL

These routes track properties we own or are financing.

### Portfolio Management
```
GET  /portfolio                               EXISTS    Already Useful  
GET  /portfolio/summary                       EXISTS    Already Useful
GET  /portfolio/{property_id}                 EXISTS    Already Useful
POST /portfolio/add                           EXISTS    Already Useful
GET  /portfolio/analyze                       EXISTS    Useful Later
GET  /holdings                                EXISTS    Already Useful
GET  /holdings/{holding_id}                   EXISTS    Already Useful
```

**Status:** Portfolio tracking fully implemented.  
**Post-Launch Use Case:** After a case is CLOSED, add to portfolio.  
**Not Required Day-One:** But essential for post-close workflow.

**Integration Path:**
```
Case reaches CLOSED stage
  ↓
If strategy="HOLD" or "PARTNERSHIP"
  ↓
→ POST /portfolio/add with case data
  ↓
Property now tracked in holdings
```

---

## SECTION 4: COMMUNITY & MARKET DATA - ALREADY USEFUL

These routes provide market intelligence and community data.

### Community Management
```
GET  /community                               EXISTS    Useful Later
GET  /community/{community_id}                EXISTS    Useful Later
POST /community                               EXISTS    Useful Later
GET  /market-data                             EXISTS    Useful Later
GET  /market-data/{zone}                      EXISTS    Useful Later (when zones live)
```

**Status:** Community data routes exist but not integrated to execution layer yet.  
**Future Use:** Market analysis for strategy classification.  
**Not Required:** Pre-launch, but useful for historical context.

---

## SECTION 5: CAPITAL & FUNDING ROUTES - USEFUL LATER

These routes coordinate capital, investor returns, and funding.

### Capital Management
```
GET  /capital                                 EXISTS    Useful Later (year 1)
GET  /capital/available                       EXISTS    Useful Later (funding available)
POST /capital/allocate                        EXISTS    Useful Later (commit capital to deal)
GET  /capital/returns                         EXISTS    Useful Later (track investor returns)
GET  /capital/performance                     EXISTS    Useful Later (ROI dashboard)
```

**Status:** Capital module exists but not connected to execution layer.  
**Post-Launch Timeline:** Connect post-month-1 (after first closes).  
**Use Case:** When deal goes UNDER_CONTRACT, allocate capital.

```
Case reaches UNDER_CONTRACT
  ↓
→ POST /capital/allocate {"case_id": 3, "amount": 250000}
  ↓
Capital reserved for this deal
  ↓
When deal CLOSED → capital moved to portfolio
```

---

## SECTION 6: CONTRACTS & LEGAL ROUTES - ALREADY USEFUL

These routes manage documents and legal workflows.

### Contracts & Documents
```
GET  /contracts                               EXISTS    Already Useful
GET  /contracts/{contract_id}                 EXISTS    Already Useful
POST /contracts/create                        EXISTS    Already Useful
GET  /contracts/purchase-agreement            EXISTS    Already Useful
GET  /contracts/offer-letter                  EXISTS    Already Useful
GET  /document-route                          EXISTS    Already Useful
```

**Status:** Contract templates and routing fully implemented.  
**Day-One Use:** Manual - closer pulls templates from /contracts.  
**Post-Launch:** Auto-populate offer letter with case data.

**Integration (Later):**
```
→ GET /contracts/offer-letter
  ↓
Get template
  ↓
→ POST /contracts/create with case data
  ↓
Pre-filled offer letter generated
  ↓
Ready for seller and closer to sign
```

---

## SECTION 7: GOVERNANCE & AUDIT - ALREADY USEFUL

These routes provide system governance and audit trails.

### Governance & Audit
```
GET  /governance                              EXISTS    Already Useful
GET  /governance/audit-log                    EXISTS    Already Useful
GET  /governance/decision-log                 EXISTS    Already Useful
POST /governance/audit-event                  EXISTS    Already Useful
```

**Status:** Full audit trail system implemented.  
**Day-One:** Automatic - all case changes logged to audit-log.  
**Compliance:** Required for million-path (need to know who decided what).

**Automatic Integration:**
- Every POST /execution/cases/{id}/advance → Auto-logged to /governance/audit-log
- Every case status change → /governance/decision-log entry

---

## SECTION 8: FLOW/PIPELINE ROUTES - USEFUL LATER

These routes define multi-step workflows and deal pipelines.

### Flow/Pipeline Management
```
GET  /flow/full-deal-pipeline                 EXISTS    Useful Later
GET  /flow/profit-allocation                  EXISTS    Useful Later
GET  /flow/funfunds-plan                      EXISTS    Useful Later
```

**Status:** Advanced pipeline routing exists but not connected to execution layer.  
**Future Timeline:** Year 1+ for complex multi-step workflow automation.  
**Not Required:** Pre-launch.

---

## SECTION 9: BUILDER ROUTES - ALREADY USEFUL

These routes coordinate with internal "builder" system (construction/rehab).

### Builder Coordination
```
GET  /builder                                 EXISTS    Already Useful
GET  /builder/projects                        EXISTS    Already Useful
POST /builder/estimate                        EXISTS    Already Useful
GET  /builder/contractors                     EXISTS    Already Useful
POST /builder/register-contractor             EXISTS    Already Useful
```

**Status:** Builder module ready to coordinate flips and rehabs.  
**Post-Launch Use:** After case classified as FLIP, integration with builder.  
**Signal Flow:**
```
Case → strategy = "FLIP"
  ↓
→ POST /builder/estimate {property, specs}
  ↓
API returns contractor quotes
  ↓
Our repair estimate now data-backed
```

---

## SECTION 10: ARBITRAGE ROUTES - NOISY (Pre-Million-Path)

These routes handle complex multi-zone arbitrage strategies.

### Arbitrage Engine
```
GET  /arbitrage                               EXISTS    Noisy (not launch-focused)
GET  /arbitrage/opportunities                 EXISTS    Noisy (internal use only)
POST /arbitrage/analyze                       EXISTS    Noisy (too advanced for day-one)
GET  /arbitrage/zones                         EXISTS    Noisy (future multi-zone feature)
```

**Status:** Arbitrage module exists but not relevant to execution layer.  
**Skip For:** Day-one launch - too complex.  
**Activate:** Year 2+ when multi-zone established and cash flow high.

**Why Skip:** 
- Requires 3+ established zones
- Needs sophisticated pricing models
- Low priority vs. getting first zone stable

---

## SECTION 11: BRRRR ROUTES - USEFUL LATER

These routes support Buy-Rehab-Rent-Refinance strategy (hold + leverage).

### BRRRR Workflow
```
GET  /brrrr                                   EXISTS    Useful Later
GET  /brrrr/calculator                        EXISTS    Useful Later
POST /brrrr/analyze-deal                      EXISTS    Useful Later
```

**Status:** BRRRR-specific routes exist but not connected.  
**Future Timeline:** Month 2-3 post-launch when first properties held.  
**Not Blocking:** Day-one execution.

---

## SECTION 12: WHOLESALE/WHOLESALING - ALREADY USEFUL

These routes manage wholesale strategy specifically.

### Wholesale Coordination
```
GET  /wholesale                               EXISTS    Already Useful
GET  /wholesale/buyers                        EXISTS    Already Useful
POST /wholesale/match-buyer                   EXISTS    Already Useful
GET  /wholesale/profit-tracker                EXISTS    Already Useful
```

**Status:** Wholesale routes ready to use.  
**Day-One Integration:** When case classified WHOLESALE, operator manually finds buyer.  
**Post-Launch:** Auto-notify registered wholesalers.

---

## SECTION 13: UNDERWRITING - USEFUL LATER

These routes handle advanced underwriting and financial analysis.

### Underwriting Engine
```
GET  /underwriter                             EXISTS    Useful Later
POST /underwriter/analyze                     EXISTS    Useful Later
GET  /underwriter/risk-score                  EXISTS    Useful Later
```

**Status:** Underwriting exists but not connected to execution layer.  
**Future Timeline:** Integrate post-month-1 for automatic risk scoring.  
**Not Required:** Initial manual analysis sufficient.

---

## SECTION 14: RESEARCH - USEFUL LATER

These routes provide market research and data integration.

### Research Tools
```
GET  /research                                EXISTS    Useful Later
GET  /research/comparables                    EXISTS    Useful Later
GET  /research/market-trends                  EXISTS    Useful Later
GET  /research/property-data                  EXISTS    Useful Later
```

**Status:** Research routes exist, not connected to VA workflow yet.  
**Post-Launch Integration:** VA uses /research/comparables when qualifying deals.  
**Not Required:** Day-one (VA does manual research).

---

## SECTION 15: MEDIA & CONTENT - NOISY

These routes manage media, website, marketing content.

### Media Management
```
GET  /media                                   EXISTS    Noisy (marketing layer)
POST /media/upload                            EXISTS    Noisy (asset management)
GET  /media/{id}                              EXISTS    Noisy (delivery)
```

**Status:** Media routes not relevant to execution layer.  
**Skip For:** Entire pre-launch phase.

---

## SECTION 16: INVESTOR - USEFUL LATER

These routes manage investor relationships and capital partners.

### Investor Management
```
GET  /investor                                EXISTS    Useful Later
GET  /investor/{investor_id}                  EXISTS    Useful Later
POST /investor                                EXISTS    Useful Later
GET  /investor/dashboard                      EXISTS    Useful Later
GET  /investor/returns                        EXISTS    Useful Later
```

**Status:** Investor portal exists.  
**Use Timeline:** Year 1+ when raising external capital.  
**Not Required:** Pre-launch (all internal capital initially).

---

## SECTION 17: REGISTRATIONS & COMPLIANCE - USEFUL LATER

These routes handle business registrations, entity setup, and compliance.

### Registration Navigator
```
GET  /registration-navigator                 EXISTS    Useful Later
POST /business-entity                         EXISTS    Useful Later
GET  /compliance-check                        EXISTS    Useful Later
```

**Status:** Registration routes exist but not execution-connected.  
**Future Use:** When partnerships or multi-entity deals needed.  
**Not Required:** Pre-launch.

---

## SECTION 18: NOTIFICATIONS - ALREADY USEFUL

These routes handle alerts, emails, and team notifications.

### Notification System
```
POST /notify                                  EXISTS    Already Useful
GET  /notifications                           EXISTS    Already Useful
POST /subscribe                               EXISTS    Already Useful
GET  /notification-settings                   EXISTS    Already Useful
```

**Status:** Notification system fully implemented.  
**Auto-Integration:** Every case advancement can trigger notifications.  
**Day-One Use:** Manual task assignment emails.  
**Post-Launch:** Auto-notify assigned team members.

---

## SECTION 19: EMPIRE DASHBOARD - USEFUL LATER

These routes provide high-level business intelligence and dashboarding.

### Empire State Management
```
GET  /empire/dashboard                        EXISTS    Useful Later (year 1)
GET  /empire/metrics                          EXISTS    Useful Later (reporting)
GET  /empire/kpi                              EXISTS    Useful Later (KPI tracking)
GET  /empire/state                            EXISTS    Useful Later (business state)
```

**Status:** Empire dashboard exists but not populated with execution data.  
**Future Timeline:** Month 3+ when enough deals closed to report on.  
**Not Required:** Pre-launch.

---

## SECTION 20: GRANTS & INCENTIVES - NOISY

These routes handle specialized incentment programs.

### Grants System
```
GET  /grants                                  EXISTS    Noisy (not execution-focused)
POST /grants/apply                            EXISTS    Noisy (compliance heavy)
```

**Status:** Grants module not relevant to million-path.  
**Skip For:** Pre-launch focus.

---

## ROUTE PRIORITY MATRIX

| Route Family | Launch Critical | Already Useful | Post-Launch | Noisy | Action |
|--------------|-----------------|-----------------|------------|-------|--------|
| Execution | ✅✅ | - | - | - | TEST FIRST |
| Buyer/Match | - | ✅ | ✅ | - | VERIFY WEEK 1 |
| Portfolio | - | ✅ | ✅ | - | WIRE WEEK 2 |
| Capital | - | - | ✅ | - | WIRE MONTH 1 |
| Contracts | - | ✅ | ✅ | - | WIRE WEEK 1 |
| Governance | - | ✅ | ✅ | - | AUTO WIRE |
| Builder | - | - | ✅ | - | WIRE MONTH 1 |
| Arbitrage | - | - | - | ✅ | IGNORE |
| BRRRR | - | - | ✅ | - | WIRE YEAR 1 |
| Wholesale | - | ✅ | ✅ | - | WIRE WEEK 2 |
| Research | - | - | ✅ | - | WIRE VA |
| Media | - | - | - | ✅ | IGNORE |
| Investor | - | - | ✅ | - | WIRE YEAR 1 |
| Registration | - | - | ✅ | - | WIRE YEAR 1 |
| Notifications | - | ✅ | ✅ | - | WIRE WEEK 1 |
| Empire | - | - | ✅ | - | WIRE MONTH 3 |
| Grants | - | - | - | ✅ | IGNORE |

---

## VERIFICATION CHECKLIST (Pre-WeWeb)

### Week 1 - Test Launch Routes
- [ ] POST /execution/intake (test: create new intake)
- [ ] POST /execution/intake/{id}/process (test: classify case)
- [ ] GET /execution/cases/{id} (test: pull full case)
- [ ] GET /execution/cases/{id}/tasks (test: task list)
- [ ] GET /execution/cases/{id}/next-action (test: next step)
- [ ] POST /execution/cases/{id}/advance (test: stage transition)
- [ ] GET /execution/cases/{id}/events (test: audit trail)

### Week 1 - Wire Complementary Routes
- [ ] GET /contracts/offer-letter (test: template access)
- [ ] GET /buyer (test: buyer lookup)
- [ ] POST /notify (test: send notification)

### Week 2 - Verify Integration Points
- [ ] POST /portfolio/add (test: add closed deal to portfolio)
- [ ] POST /wholesale/match-buyer (test: wholesale buyer matching)
- [ ] POST /builder/estimate (test: contractor quotes)

### Month 1+ - Advanced Integrations
- [ ] POST /capital/allocate (test: capital reservation)
- [ ] GET /empire/dashboard (test: reporting)
- [ ] POST /investor/notify (test: investor updates)

---

## ROUTE WIRING TIMELINE

```
WEEK 1: Execution + Contracts + Notifications
  ↓
WEEK 2: Buyer Matching + Portfolio + Wholesale
  ↓
MONTH 1: Capital + Builder + Governance
  ↓
MONTH 2: Research Integration (VA tool)
  ↓
MONTH 3: Empire Dashboard + Analytics
  ↓
YEAR 1: Arbitrage, Investor, Registration
```

---

## WHAT TO IGNORE (Pre-Million-Path)

❌ Media/Content routes (marketing layer)  
❌ Grants routes (incentive programs)  
❌ Arbitrage routes (too advanced)  
❌ Registration/Compliance routes (future legal layer)  
❌ Advanced Investor portal (post-revenue feature)  
❌ Research integration (VA manual for now)  

**Reason:** Scope creep kills launches. Focus on core execution layer first.

---

## NOTES FOR DEVELOPERS

1. **Do NOT call routes you haven't tested.** Test each route with real data before WeWeb build.
2. **Do NOT assume routes work.** Verify 200 responses and valid data.
3. **Do NOT wire untested routes into WeHub.** Manual integration first, automation later.
4. **Do NOT change route signatures.** All existing routes must remain backward-compatible.

---

**Document Owner:** Architecture / Route Mapping Team  
**Status:** AUDIT COMPLETED - Ready for implementation  
**Last Updated:** 2026-04-13  
**Next Review:** Pre-WeWeb launch verification  
