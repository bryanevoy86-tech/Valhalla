# MILLION-PATH: Scale Data Model Design

**Status:** PROPOSED (NOT APPLIED)  
**Purpose:** Define required scale-layer fields for multi-zone, team delegation, multi-strategy support  
**Timeline:** Safe for post-WeWeb migration (no breaking changes)  
**Last Updated:** 2026-04-13  

---

## PHILOSOPHY

This document defines what fields the system MUST support to enable the million-path scaling vision. It is a DESIGN DOCUMENT, not a migration yet.

**Key Principles:**
- Non-breaking: All fields are additive with sensible defaults
- Backward-compatible: Existing cases continue to work
- Safe for later: Can be applied in migration after WeWeb stabilizes
- Foundation-ready: Every field can be soft-provisioned today via constants/enums

---

## A. DEAL / INTAKE SCALE FIELDS

### Current Live Model (deal_intake_exec)
```
- id (PK)
- raw_text (VARCHAR, original opportunity text)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### Proposed Scale Additions

#### A1. Geographic Identifiers
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| zone_id | UUID | NULL | Which zone owns this deal | YES* |
| market | VARCHAR(50) | "unclassified" | Market cluster (suburban, urban, rural) | YES |
| state_province | CHAR(2) | NULL | State/province abbreviation | YES |
| country | CHAR(2) | "US" | Country code | YES |
| city | VARCHAR(100) | NULL | City name | YES |
| zip_postal | VARCHAR(20) | NULL | Postal code | YES |

*Can add immediately with NULL default; populate via WeWeb form

#### A2. Deal Classification
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| strategy | VARCHAR(50) | "wholesale" | Primary strategy (wholesale, hold, flip, partnership) | YES |
| exit_type | VARCHAR(50) | "unknown" | How we'll exit (retail, wholesaler buyer, hold, partnership exit) | YES |
| source | VARCHAR(100) | "manual_intake" | Where lead came from (MLS, referral, direct, website) | YES |
| confidence_score | FLOAT | 0.0 | ML classification confidence (0-100) | YES |
| risk_level | VARCHAR(20) | "medium" | Risk assessment (low, medium, high, critical) | YES |

#### A3. Deal Value Signals
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| purchase_price_estimate | NUMERIC | 0 | What we'd pay | YES |
| arv_estimate | NUMERIC | 0 | Estimated after-repair value | YES |
| repair_estimate | NUMERIC | 0 | Estimated repairs | YES |
| profit_margin_estimate | NUMERIC | 0 | Estimated profit | YES |
| holding_period_months | INT | 0 | How long we'd hold | YES |

#### A4. Sourcing Metadata
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| lead_source_id | UUID | NULL | FK to LeadSource table | YES |
| buyer_profile_id | UUID | NULL | FK to buyer profile this matches | YES |
| partnership_id | UUID | NULL | If partnership deal, which partner | YES |
| campaign_id | VARCHAR(100) | NULL | Marketing campaign identifier | YES |

### Implementation Safety
- ✅ All fields nullable or have safe defaults
- ✅ Can be added without dropping/recreating table
- ✅ Existing data continues with NULL/defaults
- ✅ Can populate gradually with WeWeb forms
- ✅ Ready for migration timestamp: post-WeWeb-launch

---

## B. PIPELINE / CASE SCALE FIELDS

### Current Live Model (execution_cases)
```
- id (PK)
- intake_id (FK)
- case_type (VARCHAR)
- route_target (VARCHAR)
- current_stage (VARCHAR)
- current_status (VARCHAR)
- safe_mode (BOOLEAN)
- blocked (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### Proposed Scale Additions

#### B1. Pipeline & Workflow
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| pipeline_stage | VARCHAR(50) | "intake" | Current stage (intake → processed → contacted → negotiating → under_contract → closed) | YES |
| stage_history | JSONB | [] | Timeline of stage transitions | YES |
| days_in_stage | INT | 0 | Calculated field: days at current stage | YES |
| sla_deadline | TIMESTAMP | NULL | When this case must move to next stage | YES |

#### B2. Assignment & Ownership
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| assigned_to_user_id | UUID | NULL | Who owns this case | YES |
| owner_role | VARCHAR(50) | NULL | Owner's role (king, va_intake, va_qualify, closer) | YES |
| escalated_to | UUID | NULL | If escalated, who to | YES |
| zone_assigned | UUID | NULL | Which zone manager owns it | YES |
| team_assigned | VARCHAR(100) | NULL | Which team/group owns it | YES |

#### B3. Priority & Urgency
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| priority_level | INT | 5 | 1=critical, 10=lowest | YES |
| urgency_flag | BOOLEAN | FALSE | Is this time-sensitive? | YES |
| escalation_flag | BOOLEAN | FALSE | Does this need immediate attention? | YES |
| hold_flag | BOOLEAN | FALSE | Is this on hold? | YES |
| hold_reason | VARCHAR(500) | NULL | Why on hold? | YES |

#### B4. Deal Decisions
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| final_decision | VARCHAR(50) | NULL | (proceed, pass, hold, escalate, parked) | YES |
| decision_rationale | TEXT | NULL | Why we decided this | YES |
| decision_maker | UUID | NULL | Who made the decision | YES |
| decision_timestamp | TIMESTAMP | NULL | When decided | YES |

#### B5. Financial Tracking
| Field | Type | Default | Purpose | Safe Now? |
|-------|------|---------|---------|-----------|
| total_profit_expected | NUMERIC | 0 | Final profit projection | YES |
| roi_percentage | NUMERIC | 0 | Return on investment % | YES |
| year_to_date_profit | NUMERIC | 0 | Contribution to annual P&L | YES |
| deal_status_financial | VARCHAR(50) | "pending" | Financial stage (pending, funded, closed, loss) | YES |

### Implementation Safety
- ✅ All additive fields with sensible defaults
- ✅ Can be applied in single non-blocking migration
- ✅ JSONB fields allow flexible history tracking
- ✅ FKs to users/teams enable later delegation features
- ✅ Ready for migration timestamp: post-WeWeb-launch

---

## C. ZONE DATA MODEL (NEW TABLE)

### Purpose
Enable multi-zone operations with geographic and market-based organization.

### Proposed Schema
```sql
CREATE TABLE zones (
  zone_id UUID PRIMARY KEY,
  zone_name VARCHAR(100) NOT NULL,
  country CHAR(2) DEFAULT 'US',
  state_province CHAR(2),
  city VARCHAR(100),
  market_type VARCHAR(50), -- suburban, urban, rural, commercial
  focus_strategy VARCHAR(100), -- primary strategy for this zone
  is_active BOOLEAN DEFAULT TRUE,
  market_conditions VARCHAR(500), -- brief market notes
  lead_volume_targets INT, -- how many deals/month
  profit_target_annual NUMERIC, -- annual P&L goal
  zone_lead_id UUID, -- FK to user (team manager)
  portfolio_value NUMERIC DEFAULT 0, -- total active deals value
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(country, state_province, city)
);
```

### Current State
- No zones table exists yet
- Can be soft-provisioned with constants/enums NOW
- Safe to create as new table post-WeWeb

### Constants File for Day-One (NON-BREAKING)
Can create `app/constants/zones.py`:
```python
ZONES = {
    "florida_miami": {
        "name": "Miami, FL",
        "country": "US",
        "state": "FL",
        "city": "Miami",
        "type": "urban",
    },
    "florida_tampa": {
        "name": "Tampa, FL",
        "country": "US",
        "state": "FL",
        "city": "Tampa",
        "type": "suburban",
    },
    # ... more zones
}
```

---

## D. TEAM / ROLE OPERATING MODEL

### Current State
- No formal role table yet
- Cases hardcoded to "king" user
- No delegation system

### Proposed Role Definition (NON-BREAKING)

Create `app/constants/roles.py`:

```python
TEAM_ROLES = {
    "owner": {
        "description": "Business owner/operator",
        "can_access": ["all_cases", "all_zones", "reporting"],
        "owns_actions": ["final_decision", "escalation_approval"],
    },
    "intake_va": {
        "description": "Virtual assistant - initial intake",
        "can_access": ["new_intakes", "assigned_cases"],
        "owns_actions": ["intake_completion", "compliance_check"],
    },
    "qualification_va": {
        "description": "Virtual assistant - deal qualification",
        "can_access": ["intake_processed_cases"],
        "owns_actions": ["financial_analysis", "viability_assessment"],
    },
    "followup_va": {
        "description": "Virtual assistant - persistent contact",
        "can_access": ["contacted_cases", "assigned_cases"],
        "owns_actions": ["seller_contact", "followup_logging"],
    },
    "closer": {
        "description": "Deal closer / negotiator",
        "can_access": ["viable_cases", "negotiating_cases"],
        "owns_actions": ["negotiate_terms", "send_contract"],
    },
    "acquisitions": {
        "description": "Acquisitions manager",
        "can_access": ["all_cases"],
        "owns_actions": ["fund_authorization", "acquisition_close"],
    },
    "dispo": {
        "description": "Disposition specialist",
        "can_access": ["closed_cases", "resale_cases"],
        "owns_actions": ["buyer_matching", "resale_coordination"],
    },
    "zone_lead": {
        "description": "Zone manager / geographic lead",
        "can_access": ["zone_cases", "zone_reporting"],
        "owns_actions": ["zone_strategy", "team_routing", "performance_review"],
    },
    "operator_admin": {
        "description": "System administrator",
        "can_access": ["all", "system_settings"],
        "owns_actions": ["user_management", "audit_access"],
    },
}
```

### Safe to Apply
- ✅ Constants file only (no DB changes)
- ✅ Can be referenced in code immediately
- ✅ Enables planning without breaking anything
- ✅ Ready for full RBAC implementation post-WeWeb

---

## WHAT IS ALREADY PRESENT

### LeadIntake Model (V1)
- ✅ Raw text capture
- ✅ Timestamps
- ⚠️  Missing: Zone, market, source, strategy fields

### ExecutionCase Model (V1)
- ✅ Case type classification
- ✅ Pipeline stage (basic)
- ✅ Blocked/safe_mode flags
- ✅ Next action determination
- ⚠️  Missing: Assigned team member, priority, escalation flag, financial tracking

### ExecutionEvent Model (V1)
- ✅ Event logging
- ⚠️  Missing: Actor role, event categorization

### Task Model (V1)
- ✅ Task list generation
- ✅ Task prioritization (basic)
- ⚠️  Missing: Assignment tracking, completion workflow

### LeadSource Model
- ✅ Exists and can be linked
- Ready to connect to Intake via lead_source_id FK

### Missing Critical Tables
- ❌ Zones table (needs creation)
- ❌ Users/Team Members table (exists elsewhere? needs integration)
- ❌ Role definitions (can be constants)
- ❌ Financial tracking (can be added to ExecutionCase)

---

## WHAT IS MISSING FOR SCALE

| Capability | Where Needed | Safe to Add? | Timeline |
|------------|-------------|-------------|----------|
| **Geographic hierarchy** | Zone → City → State → Country | YES | Post-WeWeb migration |
| **Team member assignment** | ExecutionCase.assigned_to_id | YES | Post-WeWeb migration |
| **Role-based access control** | API layer | PARTIAL | Can stub now |
| **Priority management** | ExecutionCase fields | YES | Post-WeWeb migration |
| **Financial projections** | ExecutionCase extension | YES | Post-WeWeb migration |
| **Escalation workflows** | API layers + notification | NO | Post-launch (too risky) |
| **Bulk operations** | Multiple cases at once | NO | Post-launch scaling |
| **Reporting/analytics** | Separate views | NO | Post-launch analytics |
| **Buyer matching** | External service integration | NO | Post-launch partnerships |
| **Contract automation** | External service | NO | Post-launch workflows |

---

## PROPOSED IMPLEMENTATION TIMELINE

### NOW (Already Live, No Changes)
```
✅ POST /execution/intake → lead_intake_exec table
✅ POST /execution/intake/{id}/process → execution_cases table
✅ GET /execution/cases/{id} → retrieve case
```

### IMMEDIATELY SAFE (Constants Only)
```
✅ Add app/constants/zones.py → Zone definitions
✅ Add app/constants/roles.py → Role definitions
✅ Add app/constants/strategies.py → Strategy definitions
⚠️  Deploy as documentation, don't apply to schema yet
```

### POST-WEWEB MIGRATION (Week 1)
```
📋 Add geographic fields to lead_intake_exec
   - zone_id, market, state_province, city, zip_postal
📋 Add classification fields to lead_intake_exec
   - strategy, exit_type, source, confidence_score, risk_level
📋 Add value fields to lead_intake_exec
   - purchase_price_est, arv_est, repair_est, profit_margin_est
⚠️  Test thoroughly before applying
```

### POST-WEWEB MIGRATION (Week 2)
```
📋 Add pipeline fields to execution_cases
   - pipeline_stage (extend/replace current_stage)
   - stage_history (JSONB)
   - sla_deadline
📋 Add assignment fields to execution_cases
   - assigned_to_user_id
   - owner_role
   - escalated_to
   - zone_assigned
   - team_assigned
📋 Add priority fields to execution_cases
   - priority_level, urgency_flag, escalation_flag
📋 Add decision fields to execution_cases
   - final_decision, decision_rationale, decision_maker
⚠️  Roll out incrementally with feature flags
```

### POST-WEWEB MIGRATION (Week 3+)
```
📋 Create zones table
   - One-time migration, minimal risk
📋 Integrate user/team lookup
   - Connect to existing user management
📋 Enable financial tracking views
   - Read-only reporting layer
```

---

## RISK ASSESSMENT

### Low Risk (Can apply anytime)
- Adding nullable columns to lead_intake_exec
- Adding nullable columns to execution_cases
- Creating new constants files
- Adding new standalone tables (zones)

### Medium Risk (Test carefully)
- JSONB columns (need to verify serialization)
- Foreign keys to user management (must coordinate with auth)
- Integer/numeric fields for financial tracking

### High Risk (DO NOT APPLY YET)
- Removing or renaming existing columns
- Changing primary keys or foreign keys
- Applying complex migrations to execution_cases while live
- Changing route signatures

---

## BACKWARD COMPATIBILITY CHECKLIST

- [x] All new fields have sensible defaults (NULL or 0)
- [x] Existing queries continue to work
- [x] Existing API responses not broken
- [x] No required fields added to existing tables
- [x] All new fields are optional
- [x] Constants don't affect runtime behavior

---

## DOCUMENTATION REFERENCES

- **Zones**: See MILLION_PATH_ZONE_MODEL.md
- **Roles**: See MILLION_PATH_TEAM_MODEL.md
- **Strategies**: See MILLION_PATH_STRATEGY_LAYER.md
- **Pipeline States**: See MILLION_PATH_PIPELINE_STATES.md

---

## NEXT STEPS

1. **Week 1**: Review this model with architect
2. **Week 2**: Apply constants files (zero-risk)
3. **Week 3**: Create zones table (new table, safe)
4. **Week 4+**: Roll out field additions in batches with feature flags

---

**Document Owner:** Architecture Team  
**Review Required:** Before applying any migrations  
**Last Updated:** 2026-04-13  
**Status:** DESIGN PHASE - NOT YET APPLIED  
