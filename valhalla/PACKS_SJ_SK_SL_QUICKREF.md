# PACK SJ-SL Quick Reference

## 📁 File Locations

### Models
- `app/models/wholesale_deals.py` - 5 classes, ~180 lines
- `app/models/opportunity_tracker.py` - 4 classes, ~170 lines  
- `app/models/personal_dashboard.py` - 7 classes, ~200 lines

### Schemas
- `app/schemas/wholesale_deals.py` - 6 schemas
- `app/schemas/opportunity_tracker.py` - 5 schemas
- `app/schemas/personal_dashboard.py` - 8 schemas

### Services
- `app/services/wholesale_deals.py` - 11 functions
- `app/services/opportunity_tracker.py` - 11 functions
- `app/services/personal_dashboard.py` - 15 functions

### Routers
- `app/routers/wholesale_deals.py` - 15 endpoints, /wholesale prefix
- `app/routers/opportunity_tracker.py` - 10 endpoints, /opportunities prefix
- `app/routers/personal_dashboard.py` - 13 endpoints, /life prefix

### Tests
- `app/tests/test_wholesale_deals.py` - 5 test classes, 15 methods
- `app/tests/test_opportunity_tracker.py` - 6 test classes, 15 methods
- `app/tests/test_personal_dashboard.py` - 8 test classes, 20+ methods

### Integration
- `app/main.py` - Added 3 router registrations (lines 720-741)
- `alembic/env.py` - Added 16 model imports (lines 131-161)
- `alembic/versions/0112_add_packs_sj_through_sl_models.py` - Migration file

---

## 🔗 API Endpoint Overview

### PACK SJ: Wholesale Deals (`/wholesale`)
```
POST   /wholesale/leads                    Create wholesale lead
GET    /wholesale/leads                    List all leads
GET    /wholesale/leads/{lead_id}          Get specific lead
PUT    /wholesale/leads/{lead_id}/stage    Update lead stage

POST   /wholesale/offers                   Create offer
GET    /wholesale/offers/lead/{lead_id}    Get offers for lead
PUT    /wholesale/offers/{offer_id}/status Update offer status

POST   /wholesale/buyers                   Create buyer profile
GET    /wholesale/buyers                   List all buyers

POST   /wholesale/assignments              Create assignment
GET    /wholesale/assignments/lead/{lead_id} Get assignments for lead

GET    /wholesale/pipeline                 Get pipeline summary
POST   /wholesale/pipeline/snapshot        Create pipeline snapshot
```

### PACK SK: Opportunities (`/opportunities`)
```
POST   /opportunities/                     Create opportunity
GET    /opportunities/                     List opportunities (filters: category, status)
GET    /opportunities/{opportunity_id}     Get specific opportunity
PUT    /opportunities/{opportunity_id}/status Update opportunity status

POST   /opportunities/{opportunity_id}/score Create score/evaluation
POST   /opportunities/{opportunity_id}/performance Log performance
GET    /opportunities/{opportunity_id}/performance Get performance logs

POST   /opportunities/{opportunity_id}/summary Create period summary
GET    /opportunities/{opportunity_id}/summary Get summary

GET    /opportunities/comparison/metrics    Compare all opportunities
```

### PACK SL: Personal Dashboard (`/life`)
```
POST   /life/focus-areas                   Create focus area
GET    /life/focus-areas                   List focus areas (filter: category)

POST   /life/routines                      Create routine
GET    /life/routines                      List active routines

POST   /life/routines/{routine_id}/completion Log completion
GET    /life/routines/{routine_id}/completion-rate Get completion rate

POST   /life/family-snapshots              Create family snapshot

POST   /life/dashboard/weekly              Create weekly dashboard

POST   /life/goals                         Create goal
GET    /life/goals                         List active goals
PUT    /life/goals/{goal_id}/progress      Update goal progress

POST   /life/mood                          Log mood entry
GET    /life/mood/recent                   Get recent mood logs (days param)

GET    /life/metrics                       Get life operations metrics
```

---

## 📊 Data Models Summary

### PACK SJ: Wholesale (5 tables)
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `wholesale_leads` | lead_id, stage, seller_name, property_address | Core lead tracking |
| `wholesale_offers` | offer_id, lead_id, offer_price, arv, repair_estimate | Offer management |
| `buyer_profiles` | buyer_id, name, criteria (JSON), status | Buyer tracking |
| `assignment_records` | assignment_id, lead_id, buyer_id, assignment_fee | Assignment workflow |
| `wholesale_pipeline_snapshots` | snapshot_id, date, by_stage (JSON), hot_leads | Pipeline aggregation |

### PACK SK: Opportunities (4 tables)
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `opportunities` | opportunity_id, name, category, startup_cost, status | Opportunity tracking |
| `opportunity_scores` | score_id, opportunity_id, time_efficiency/scalability/difficulty/personal_interest | User-defined scoring |
| `opportunity_performance` | log_id, opportunity_id, date, effort_hours, revenue | Performance tracking |
| `opportunity_summaries` | summary_id, opportunity_id, period, total_effort_hours, total_revenue, roi | Period summaries |

### PACK SL: Personal (7 tables)
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `focus_areas` | area_id, name, category, priority_level | Life categories |
| `personal_routines` | routine_id, focus_area_id, frequency, status | Habit definitions |
| `routine_completions` | completion_id, routine_id, date, completed (0/1) | Daily tracking |
| `family_snapshots` | snapshot_id, date, kids_notes (JSON), partner_notes | Family observations |
| `life_dashboards` | dashboard_id, week_of, wins/challenges/habits_tracked (JSON) | Weekly summary |
| `personal_goals` | goal_id, name, category, deadline, progress_percent | Goal tracking |
| `mood_logs` | log_id, date, mood, energy_level | Mood/energy tracking |

---

## 🧪 Test Coverage

### SJ Wholesale Deals (15 tests)
- TestWholesaleLeads: create, list, get, update stage
- TestOffers: create, list by lead, update status
- TestBuyers: create, list
- TestAssignments: create, get by lead
- TestPipeline: get summary, create snapshot

### SK Opportunities (15 tests)
- TestOpportunities: create, list, get, update status
- TestScoring: create score
- TestPerformance: log performance, get logs
- TestSummaries: create summary, get summary
- TestComparison: compare opportunities

### SL Personal Dashboard (20+ tests)
- TestFocusAreas: create, list
- TestRoutines: create, list
- TestCompletion: log completion, get rate
- TestFamilySnapshots: create snapshot
- TestDashboard: create weekly dashboard
- TestGoals: create, list, update progress
- TestMoodLogs: log mood, get recent
- TestMetrics: calculate metrics

---

## 🗄️ Database Migration

**Revision ID:** 0112
**Revises:** 0111
**Tables Created:** 19 total
- SJ: 5 tables
- SK: 4 tables  
- SL: 7 tables

**Key Features:**
- Proper FK relationships with CASCADE
- Unique constraints on business IDs
- Indexes on common query fields
- Server-side timestamps (created_at, updated_at)
- JSON fields for flexible metadata

---

## 🚀 Deployment Checklist

✅ Models created and validated
✅ Schemas created with Pydantic v2 config
✅ Services implemented (37 functions)
✅ Routers created (38 endpoints)
✅ Tests written (50+ methods)
✅ main.py updated with router registrations
✅ alembic/env.py updated with model imports
✅ Migration file 0112 created
✅ All files compile without syntax errors

**Next Steps:**
1. Run migration: `alembic upgrade head`
2. Run tests: `pytest app/tests/test_*.py`
3. Start API: `uvicorn app.main:app --reload`
4. Access docs: `http://localhost:8000/docs`

---

## 💡 Design Principles Implemented

### Non-Directive SJ & SK
- SJ doesn't recommend offers or ARV values
- SK doesn't assess opportunity viability
- Both store and organize user data without judgment

### User Agency
- SJ: User supplies all offer data
- SK: User defines scoring criteria  
- SL: User provides all observations and preferences

### Safe Data Capture (SL)
- No medical interpretation
- No psychological analysis
- No automatic recommendations
- All data explicitly user-provided

### Proper Relationships
- SJ: Offers→Leads, Assignments→Leads+Buyers
- SK: Scores/Performance/Summaries→Opportunities
- SL: Routines→FocusAreas, Completions→Routines

---

## 📝 Notes

All files follow project conventions:
- SQLAlchemy ORM with DeclarativeBase
- Pydantic v2 with from_attributes=True
- FastAPI APIRouter pattern
- pytest TestClient for testing
- Alembic for migrations
- JSON fields for flexible data

Routers are registered with try/except blocks for graceful failure handling.
All tests use in-memory SQLite database for isolation.
All service functions include proper error handling and database transactions.
