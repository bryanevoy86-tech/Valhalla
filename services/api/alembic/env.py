from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Ensure /app/services/api is on sys.path so 'from app.*' imports resolve
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

# Import Base from app.core.db (NOT 'valhalla')
from app.core.db import Base

# Models imported for metadata discovery
from app.models.builder import BuilderTask, BuilderEvent
from app.models.capital import CapitalIntake
from app.integrity.models import IntegrityEvent
from app.models.grants import GrantSource, GrantRecord
from app.models.match import Buyer, DealBrief
from app.models.contracts import ContractTemplate
# from app.models.contracts import ContractRecord  # Doesn't exist
from app.models.intake import LeadIntake
from app.models.notify import Outbox
from app.loki.models import LokiReview, LokiFinding
from app.god.models import GodReviewCase, GodReviewEvent
from app.sync.models import GodSyncRecord
from app.specialists.models import HumanSpecialist, SpecialistCaseComment
from app.models.god_verdicts import GodVerdict
from app.models.disputes import Dispute
from app.models.meeting_recordings import MeetingRecording
from app.models.tax_interpretations import TaxOpinion
from app.models.god_case import GodCase
from app.models.specialist_feedback import SpecialistFeedback

# PACK AP: Decision Governance
from app.models.decision_governance import DecisionPolicy, DecisionRecord

# PACK AQ: Workflow Guardrails  
from app.models.workflow_guardrails import WorkflowGuardrail

# PACK AR: Heimdall Workload
from app.models.heimdall_workload import HeimdallJob, HeimdallWorkloadConfig

# PACK AS: Empire Journal Engine
from app.models.empire_journal import JournalEntry

# PACK AT: User Summary Snapshots
from app.models.user_summary import UserSummarySnapshot

# PACK AU: Trust & Residency Profiles
from app.models.trust_residency import TrustResidencyProfile

# PACK AV: Story Mode Engine
from app.models.story_mode import StoryPrompt, StoryOutput

# PACK AW: Entity Links / Relationship Graph
from app.models.entity_links import EntityLink

# PACK AX: Feature Flags & Experiments
from app.models.feature_flags import FeatureFlag

# Additional models referenced in services
from app.models.children import ChildrenHub
from app.models.freeze_events import FreezeEvent

# PACK SA: Grant Eligibility Engine
from app.models.grant_eligibility import GrantProfile, EligibilityChecklist

# PACK SB: Business Registration Navigator
from app.models.registration_navigator import RegistrationFlowStep, RegistrationStageTracker

# PACK SC: Banking & Accounts Structure Planner
from app.models.banking_structure_planner import (
    BankAccountPlan,
    AccountSetupChecklist,
    AccountIncomeMapping,
)

# PACK SD: Credit Card & Spending Framework
from app.models.credit_card_spending import (
    CreditCardProfile,
    SpendingRule,
    SpendingTransaction,
    MonthlySpendingSummary,
)

# PACK SE: Vehicle Use & Expense Categorization
from app.models.vehicle_tracking import (
    VehicleProfile,
    VehicleTripLog,
    VehicleExpense,
    MileageSummary,
)

# PACK SF: CRA Document Vault & Organization
from app.models.cra_organization import (
    CRADocument,
    CRASummary,
    CRACategoryMap,
    FiscalYearSnapshot,
)

# PACK SG: Income Routing & Separation Engine
from app.models.income_routing import (
    IncomeRouteRule,
    IncomeEvent,
    IncomeRoutingLog,
    IncomeRoutingSummary,
)

# PACK SH: Multi-Year Projection Snapshot Framework
from app.models.projection_framework import (
    ProjectionScenario,
    ProjectionYear,
    ProjectionVariance,
    ProjectionReport,
)

# PACK SI: Real Estate Acquisition & BRRRR Planner
from app.models.brrrr_planner import (
    BRRRRDeal,
    BRRRRFundingPlan,
    BRRRRCashflowEntry,
    BRRRRRefinanceSnapshot,
    BRRRRSummary,
)

# PACK SJ: Wholesale Deal Machine
from app.models.wholesale_deals import (
    WholesaleLead,
    WholesaleOffer,
    AssignmentRecord,
    BuyerProfile,
    WholesalePipelineSnapshot,
)

# PACK SK: Arbitrage/Side-Hustle Opportunity Tracker
from app.models.opportunity_tracker import (
    Opportunity,
    OpportunityScore,
    OpportunityPerformance,
    OpportunitySummary,
)

# PACK SL: Personal Master Dashboard
from app.models.personal_dashboard import (
    FocusArea,
    PersonalRoutine,
    RoutineCompletion,
    FamilySnapshot,
    LifeDashboard,
    PersonalGoal,
    MoodLog,
)

# PACK SM: Kids Education & Development Engine
from app.models.kids_education import (
    ChildProfile,
    LearningPlan,
    EducationLog,
    ChildSummary,
)

# PACK SN: Mental Load Offloading Engine
from app.models.mental_load import (
    MentalLoadEntry,
    DailyLoadSummary,
    LoadOffloadWorkflow,
)

# PACK SO: Long-Term Empire Governance Map
from app.models.empire_governance import (
    EmpireRole,
    RoleHierarchy,
    SuccessionPlan,
    EmpireGovernanceMap,
)

# PACK SP: Life Event & Crisis Management Engine
from app.models.pack_sp import (
    CrisisProfile,
    CrisisActionStep,
    CrisisLogEntry,
    CrisisWorkflow,
)

# PACK SQ: Partner / Marriage Stability Ops Module
from app.models.pack_sq import (
    RelationshipOpsProfile,
    CoParentingSchedule,
    HouseholdResponsibility,
    CommunicationLog,
)

# PACK SO Legacy: Long-Term Legacy & Succession Archive Engine
from app.models.pack_so_legacy import (
    LegacyProfile,
    KnowledgePackage,
    SuccessionStage,
    LegacyVault,
)

# PACK ST: Financial Stress Early Warning Engine
from app.models.pack_st import (
    FinancialIndicator,
    FinancialStressEvent,
    FinancialStressSummary,
)

# PACK SU: Personal Safety & Risk Mitigation Planner
from app.models.pack_su import (
    SafetyCategory,
    SafetyChecklist,
    SafetyPlan,
    SafetyEventLog,
)

# PACK SV: Empire Growth Navigator
from app.models.pack_sv import (
    EmpireGoal,
    GoalMilestone,
    ActionStep,
)

# PACK SW: Life Timeline & Major Milestones Engine
from app.models.pack_sw import (
    LifeEvent,
    LifeMilestone,
    LifeTimelineSnapshot,
)

# PACK SX: Emotional Neutrality & Stability Log
from app.models.pack_sx import (
    EmotionalStateEntry,
    StabilityLog,
    NeutralSummary,
)

# PACK SY: Strategic Decision History & Reason Archive
from app.models.pack_sy import (
    StrategicDecision,
    DecisionRevision,
    DecisionChainSnapshot,
)

# PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive
from app.models.pack_sz import (
    PhilosophyRecord,
    EmpirePrinciple,
    PhilosophySnapshot,
)

# PACK TA: Trust, Loyalty & Relationship Mapping
from app.models.pack_ta import (
    RelationshipProfile,
    TrustEventLog,
    RelationshipMapSnapshot,
)

# PACK TB: Daily Behavioral Rhythm & Tempo Engine
from app.models.pack_tb import (
    DailyRhythmProfile,
    TempoRule,
    DailyTempoSnapshot,
)

# PACK TC: Heimdall Ultra Mode Engine
from app.models.heimdall_ultra import HeimdallUltraConfig

# PACK TD: Resilience & Recovery Planner
from app.models.resilience import SetbackEvent, RecoveryPlan, RecoveryAction

# PACK TE: Life Roles & Capacity Engine
from app.models.life_roles import LifeRole, RoleCapacitySnapshot

# PACK TF: System Tune List Engine
from app.models.system_tune import TuneArea, TuneItem

# PACK TG: Mental Load Offloading Engine
from app.models.mental_load import MentalLoadEntry, MentalLoadSummary

# PACK TH: Crisis Management Engine
from app.models.crisis import CrisisProfile, CrisisActionStep, CrisisLogEntry

# PACK TI: Financial Stress Early Warning Engine
from app.models.financial_stress import FinancialIndicator, FinancialStressEvent

# Research models not yet created - comment out for now
# from app.models.research import ResearchSource, ResearchDoc, ResearchQuery, Playbook

config = context.config

# Pull DATABASE_URL from environment for Render and force-set it on the config
db_url = os.getenv("DATABASE_URL")
if db_url:
    # Ensure Alembic uses the env var rather than the fallback in alembic.ini
    config.set_main_option("sqlalchemy.url", db_url)
else:
    # Fall back to value from alembic.ini section if env var not set
    section = config.get_section(config.config_ini_section) or {}
    # no-op: section already contains sqlalchemy.url from alembic.ini

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # engine_from_config expects the section dict and a prefix such as
    # 'sqlalchemy.' to pull the URL/opts. Use the alembic config section here.
    cfg_section = config.get_section(config.config_ini_section) or {}
    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
