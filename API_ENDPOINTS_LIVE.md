# VALHALLA API ENDPOINTS - UPDATED

**Status:** ✅ 73 endpoints live  
**Last Updated:** January 2, 2026

---

## 🎯 COMMAND CENTER (NEW - 3 endpoints)
```
GET  /core/command/what_now       → Top 7 priorities today
GET  /core/command/daily_brief    → Morning digest
GET  /core/command/weekly_review  → End-of-week summary
```

## 💰 GRANTS (NEW - 5 endpoints)
```
POST /core/grants                           Create grant
GET  /core/grants?q=&country=CA             List/search grants
GET  /core/grants/{grant_id}                Get grant details
POST /core/grants/{grant_id}/proof_pack     Required documents checklist
POST /core/grants/{grant_id}/deadline_followup  Create reminder task
```

## 🏦 LOANS (NEW - 5 endpoints)
```
POST /core/loans                                     Create loan
GET  /core/loans?country=CA&product_type=microloan List loans
GET  /core/loans/{loan_id}                          Get loan details
POST /core/loans/{loan_id}/underwriting_checklist   Required documents
POST /core/loans/recommend_next                     Get best fit loans
```

---

## 🏛️ CORE SYSTEM (3 endpoints)
```
GET /core/healthz                Health check
GET /core/whoami                  Current identity
GET /core/reality/weekly_audit    Compliance audit
```

---

## ⚙️ GOVERNANCE & RISK (6 endpoints)
```
GET  /core/cone/state             Current band + metadata
POST /core/cone/decide            Make decision w/ reason
GET  /core/cone/history           Band history
```

---

## 💼 DEALS (16 endpoints)
```
GET    /core/deals                List all deals
POST   /core/deals                Create deal
GET    /core/deals/{id}           Get deal
PUT    /core/deals/{id}           Update deal
DELETE /core/deals/{id}           Archive deal
GET    /core/deals/search         Search (filters)
POST   /core/deals/{id}/import    Batch import
GET    /core/deals/summary/{id}   Deal summary
POST   /core/deals/score          Score deal
GET    /core/deals/{id}/offer     Offer sheet
GET    /core/deals/{id}/next      Next action
GET    /core/deals/{id}/scripts   Generate scripts
GET    /core/deals/{id}/disposition Complete package
POST   /core/deals/seed           Generate test data
```

---

## 👥 CONTACT & FOLLOW-UP (5 endpoints)
```
POST  /core/deals/{id}/contact   Log contact attempt
GET   /core/deals/{id}/contacts  View contact history
POST  /core/followups            Create follow-up
GET   /core/followups/queue      Get queue
PATCH /core/followups/{id}       Update status
```

---

## 🤝 BUYERS (5 endpoints)
```
POST /core/buyers           Create buyer
GET  /core/buyers           List buyers
GET  /core/buyers/match     Match to deal
GET  /core/buyers/{id}/criteria  Buyer filters
PUT  /core/buyers/{id}      Update buyer
```

---

## 🚀 PIPELINE (6 endpoints)
```
GET  /core/go                   List opportunities
POST /core/go                   Create opportunity
GET  /core/go/{id}/session      Session data
POST /core/go/{id}/session      Update session
GET  /core/go/{id}/summary      Opportunity summary
```

---

## 📊 OPERATIONS (8+ endpoints)
```
GET  /core/visibility           Pipeline breakdown
POST /core/visibility/drill      Drill into segment
GET  /core/alerts               Active alerts
GET  /core/intake               Lead queue
POST /core/intake/{id}/qualify  Qualify lead
GET  /core/jobs                 Job queue status
POST /core/jobs/{id}/retry      Retry failed job
```

---

## 💳 CAPITAL (4 endpoints)
```
GET  /core/capital/summary      Current allocation
POST /core/capital/scenario     "What-if" analysis
GET  /core/capital/limits       Engine caps
```

---

## ⚙️ CONFIGURATION (6+ endpoints)
```
GET  /core/config              Current config
POST /core/config              Update settings
GET  /core/canon               Engine definitions
GET  /core/health/dashboard    System metrics
GET  /core/notifications       Notification log
```

---

## 📁 DATA & INTEGRATION (4+ endpoints)
```
GET  /core/export              Create export bundle
POST /core/import              Batch import deals
GET  /core/knowledge           Search knowledge base
POST /core/knowledge/add       Add reference
```

---

## 📋 REFERENCE (2 endpoints)
```
GET /core/onboarding                Initial system payload
GET /core/go/next_step_with_sources  Next step suggestions
```

---

## 📊 ENDPOINT SUMMARY

| Category | Count |
|----------|-------|
| Command Center | 3 |
| Grants | 5 |
| Loans | 5 |
| Core System | 3 |
| Deals | 16 |
| Contact/Follow-up | 5 |
| Buyers | 5 |
| Pipeline | 6 |
| Operations | 8 |
| Capital | 4 |
| Configuration | 6 |
| Data/Integration | 4 |
| Reference | 2 |
| **TOTAL** | **73** |

---

## 🔐 Access Pattern

All endpoints are under `/core` prefix:
```
Base URL: http://localhost:4000
API Base: http://localhost:4000/core
Docs: http://localhost:4000/docs (Swagger UI)
Schema: http://localhost:4000/openapi.json
```

---

## 🎯 Most Useful Endpoints to Start With

1. **Check System Health**
   ```bash
   curl http://localhost:4000/core/healthz
   ```

2. **Get Today's Priorities**
   ```bash
   curl http://localhost:4000/core/command/what_now
   ```

3. **Get Morning Brief**
   ```bash
   curl http://localhost:4000/core/command/daily_brief
   ```

4. **Create a Test Deal**
   ```bash
   curl -X POST http://localhost:4000/core/deals \
     -H "Content-Type: application/json" \
     -d '{"address":"123 Main St","city":"Winnipeg","province":"MB","strategy":"wholesale"}'
   ```

5. **List All Grants**
   ```bash
   curl http://localhost:4000/core/grants?country=CA
   ```

6. **Get Loan Recommendations**
   ```bash
   curl -X POST http://localhost:4000/core/loans/recommend_next \
     -H "Content-Type: application/json" \
     -d '{"country":"CA","needs_amount":50000}'
   ```

---

**Ready for:** Frontend integration, automation, batch operations, reporting  
**Deployment Status:** 🟢 LIVE
