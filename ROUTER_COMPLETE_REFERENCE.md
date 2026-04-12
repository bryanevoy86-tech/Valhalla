# VALHALLA - COMPLETE ROUTER REFERENCE

**Total Routers:** 150+  
**Total Estimated Endpoints:** 350+

---

## Router Inventory by Category

### SYSTEM & ADMINISTRATION (22 routers)

```
✓ admin.py                    - Admin panel core functionality
✓ admin_bootstrap.py          - System initialization & setup
✓ admin_build.py              - Build management & versioning
✓ admin_dashboard.py          - Admin dashboard data endpoints
✓ admin_dependencies.py       - Admin dependency management
✓ admin_go_live.py            - Go-live coordination & cutover
✓ admin_handoff.py            - Project handoff procedures
✓ admin_healthcheck.py        - Health monitoring & alerts
✓ admin_heimdall.py           - Heimdall agent administration
✓ admin_logs.py               - Log management & retrieval
✓ admin_ops.py                - Operations management
✓ admin_privacy.py            - Privacy & data protection
✓ admin_secscan.py            - Security scanning operations
✓ admin_system_summary.py     - System overview & summary
✓ admin_todo.py               - Task/todo management
✓ system_boot.py              - System bootstrap (PRIORITY LOAD)
✓ system_config.py            - Configuration management
✓ system_health.py            - Health status endpoints
✓ system_log.py               - System logging
✓ system_selftest.py          - Self-diagnostics & testing
✓ system_status.py            - Overall system status
✓ health.py                   - Health check endpoints
```

---

### DEAL MANAGEMENT (10 routers)

```
✓ deals.py                    - Core deal CRUD operations
✓ deal_analyzer.py            - Deal analysis & AI insights
✓ deal_finalization.py        - Closing & finalization
✓ deal_lifecycle.py           - Deal workflow state management
✓ deal_workflow_status.py     - Workflow tracking & status
✓ wholesale_deals.py          - Wholesale deal operations
✓ wholesale_engine.py         - Wholesale calculations & ROI
✓ flow_lead_to_deal.py        - Lead to deal conversion pipeline
✓ opportunity.py              - Opportunity tracking
✓ opportunity_tracker.py      - Opportunity analytics
```

---

### LEAD MANAGEMENT (6 routers)

```
✓ leads.py                    - Core lead CRUD & intake
✓ leads_status.py             - Lead status tracking & updates
✓ lead_engine.py              - Lead scoring & qualification
✓ registration_navigator.py   - Registration workflow
✓ intake.py                   - Lead intake process
✓ intake_admin.py             - Intake administration
```

---

### USER & AUTHENTICATION (3 routers)

```
✓ users.py                    - User management CRUD
✓ user_summary.py             - User profile summary data
✓ (auth services)             - Authentication logic (service layer)
```

---

### GOVERNANCE & DECISION ENGINE (10 routers)

```
✓ governance_orchestrator.py  - Central governance hub & coordinator
✓ governance_king.py          - King governance pattern
✓ governance_queen.py         - Queen governance pattern
✓ governance_loki.py          - Loki strategic governance
✓ governance_odin.py          - Odin decision authority
✓ governance_tyr.py           - Tyr enforcement engine
✓ governance_policy.py        - Policy management & creation
✓ governance_decisions.py     - Decision tracking & history
✓ decision_governance.py      - Governance rules & constraints
✓ decision_recommendation.py  - Recommendation engine
```

---

### CONTRACT MANAGEMENT (8 routers)

```
✓ contracts.py                - Contract CRUD operations
✓ contracts_lifecycle.py      - Contract workflow lifecycle
✓ contracts_pipeline.py       - Contract pipeline management
✓ contracts_webhooks.py       - Contract event webhooks
✓ contracts_upload.py         - Document upload handling
✓ contract_engine.py          - Contract automation
✓ document_routing.py         - Document flow & routing
✓ agreements.py               - Agreement management
```

---

### FINANCIAL OPERATIONS (15 routers)

```
✓ accounting.py               - General accounting entries
✓ banking_structure_planner.py- Bank account planning
✓ capital.py                  - Capital management & allocation
✓ finance.py                  - Financial calculations
✓ finops.py                   - Financial operations
✓ payments.py                 - Payment processing
✓ income_routing.py           - Income distribution & routing
✓ tax_tracker.py              - Tax tracking & categorization
✓ tax_bridge.py               - Tax system integration
✓ credit_card_spending.py     - Credit card tracking
✓ buyer_liquidity.py          - Buyer liquidity analysis
✓ grants.py                   - Grant management
✓ grant_eligibility.py        - Grant qualification
✓ flow_profit_allocation.py   - Profit distribution
✓ flow_tax_snapshot.py        - Tax reports & snapshots
```

---

### ANALYTICS & REPORTING (10 routers)

```
✓ analytics.py                - Analytics core functionality
✓ analytics_engine.py         - Analytics calculations
✓ metrics.py                  - Metrics collection & tracking
✓ reports.py                  - Report generation
✓ portfolio_dashboard.py      - Portfolio view endpoints
✓ personal_dashboard.py       - Personal dashboard data
✓ operational_dashboard.py    - Operations dashboard
✓ empire_dashboard.py         - Executive dashboard
✓ security_dashboard.py       - Security monitoring dashboard
✓ ui_dashboard.py             - UI dashboard backend
```

---

### NOTIFICATIONS & COMMUNICATIONS (7 routers)

```
✓ notifications.py            - Notification core
✓ notification_bridge.py      - 3rd party notification bridge
✓ notification_channel.py     - Channel management (Email, SMS, etc)
✓ notification_orchestrator.py- Notification orchestration
✓ messaging.py                - Messaging service
✓ notify.py                   - Notification operations
✓ notify_test.py              - Notification testing
```

---

### COMPLIANCE & SECURITY (12 routers)

```
✓ audit.py                    - Audit logging & trails
✓ compliance.py               - Compliance rules & checks
✓ security.py                 - Security operations
✓ security_actions.py         - Security action endpoints
✓ security_policy.py          - Security policy management
✓ security_dashboard.py       - Security monitoring
✓ integrity.py                - Data integrity checks
✓ integrity_monitor.py        - Integrity monitoring
✓ encryption.py               - Encryption operations
✓ data_retention.py           - Data retention policies
✓ event_log.py                - Event logging
✓ internal_auditor.py         - Internal audit operations
```

---

### AI & DECISION ENGINES (15+ routers)

```
✓ heimdall.py                 - Heimdall AI agent core
✓ heimdall_build_gate.py      - Build gate decisions
✓ heimdall_governance.py      - Governance decisions
✓ heimdall_training.py        - AI model training
✓ heimdall_workload.py        - Workload management
✓ jarvis.py                   - Jarvis orchestration (Heimdall companion)
✓ explanation_engine.py       - Decision explanation
✓ scenario_simulator.py       - Scenario simulation & testing
✓ strategic_mode.py           - Strategic execution mode
✓ narrative.py                - Narrative generation
✓ story_engine.py             - Story creation engine
✓ story_mode.py               - Story mode operations
✓ research.py                 - Research operations
✓ research_semantic.py        - Semantic research
✓ insight.py                  - Insight generation
```

---

### BUSINESS PROCESSES - DEAL WORKFLOWS (8 routers)

```
✓ arbitrage.py                - Arbitrage opportunity analysis
✓ brrrr.py                    - BRRRR strategy evaluation
✓ brrrr_planner.py            - BRRRR planning & analysis
✓ closers.py                  - Closer management
✓ closer_engine.py            - Closer assignment & performance
✓ closing_playbook.py         - Closing procedures & checklists
✓ flow_prepare_closing.py     - Closing preparation workflow
✓ deal_workflow_status.py     - Workflow tracking
```

---

### BUYER & INVESTOR OPERATIONS (8 routers)

```
✓ buyers.py                   - Buyer directory & management
✓ buyer_match.py              - Buyer-deal matching
✓ buyer_liquidity.py          - Buyer liquidity analysis
✓ investor_module.py          - Investor tracking
✓ relationships.py            - Relationship management
✓ match.py                    - Deal/buyer/investor matching
✓ opportunity.py              - Opportunity tracking
✓ opportunity_tracker.py      - Opportunity analytics
```

---

### ADVANCED NEGOTIATION (5 routers)

```
✓ advanced_negotiation_techniques.py - Negotiation strategies
✓ negotiations.py             - Negotiation tracking
✓ negotiation_strategies.py   - Strategy management
✓ neg_enhance.py              - Negotiation enhancement
✓ offer_strategy.py           - Offer & counter-offer management
```

---

### PROFESSIONAL SERVICES (6 routers)

```
✓ specialists.py              - Specialist directory
✓ specialist_feedback.py      - Specialist feedback
✓ pro_alignment_engine.py     - Professional alignment tracking
✓ pro_behavioral_extract.py   - Behavior analysis
✓ pro_handoff.py              - Professional handoff procedures
✓ pro_scorecard.py            - Professional scorecard & metrics
```

---

### PROFESSIONAL UTILITIES (5 routers)

```
✓ pro_tasks.py                - Professional task management
✓ pro_retainer.py             - Retainer agreement management
✓ brain_state.py              - Professional state tracking
✓ behavior.py                 - Behavior tracking
✓ behavioral_profiles.py      - Behavior profiling
```

---

### SCHEDULING & AUTOMATION (6 routers)

```
✓ scheduled_jobs.py           - Job scheduling
✓ job.py                      - Job management
✓ jobs.py                     - Job operations
✓ daily_rhythm.py             - Daily task automation
✓ flow_notifications.py       - Notification automation
✓ flows/cron                  - Cron job handlers
```

---

### DATA & KNOWLEDGE (10+ routers)

```
✓ knowledge.py                - Knowledge base management
✓ docs.py                     - Documentation endpoints
✓ documentation_routing.py    - Doc routing & distribution
✓ data_lineage.py             - Data tracking & lineage
✓ legal.py                    - Legal document management
✓ lawyer_feed.py              - Legal information feed
✓ education_engine.py         - Learning content
✓ media_engine.py             - Media management
✓ playbooks.py                - Operational playbooks
✓ pantry.py                   - Resource library
```

---

### RESEARCH & INSIGHTS (5 routers)

```
✓ research.py                 - Research operations
✓ research_semantic.py        - Semantic research
✓ insight.py                  - Insight generation
✓ explanation_engine.py       - Explanation generation
✓ philosophy.py               - Philosophy/doctrine engine
```

---

### MONITORING & LOGGING (8 routers)

```
✓ telemetry.py                - Telemetry collection
✓ telemetry_event.py          - Event telemetry
✓ logging.py                  - Log management
✓ system_log.py               - System logging
✓ health.py                   - Health check endpoints
✓ metrics.py                  - Metrics tracking
✓ maintenance.py              - System maintenance
✓ trajectory.py               - Performance trajectory
```

---

### HOUSING & REAL ESTATE (8 routers)

```
✓ community.py                - Community information
✓ realestate.py               - Real estate operations
✓ title.py                    - Title management
✓ property/housing operations - Property tracking
✓ vehicle_tracking.py         - Vehicle tracking
✓ holdings_engine.py          - Holdings management
✓ entity_links.py             - Entity relationships
✓ real estate related utils   - Support functions
```

---

### HOUSEHOLD & PERSONAL (8 routers)

```
✓ children.py                 - Family/children tracking
✓ kids_education.py           - Children's education
✓ mental_load.py              - Mental load tracking
✓ trust_residency.py          - Trust & residency
✓ trajectory.py               - Life trajectory
✓ projection_framework.py     - Future projections
✓ scenario_simulator.py       - Life scenario simulation
✓ personal_dashboard.py       - Personal view
```

---

### SPECIAL PURPOSE MODULES (10+ routers)

```
✓ builder.py                  - Third-party builder integration
✓ blackice.py                 - BlackICE security system
✓ brrrr.py / brrrr_planner.py - BRRRR investment strategy
✓ empire_journal.py           - Empire journaling
✓ empire_governance.py        - Empire governance
✓ freeze.py                   - Freeze operations
✓ freeze_events.py            - Freeze event tracking
✓ flow_*.py (multiple)        - Various workflow engines
✓ god_*.py (multiple)         - God module (arbitration/verdicts)
✓ king.py / queen.py          - Governance patterns
✓ loki.py / odin.py           - Advanced governance
✓ resort.py                   - Resort/vacation management
✓ honeypot_bridge.py          - Honeypot system integration
```

---

### DECISION & GOVERNANCE ENGINES (8 routers)

```
✓ decision_governance.py      - Decision governance rules
✓ decision_outcome.py         - Outcome tracking
✓ decision_recommendation.py  - Recommendations
✓ strategic_decision.py       - Strategic decisions
✓ strategic_event.py          - Strategic events
✓ strategic_mode.py           - Strategic mode execution
✓ outcomes.py                 - Outcome management
✓ workflow_guardrails.py      - Workflow safeguards
```

---

### DEPLOYMENT & VERIFICATION (5 routers)

```
✓ deployment_profile.py       - Deployment profiles
✓ deploy_check.py             - Deployment verification
✓ go_live.py                  - Go-live operations (admin)
✓ admin_go_live.py            - Admin go-live management
✓ verification endpoints      - System verification
```

---

### SPECIALIZED ANALYTICS (8 routers)

```
✓ dispo_engine.py             - Disposition analysis
✓ underwriter.py              - Underwriting operations
✓ underwriting_engine.py      - Underwriting automation
✓ risk.py                     - Risk assessment
✓ risk_monitoring_system.py   - Risk monitoring
✓ regression.py               - Regression tracking
✓ scenario_simulator.py       - Scenario analysis
✓ trajectory.py               - Trajectory analysis
```

---

### WORKFLOW & ORCHESTRATION (8 routers)

```
✓ workflows.py                - Workflow core
✓ workflow_guardrails.py      - Workflow guardrails
✓ orchestrator.py             - Workflow orchestration
✓ governance_orchestrator.py  - Governance orchestration
✓ notification_orchestrator.py- Notification orchestration
✓ flow_*.py (multiple)        - Specific workflows
✓ pipeline/ (multiple)        - Pipeline management
✓ cron/ (multiple)            - Scheduled workflows
```

---

### SUPPORT & UTILITIES (15+ routers)

```
✓ api_clients.py              - API client management
✓ feature_flags.py            - Feature flag management
✓ features.py                 - Feature management
✓ language/languages.py       - Multilingual support
✓ model_provider.py           - AI model providers
✓ rate_limit.py               - Rate limiting
✓ rbac.py                     - Role-based access control
✓ roles.py                    - Role management
✓ security_actions.py         - Security actions
✓ sync_engine.py              - Data synchronization
✓ tuning_rules.py             - System tuning
✓ triggers.py                 - Trigger management
✓ providers.py                - Provider management
✓ exports_*.py (multiple)     - Export functionality
✓ pack_*.py (multiple)        - Feature pack implementations
```

---

### BUSINESS INTELLIGENCE (5 routers)

```
✓ influence.py                - Influence tracking
✓ narrative.py                - Narrative generation
✓ story_engine.py             - Story creation
✓ explanation_engine.py       - Decision explanation
✓ insight.py                  - Insight generation
```

---

### INTEGRATION & BRIDGES (5 routers)

```
✓ notification_bridge.py      - Notification bridge
✓ tax_bridge.py               - Tax system bridge
✓ honeypot_bridge.py          - Honeypot integration
✓ api_clients.py              - External API clients
✓ integrations/ (service)     - Integration services
```

---

## Endpoint Count by Category

```
Admin & System              24-30 endpoints
Deal Management             20-25 endpoints
Lead Management             10-15 endpoints
User & Auth                 8-10 endpoints
Governance & Decisions      20-25 endpoints
Contracts                   18-22 endpoints
Financial Operations        30-35 endpoints
Analytics & Reporting       20-25 endpoints
Notifications               12-15 endpoints
Compliance & Security       18-22 endpoints
AI & Decision Engines       25-30 endpoints
Business Processes          40-50 endpoints
Scheduling & Automation     10-12 endpoints
Knowledge & Data            15-20 endpoints
Monitoring & Logging        15-18 endpoints
Specialized Operations      25-30 endpoints
───────────────────────────────────────────
TOTAL:                      350-450 endpoints
```

---

## Common Endpoint Patterns

### List/Retrieve
```
GET    /resource              - List all with pagination
GET    /resource/{id}         - Get single item
GET    /resource/search       - Search with filters
```

### Create/Update/Delete
```
POST   /resource              - Create new
PUT    /resource/{id}         - Update
PATCH  /resource/{id}         - Partial update
DELETE /resource/{id}         - Delete
```

### Action Endpoints
```
POST   /resource/{id}/action  - Trigger action
POST   /resource/{id}/finalize- Finalize/complete
POST   /resource/{id}/cancel  - Cancel
POST   /resource/{id}/approve - Approve/accept
```

### Status/Analysis
```
GET    /resource/{id}/status  - Get status
GET    /resource/{id}/analysis- Get analysis
GET    /resource/{id}/metrics - Get metrics
GET    /resource/{id}/history - Get history
```

### Batch Operations
```
POST   /resource/batch        - Batch create
PUT    /resource/batch        - Batch update
DELETE /resource/batch        - Batch delete
POST   /resource/bulk-action  - Bulk operations
```

---

## Router Dependencies

### Core Dependencies (always loaded)
- `system_boot.py` - Core system
- `health.py` - Health checks
- `jarvis.py` - Heimdall agent

### Common Service Dependencies
- `users.py` - For authentication
- `auth/` - Authentication services
- `rbac.py` - Access control
- `audit.py` - Audit logging

### Feature Dependencies
- Each module can depend on services and models
- Models loaded via `app.models.__init__`
- Services loaded as singletons with dependency injection

---

## Auto-Loading Process

```python
# app/main.py auto-loads routers like this:

for module_info in pkgutil.iter_modules([routers_package_path]):
    mod_name = module_info.name
    if mod_name not in skip_modules:  # Skip system_boot, __init__
        try:
            mod = import_module(f"{routers_pkg}.{mod_name}")
            router = getattr(mod, "router", None)
            if router:
                app.include_router(router)
                log.info(f"Autoloaded router: {mod_name}")
        except Exception as e:
            log.error(f"Failed loading {mod_name}: {e}")
```

---

## Router Prefix Mapping

Each router typically uses a prefix like:

```
✓ /admin - Admin operations
✓ /deals - Deal management
✓ /leads - Lead management
✓ /users - User management
✓ /governance - Governance
✓ /contracts - Contract operations
✓ /accounting - Financial
✓ /analytics - Analytics
✓ /notifications - Notifications
✓ /security - Security
✓ /ai - AI operations
✓ /workflows - Workflow operations
✓ /reports - Reporting
✓ /health - Health checks
✓ /system - System operations
... and many more custom prefixes
```

---

## Feature Packs

Many routers are organized into feature packs:

```
PACK A-B-C: Foundational Systems
PACK D-E: Financial Core
PACK F-G: Lead Management
PACK H-I: Deal Advancement
PACK J-K: Automation & Integration
PACK L-M-N: Advanced Features
PACK O-P-Q: Business Intelligence
PACK SPA: Special Purpose Application
PACK BSE: Banking & Settlement
... and many more specialized packs
```

Each pack typically includes routers, models, services, and schemas.

---

## Router Health Check

To verify router status:

```bash
# Get loaded router count
curl http://localhost:4000/healthz

# Expected response includes:
# "routers_loaded": <count>

# View all routes
python tmp_print_routes.py

# Verify specific router
pytest -k "test_<router_name>"
```

---

## Documentation Location

For detailed documentation on specific routers:

1. Check inline docstrings in router file
2. See FastAPI auto-docs: `http://localhost:4000/docs`
3. Check feature pack documentation
4. Review related model definitions in `models/`
5. Review related schemas in `schemas/`

---

**Generated:** April 12, 2026

