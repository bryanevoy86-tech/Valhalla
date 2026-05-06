# MILLION-PATH PREP: Non-Breaking Enhancements

**Status:** IMPLEMENTATION-READY  
**Risk Level:** LOW (no migrations, no route changes, no data structure changes)  
**Purpose:** Add supporting code that enables scaling without breaking live system  
**Timeline:** Before WeWeb connects or after, both safe  
**Last Updated:** 2026-04-13  

---

## WHAT'S SAFE TO DO NOW

✅ Create constants/enums files (Strategies, Roles, Zones, Stages)  
✅ Add documentation strings to routes  
✅ Create internal mapping files  
✅ Add comments to codebase  
✅ Create validation utilities  
✅ Add logging utilities  
✅ Define future data models (as code stubs)  
✅ Add route metadata  

❌ Do NOT: Change route signatures, add migrations, change data models, refactor execution layer  

---

## NON-BREAKING PREP TASKS

### TASK 1: Create Strategies Constants

**File:** `app/constants/strategies.py`

**Risk:** ZERO (new file, no imports anywhere yet)

**Implementation:**

```python
"""
Million-Path Strategy Layer Constants

This file defines the four launch-capable strategies and future strategies.
Used for case classification and team routing.
"""

from enum import Enum
from typing import Dict, Any

class StrategyType(str, Enum):
    """Launch-capable strategies"""
    WHOLESALE = "wholesale"
    HOLD = "hold"
    FLIP = "flip"
    PARTNERSHIP = "partnership"

class StrategyTypeAdvanced(str, Enum):
    """Future strategies (Year 2+)"""
    COMMERCIAL = "commercial"
    CREATIVE_FINANCE = "creative_finance"
    DEVELOPMENT = "development"
    ARBITRAGE = "arbitrage"
    ACQUISITION_FOR_EQUITY = "acquisition_for_equity"

STRATEGIES: Dict[str, Dict[str, Any]] = {
    "WHOLESALE": {
        "key": StrategyType.WHOLESALE,
        "name": "Wholesale",
        "description": "Buy low, sell to investor quickly, profit on spread",
        "min_spread_percent": 0.10,  # 10%
        "min_spread_dollars": 5000,
        "typical_timeline_days": 14,
        "owner_role": "wholesale_specialist",
        "risk_level": "low",
        "allows_partnership": False,
    },
    "HOLD": {
        "key": StrategyType.HOLD,
        "name": "Hold for Cash Flow",
        "description": "Rent out property, collect cash flow and appreciation",
        "min_cap_rate": 0.05,  # 5%
        "typical_hold_years": 5,
        "owner_role": "portfolio_manager",
        "risk_level": "medium",
        "allows_partnership": True,
    },
    "FLIP": {
        "key": StrategyType.FLIP,
        "name": "Flip / Renovate",
        "description": "Renovate and sell retail for profit",
        "min_profit_percent": 0.25,  # 25%
        "min_profit_dollars": 20000,
        "typical_timeline_days": 180,  # 6 months
        "owner_role": "construction_manager",
        "risk_level": "high",
        "allows_partnership": False,
    },
    "PARTNERSHIP": {
        "key": StrategyType.PARTNERSHIP,
        "name": "Partnership",
        "description": "Co-own with investor partner, split equity and profit",
        "min_our_equity_percent": 0.15,  # 15%
        "min_our_equity_dollars": 50000,
        "typical_hold_years": 5,
        "owner_role": "partnership_manager",
        "risk_level": "medium",
        "allows_partnership": True,
    },
}

STRATEGY_LIST = [s["key"] for s in STRATEGIES.values()]

def get_strategy_by_key(key: str) -> Dict[str, Any]:
    """Get strategy definition by key"""
    for strategy in STRATEGIES.values():
        if strategy["key"].value == key:
            return strategy
    return None

def is_viable_strategy(strategy: str) -> bool:
    """Check if strategy is in launch-capable list"""
    return strategy in STRATEGY_LIST
```

**Usage:** (Future - not yet integrated)
```python
from app.constants.strategies import STRATEGIES, StrategyType
# When classifying a case: get profitability threshold
strategy = STRATEGIES[StrategyType.WHOLESALE]
min_spread = strategy["min_spread_dollars"]
```

---

### TASK 2: Create Roles Constants

**File:** `app/constants/roles.py`

**Risk:** ZERO (new file, documentation only)

**Implementation:**

```python
"""
Million-Path Team Roles & RBAC

This file defines roles, permissions, and access levels.
Used for team delegation and access control (future: role-based API).
"""

from enum import Enum
from typing import Dict, List, Set

class RoleType(str, Enum):
    """Team role enumeration"""
    OWNER = "owner"
    INTAKE_VA = "intake_va"
    QUALIFICATION_VA = "qualification_va"
    FOLLOWUP_VA = "followup_va"
    CLOSER = "closer"
    ACQUISITIONS = "acquisitions"
    DISPO = "dispo"
    ZONE_LEAD = "zone_lead"
    OPERATOR_ADMIN = "operator_admin"

ROLES: Dict[str, Dict[str, any]] = {
    "OWNER": {
        "key": RoleType.OWNER,
        "title": "Owner",
        "description": "Business owner, final decision authority",
        "can_read_routes": [
            "GET /execution/cases",
            "GET /execution/cases/{id}",
            "GET /portfolio",
            "GET /governance/audit-log",
            "GET /team",
        ],
        "can_write_routes": [
            "POST /execution/cases/{id}/advance",
            "POST /execution/cases/{id}/assign",
            "POST /users",
        ],
        "owns_decisions": ["final_approval", "strategy", "team_hiring"],
        "max_cases_assigned": None,  # unlimited
        "launch_capable": True,
    },
    "INTAKE_VA": {
        "key": RoleType.INTAKE_VA,
        "title": "Intake Assistant",
        "description": "Initial opportunity intake and research",
        "can_read_routes": [
            "GET /execution/cases?stage=intake_processed",
            "GET /execution/cases/{id}",
        ],
        "can_write_routes": [
            "POST /execution/cases/{id}/add-notes",
        ],
        "owns_decisions": ["filter_disqualifiers", "compliance_check"],
        "max_cases_assigned": 20,
        "launch_capable": False,  # Need to hire VA first
    },
    "QUALIFICATION_VA": {
        "key": RoleType.QUALIFICATION_VA,
        "title": "Qualification Assistant",
        "description": "Financial analysis and deal viability assessment",
        "can_read_routes": [
            "GET /execution/cases?stage=intake_processed",
            "GET /execution/cases/{id}",
            "GET /research/comparables",
        ],
        "can_write_routes": [
            "POST /execution/cases/{id}/add-financial-analysis",
        ],
        "owns_decisions": ["viability_assessment"],
        "max_cases_assigned": 15,
        "launch_capable": False,
    },
    "FOLLOWUP_VA": {
        "key": RoleType.FOLLOWUP_VA,
        "title": "Followup Assistant",
        "description": "Seller contact, relationship building, persistence",
        "can_read_routes": [
            "GET /execution/cases?stage=ready_for_contact,contacted",
            "GET /execution/cases/{id}",
            "GET /contracts/offer-letter",
        ],
        "can_write_routes": [
            "POST /execution/cases/{id}/log-contact",
            "POST /execution/cases/{id}/add-seller-profile",
        ],
        "owns_decisions": ["contact_attempt", "followup_timing"],
        "max_cases_assigned": 25,
        "launch_capable": False,
    },
    "CLOSER": {
        "key": RoleType.CLOSER,
        "title": "Deal Closer",
        "description": "Negotiation, term finalization, contract management",
        "can_read_routes": [
            "GET /execution/cases?stage=contacted,negotiating",
            "GET /execution/cases/{id}",
            "GET /contracts",
        ],
        "can_write_routes": [
            "POST /execution/cases/{id}/update-negotiation-status",
            "POST /execution/cases/{id}/advance",
        ],
        "owns_decisions": ["negotiate_terms", "advance_to_contract"],
        "max_cases_assigned": 10,
        "launch_capable": False,
    },
    "DISPO": {
        "key": RoleType.DISPO,
        "title": "Disposition Manager",
        "description": "Exit strategy, buyer matching, property placement",
        "can_read_routes": [
            "GET /execution/cases?stage=closed",
            "GET /buyer",
            "GET /portfolio",
        ],
        "can_write_routes": [
            "POST /portfolio/add",
            "POST /buyer_match",
        ],
        "owns_decisions": ["buyer_matching", "exit_strategy"],
        "max_cases_assigned": 20,
        "launch_capable": False,
    },
    "ZONE_LEAD": {
        "key": RoleType.ZONE_LEAD,
        "title": "Zone Leader",
        "description": "Geographic area manager, team coordinator",
        "can_read_routes": [
            "GET /execution/cases?zone={zone_id}",
            "GET /execution/cases/{id}",
            "GET /zone/{zone_id}/dashboard",
        ],
        "can_write_routes": [
            "POST /execution/cases/{id}/process",  # within zone
            "POST /execution/cases/{id}/assign",  # within zone
            "POST /zone/{zone_id}/settings",
        ],
        "owns_decisions": ["zone_strategy", "team_routing"],
        "max_cases_assigned": None,  # zone-wide, unlimited
        "launch_capable": False,
    },
    "OPERATOR_ADMIN": {
        "key": RoleType.OPERATOR_ADMIN,
        "title": "System Administrator",
        "description": "System access, audit, compliance",
        "can_read_routes": ["GET /governance/audit-log", "GET /users"],
        "can_write_routes": ["POST /users", "POST /system/settings"],
        "owns_decisions": ["user_management", "system_configuration"],
        "max_cases_assigned": 0,
        "launch_capable": False,
    },
}

def get_role_by_key(key: str) -> Dict[str, any]:
    """Get role definition by key"""
    for role in ROLES.values():
        if role["key"].value == key:
            return role
    return None

def is_launch_capable_role(role: str) -> bool:
    """Check if this role can be used on day-one"""
    role_def = get_role_by_key(role)
    return role_def and role_def.get("launch_capable", False)

def get_launch_roles() -> List[str]:
    """Get all day-one capable roles"""
    return [r["key"].value for r in ROLES.values() if r.get("launch_capable")]
```

---

### TASK 3: Create Pipeline Stages Constants

**File:** `app/constants/pipeline_stages.py`

**Risk:** ZERO (new file, documentation)

**Implementation:**

```python
"""
Million-Path Pipeline Stages

Defines all possible case stages and stage transitions.
Used for validation and workflow routing.
"""

from enum import Enum
from typing import Dict, List, Set

class PipelineStage(str, Enum):
    """Launch-capable stages"""
    INTAKE = "intake"
    INTAKE_PROCESSED = "intake_processed"
    READY_FOR_CONTACT = "ready_for_contact"
    CONTACTED = "contacted"
    NEGOTIATING = "negotiating"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"
    DEAD = "dead"

class PipelineStageAdvanced(str, Enum):
    """Future stages (Year 2+)"""
    DISPO_READY = "dispo_ready"
    BUYER_MATCHING = "buyer_matching"
    HOLD_REVIEW = "hold_review"
    PARTNERSHIP_REVIEW = "partnership_review"
    LEGAL_REVIEW = "legal_review"
    FUNDING_READY = "funding_ready"

# Define valid stage transitions
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    PipelineStage.INTAKE.value: {
        PipelineStage.INTAKE_PROCESSED.value,
    },
    PipelineStage.INTAKE_PROCESSED.value: {
        PipelineStage.READY_FOR_CONTACT.value,
        PipelineStage.DEAD.value,
    },
    PipelineStage.READY_FOR_CONTACT.value: {
        PipelineStage.CONTACTED.value,
        PipelineStage.DEAD.value,
    },
    PipelineStage.CONTACTED.value: {
        PipelineStage.NEGOTIATING.value,
        PipelineStage.DEAD.value,
    },
    PipelineStage.NEGOTIATING.value: {
        PipelineStage.UNDER_CONTRACT.value,
        PipelineStage.DEAD.value,
    },
    PipelineStage.UNDER_CONTRACT.value: {
        PipelineStage.CLOSED.value,
        PipelineStage.DEAD.value,
    },
    PipelineStage.CLOSED.value: set(),  # Terminal
    PipelineStage.DEAD.value: set(),  # Terminal
}

STAGE_DEFINITIONS: Dict[str, Dict[str, any]] = {
    "INTAKE": {
        "key": PipelineStage.INTAKE,
        "name": "Intake",
        "description": "Initial opportunity capture",
        "owner_role": "intake_va",
        "duration_estimate_hours": 0.25,
        "typical_tasks": ["parse_opportunity"],
        "is_terminal": False,
    },
    "INTAKE_PROCESSED": {
        "key": PipelineStage.INTAKE_PROCESSED,
        "name": "Intake Processed",
        "description": "System analyzed, awaiting operator decision",
        "owner_role": "owner",
        "duration_estimate_hours": 24,
        "typical_tasks": [
            "verify_property",
            "contact_seller",
            "calculate_spread",
            "decision_go_nogo",
        ],
        "is_terminal": False,
    },
    "READY_FOR_CONTACT": {
        "key": PipelineStage.READY_FOR_CONTACT,
        "name": "Ready for Contact",
        "description": "Approved, now time to contact seller",
        "owner_role": "followup_va",
        "duration_estimate_hours": 4,
        "typical_tasks": ["prepare_contact_package"],
        "is_terminal": False,
    },
    "CONTACTED": {
        "key": PipelineStage.CONTACTED,
        "name": "Contacted",
        "description": "Seller engaged, building relationship",
        "owner_role": "followup_va",
        "duration_estimate_hours": 48,
        "typical_tasks": ["seller_calls", "terms_discussion"],
        "is_terminal": False,
    },
    "NEGOTIATING": {
        "key": PipelineStage.NEGOTIATING,
        "name": "Negotiating",
        "description": "Terms being finalized",
        "owner_role": "closer",
        "duration_estimate_hours": 168,
        "typical_tasks": [
            "finalize_offer",
            "inspection_contingency",
            "timeline_agreement",
        ],
        "is_terminal": False,
    },
    "UNDER_CONTRACT": {
        "key": PipelineStage.UNDER_CONTRACT,
        "name": "Under Contract",
        "description": "Legal agreement signed, closing process",
        "owner_role": "acquisitions",
        "duration_estimate_hours": 336,
        "typical_tasks": [
            "title_search",
            "inspection",
            "appraisal",
            "financing_approval",
        ],
        "is_terminal": False,
    },
    "CLOSED": {
        "key": PipelineStage.CLOSED,
        "name": "Closed",
        "description": "Ownership transferred, deal complete",
        "owner_role": "dispo",
        "duration_estimate_hours": 0,
        "typical_tasks": ["record_deed", "arrange_disposition"],
        "is_terminal": False,
    },
    "DEAD": {
        "key": PipelineStage.DEAD,
        "name": "Dead",
        "description": "Opportunity rejected or inactive",
        "owner_role": "system",
        "duration_estimate_hours": 0,
        "typical_tasks": [],
        "is_terminal": True,
    },
}

def is_valid_transition(from_stage: str, to_stage: str) -> bool:
    """Check if stage transition is allowed"""
    valid_to_stages = VALID_TRANSITIONS.get(from_stage, set())
    return to_stage in valid_to_stages

def get_next_stages(current_stage: str) -> Set[str]:
    """Get all valid next stages for a given stage"""
    return VALID_TRANSITIONS.get(current_stage, set())

def is_terminal_stage(stage: str) -> bool:
    """Check if stage is a terminal/end state"""
    stage_def = STAGE_DEFINITIONS.get(stage.upper())
    return stage_def and stage_def.get("is_terminal", False)
```

---

### TASK 4: Create Zones Constants (Soft Provisioning)

**File:** `app/constants/zones.py`

**Risk:** ZERO (soft provisioning, no table yet)

**Implementation:**

```python
"""
Million-Path Geographic Zones (Soft Provisioning)

This file defines zones for future multi-zone operations.
No database changes needed - used for planning and documentation.
Real zone table created in post-WeWeb migration.
"""

from enum import Enum
from typing import Dict, List

class ZoneKey(str, Enum):
    """Zone identifiers for future use"""
    FLORIDA_MIAMI = "florida_miami"
    FLORIDA_TAMPA = "florida_tampa"
    FLORIDA_JACKSONVILLE = "florida_jacksonville"
    TEXAS_AUSTIN = "texas_austin"
    TEXAS_DALLAS = "texas_dallas"
    TEXAS_HOUSTON = "texas_houston"
    CALIFORNIA_LA = "california_la"
    CALIFORNIA_SF = "california_sf"

ZONES_SOFT_PROVISION: Dict[str, Dict[str, any]] = {
    "florida_miami": {
        "zone_id": "florida_miami",
        "zone_name": "Miami, Florida",
        "country": "US",
        "state_province": "FL",
        "city": "Miami",
        "market_type": "urban",
        "focus_strategy": "wholesale",  # Primary strategy for this zone
        "is_active": False,  # Not active until you deploy there
        "lead_volume_targets": 20,  # Target 20 deals/month
        "profit_target_annual": 240000,  # $240k annual goal
        "zone_lead_user_id": None,  # Assign when hiring
        "description": "Primary market, urban wholesale and residential",
    },
    "florida_tampa": {
        "zone_id": "florida_tampa",
        "zone_name": "Tampa, Florida",
        "country": "US",
        "state_province": "FL",
        "city": "Tampa",
        "market_type": "suburban",
        "focus_strategy": "hold",
        "is_active": False,
        "lead_volume_targets": 15,
        "profit_target_annual": 180000,
        "zone_lead_user_id": None,
        "description": "Suburban market, good rents and appreciation",
    },
    "texas_austin": {
        "zone_id": "texas_austin",
        "zone_name": "Austin, Texas",
        "country": "US",
        "state_province": "TX",
        "city": "Austin",
        "market_type": "urban",
        "focus_strategy": "flip",
        "is_active": False,
        "lead_volume_targets": 25,
        "profit_target_annual": 300000,
        "zone_lead_user_id": None,
        "description": "High growth market, good flip potential",
    },
    # More zones can be added as you expand
}

def get_zone(zone_id: str) -> Dict[str, any]:
    """Get zone definition by ID"""
    return ZONES_SOFT_PROVISION.get(zone_id)

def get_active_zones() -> List[Dict[str, any]]:
    """Get all currently active zones"""
    return [z for z in ZONES_SOFT_PROVISION.values() if z.get("is_active")]

def list_all_zones() -> List[Dict[str, any]]:
    """List all provisioned zones (active and inactive)"""
    return list(ZONES_SOFT_PROVISION.values())

# Note: When you expand to new zone, simply:
# 1. Add it to ZONES_SOFT_PROVISION above
# 2. Set is_active = True
# 3. Assign zone_lead_user_id when you hire zone manager
# 4. No database migration needed
```

---

## SUMMARY: SAFE ENHANCEMENTS

### Could Do This Week (Zero Risk):

```
✅ Create app/constants/strategies.py
✅ Create app/constants/roles.py
✅ Create app/constants/pipeline_stages.py
✅ Create app/constants/zones.py
✅ Add docstrings to existing routes
✅ Create internal documentation utilities
```

### Timeline:
- Do this NOW or do it AFTER WeWeb launch - both timing is safe
- These constants enable future scaling without breaking anything live
- No imports needed yet - they're just reference files

### Next Steps (After Launch):
```
⏳ Import strategies constants into case classification logic
⏳ Import roles constants into API gateway (RBAC)
⏳ Import stages constants into validation layer
⏳ Create zones table migration (week 2 post-launch)
```

---

## CHANGELOG ENTRY

If you implement the above, add to a separate changelog file:

**File:** `docs/MILLION_PATH_PREP_CHANGELOG.md`

```markdown
# Million-Path Prep Changes

## 2026-04-13

### Added (Non-Breaking)
- [x] Created app/constants/strategies.py
  - Defined StrategyType enum (Wholesale, Hold, Flip, Partnership)
  - Added STRATEGIES dict with profitability thresholds
  - 0 breaking changes, 0 deployments needed
  
- [x] Created app/constants/roles.py
  - Defined RoleType enum (Owner, VAs, Closer, etc.)
  - Added ROLES dict with permissions (future RBAC)
  - 0 breaking changes, 0 deployments needed
  
- [x] Created app/constants/pipeline_stages.py
  - Defined PipelineStage enum (Intake → Closed)
  - Added VALID_TRANSITIONS for stage routing
  - 0 breaking changes, 0 deployments needed
  
- [x] Created app/constants/zones.py
  - Soft-provisioned future zones (Miami, Tampa, Austin, etc.)
  - No database changes, documentation only
  - 0 breaking changes, 0 deployments needed

### Status
All non-breaking prep complete. System ready for:
- Day-one Execution Console launch ✓
- Million-path scaling foundation locked in ✓
- Zero technical debt introduced ✓
```

---

**Document Owner:** Engineering / Architecture  
**Status:** IMPLEMENTATION-READY  
**Risk Level:** ZERO  
**Last Updated:** 2026-04-13  
