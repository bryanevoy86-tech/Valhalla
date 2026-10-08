from __future__ import annotations

import json
import re
from hashlib import sha1
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.completion_registry import (
    DatasetRegistryItem,
    EngineRegistryItem,
    LegacyGovernancePolicy,
    LegacyInstancePolicyState,
    LegacyInstanceWorkItem,
    LegacyInstanceRegistryItem,
    LegacyOrchestrationEvent,
    LearningAuditEvent,
    LearningCurriculumRegistryItem,
    LearningDomainRegistryItem,
    LearningFeedbackRecord,
    KnowledgeRegistryItem,
    LearningTaskQueueItem,
    LearningPromotionRecord,
    RegistryStates,
    ScenarioExecutionRecord,
    ScenarioRegistryItem,
    ScoringRegistryItem,
    SourceRegistryItem,
    TemplateRegistryItem,
)
from app.services.data_safety import DatasetSafetyInput, evaluate_dataset_safety
from app.services.scenario_safety import ScenarioSafetyInput, evaluate_scenario_safety

router = APIRouter(prefix="/api/completion", tags=["completion-registry"])

ALLOWED_TERMINAL_STATES = {
    RegistryStates.ACTIVE_AND_VERIFIED,
    RegistryStates.BUILT_TESTED_FEATURE_GATED,
    RegistryStates.PROFESSIONALLY_GATED,
    RegistryStates.EXTERNALLY_BLOCKED,
    RegistryStates.SUPERSEDED_REJECTED_NOT_APPLICABLE,
}


def _ensure_registry_tables(db: Session) -> None:
    bind = db.get_bind()
    KnowledgeRegistryItem.__table__.create(bind=bind, checkfirst=True)
    TemplateRegistryItem.__table__.create(bind=bind, checkfirst=True)
    ScoringRegistryItem.__table__.create(bind=bind, checkfirst=True)
    SourceRegistryItem.__table__.create(bind=bind, checkfirst=True)
    DatasetRegistryItem.__table__.create(bind=bind, checkfirst=True)
    ScenarioRegistryItem.__table__.create(bind=bind, checkfirst=True)
    ScenarioExecutionRecord.__table__.create(bind=bind, checkfirst=True)
    LearningPromotionRecord.__table__.create(bind=bind, checkfirst=True)
    LearningTaskQueueItem.__table__.create(bind=bind, checkfirst=True)
    LearningDomainRegistryItem.__table__.create(bind=bind, checkfirst=True)
    LearningCurriculumRegistryItem.__table__.create(bind=bind, checkfirst=True)
    LearningFeedbackRecord.__table__.create(bind=bind, checkfirst=True)
    LearningAuditEvent.__table__.create(bind=bind, checkfirst=True)
    EngineRegistryItem.__table__.create(bind=bind, checkfirst=True)
    LegacyInstanceRegistryItem.__table__.create(bind=bind, checkfirst=True)
    LegacyGovernancePolicy.__table__.create(bind=bind, checkfirst=True)
    LegacyInstancePolicyState.__table__.create(bind=bind, checkfirst=True)
    LegacyOrchestrationEvent.__table__.create(bind=bind, checkfirst=True)
    LegacyInstanceWorkItem.__table__.create(bind=bind, checkfirst=True)


def _ensure_terminal_state(state: str) -> str:
    if state not in ALLOWED_TERMINAL_STATES:
        raise HTTPException(status_code=422, detail=f"Unsupported terminal_state: {state}")
    return state


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


DATASET_TYPES = {
    "REAL_KNOWLEDGE",
    "GOLD_BENCHMARK",
    "SYNTHETIC_OPERATIONAL",
    "PRACTICE",
    "FAILURE_SCENARIO",
    "LOAD_TEST",
    "VERIFIED_REAL_OUTCOME",
}

SCENARIO_CATEGORIES = {
    "NORMAL",
    "EDGE",
    "MISSING_DATA",
    "BAD_DATA",
    "DUPLICATE",
    "FRAUD",
    "STALE_KNOWLEDGE",
    "PROVIDER_FAILURE",
    "WORKER_FAILURE",
    "UNKNOWN_OUTCOME",
    "APPROVAL_FAILURE",
    "PROFESSIONAL_ESCALATION",
    "OWNER_MODIFICATION",
    "EMERGENCY_STOP",
    "RECOVERY",
    "CROSS_BUSINESS",
    "CROSS_JURISDICTION",
    "REPLICATION",
}

LEARNING_STATES = {
    "OBSERVED",
    "CANDIDATE",
    "SUPPORTED",
    "REVIEW_REQUIRED",
    "APPROVED",
    "ACTIVE",
    "REJECTED",
    "SUPERSEDED",
}

PROMPT_INJECTION_PATTERNS = [
    "ignore all previous rules",
    "reveal the api key",
    "send money",
    "transfer money",
    "approve this automatically",
    "change the owner's policy",
    "call this external url",
    "disable shadow mode",
    "send an email to this seller",
    "call this phone number",
    "publish this listing",
]

POISONED_DATA_PATTERNS = [
    "BEGIN_MALICIOUS_PAYLOAD",
    "TRAINING_POISON",
    "DATASET_BACKDOOR",
    "\u003cscript\u003e",
    "drop table",
]

SENSITIVE_DATA_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

STALE_SOFT_DAYS = 365
STALE_HARD_DAYS = 730

SOURCE_TRUST_RANKS = {
    "government": 4,
    "regulator": 4,
    "court": 4,
    "tax_authority": 4,
    "official_docs": 4,
    "official_documentation": 4,
    "research": 3,
    "university": 3,
    "industry_body": 3,
    "operator_note": 2,
    "community": 2,
    "interview": 2,
    "blog": 1,
    "forum": 1,
}

ALLOWED_SOURCE_PERMISSION_STATUSES = {
    "allowed",
    "granted",
    "public",
    "public_data",
}

ALLOWED_SOURCE_LICENSE_STATUSES = {
    "open",
    "public_domain",
    "government_open_data",
    "cc_by",
    "cc0",
}

ALLOWED_SOURCE_TRUST_TIERS = {"tier1", "tier2", "tier3", "tier4"}
ALLOWED_SOURCE_GOVERNANCE_STATUSES = {
    "approved",
    "review_required",
    "blocked",
    "external_blocked",
}

ENGINE_ALLOWED_STATES = {"OFF", "SANDBOX", "BLOCKED", "READY", "ACTIVE"}

PLANNED_ENGINE_CATALOG: dict[str, dict[str, str]] = {
    "wholesaling": {"name": "Wholesaling", "category": "real_estate", "business_industry": "residential_real_estate"},
    "brrrr": {"name": "BRRRR", "category": "real_estate", "business_industry": "residential_real_estate"},
    "flips": {"name": "Flips", "category": "real_estate", "business_industry": "residential_real_estate"},
    "rentals": {"name": "Rentals", "category": "real_estate", "business_industry": "residential_real_estate"},
    "multifamily": {"name": "Multifamily", "category": "real_estate", "business_industry": "multifamily_real_estate"},
    "commercial": {"name": "Commercial", "category": "real_estate", "business_industry": "commercial_real_estate"},
    "business_acquisitions": {"name": "Business Acquisitions", "category": "acquisitions", "business_industry": "operating_businesses"},
    "ai_microbusinesses": {"name": "AI/Passive Microbusinesses", "category": "digital_business", "business_industry": "ai_microbusiness"},
    "saas_subscription_products": {"name": "SaaS/Subscription Products", "category": "digital_business", "business_industry": "saas"},
    "arbitrage": {"name": "Arbitrage", "category": "capital", "business_industry": "market_arbitrage"},
    "market_intelligence": {"name": "Market Intelligence", "category": "intelligence", "business_industry": "cross_market_intelligence"},
    "ops_automation": {"name": "Ops Automation", "category": "operations", "business_industry": "operations_automation"},
    "trading_advisory": {"name": "Trading Advisory", "category": "capital", "business_industry": "trading_advisory"},
}


class KnowledgeRegistryCreate(BaseModel):
    item_id: str
    source: str
    source_type: str
    title: str
    terminal_state: str
    jurisdiction: str | None = None
    market: str | None = None
    effective_date: date | None = None
    retrieved_date: date | None = None
    review_date: date | None = None
    expires_date: date | None = None
    license_status: str | None = None
    permission_status: str | None = None
    quality_score: float | None = None
    confidence_score: float | None = None
    version: str | None = None
    superseded_by: str | None = None
    review_status: str | None = None
    allowed_systems: list[str] = Field(default_factory=list)
    citation_ref: str | None = None
    url: str | None = None
    refresh_schedule: str | None = None
    excluded: bool = False
    notes: str | None = None


class KnowledgeRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    item_id: str
    source: str
    source_type: str
    title: str
    terminal_state: str
    allowed_systems: list[str]
    citation_ref: str | None
    review_status: str | None


class TemplateRegistryCreate(BaseModel):
    template_id: str
    family: str
    purpose: str
    audience: str
    version: str
    status: str
    terminal_state: str
    channel: str | None = None
    jurisdiction: str | None = None
    entity: str | None = None
    effective_date: date | None = None
    review_date: date | None = None
    superseded_by: str | None = None
    source_owner: str | None = None
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: list[str] = Field(default_factory=list)
    required_attachments: list[str] = Field(default_factory=list)
    approval_required: bool = True
    professional_review_required: bool = False
    professional_review_status: str | None = None
    signature_required: bool = False
    template_hash: str | None = None
    test_cases_ref: str | None = None
    notes: str | None = None


class TemplateRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    template_id: str
    family: str
    purpose: str
    status: str
    terminal_state: str
    required_variables: list[str]
    superseded_by: str | None


class ScoringRegistryCreate(BaseModel):
    score_id: str
    canonical_name: str
    business_purpose: str
    formula_description: str
    version: str
    owner_approval_status: str
    terminal_state: str
    input_fields: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)
    weights: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    normalization: str | None = None
    effective_start: date | None = None
    effective_end: date | None = None
    jurisdiction: str | None = None
    market: str | None = None
    professional_approval_status: str | None = None
    confidence_handling: str | None = None
    missing_data_behavior: str | None = None
    bias_compliance_notes: str | None = None
    benchmark_ref: str | None = None
    acceptable_error_range: str | None = None
    drift_policy: str | None = None
    override_policy: str | None = None
    rollback_policy: str | None = None
    prohibited_actions: str | None = None
    active: bool = True
    notes: str | None = None


class ScoringRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    score_id: str
    canonical_name: str
    version: str
    terminal_state: str
    input_fields: list[str]
    active: bool


class SourceRegistryCreate(BaseModel):
    source_id: str
    canonical_name: str
    source_type: str
    data_class: str
    terminal_state: str
    owner: str | None = None
    jurisdiction: str | None = None
    market: str | None = None
    citation_ref: str | None = None
    permission_status: str | None = "public"
    license_status: str | None = "government_open_data"
    rights_statement_url: str | None = None
    robots_policy: str | None = "allowed"
    trust_tier: str | None = "tier2"
    provenance_method: str | None = "api"
    freshness_sla_hours: int | None = None
    last_verified_at: datetime | None = None
    governance_status: str | None = "approved"
    shadow_approved: bool = True
    mode_allowlist: list[str] = Field(default_factory=list)
    active: bool = True
    notes: str | None = None


class SourceRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    source_id: str
    canonical_name: str
    source_type: str
    data_class: str
    terminal_state: str
    permission_status: str | None
    license_status: str | None
    rights_statement_url: str | None
    robots_policy: str | None
    trust_tier: str | None
    provenance_method: str | None
    freshness_sla_hours: int | None
    last_verified_at: datetime | None
    governance_status: str | None
    shadow_approved: bool
    mode_allowlist: list[str]
    active: bool


class SourceUsageCheckIn(BaseModel):
    source_id: str
    mode: str


class SourceUsageCheckOut(BaseModel):
    source_id: str
    mode: str
    allowed: bool
    reason: str


class DatasetRegistryCreate(BaseModel):
    dataset_id: str
    name: str
    type: str
    purpose: str
    domain: str
    jurisdiction: str | None = None
    business_engine: str | None = None
    record_count: int = 0
    generation_method: str | None = None
    generator_version: str | None = None
    seed: str | None = None
    created_at: datetime | None = None
    validated_at: datetime | None = None
    learning_eligibility: bool = False
    live_kpi_eligibility: bool = False
    accounting_eligibility: bool = False
    external_execution_eligibility: bool = False
    do_not_contact: bool = True
    expected_behavior: str | None = None
    isolation_policy: str | None = None
    purge_archive_procedure: str | None = None
    test_coverage: str | None = None
    status: str
    source_id: str | None = None
    terminal_state: str
    notes: str | None = None


class DatasetRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    dataset_id: str
    name: str
    type: str
    domain: str
    jurisdiction: str | None
    business_engine: str | None
    learning_eligibility: bool
    live_kpi_eligibility: bool
    accounting_eligibility: bool
    external_execution_eligibility: bool
    do_not_contact: bool
    source_id: str | None
    terminal_state: str
    status: str


class DatasetUseValidationIn(BaseModel):
    dataset_id: str
    mode: str
    requested_action: str
    source_id: str | None = None
    jurisdiction: str | None = None
    business_scope: str | None = None


class DatasetUseValidationOut(BaseModel):
    dataset_id: str
    mode: str
    requested_action: str
    allowed: bool
    reason: str


class ScenarioRegistryCreate(BaseModel):
    scenario_id: str
    name: str
    category: str
    domain: str
    jurisdiction: str | None = None
    business_engine: str | None = None
    difficulty: str
    initial_state: str
    input_dataset: str
    expected_allowed_actions: list[str] = Field(default_factory=list)
    expected_prohibited_actions: list[str] = Field(default_factory=list)
    expected_owner_message: str
    expected_specialist_reviews: list[str] = Field(default_factory=list)
    expected_approval_requirement: str
    expected_final_state: str
    expected_audit_events: list[str] = Field(default_factory=list)
    failure_injection: str | None = None
    recovery_path: str | None = None
    practice_safe: bool = True
    external_side_effects_allowed: bool = False
    version: str
    status: str
    terminal_state: str
    notes: str | None = None


class ScenarioRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    scenario_id: str
    name: str
    category: str
    domain: str
    jurisdiction: str | None
    business_engine: str | None
    input_dataset: str
    expected_allowed_actions: list[str]
    expected_prohibited_actions: list[str]
    expected_final_state: str
    practice_safe: bool
    external_side_effects_allowed: bool
    version: str
    status: str
    terminal_state: str


class ScenarioSafetyOut(BaseModel):
    scenario_id: str
    safe: bool
    blocking_reasons: list[str]
    lineage: dict[str, Any] = Field(default_factory=dict)


class ScenarioInstantiateIn(BaseModel):
    scenario_id: str
    mode: str = "practice"
    input_payload: dict[str, Any] = Field(default_factory=dict)


class ScenarioExecutionOut(BaseModel):
    execution_id: str
    scenario_id: str
    mode: str
    status: str
    run_kind: str
    replay_of_execution_id: str | None


class ScenarioResultIn(BaseModel):
    execution_id: str
    status: str
    actual_result: dict[str, Any] = Field(default_factory=dict)
    audit_evidence: list[str] = Field(default_factory=list)


class ScenarioCompareOut(BaseModel):
    execution_id: str
    scenario_id: str
    passed: bool
    mismatches: list[str]


class KnowledgeRetrieveIn(BaseModel):
    question: str
    domain: str
    jurisdiction: str | None = None
    mode: str = "practice"
    risk_level: str = "medium"


class KnowledgeIngestIn(BaseModel):
    ingestion_id: str
    trigger_type: str
    source_id: str
    item_id: str
    title: str
    domain: str
    mode: str = "practice"
    jurisdiction: str | None = None
    market: str | None = None
    retrieved_at: datetime | None = None
    review_date: date | None = None
    version: str | None = None
    citation_ref: str | None = None
    content_excerpt: str | None = None
    notes: str | None = None
    license_status: str | None = None
    permission_status: str | None = None
    robots_allowed: bool = True
    queue_followup_task: bool = True


class KnowledgeIngestOut(BaseModel):
    ingestion_id: str
    status: str
    item_id: str
    trigger_type: str
    source_id: str
    followup_task_id: str | None = None
    reverify_task_id: str | None = None
    freshness_state: str


class ShadowWinnipegRehearsalIn(BaseModel):
    batch_id: str
    limit: int = Field(default=20, ge=20, le=50)
    mode: str = "practice"
    source_ids: list[str] = Field(default_factory=lambda: ["SRC-WPG-OPEN-DATA", "SRC-CANADA-OPEN-DATA"])


class ShadowWinnipegRehearsalOut(BaseModel):
    batch_id: str
    mode: str
    requested_limit: int
    fetched: int
    inserted: int
    duplicates: int
    blocked: int
    rejected: int
    parse_failures: int
    source_failures: int
    valuation_confidence_low: int
    buyer_data_insufficient: int
    contact_not_verified: int
    pending_human_review: int
    sources_used: list[str]


class KnowledgeRetrieveOut(BaseModel):
    question: str
    facts: list[dict[str, Any]]
    assumptions: list[dict[str, Any]]
    blocked_sources: list[dict[str, Any]]
    human_review_required: bool = False
    escalation_reasons: list[str] = Field(default_factory=list)


class LearningPromotionIn(BaseModel):
    learning_id: str
    dataset_id: str
    domain: str
    source_quality: float = 0.0
    sample_size: int = 0
    repeatable: bool = False
    jurisdiction: str | None = None
    business_scope: str | None = None
    risk_level: str = "medium"
    benchmark_result: str = "unknown"
    actual_outcome_class: str = "unverified"
    professional_required: bool = False


class LearningPromotionOut(BaseModel):
    learning_id: str
    dataset_id: str
    current_state: str
    decision_reason: str


class LearningTaskCreate(BaseModel):
    task_id: str
    task_type: str
    domain: str
    priority: str = "normal"
    status: str = "queued"
    jurisdiction: str | None = None
    business_scope: str | None = None
    knowledge_item_id: str | None = None
    learning_id: str | None = None
    reason: str | None = None
    assigned_to: str | None = None
    due_at: datetime | None = None


class LearningTaskOut(BaseModel):
    model_config = {"from_attributes": True}

    task_id: str
    task_type: str
    status: str
    priority: str
    domain: str
    jurisdiction: str | None
    business_scope: str | None
    knowledge_item_id: str | None
    learning_id: str | None
    reason: str | None
    assigned_to: str | None


class ReverifyStaleOut(BaseModel):
    created: int
    existing_open: int
    examined: int


class LearningDomainCreate(BaseModel):
    domain_id: str
    canonical_name: str
    terminal_state: str
    jurisdiction: str | None = None
    business_scope: str | None = None
    owner: str | None = None
    status: str = "active"
    notes: str | None = None


class LearningDomainOut(BaseModel):
    model_config = {"from_attributes": True}

    domain_id: str
    canonical_name: str
    terminal_state: str
    jurisdiction: str | None
    business_scope: str | None
    owner: str | None
    status: str


class LearningCurriculumCreate(BaseModel):
    curriculum_id: str
    domain_id: str
    title: str
    version: str
    terminal_state: str
    jurisdiction: str | None = None
    business_scope: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    playbooks: list[str] = Field(default_factory=list)
    benchmarks: list[str] = Field(default_factory=list)
    assessments: list[str] = Field(default_factory=list)
    promotion_gates: dict[str, float] = Field(default_factory=dict)
    status: str = "active"
    notes: str | None = None


class LearningCurriculumOut(BaseModel):
    model_config = {"from_attributes": True}

    curriculum_id: str
    domain_id: str
    title: str
    version: str
    terminal_state: str
    jurisdiction: str | None
    business_scope: str | None
    learning_objectives: list[str]
    playbooks: list[str]
    benchmarks: list[str]
    assessments: list[str]
    promotion_gates: dict[str, float]
    status: str


class LearningFeedbackIn(BaseModel):
    feedback_id: str
    feedback_type: str
    domain: str
    curriculum_id: str | None = None
    learning_id: str | None = None
    jurisdiction: str | None = None
    business_scope: str | None = None
    benchmark_score: float | None = None
    assessment_score: float | None = None
    operational_score: float | None = None
    outcome_class: str | None = None
    high_impact: bool = False
    human_review_required: bool = False
    notes: str | None = None


class LearningFeedbackOut(BaseModel):
    model_config = {"from_attributes": True}

    feedback_id: str
    feedback_type: str
    domain: str
    curriculum_id: str | None
    learning_id: str | None
    jurisdiction: str | None
    business_scope: str | None
    benchmark_score: float | None
    assessment_score: float | None
    operational_score: float | None
    outcome_class: str | None
    high_impact: bool
    human_review_required: bool
    notes: str | None


class LearningMasteryEvaluateIn(BaseModel):
    mastery_id: str
    curriculum_id: str
    domain: str
    jurisdiction: str | None = None
    business_scope: str | None = None
    benchmark_score: float
    assessment_score: float
    operational_score: float
    high_impact: bool = False


class LearningMasteryOut(BaseModel):
    mastery_id: str
    curriculum_id: str
    domain: str
    mastery_score: float
    promotion_state: str
    human_review_required: bool
    open_reverify_tasks: int
    reasons: list[str] = Field(default_factory=list)


class LearningAuditOut(BaseModel):
    model_config = {"from_attributes": True}

    event_id: str
    event_type: str
    domain: str
    curriculum_id: str | None
    learning_id: str | None
    severity: str
    message: str
    payload: dict[str, Any]


def _normalize_engine_state(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in ENGINE_ALLOWED_STATES:
        raise HTTPException(
            status_code=422,
            detail=f"engine state must be one of {sorted(ENGINE_ALLOWED_STATES)}",
        )
    return normalized


class EngineRegistryIn(BaseModel):
    engine_id: str
    name: str
    category: str
    business_industry: str
    jurisdiction_scope: list[str] = Field(default_factory=list)
    current_state: str
    dependencies: list[str] = Field(default_factory=list)
    readiness_requirements: list[str] = Field(default_factory=list)
    missing_blockers: list[str] = Field(default_factory=list)
    activation_criteria: list[str] = Field(default_factory=list)
    risk_requirements: list[str] = Field(default_factory=list)
    approval_requirements: list[str] = Field(default_factory=list)
    integration_requirements: list[str] = Field(default_factory=list)
    capital_requirements: list[str] = Field(default_factory=list)
    heimdall_recommendation: str | None = None
    activation_history: list[dict[str, Any]] = Field(default_factory=list)
    audit_state: str = "NO_RECENT_ACTIVATION"
    legacy_instance_id: str | None = None
    notes: str | None = None


class EngineRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    engine_id: str
    name: str
    category: str
    business_industry: str
    jurisdiction_scope: list[str]
    current_state: str
    dependencies: list[str]
    readiness_requirements: list[str]
    missing_blockers: list[str]
    activation_criteria: list[str]
    risk_requirements: list[str]
    approval_requirements: list[str]
    integration_requirements: list[str]
    capital_requirements: list[str]
    heimdall_recommendation: str | None
    activation_history: list[dict[str, Any]]
    audit_state: str
    legacy_instance_id: str | None
    notes: str | None


class LegacyInstanceRegistryIn(BaseModel):
    legacy_instance_id: str
    display_name: str
    parent_instance_id: str | None = None
    assigned_businesses: list[str] = Field(default_factory=list)
    assigned_jurisdictions: list[str] = Field(default_factory=list)
    local_knowledge_context: dict[str, Any] = Field(default_factory=dict)
    permissions: dict[str, Any] = Field(default_factory=dict)
    integrations: dict[str, Any] = Field(default_factory=dict)
    engines: list[str] = Field(default_factory=list)
    synchronization_status: str = "PENDING"
    isolation_state: str = "ISOLATED"
    failover_state: str = "NOT_TRIGGERED"
    audit_state: str = "BASELINE_ONLY"
    status: str = "PARTIAL"
    notes: str | None = None


class LegacyInstanceRegistryOut(BaseModel):
    model_config = {"from_attributes": True}

    legacy_instance_id: str
    display_name: str
    parent_instance_id: str | None
    assigned_businesses: list[str]
    assigned_jurisdictions: list[str]
    local_knowledge_context: dict[str, Any]
    permissions: dict[str, Any]
    integrations: dict[str, Any]
    engines: list[str]
    synchronization_status: str
    isolation_state: str
    failover_state: str
    audit_state: str
    status: str
    notes: str | None


class LegacyGovernancePolicyIn(BaseModel):
    policy_id: str
    policy_scope: str = "GLOBAL"
    policy_version: str
    autonomy_policy: dict[str, Any]
    ethics_evidence_policy: dict[str, Any]
    kill_shield_policy: dict[str, Any]
    engine_activation_policy: dict[str, Any]
    jurisdiction_restrictions: dict[str, Any]
    approval_requirements: dict[str, Any]
    audit_requirements: dict[str, Any]


class LegacyProvisionRequest(BaseModel):
    legacy_instance_id: str
    display_name: str
    parent_instance_id: str = "PRIMARY_HEIMDALL"
    business_id: str
    industry: str
    jurisdiction: str
    allowed_engines: list[str] = Field(default_factory=list)
    operating_objectives: list[str] = Field(default_factory=list)
    data_namespace: str
    integration_profile: dict[str, Any] = Field(default_factory=dict)
    risk_profile: dict[str, Any] = Field(default_factory=dict)
    permissions: dict[str, Any] = Field(default_factory=dict)
    local_knowledge_refs: list[str] = Field(default_factory=list)
    policy_id: str


class LegacyPolicyPropagationRequest(BaseModel):
    policy_id: str
    target_instances: list[str] | None = None


class LegacyConflictCheckRequest(BaseModel):
    legacy_instance_id: str
    expected_policy_version: str
    expected_engine_states: dict[str, str] = Field(default_factory=dict)
    required_jurisdiction_context: str
    task_idempotency_key: str | None = None


class LegacyWorkAssignRequest(BaseModel):
    action_id: str
    idempotency_key: str
    legacy_instance_id: str
    business_id: str
    industry: str
    jurisdiction: str
    engine_id: str
    objective: str
    data_namespace: str
    risk_profile: str = "standard"
    integration_profile: str = "default"
    payload: dict[str, Any] = Field(default_factory=dict)


class LegacyFailoverRequest(BaseModel):
    failed_instance_id: str
    recovery_instance_id: str | None = None


class LegacyRecoveryRequest(BaseModel):
    legacy_instance_id: str
    synchronize_policy: bool = True


ALLOWED_LEGACY_STATUSES = {"PASS", "PARTIAL", "FAIL", "EXTERNAL_OWNER_ACTION_REQUIRED"}


def _contains_governance_bypass(payload: Any) -> bool:
    if isinstance(payload, dict):
        for k, v in payload.items():
            key = str(k).strip().lower()
            if key in {
                "bypass_governance",
                "disable_approval",
                "disable_audit",
                "disable_ethics",
                "disable_kill_shield",
            } and bool(v):
                return True
            if _contains_governance_bypass(v):
                return True
        return False
    if isinstance(payload, list):
        return any(_contains_governance_bypass(v) for v in payload)
    return False


def _require_no_governance_bypass(*payloads: Any) -> None:
    if any(_contains_governance_bypass(p) for p in payloads):
        raise HTTPException(status_code=409, detail="local customization cannot bypass core governance")


ALLOWED_TASK_STATUSES = {"queued", "in_progress", "blocked", "completed", "cancelled"}
ALLOWED_TASK_PRIORITIES = {"low", "normal", "high", "critical"}


def _normalize_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized in {"sandbox", "shadow"}:
        return "practice"
    if normalized not in {"practice", "test", "live"}:
        raise HTTPException(status_code=422, detail="mode must be one of practice|test|live")
    return normalized


def _normalize_source_permission_status(value: str | None) -> str:
    return str(value or "public").strip().lower()


def _normalize_source_license_status(value: str | None) -> str:
    return str(value or "government_open_data").strip().lower()


def _normalize_source_trust_tier(value: str | None) -> str:
    tier = str(value or "tier2").strip().lower()
    if tier not in ALLOWED_SOURCE_TRUST_TIERS:
        raise HTTPException(status_code=422, detail=f"trust_tier must be one of {sorted(ALLOWED_SOURCE_TRUST_TIERS)}")
    return tier


def _normalize_source_governance_status(value: str | None) -> str:
    status = str(value or "approved").strip().lower()
    if status not in ALLOWED_SOURCE_GOVERNANCE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"governance_status must be one of {sorted(ALLOWED_SOURCE_GOVERNANCE_STATUSES)}",
        )
    return status


def _assert_source_shadow_ready(row: SourceRegistryItem) -> None:
    permission = _normalize_source_permission_status(row.permission_status)
    license_status = _normalize_source_license_status(row.license_status)
    trust_tier = _normalize_source_trust_tier(row.trust_tier)
    governance_status = _normalize_source_governance_status(row.governance_status)
    robots_policy = str(row.robots_policy or "allowed").strip().lower()

    if permission not in ALLOWED_SOURCE_PERMISSION_STATUSES:
        raise HTTPException(status_code=409, detail="source permission_status is not approved for shadow use")
    if license_status not in ALLOWED_SOURCE_LICENSE_STATUSES:
        raise HTTPException(status_code=409, detail="source license_status is not approved for shadow use")
    if robots_policy not in {"allowed", "explicit_allow", "api"}:
        raise HTTPException(status_code=409, detail="source robots_policy blocks shadow ingestion")
    if trust_tier not in {"tier1", "tier2"}:
        raise HTTPException(status_code=409, detail="source trust_tier must be tier1 or tier2 for shadow mode")
    if governance_status != "approved" or not bool(row.shadow_approved):
        raise HTTPException(status_code=409, detail="source governance status is not approved for shadow mode")


def _default_allowlist_for_data_class(data_class: str) -> set[str]:
    cls = (data_class or "").strip().lower()
    if cls == "live":
        return {"live", "test", "practice"}
    if cls == "sandbox":
        return {"test", "practice"}
    if cls in {"test", "synthetic"}:
        return {"test", "practice"}
    raise HTTPException(status_code=422, detail="data_class must be one of live|sandbox|test|synthetic")


def _dataset_type_or_error(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized not in DATASET_TYPES:
        raise HTTPException(status_code=422, detail=f"unsupported dataset type: {value}")
    return normalized


def _scenario_category_or_error(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized not in SCENARIO_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"unsupported scenario category: {value}")
    return normalized


def _contains_prompt_injection(text: str | None) -> str | None:
    raw = (text or "").strip().lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern in raw:
            return pattern
    return None


def _contains_poisoned_data_pattern(text: str | None) -> str | None:
    raw = (text or "").strip().lower()
    for pattern in POISONED_DATA_PATTERNS:
        if pattern.lower() in raw:
            return pattern
    return None


def _is_stale(review_date: date | None, stale_after_days: int = 30) -> bool:
    if review_date is None:
        return True
    return review_date < (datetime.now(timezone.utc).date() - timedelta(days=stale_after_days))


def _review_age_days(review_date: date | None) -> int | None:
    if review_date is None:
        return None
    return max(0, (datetime.now(timezone.utc).date() - review_date).days)


def _freshness_state(review_date: date | None) -> str:
    age_days = _review_age_days(review_date)
    if age_days is None:
        return "unknown"
    if age_days > STALE_HARD_DAYS:
        return "hard_stale"
    if age_days > STALE_SOFT_DAYS:
        return "soft_stale"
    return "fresh"


def _effective_confidence(confidence_score: float | None, review_date: date | None) -> float:
    confidence = float(confidence_score or 0.0)
    freshness = _freshness_state(review_date)
    if freshness == "soft_stale":
        # Confidence decay for stale material older than one year.
        return max(0.0, confidence - 0.15)
    if freshness == "hard_stale":
        return max(0.0, confidence - 0.35)
    return confidence


def _source_trust_rank(source_type: str | None) -> int:
    key = str(source_type or "").strip().lower()
    return SOURCE_TRUST_RANKS.get(key, 0)


def _title_key(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _contains_sensitive_data(text: str | None) -> str | None:
    raw = str(text or "")
    for label, pattern in SENSITIVE_DATA_PATTERNS.items():
        if pattern.search(raw):
            return label
    return None


def _normalize_task_status(status: str) -> str:
    value = str(status or "queued").strip().lower()
    if value not in ALLOWED_TASK_STATUSES:
        raise HTTPException(status_code=422, detail=f"unsupported task status: {status}")
    return value


def _normalize_task_priority(priority: str) -> str:
    value = str(priority or "normal").strip().lower()
    if value not in ALLOWED_TASK_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"unsupported task priority: {priority}")
    return value


def _normalize_trigger_type(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in {"push", "scheduled", "event"}:
        raise HTTPException(status_code=422, detail="trigger_type must be one of push|scheduled|event")
    return normalized


def _permission_or_license_blocked(permission_status: str | None, license_status: str | None) -> str | None:
    denied_permission = {"denied", "forbidden", "disallowed", "no_permission", "blocked"}
    blocked_license = {"forbidden", "restricted", "proprietary_no_derivatives", "no_redistribution"}
    permission = str(permission_status or "").strip().lower()
    license_value = str(license_status or "").strip().lower()

    if permission in denied_permission:
        return "permission_status blocks ingestion"
    if license_value in blocked_license:
        return "license_status blocks ingestion"
    return None


def _normalize_feedback_type(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in {"assessment", "benchmark", "operational_result", "mastery_evaluation"}:
        raise HTTPException(status_code=422, detail="feedback_type must be one of assessment|benchmark|operational_result|mastery_evaluation")
    return normalized


def _promotion_gates(payload: dict[str, Any] | None) -> dict[str, float]:
    defaults = {
        "assessment_min": 0.8,
        "benchmark_min": 0.8,
        "operational_min": 0.75,
        "mastery_min": 0.8,
        "max_open_reverify_tasks": 0.0,
    }
    if not payload:
        return defaults

    gates = dict(defaults)
    for key in list(defaults.keys()):
        if key in payload:
            try:
                gates[key] = float(payload[key])
            except Exception:
                raise HTTPException(status_code=422, detail=f"promotion gate '{key}' must be numeric")
    return gates


def _create_learning_audit_event(
    db: Session,
    *,
    event_id: str,
    event_type: str,
    domain: str,
    message: str,
    curriculum_id: str | None = None,
    learning_id: str | None = None,
    severity: str = "info",
    payload: dict[str, Any] | None = None,
) -> None:
    row = LearningAuditEvent(
        event_id=event_id,
        event_type=event_type,
        domain=domain,
        curriculum_id=curriculum_id,
        learning_id=learning_id,
        severity=severity,
        message=message,
        payload_json=json.dumps(payload or {}),
    )
    db.add(row)


def _engine_registry_out(row: EngineRegistryItem) -> EngineRegistryOut:
    return EngineRegistryOut(
        engine_id=row.engine_id,
        name=row.name,
        category=row.category,
        business_industry=row.business_industry,
        jurisdiction_scope=_loads(row.jurisdiction_scope_json, []),
        current_state=row.current_state,
        dependencies=_loads(row.dependencies_json, []),
        readiness_requirements=_loads(row.readiness_requirements_json, []),
        missing_blockers=_loads(row.missing_blockers_json, []),
        activation_criteria=_loads(row.activation_criteria_json, []),
        risk_requirements=_loads(row.risk_requirements_json, []),
        approval_requirements=_loads(row.approval_requirements_json, []),
        integration_requirements=_loads(row.integration_requirements_json, []),
        capital_requirements=_loads(row.capital_requirements_json, []),
        heimdall_recommendation=row.heimdall_recommendation,
        activation_history=_loads(row.activation_history_json, []),
        audit_state=row.audit_state,
        legacy_instance_id=row.legacy_instance_id,
        notes=row.notes,
    )


def _legacy_instance_out(row: LegacyInstanceRegistryItem) -> LegacyInstanceRegistryOut:
    return LegacyInstanceRegistryOut(
        legacy_instance_id=row.legacy_instance_id,
        display_name=row.display_name,
        parent_instance_id=row.parent_instance_id,
        assigned_businesses=_loads(row.assigned_businesses_json, []),
        assigned_jurisdictions=_loads(row.assigned_jurisdictions_json, []),
        local_knowledge_context=_loads(row.local_knowledge_context_json, {}),
        permissions=_loads(row.permissions_json, {}),
        integrations=_loads(row.integrations_json, {}),
        engines=_loads(row.engines_json, []),
        synchronization_status=row.synchronization_status,
        isolation_state=row.isolation_state,
        failover_state=row.failover_state,
        audit_state=row.audit_state,
        status=row.status,
        notes=row.notes,
    )


@router.post("/engine-registry/items", response_model=EngineRegistryOut)
def upsert_engine_registry_item(payload: EngineRegistryIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    state = _normalize_engine_state(payload.current_state)

    row = db.query(EngineRegistryItem).filter(EngineRegistryItem.engine_id == payload.engine_id).first()
    if row is None:
        row = EngineRegistryItem(engine_id=payload.engine_id)
        db.add(row)

    row.name = payload.name
    row.category = payload.category
    row.business_industry = payload.business_industry
    row.jurisdiction_scope_json = json.dumps(payload.jurisdiction_scope)
    row.current_state = state
    row.dependencies_json = json.dumps(payload.dependencies)
    row.readiness_requirements_json = json.dumps(payload.readiness_requirements)
    row.missing_blockers_json = json.dumps(payload.missing_blockers)
    row.activation_criteria_json = json.dumps(payload.activation_criteria)
    row.risk_requirements_json = json.dumps(payload.risk_requirements)
    row.approval_requirements_json = json.dumps(payload.approval_requirements)
    row.integration_requirements_json = json.dumps(payload.integration_requirements)
    row.capital_requirements_json = json.dumps(payload.capital_requirements)
    row.heimdall_recommendation = payload.heimdall_recommendation
    row.activation_history_json = json.dumps(payload.activation_history)
    row.audit_state = payload.audit_state
    row.legacy_instance_id = payload.legacy_instance_id
    row.notes = payload.notes

    db.commit()
    db.refresh(row)
    return _engine_registry_out(row)


@router.get("/engine-registry/items", response_model=list[EngineRegistryOut])
def list_engine_registry_items(
    db: Session = Depends(get_db),
    current_state: str | None = None,
    legacy_instance_id: str | None = None,
):
    _ensure_registry_tables(db)
    q = db.query(EngineRegistryItem)
    if current_state:
        q = q.filter(EngineRegistryItem.current_state == _normalize_engine_state(current_state))
    if legacy_instance_id:
        q = q.filter(EngineRegistryItem.legacy_instance_id == legacy_instance_id)
    rows = q.order_by(EngineRegistryItem.engine_id.asc()).all()
    return [_engine_registry_out(row) for row in rows]


@router.get("/engine-registry/audit")
def audit_engine_registry(db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    rows = db.query(EngineRegistryItem).all()
    by_id = {row.engine_id: row for row in rows}

    missing_planned = sorted([engine_id for engine_id in PLANNED_ENGINE_CATALOG if engine_id not in by_id])

    field_issues: list[dict[str, Any]] = []
    invalid_states: list[dict[str, Any]] = []
    for row in rows:
        if row.current_state not in ENGINE_ALLOWED_STATES:
            invalid_states.append(
                {
                    "engine_id": row.engine_id,
                    "current_state": row.current_state,
                    "allowed": sorted(ENGINE_ALLOWED_STATES),
                }
            )
        required = {
            "name": row.name,
            "category": row.category,
            "business_industry": row.business_industry,
            "audit_state": row.audit_state,
        }
        missing_fields = [k for k, v in required.items() if not str(v or "").strip()]
        if missing_fields:
            field_issues.append({"engine_id": row.engine_id, "missing_fields": missing_fields})

    represented = sorted([row.engine_id for row in rows])
    return {
        "planned_engines_expected": sorted(PLANNED_ENGINE_CATALOG.keys()),
        "planned_engines_represented": sorted([engine_id for engine_id in represented if engine_id in PLANNED_ENGINE_CATALOG]),
        "missing_planned_engines": missing_planned,
        "unplanned_registry_engines": sorted([engine_id for engine_id in represented if engine_id not in PLANNED_ENGINE_CATALOG]),
        "invalid_state_entries": invalid_states,
        "missing_required_fields": field_issues,
        "registry_pass": len(missing_planned) == 0 and len(invalid_states) == 0 and len(field_issues) == 0,
    }


@router.post("/legacy-instances", response_model=LegacyInstanceRegistryOut)
def upsert_legacy_instance(payload: LegacyInstanceRegistryIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    if payload.status not in ALLOWED_LEGACY_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(ALLOWED_LEGACY_STATUSES)}")
    _require_no_governance_bypass(payload.local_knowledge_context, payload.permissions, payload.integrations)

    row = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == payload.legacy_instance_id
    ).first()
    if row is None:
        row = LegacyInstanceRegistryItem(legacy_instance_id=payload.legacy_instance_id)
        db.add(row)

    row.display_name = payload.display_name
    row.parent_instance_id = payload.parent_instance_id
    row.assigned_businesses_json = json.dumps(payload.assigned_businesses)
    row.assigned_jurisdictions_json = json.dumps(payload.assigned_jurisdictions)
    row.local_knowledge_context_json = json.dumps(payload.local_knowledge_context)
    row.permissions_json = json.dumps(payload.permissions)
    row.integrations_json = json.dumps(payload.integrations)
    row.engines_json = json.dumps(payload.engines)
    row.synchronization_status = payload.synchronization_status
    row.isolation_state = payload.isolation_state
    row.failover_state = payload.failover_state
    row.audit_state = payload.audit_state
    row.status = payload.status
    row.notes = payload.notes

    db.commit()
    db.refresh(row)
    return _legacy_instance_out(row)


@router.get("/legacy-instances", response_model=list[LegacyInstanceRegistryOut])
def list_legacy_instances(db: Session = Depends(get_db), status: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(LegacyInstanceRegistryItem)
    if status:
        q = q.filter(LegacyInstanceRegistryItem.status == status)
    rows = q.order_by(LegacyInstanceRegistryItem.legacy_instance_id.asc()).all()
    return [_legacy_instance_out(row) for row in rows]


def _orchestration_event(
    db: Session,
    *,
    legacy_instance_id: str | None,
    event_type: str,
    message: str,
    severity: str = "info",
    payload: dict[str, Any] | None = None,
) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    event_id = f"LEGACY-EVT-{event_type}-{stamp}"
    db.add(
        LegacyOrchestrationEvent(
            event_id=event_id,
            legacy_instance_id=legacy_instance_id,
            event_type=event_type,
            severity=severity,
            message=message,
            payload_json=json.dumps(payload or {}),
        )
    )


def _get_active_policy_or_404(db: Session, policy_id: str) -> LegacyGovernancePolicy:
    row = db.query(LegacyGovernancePolicy).filter(
        LegacyGovernancePolicy.policy_id == policy_id,
        LegacyGovernancePolicy.active.is_(True),
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="active governance policy not found")
    return row


@router.post("/legacy-orchestration/policies")
def upsert_legacy_governance_policy(payload: LegacyGovernancePolicyIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _require_no_governance_bypass(
        payload.autonomy_policy,
        payload.ethics_evidence_policy,
        payload.kill_shield_policy,
        payload.engine_activation_policy,
        payload.jurisdiction_restrictions,
        payload.approval_requirements,
        payload.audit_requirements,
    )

    row = db.query(LegacyGovernancePolicy).filter(LegacyGovernancePolicy.policy_id == payload.policy_id).first()
    if row is None:
        row = LegacyGovernancePolicy(policy_id=payload.policy_id)
        db.add(row)

    row.policy_scope = payload.policy_scope
    row.policy_version = payload.policy_version
    row.autonomy_policy_json = json.dumps(payload.autonomy_policy)
    row.ethics_evidence_policy_json = json.dumps(payload.ethics_evidence_policy)
    row.kill_shield_policy_json = json.dumps(payload.kill_shield_policy)
    row.engine_activation_policy_json = json.dumps(payload.engine_activation_policy)
    row.jurisdiction_restrictions_json = json.dumps(payload.jurisdiction_restrictions)
    row.approval_requirements_json = json.dumps(payload.approval_requirements)
    row.audit_requirements_json = json.dumps(payload.audit_requirements)
    row.active = True

    _orchestration_event(
        db,
        legacy_instance_id=None,
        event_type="POLICY_UPSERTED",
        message=f"Primary Heimdall set policy {payload.policy_id} version {payload.policy_version}",
        payload={"policy_id": payload.policy_id, "policy_version": payload.policy_version},
    )

    db.commit()
    return {"policy_id": row.policy_id, "policy_version": row.policy_version, "active": row.active}


@router.post("/legacy-orchestration/provision")
def provision_legacy_instance(payload: LegacyProvisionRequest, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _require_no_governance_bypass(payload.permissions, payload.integration_profile, payload.risk_profile)
    policy = _get_active_policy_or_404(db, payload.policy_id)

    row = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == payload.legacy_instance_id
    ).first()
    if row is None:
        row = LegacyInstanceRegistryItem(legacy_instance_id=payload.legacy_instance_id)
        db.add(row)

    row.display_name = payload.display_name
    row.parent_instance_id = payload.parent_instance_id
    row.assigned_businesses_json = json.dumps([payload.business_id])
    row.assigned_jurisdictions_json = json.dumps([payload.jurisdiction])
    row.permissions_json = json.dumps(payload.permissions)
    row.integrations_json = json.dumps(payload.integration_profile)
    row.engines_json = json.dumps(payload.allowed_engines)
    row.synchronization_status = "SYNCED"
    row.isolation_state = "ISOLATED"
    row.failover_state = "NOT_TRIGGERED"
    row.audit_state = "PROVISIONED_UNDER_PRIMARY_GOVERNANCE"
    row.status = "PARTIAL"
    row.local_knowledge_context_json = json.dumps(
        {
            "business_id": payload.business_id,
            "industry": payload.industry,
            "jurisdiction": payload.jurisdiction,
            "data_namespace": payload.data_namespace,
            "operating_objectives": payload.operating_objectives,
            "local_knowledge_refs": payload.local_knowledge_refs,
            "risk_profile": payload.risk_profile,
            "governance": {
                "policy_id": policy.policy_id,
                "policy_version": policy.policy_version,
            },
        }
    )

    policy_state = db.query(LegacyInstancePolicyState).filter(
        LegacyInstancePolicyState.legacy_instance_id == payload.legacy_instance_id
    ).first()
    if policy_state is None:
        policy_state = LegacyInstancePolicyState(legacy_instance_id=payload.legacy_instance_id, policy_id=policy.policy_id)
        db.add(policy_state)
    policy_state.policy_id = policy.policy_id
    policy_state.policy_version = policy.policy_version
    policy_state.sync_status = "SYNCED"
    policy_state.divergence_reason = None
    policy_state.propagated_at = datetime.utcnow()

    _orchestration_event(
        db,
        legacy_instance_id=payload.legacy_instance_id,
        event_type="INSTANCE_PROVISIONED",
        message=f"Provisioned {payload.legacy_instance_id} for business {payload.business_id} in {payload.jurisdiction}",
        payload={
            "business_id": payload.business_id,
            "industry": payload.industry,
            "jurisdiction": payload.jurisdiction,
            "engines": payload.allowed_engines,
        },
    )

    db.commit()
    return {
        "legacy_instance_id": payload.legacy_instance_id,
        "status": "PROVISIONED",
        "policy_version": policy.policy_version,
    }


@router.post("/legacy-orchestration/policies/propagate")
def propagate_legacy_policy(payload: LegacyPolicyPropagationRequest, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    policy = _get_active_policy_or_404(db, payload.policy_id)
    q = db.query(LegacyInstanceRegistryItem)
    if payload.target_instances:
        q = q.filter(LegacyInstanceRegistryItem.legacy_instance_id.in_(payload.target_instances))
    rows = q.all()

    propagated = 0
    blocked: list[str] = []
    for row in rows:
        integrations = _loads(row.integrations_json, {})
        if bool(integrations.get("policy_propagation_blocked", False)):
            row.synchronization_status = "BLOCKED"
            blocked.append(row.legacy_instance_id)
            state = db.query(LegacyInstancePolicyState).filter(
                LegacyInstancePolicyState.legacy_instance_id == row.legacy_instance_id
            ).first()
            if state is not None:
                state.sync_status = "DIVERGED"
                state.divergence_reason = "propagation blocked by integration profile"
            _orchestration_event(
                db,
                legacy_instance_id=row.legacy_instance_id,
                event_type="POLICY_PROPAGATION_BLOCKED",
                severity="warning",
                message="Policy propagation blocked for legacy instance",
                payload={"policy_id": policy.policy_id, "policy_version": policy.policy_version},
            )
            continue

        state = db.query(LegacyInstancePolicyState).filter(
            LegacyInstancePolicyState.legacy_instance_id == row.legacy_instance_id
        ).first()
        if state is None:
            state = LegacyInstancePolicyState(legacy_instance_id=row.legacy_instance_id, policy_id=policy.policy_id)
            db.add(state)
        state.policy_id = policy.policy_id
        state.policy_version = policy.policy_version
        state.sync_status = "SYNCED"
        state.divergence_reason = None
        state.propagated_at = datetime.utcnow()
        row.synchronization_status = "SYNCED"
        propagated += 1

        local = _loads(row.local_knowledge_context_json, {})
        local["governance"] = {"policy_id": policy.policy_id, "policy_version": policy.policy_version}
        row.local_knowledge_context_json = json.dumps(local)

        _orchestration_event(
            db,
            legacy_instance_id=row.legacy_instance_id,
            event_type="POLICY_PROPAGATED",
            message=f"Policy {policy.policy_version} propagated",
            payload={"policy_id": policy.policy_id, "policy_version": policy.policy_version},
        )

    db.commit()
    return {
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "propagated": propagated,
        "blocked_instances": blocked,
    }


@router.post("/legacy-orchestration/conflicts/check")
def check_legacy_conflicts(payload: LegacyConflictCheckRequest, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    row = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == payload.legacy_instance_id
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="legacy instance not found")

    local = _loads(row.local_knowledge_context_json, {})
    policy_state = db.query(LegacyInstancePolicyState).filter(
        LegacyInstancePolicyState.legacy_instance_id == payload.legacy_instance_id
    ).first()
    engines = set(_loads(row.engines_json, []))
    assigned_jurisdictions = set(_loads(row.assigned_jurisdictions_json, []))

    conflicts: list[dict[str, Any]] = []
    if policy_state is None or policy_state.policy_version != payload.expected_policy_version:
        conflicts.append(
            {
                "type": "STALE_POLICY_VERSION",
                "actual": None if policy_state is None else policy_state.policy_version,
                "expected": payload.expected_policy_version,
                "resolution": "PRIMARY_AUTHORITY_PROPAGATE_OR_APPROVE_EXCEPTION",
            }
        )

    if payload.required_jurisdiction_context not in assigned_jurisdictions:
        conflicts.append(
            {
                "type": "OUTDATED_JURISDICTION_CONTEXT",
                "actual": sorted(assigned_jurisdictions),
                "expected": payload.required_jurisdiction_context,
                "resolution": "REVERIFY_AND_ESCALATE",
            }
        )

    for engine_id, expected_state in payload.expected_engine_states.items():
        if engine_id not in engines:
            conflicts.append(
                {
                    "type": "CONFLICTING_ENGINE_STATE",
                    "engine_id": engine_id,
                    "actual": "NOT_ASSIGNED",
                    "expected": expected_state,
                    "resolution": "PRIMARY_AUTHORITY_REASSIGN_OR_APPROVE",
                }
            )

    if payload.task_idempotency_key:
        dup = db.query(LegacyInstanceWorkItem).filter(
            LegacyInstanceWorkItem.idempotency_key == payload.task_idempotency_key,
            LegacyInstanceWorkItem.legacy_instance_id != payload.legacy_instance_id,
        ).first()
        if dup is not None:
            conflicts.append(
                {
                    "type": "DUPLICATE_TASK_IDENTITY",
                    "actual": dup.legacy_instance_id,
                    "expected": payload.legacy_instance_id,
                    "resolution": "BLOCK_DUPLICATE_AND_ESCALATE",
                }
            )

    if conflicts:
        row.synchronization_status = "DIVERGED"
        _orchestration_event(
            db,
            legacy_instance_id=payload.legacy_instance_id,
            event_type="CONFLICT_DETECTED",
            severity="warning",
            message="Legacy divergence/conflict detected",
            payload={"conflicts": conflicts, "namespace": local.get("data_namespace")},
        )
        if policy_state is not None:
            policy_state.sync_status = "DIVERGED"
            policy_state.divergence_reason = "; ".join(c["type"] for c in conflicts)
    else:
        row.synchronization_status = "SYNCED"

    db.commit()
    return {"legacy_instance_id": payload.legacy_instance_id, "conflicts": conflicts, "has_conflict": len(conflicts) > 0}


@router.post("/legacy-orchestration/work/assign")
def assign_legacy_work(payload: LegacyWorkAssignRequest, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    row = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == payload.legacy_instance_id
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="legacy instance not found")

    existing = db.query(LegacyInstanceWorkItem).filter(
        LegacyInstanceWorkItem.idempotency_key == payload.idempotency_key
    ).first()
    if existing is not None:
        if existing.legacy_instance_id != payload.legacy_instance_id:
            _orchestration_event(
                db,
                legacy_instance_id=payload.legacy_instance_id,
                event_type="DUPLICATE_WORK_BLOCKED",
                severity="warning",
                message="Duplicate action identity blocked across legacy instances",
                payload={"idempotency_key": payload.idempotency_key, "existing_instance": existing.legacy_instance_id},
            )
            db.commit()
            raise HTTPException(status_code=409, detail="duplicate action identity detected across legacy instances")
        return {
            "action_id": existing.action_id,
            "legacy_instance_id": existing.legacy_instance_id,
            "status": existing.status,
            "duplicate": True,
        }

    local = _loads(row.local_knowledge_context_json, {})
    if local.get("jurisdiction") != payload.jurisdiction:
        raise HTTPException(status_code=409, detail="requested jurisdiction does not match legacy context; re-verification required")

    if payload.engine_id not in set(_loads(row.engines_json, [])):
        raise HTTPException(status_code=409, detail="requested engine is not assigned to this legacy instance")

    item = LegacyInstanceWorkItem(
        action_id=payload.action_id,
        idempotency_key=payload.idempotency_key,
        legacy_instance_id=payload.legacy_instance_id,
        business_id=payload.business_id,
        industry=payload.industry,
        jurisdiction=payload.jurisdiction,
        engine_id=payload.engine_id,
        objective=payload.objective,
        status="queued",
        risk_profile=payload.risk_profile,
        integration_profile=payload.integration_profile,
        namespace=payload.data_namespace,
        payload_json=json.dumps(payload.payload),
    )
    db.add(item)
    _orchestration_event(
        db,
        legacy_instance_id=payload.legacy_instance_id,
        event_type="WORK_ASSIGNED",
        message=f"Assigned work {payload.action_id}",
        payload={"business_id": payload.business_id, "jurisdiction": payload.jurisdiction},
    )
    db.commit()
    return {"action_id": item.action_id, "legacy_instance_id": item.legacy_instance_id, "status": item.status, "duplicate": False}


@router.post("/legacy-orchestration/failover")
def failover_legacy_instance(payload: LegacyFailoverRequest, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    failed = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == payload.failed_instance_id
    ).first()
    if failed is None:
        raise HTTPException(status_code=404, detail="failed instance not found")

    failed.failover_state = "FAILED"
    failed.synchronization_status = "BLOCKED"
    failed.status = "PARTIAL"

    reassigned = 0
    paused = 0
    if payload.recovery_instance_id:
        recovery = db.query(LegacyInstanceRegistryItem).filter(
            LegacyInstanceRegistryItem.legacy_instance_id == payload.recovery_instance_id
        ).first()
        if recovery is None:
            raise HTTPException(status_code=404, detail="recovery instance not found")

        failed_businesses = set(_loads(failed.assigned_businesses_json, []))
        recovery_businesses = set(_loads(recovery.assigned_businesses_json, []))

        q = db.query(LegacyInstanceWorkItem).filter(
            LegacyInstanceWorkItem.legacy_instance_id == payload.failed_instance_id,
            LegacyInstanceWorkItem.status.in_(["queued", "in_progress"]),
        )
        for item in q.all():
            if item.business_id in recovery_businesses and item.business_id in failed_businesses:
                item.reassigned_from_instance_id = payload.failed_instance_id
                item.legacy_instance_id = payload.recovery_instance_id
                item.status = "queued"
                reassigned += 1
            else:
                item.status = "paused"
                paused += 1
    else:
        q = db.query(LegacyInstanceWorkItem).filter(
            LegacyInstanceWorkItem.legacy_instance_id == payload.failed_instance_id,
            LegacyInstanceWorkItem.status.in_(["queued", "in_progress"]),
        )
        for item in q.all():
            item.status = "paused"
            paused += 1

    _orchestration_event(
        db,
        legacy_instance_id=payload.failed_instance_id,
        event_type="FAILOVER_TRIGGERED",
        severity="warning",
        message="Legacy instance failover triggered",
        payload={
            "failed_instance": payload.failed_instance_id,
            "recovery_instance": payload.recovery_instance_id,
            "reassigned": reassigned,
            "paused": paused,
        },
    )

    db.commit()
    return {
        "failed_instance_id": payload.failed_instance_id,
        "recovery_instance_id": payload.recovery_instance_id,
        "reassigned": reassigned,
        "paused": paused,
    }


@router.post("/legacy-orchestration/recover")
def recover_legacy_instance(payload: LegacyRecoveryRequest, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    row = db.query(LegacyInstanceRegistryItem).filter(
        LegacyInstanceRegistryItem.legacy_instance_id == payload.legacy_instance_id
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="legacy instance not found")

    row.failover_state = "RECOVERED"
    row.synchronization_status = "SYNCED"
    if payload.synchronize_policy:
        policy_state = db.query(LegacyInstancePolicyState).filter(
            LegacyInstancePolicyState.legacy_instance_id == payload.legacy_instance_id
        ).first()
        if policy_state is not None:
            policy_state.sync_status = "SYNCED"
            policy_state.divergence_reason = None
            policy_state.propagated_at = datetime.utcnow()

    _orchestration_event(
        db,
        legacy_instance_id=payload.legacy_instance_id,
        event_type="FAILOVER_RECOVERED",
        message="Legacy instance recovered and synchronized",
    )
    db.commit()
    return {"legacy_instance_id": payload.legacy_instance_id, "status": "RECOVERED"}


@router.get("/legacy-orchestration/health")
def legacy_orchestration_health(db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    rows = db.query(LegacyInstanceRegistryItem).order_by(LegacyInstanceRegistryItem.legacy_instance_id.asc()).all()

    instances: list[dict[str, Any]] = []
    blocked = 0
    for row in rows:
        policy_state = db.query(LegacyInstancePolicyState).filter(
            LegacyInstancePolicyState.legacy_instance_id == row.legacy_instance_id
        ).first()
        pending_work = db.query(LegacyInstanceWorkItem).filter(
            LegacyInstanceWorkItem.legacy_instance_id == row.legacy_instance_id,
            LegacyInstanceWorkItem.status.in_(["queued", "in_progress", "paused"]),
        ).count()

        sync_status = row.synchronization_status
        if sync_status in {"BLOCKED", "DIVERGED"}:
            blocked += 1

        instances.append(
            {
                "legacy_instance_id": row.legacy_instance_id,
                "businesses": _loads(row.assigned_businesses_json, []),
                "jurisdictions": _loads(row.assigned_jurisdictions_json, []),
                "engines": _loads(row.engines_json, []),
                "policy_version": None if policy_state is None else policy_state.policy_version,
                "policy_sync_status": None if policy_state is None else policy_state.sync_status,
                "synchronization_status": sync_status,
                "failover_state": row.failover_state,
                "isolation_state": row.isolation_state,
                "pending_work": pending_work,
            }
        )

    event_count = db.query(LegacyOrchestrationEvent).count()
    return {
        "instances": instances,
        "blocked_or_diverged_instances": blocked,
        "events_recorded": event_count,
    }


@router.post("/knowledge-items", response_model=KnowledgeRegistryOut)
def create_knowledge_item(payload: KnowledgeRegistryCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)

    exists = db.query(KnowledgeRegistryItem).filter(KnowledgeRegistryItem.item_id == payload.item_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="item_id already exists")

    item = KnowledgeRegistryItem(
        item_id=payload.item_id,
        source=payload.source,
        source_type=payload.source_type,
        title=payload.title,
        terminal_state=payload.terminal_state,
        jurisdiction=payload.jurisdiction,
        market=payload.market,
        effective_date=payload.effective_date,
        retrieved_date=payload.retrieved_date,
        review_date=payload.review_date,
        expires_date=payload.expires_date,
        license_status=payload.license_status,
        permission_status=payload.permission_status,
        quality_score=payload.quality_score,
        confidence_score=payload.confidence_score,
        version=payload.version,
        superseded_by=payload.superseded_by,
        review_status=payload.review_status,
        allowed_systems_json=json.dumps(payload.allowed_systems),
        citation_ref=payload.citation_ref,
        url=payload.url,
        refresh_schedule=payload.refresh_schedule,
        excluded=payload.excluded,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return KnowledgeRegistryOut(
        id=item.id,
        item_id=item.item_id,
        source=item.source,
        source_type=item.source_type,
        title=item.title,
        terminal_state=item.terminal_state,
        allowed_systems=_loads(item.allowed_systems_json, []),
        citation_ref=item.citation_ref,
        review_status=item.review_status,
    )


@router.get("/knowledge-items", response_model=list[KnowledgeRegistryOut])
def list_knowledge_items(db: Session = Depends(get_db), terminal_state: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(KnowledgeRegistryItem)
    if terminal_state:
        q = q.filter(KnowledgeRegistryItem.terminal_state == terminal_state)

    rows = q.order_by(KnowledgeRegistryItem.id.desc()).limit(500).all()
    return [
        KnowledgeRegistryOut(
            id=row.id,
            item_id=row.item_id,
            source=row.source,
            source_type=row.source_type,
            title=row.title,
            terminal_state=row.terminal_state,
            allowed_systems=_loads(row.allowed_systems_json, []),
            citation_ref=row.citation_ref,
            review_status=row.review_status,
        )
        for row in rows
    ]


@router.post("/template-items", response_model=TemplateRegistryOut)
def create_template_item(payload: TemplateRegistryCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)

    exists = db.query(TemplateRegistryItem).filter(TemplateRegistryItem.template_id == payload.template_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="template_id already exists")

    if payload.superseded_by is None and payload.terminal_state != RegistryStates.SUPERSEDED_REJECTED_NOT_APPLICABLE:
        supersede_q = db.query(TemplateRegistryItem).filter(
            TemplateRegistryItem.family == payload.family,
            TemplateRegistryItem.purpose == payload.purpose,
            TemplateRegistryItem.audience == payload.audience,
            TemplateRegistryItem.superseded_by.is_(None),
        )
        if payload.channel is None:
            supersede_q = supersede_q.filter(TemplateRegistryItem.channel.is_(None))
        else:
            supersede_q = supersede_q.filter(TemplateRegistryItem.channel == payload.channel)

        if payload.jurisdiction is None:
            supersede_q = supersede_q.filter(TemplateRegistryItem.jurisdiction.is_(None))
        else:
            supersede_q = supersede_q.filter(TemplateRegistryItem.jurisdiction == payload.jurisdiction)

        if payload.entity is None:
            supersede_q = supersede_q.filter(TemplateRegistryItem.entity.is_(None))
        else:
            supersede_q = supersede_q.filter(TemplateRegistryItem.entity == payload.entity)

        supersede_q.update({"superseded_by": payload.template_id}, synchronize_session=False)

    item = TemplateRegistryItem(
        template_id=payload.template_id,
        family=payload.family,
        purpose=payload.purpose,
        audience=payload.audience,
        channel=payload.channel,
        jurisdiction=payload.jurisdiction,
        entity=payload.entity,
        version=payload.version,
        effective_date=payload.effective_date,
        review_date=payload.review_date,
        superseded_by=payload.superseded_by,
        source_owner=payload.source_owner,
        required_variables_json=json.dumps(payload.required_variables),
        optional_variables_json=json.dumps(payload.optional_variables),
        required_attachments_json=json.dumps(payload.required_attachments),
        approval_required=payload.approval_required,
        professional_review_required=payload.professional_review_required,
        professional_review_status=payload.professional_review_status,
        signature_required=payload.signature_required,
        status=payload.status,
        template_hash=payload.template_hash,
        test_cases_ref=payload.test_cases_ref,
        terminal_state=payload.terminal_state,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return TemplateRegistryOut(
        id=item.id,
        template_id=item.template_id,
        family=item.family,
        purpose=item.purpose,
        status=item.status,
        terminal_state=item.terminal_state,
        required_variables=_loads(item.required_variables_json, []),
        superseded_by=item.superseded_by,
    )


@router.get("/template-items", response_model=list[TemplateRegistryOut])
def list_template_items(db: Session = Depends(get_db), terminal_state: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(TemplateRegistryItem)
    if terminal_state:
        q = q.filter(TemplateRegistryItem.terminal_state == terminal_state)

    rows = q.order_by(TemplateRegistryItem.id.desc()).limit(500).all()
    return [
        TemplateRegistryOut(
            id=row.id,
            template_id=row.template_id,
            family=row.family,
            purpose=row.purpose,
            status=row.status,
            terminal_state=row.terminal_state,
            required_variables=_loads(row.required_variables_json, []),
            superseded_by=row.superseded_by,
        )
        for row in rows
    ]


@router.post("/scoring-items", response_model=ScoringRegistryOut)
def create_scoring_item(payload: ScoringRegistryCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)

    exists = db.query(ScoringRegistryItem).filter(ScoringRegistryItem.score_id == payload.score_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="score_id already exists")

    if payload.active:
        db.query(ScoringRegistryItem).filter(
            ScoringRegistryItem.canonical_name == payload.canonical_name,
            ScoringRegistryItem.active.is_(True),
        ).update({"active": False}, synchronize_session=False)

    item = ScoringRegistryItem(
        score_id=payload.score_id,
        canonical_name=payload.canonical_name,
        business_purpose=payload.business_purpose,
        input_fields_json=json.dumps(payload.input_fields),
        formula_description=payload.formula_description,
        rules_json=json.dumps(payload.rules),
        weights_json=json.dumps(payload.weights),
        thresholds_json=json.dumps(payload.thresholds),
        normalization=payload.normalization,
        version=payload.version,
        effective_start=payload.effective_start,
        effective_end=payload.effective_end,
        jurisdiction=payload.jurisdiction,
        market=payload.market,
        owner_approval_status=payload.owner_approval_status,
        professional_approval_status=payload.professional_approval_status,
        confidence_handling=payload.confidence_handling,
        missing_data_behavior=payload.missing_data_behavior,
        bias_compliance_notes=payload.bias_compliance_notes,
        benchmark_ref=payload.benchmark_ref,
        acceptable_error_range=payload.acceptable_error_range,
        drift_policy=payload.drift_policy,
        override_policy=payload.override_policy,
        rollback_policy=payload.rollback_policy,
        prohibited_actions=payload.prohibited_actions,
        terminal_state=payload.terminal_state,
        active=payload.active,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return ScoringRegistryOut(
        id=item.id,
        score_id=item.score_id,
        canonical_name=item.canonical_name,
        version=item.version,
        terminal_state=item.terminal_state,
        input_fields=_loads(item.input_fields_json, []),
        active=item.active,
    )


@router.get("/scoring-items", response_model=list[ScoringRegistryOut])
def list_scoring_items(db: Session = Depends(get_db), terminal_state: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(ScoringRegistryItem)
    if terminal_state:
        q = q.filter(ScoringRegistryItem.terminal_state == terminal_state)

    rows = q.order_by(ScoringRegistryItem.id.desc()).limit(500).all()
    return [
        ScoringRegistryOut(
            id=row.id,
            score_id=row.score_id,
            canonical_name=row.canonical_name,
            version=row.version,
            terminal_state=row.terminal_state,
            input_fields=_loads(row.input_fields_json, []),
            active=row.active,
        )
        for row in rows
    ]


@router.post("/source-items", response_model=SourceRegistryOut)
def create_source_item(payload: SourceRegistryCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)

    exists = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == payload.source_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="source_id already exists")

    _default_allowlist_for_data_class(payload.data_class)

    normalized_allowlist = [_normalize_mode(mode) for mode in payload.mode_allowlist]
    permission_status = _normalize_source_permission_status(payload.permission_status)
    license_status = _normalize_source_license_status(payload.license_status)
    trust_tier = _normalize_source_trust_tier(payload.trust_tier)
    governance_status = _normalize_source_governance_status(payload.governance_status)

    item = SourceRegistryItem(
        source_id=payload.source_id,
        canonical_name=payload.canonical_name,
        source_type=payload.source_type,
        data_class=payload.data_class.strip().lower(),
        owner=payload.owner,
        jurisdiction=payload.jurisdiction,
        market=payload.market,
        citation_ref=payload.citation_ref,
        permission_status=permission_status,
        license_status=license_status,
        rights_statement_url=payload.rights_statement_url,
        robots_policy=str(payload.robots_policy or "allowed").strip().lower(),
        trust_tier=trust_tier,
        provenance_method=payload.provenance_method,
        freshness_sla_hours=payload.freshness_sla_hours,
        last_verified_at=payload.last_verified_at,
        governance_status=governance_status,
        shadow_approved=payload.shadow_approved,
        mode_allowlist_json=json.dumps(normalized_allowlist),
        active=payload.active,
        terminal_state=payload.terminal_state,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return SourceRegistryOut(
        id=item.id,
        source_id=item.source_id,
        canonical_name=item.canonical_name,
        source_type=item.source_type,
        data_class=item.data_class,
        terminal_state=item.terminal_state,
        permission_status=item.permission_status,
        license_status=item.license_status,
        rights_statement_url=item.rights_statement_url,
        robots_policy=item.robots_policy,
        trust_tier=item.trust_tier,
        provenance_method=item.provenance_method,
        freshness_sla_hours=item.freshness_sla_hours,
        last_verified_at=item.last_verified_at,
        governance_status=item.governance_status,
        shadow_approved=item.shadow_approved,
        mode_allowlist=_loads(item.mode_allowlist_json, []),
        active=item.active,
    )


@router.get("/source-items", response_model=list[SourceRegistryOut])
def list_source_items(db: Session = Depends(get_db), terminal_state: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(SourceRegistryItem)
    if terminal_state:
        q = q.filter(SourceRegistryItem.terminal_state == terminal_state)

    rows = q.order_by(SourceRegistryItem.id.desc()).limit(500).all()
    return [
        SourceRegistryOut(
            id=row.id,
            source_id=row.source_id,
            canonical_name=row.canonical_name,
            source_type=row.source_type,
            data_class=row.data_class,
            terminal_state=row.terminal_state,
            permission_status=row.permission_status,
            license_status=row.license_status,
            rights_statement_url=row.rights_statement_url,
            robots_policy=row.robots_policy,
            trust_tier=row.trust_tier,
            provenance_method=row.provenance_method,
            freshness_sla_hours=row.freshness_sla_hours,
            last_verified_at=row.last_verified_at,
            governance_status=row.governance_status,
            shadow_approved=row.shadow_approved,
            mode_allowlist=_loads(row.mode_allowlist_json, []),
            active=row.active,
        )
        for row in rows
    ]


@router.post("/source-items/validate-use", response_model=SourceUsageCheckOut)
def validate_source_usage(payload: SourceUsageCheckIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    mode = _normalize_mode(payload.mode)

    row = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == payload.source_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="source_id not found")

    if not row.active:
        raise HTTPException(status_code=409, detail="source is inactive")

    allowlist_raw = _loads(row.mode_allowlist_json, [])
    if allowlist_raw:
        allowed_modes = {m for m in (_normalize_mode(v) for v in allowlist_raw)}
    else:
        allowed_modes = _default_allowlist_for_data_class(row.data_class)

    if mode not in allowed_modes:
        raise HTTPException(
            status_code=409,
            detail=f"source '{row.source_id}' with data_class '{row.data_class}' is not allowed in mode '{mode}'",
        )

    if mode in {"practice", "test"} and row.data_class == "live":
        _assert_source_shadow_ready(row)

    return SourceUsageCheckOut(
        source_id=row.source_id,
        mode=mode,
        allowed=True,
        reason="Source is authorized for requested mode",
    )


@router.post("/dataset-items", response_model=DatasetRegistryOut)
def create_dataset_item(payload: DatasetRegistryCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)
    dataset_type = _dataset_type_or_error(payload.type)

    exists = db.query(DatasetRegistryItem).filter(DatasetRegistryItem.dataset_id == payload.dataset_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="dataset_id already exists")

    item = DatasetRegistryItem(
        dataset_id=payload.dataset_id,
        name=payload.name,
        dataset_type=dataset_type,
        purpose=payload.purpose,
        domain=payload.domain,
        jurisdiction=payload.jurisdiction,
        business_engine=payload.business_engine,
        record_count=payload.record_count,
        generation_method=payload.generation_method,
        generator_version=payload.generator_version,
        seed=payload.seed,
        created_at_source=payload.created_at,
        validated_at=payload.validated_at,
        learning_eligibility=payload.learning_eligibility,
        live_kpi_eligibility=payload.live_kpi_eligibility,
        accounting_eligibility=payload.accounting_eligibility,
        external_execution_eligibility=payload.external_execution_eligibility,
        do_not_contact=payload.do_not_contact,
        expected_behavior=payload.expected_behavior,
        isolation_policy=payload.isolation_policy,
        purge_archive_procedure=payload.purge_archive_procedure,
        test_coverage=payload.test_coverage,
        status=payload.status,
        source_id=payload.source_id,
        terminal_state=payload.terminal_state,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return DatasetRegistryOut(
        id=item.id,
        dataset_id=item.dataset_id,
        name=item.name,
        type=item.dataset_type,
        domain=item.domain,
        jurisdiction=item.jurisdiction,
        business_engine=item.business_engine,
        learning_eligibility=item.learning_eligibility,
        live_kpi_eligibility=item.live_kpi_eligibility,
        accounting_eligibility=item.accounting_eligibility,
        external_execution_eligibility=item.external_execution_eligibility,
        do_not_contact=item.do_not_contact,
        source_id=item.source_id,
        terminal_state=item.terminal_state,
        status=item.status,
    )


@router.get("/dataset-items", response_model=list[DatasetRegistryOut])
def list_dataset_items(db: Session = Depends(get_db), terminal_state: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(DatasetRegistryItem)
    if terminal_state:
        q = q.filter(DatasetRegistryItem.terminal_state == terminal_state)
    rows = q.order_by(DatasetRegistryItem.id.desc()).limit(500).all()
    return [
        DatasetRegistryOut(
            id=row.id,
            dataset_id=row.dataset_id,
            name=row.name,
            type=row.dataset_type,
            domain=row.domain,
            jurisdiction=row.jurisdiction,
            business_engine=row.business_engine,
            learning_eligibility=row.learning_eligibility,
            live_kpi_eligibility=row.live_kpi_eligibility,
            accounting_eligibility=row.accounting_eligibility,
            external_execution_eligibility=row.external_execution_eligibility,
            do_not_contact=row.do_not_contact,
            source_id=row.source_id,
            terminal_state=row.terminal_state,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/dataset-items/validate-use", response_model=DatasetUseValidationOut)
def validate_dataset_usage(payload: DatasetUseValidationIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    mode = _normalize_mode(payload.mode)
    action = (payload.requested_action or "").strip().lower()

    dataset = db.query(DatasetRegistryItem).filter(DatasetRegistryItem.dataset_id == payload.dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset_id not found")

    source_id = payload.source_id or dataset.source_id
    if source_id:
        source = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == source_id).first()
        if source is None:
            raise HTTPException(status_code=404, detail="source_id not found")
        allowlist_raw = _loads(source.mode_allowlist_json, [])
        if allowlist_raw:
            allowed_modes = {m for m in (_normalize_mode(v) for v in allowlist_raw)}
        else:
            allowed_modes = _default_allowlist_for_data_class(source.data_class)
        if mode not in allowed_modes:
            raise HTTPException(
                status_code=409,
                detail=f"source '{source.source_id}' with data_class '{source.data_class}' is not allowed in mode '{mode}'",
            )
        if mode in {"practice", "test"} and source.data_class == "live":
            _assert_source_shadow_ready(source)

    source_class = source.data_class if source_id else None
    result = evaluate_dataset_safety(
        DatasetSafetyInput(
            dataset_type=dataset.dataset_type,
            mode=mode,
            requested_action=action,
            source_data_class=source_class,
            learning_eligibility=dataset.learning_eligibility,
            live_kpi_eligibility=dataset.live_kpi_eligibility,
            accounting_eligibility=dataset.accounting_eligibility,
            external_execution_eligibility=dataset.external_execution_eligibility,
            do_not_contact=dataset.do_not_contact,
            dataset_jurisdiction=dataset.jurisdiction,
            request_jurisdiction=payload.jurisdiction,
            dataset_business_scope=dataset.business_engine,
            request_business_scope=payload.business_scope,
        )
    )
    if not result.allowed:
        raise HTTPException(status_code=409, detail=result.reason)

    return DatasetUseValidationOut(
        dataset_id=dataset.dataset_id,
        mode=mode,
        requested_action=action,
        allowed=True,
        reason=result.reason,
    )


@router.post("/scenario-items", response_model=ScenarioRegistryOut)
def create_scenario_item(payload: ScenarioRegistryCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)
    category = _scenario_category_or_error(payload.category)

    exists = db.query(ScenarioRegistryItem).filter(ScenarioRegistryItem.scenario_id == payload.scenario_id).first()
    if exists:
        raise HTTPException(status_code=409, detail="scenario_id already exists")

    dataset = db.query(DatasetRegistryItem).filter(DatasetRegistryItem.dataset_id == payload.input_dataset).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="input_dataset not found")

    row = ScenarioRegistryItem(
        scenario_id=payload.scenario_id,
        name=payload.name,
        category=category,
        domain=payload.domain,
        jurisdiction=payload.jurisdiction,
        business_engine=payload.business_engine,
        difficulty=payload.difficulty,
        initial_state=payload.initial_state,
        input_dataset=payload.input_dataset,
        expected_allowed_actions_json=json.dumps(payload.expected_allowed_actions),
        expected_prohibited_actions_json=json.dumps(payload.expected_prohibited_actions),
        expected_owner_message=payload.expected_owner_message,
        expected_specialist_reviews_json=json.dumps(payload.expected_specialist_reviews),
        expected_approval_requirement=payload.expected_approval_requirement,
        expected_final_state=payload.expected_final_state,
        expected_audit_events_json=json.dumps(payload.expected_audit_events),
        failure_injection=payload.failure_injection,
        recovery_path=payload.recovery_path,
        practice_safe=payload.practice_safe,
        external_side_effects_allowed=payload.external_side_effects_allowed,
        version=payload.version,
        status=payload.status,
        terminal_state=payload.terminal_state,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ScenarioRegistryOut(
        id=row.id,
        scenario_id=row.scenario_id,
        name=row.name,
        category=row.category,
        domain=row.domain,
        jurisdiction=row.jurisdiction,
        business_engine=row.business_engine,
        input_dataset=row.input_dataset,
        expected_allowed_actions=_loads(row.expected_allowed_actions_json, []),
        expected_prohibited_actions=_loads(row.expected_prohibited_actions_json, []),
        expected_final_state=row.expected_final_state,
        practice_safe=row.practice_safe,
        external_side_effects_allowed=row.external_side_effects_allowed,
        version=row.version,
        status=row.status,
        terminal_state=row.terminal_state,
    )


@router.get("/scenario-items", response_model=list[ScenarioRegistryOut])
def list_scenario_items(db: Session = Depends(get_db), category: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(ScenarioRegistryItem)
    if category:
        q = q.filter(ScenarioRegistryItem.category == _scenario_category_or_error(category))
    rows = q.order_by(ScenarioRegistryItem.id.desc()).limit(1000).all()
    return [
        ScenarioRegistryOut(
            id=row.id,
            scenario_id=row.scenario_id,
            name=row.name,
            category=row.category,
            domain=row.domain,
            jurisdiction=row.jurisdiction,
            business_engine=row.business_engine,
            input_dataset=row.input_dataset,
            expected_allowed_actions=_loads(row.expected_allowed_actions_json, []),
            expected_prohibited_actions=_loads(row.expected_prohibited_actions_json, []),
            expected_final_state=row.expected_final_state,
            practice_safe=row.practice_safe,
            external_side_effects_allowed=row.external_side_effects_allowed,
            version=row.version,
            status=row.status,
            terminal_state=row.terminal_state,
        )
        for row in rows
    ]


@router.get("/scenario-items/{scenario_id}", response_model=ScenarioRegistryOut)
def get_scenario_item(scenario_id: str, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    row = db.query(ScenarioRegistryItem).filter(ScenarioRegistryItem.scenario_id == scenario_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="scenario_id not found")
    return ScenarioRegistryOut(
        id=row.id,
        scenario_id=row.scenario_id,
        name=row.name,
        category=row.category,
        domain=row.domain,
        jurisdiction=row.jurisdiction,
        business_engine=row.business_engine,
        input_dataset=row.input_dataset,
        expected_allowed_actions=_loads(row.expected_allowed_actions_json, []),
        expected_prohibited_actions=_loads(row.expected_prohibited_actions_json, []),
        expected_final_state=row.expected_final_state,
        practice_safe=row.practice_safe,
        external_side_effects_allowed=row.external_side_effects_allowed,
        version=row.version,
        status=row.status,
        terminal_state=row.terminal_state,
    )


@router.get("/scenario-items/{scenario_id}/validate", response_model=ScenarioSafetyOut)
def validate_scenario_safety(scenario_id: str, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    scenario = db.query(ScenarioRegistryItem).filter(ScenarioRegistryItem.scenario_id == scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario_id not found")

    dataset = db.query(DatasetRegistryItem).filter(DatasetRegistryItem.dataset_id == scenario.input_dataset).first()
    source = None
    if dataset is not None and dataset.source_id:
        source = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == dataset.source_id).first()

    result = evaluate_scenario_safety(
        ScenarioSafetyInput(
            scenario_id=scenario.scenario_id,
            category=scenario.category,
            practice_safe=scenario.practice_safe,
            external_side_effects_allowed=scenario.external_side_effects_allowed,
            dataset_id=dataset.dataset_id if dataset is not None else None,
            dataset_type=dataset.dataset_type if dataset is not None else None,
            source_id=source.source_id if source is not None else dataset.source_id if dataset is not None else None,
            source_data_class=source.data_class if source is not None else None,
            jurisdiction=scenario.jurisdiction,
            business_engine=scenario.business_engine,
        )
    )

    return ScenarioSafetyOut(
        scenario_id=scenario_id,
        safe=result.safe,
        blocking_reasons=result.blocking_reasons,
        lineage=result.lineage,
    )


@router.post("/scenario-items/instantiate", response_model=ScenarioExecutionOut)
def instantiate_scenario(payload: ScenarioInstantiateIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    mode = _normalize_mode(payload.mode)
    scenario = db.query(ScenarioRegistryItem).filter(ScenarioRegistryItem.scenario_id == payload.scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario_id not found")

    safety = validate_scenario_safety(payload.scenario_id, db)
    if not safety.safe:
        raise HTTPException(status_code=409, detail="; ".join(safety.blocking_reasons))

    execution_id = f"SCN-RUN-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    record = ScenarioExecutionRecord(
        execution_id=execution_id,
        scenario_id=payload.scenario_id,
        mode=mode,
        status="instantiated",
        run_kind="synthetic",
        input_payload_json=json.dumps(payload.input_payload),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ScenarioExecutionOut(
        execution_id=record.execution_id,
        scenario_id=record.scenario_id,
        mode=record.mode,
        status=record.status,
        run_kind=record.run_kind,
        replay_of_execution_id=record.replay_of_execution_id,
    )


@router.post("/scenario-items/reset-replay/{execution_id}", response_model=ScenarioExecutionOut)
def reset_replay_scenario(execution_id: str, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    prior = db.query(ScenarioExecutionRecord).filter(ScenarioExecutionRecord.execution_id == execution_id).first()
    if prior is None:
        raise HTTPException(status_code=404, detail="execution_id not found")

    replay_id = f"SCN-RUN-{int(datetime.now(timezone.utc).timestamp() * 1000)}-REPLAY"
    replay = ScenarioExecutionRecord(
        execution_id=replay_id,
        scenario_id=prior.scenario_id,
        mode=prior.mode,
        status="instantiated",
        run_kind=prior.run_kind,
        input_payload_json=prior.input_payload_json,
        replay_of_execution_id=prior.execution_id,
    )
    db.add(replay)
    db.commit()
    db.refresh(replay)

    return ScenarioExecutionOut(
        execution_id=replay.execution_id,
        scenario_id=replay.scenario_id,
        mode=replay.mode,
        status=replay.status,
        run_kind=replay.run_kind,
        replay_of_execution_id=replay.replay_of_execution_id,
    )


@router.post("/scenario-items/record-result", response_model=ScenarioExecutionOut)
def record_scenario_result(payload: ScenarioResultIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    record = db.query(ScenarioExecutionRecord).filter(ScenarioExecutionRecord.execution_id == payload.execution_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="execution_id not found")

    record.status = payload.status
    record.actual_result_json = json.dumps(payload.actual_result)
    record.audit_evidence_json = json.dumps(payload.audit_evidence)
    if payload.status in {"completed", "failed", "blocked"}:
        record.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(record)

    return ScenarioExecutionOut(
        execution_id=record.execution_id,
        scenario_id=record.scenario_id,
        mode=record.mode,
        status=record.status,
        run_kind=record.run_kind,
        replay_of_execution_id=record.replay_of_execution_id,
    )


@router.get("/scenario-items/compare/{execution_id}", response_model=ScenarioCompareOut)
def compare_scenario_result(execution_id: str, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    record = db.query(ScenarioExecutionRecord).filter(ScenarioExecutionRecord.execution_id == execution_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="execution_id not found")

    scenario = db.query(ScenarioRegistryItem).filter(ScenarioRegistryItem.scenario_id == record.scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")

    mismatches: list[str] = []
    actual = _loads(record.actual_result_json, {})
    final_state = str(actual.get("final_state", ""))
    if final_state and final_state != scenario.expected_final_state:
        mismatches.append(f"final_state expected '{scenario.expected_final_state}' got '{final_state}'")

    executed_actions = [str(v).lower() for v in actual.get("executed_actions", [])]
    prohibited_actions = [str(v).lower() for v in _loads(scenario.expected_prohibited_actions_json, [])]
    for action in prohibited_actions:
        if action in executed_actions:
            mismatches.append(f"prohibited action executed: {action}")

    passed = len(mismatches) == 0
    record.comparison_json = json.dumps({"passed": passed, "mismatches": mismatches})
    db.commit()

    return ScenarioCompareOut(
        execution_id=record.execution_id,
        scenario_id=record.scenario_id,
        passed=passed,
        mismatches=mismatches,
    )


@router.post("/knowledge/retrieve", response_model=KnowledgeRetrieveOut)
def retrieve_knowledge(payload: KnowledgeRetrieveIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    mode = _normalize_mode(payload.mode)

    q = db.query(KnowledgeRegistryItem).filter(KnowledgeRegistryItem.excluded.is_(False))
    q = q.filter(KnowledgeRegistryItem.title.ilike(f"%{payload.domain}%") | KnowledgeRegistryItem.source.ilike(f"%{payload.domain}%"))
    if payload.jurisdiction:
        q = q.filter((KnowledgeRegistryItem.jurisdiction == payload.jurisdiction) | (KnowledgeRegistryItem.jurisdiction.is_(None)))

    rows = q.order_by(KnowledgeRegistryItem.id.desc()).limit(200).all()

    facts: list[dict[str, Any]] = []
    assumptions: list[dict[str, Any]] = []
    blocked_sources: list[dict[str, Any]] = []
    escalation_reasons: list[str] = []
    provisional_facts: list[dict[str, Any]] = []
    grouped_titles: dict[str, list[dict[str, Any]]] = {}
    high_impact = str(payload.risk_level or "").strip().lower() in {"high", "critical"}

    for row in rows:
        source = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == row.source).first()
        if source is not None:
            allowlist_raw = _loads(source.mode_allowlist_json, [])
            if allowlist_raw:
                allowed_modes = {m for m in (_normalize_mode(v) for v in allowlist_raw)}
            else:
                allowed_modes = _default_allowlist_for_data_class(source.data_class)
            if mode not in allowed_modes:
                blocked_sources.append({"source_id": source.source_id, "reason": f"mode {mode} not allowed"})
                continue

        injection = _contains_prompt_injection(row.notes)
        if injection is None:
            injection = _contains_prompt_injection(row.title)

        if injection:
            blocked_sources.append({"source_id": row.source, "reason": f"prompt-injection pattern detected: {injection}"})
            continue

        poisoned = _contains_poisoned_data_pattern(row.notes)
        if poisoned is None:
            poisoned = _contains_poisoned_data_pattern(row.title)
        if poisoned:
            blocked_sources.append({"source_id": row.source, "reason": f"poisoned-data pattern detected: {poisoned}"})
            continue

        sensitive = _contains_sensitive_data(row.notes)
        if sensitive is None:
            sensitive = _contains_sensitive_data(row.title)
        if sensitive:
            blocked_sources.append({"source_id": row.source, "reason": f"sensitive data pattern detected: {sensitive}"})
            continue

        freshness = _freshness_state(row.review_date)
        age_days = _review_age_days(row.review_date)
        effective_confidence = _effective_confidence(row.confidence_score, row.review_date)

        entry = {
            "item_id": row.item_id,
            "source": row.source,
            "title": row.title,
            "citation_ref": row.citation_ref,
            "review_status": row.review_status,
            "jurisdiction": row.jurisdiction,
            "confidence_score": row.confidence_score,
            "effective_confidence_score": round(effective_confidence, 4),
            "quality_score": row.quality_score,
            "review_date": row.review_date.isoformat() if row.review_date else None,
            "freshness_state": freshness,
            "review_age_days": age_days,
            "source_trust_rank": _source_trust_rank(row.source_type),
            "source_type": row.source_type,
        }
        quality_ok = (row.quality_score or 0) >= 0.7 and effective_confidence >= 0.7
        reviewed_ok = str(row.review_status or "").lower() in {"approved", "verified"}
        citation_ok = bool((row.citation_ref or "").strip())
        if freshness == "hard_stale":
            assumptions.append(entry)
            blocked_sources.append({"source_id": row.source, "reason": "review_date is older than 2 years; re-verification required"})
            continue

        if quality_ok and reviewed_ok and citation_ok:
            if high_impact and entry["source_trust_rank"] < 3:
                assumptions.append(entry)
                blocked_sources.append({"source_id": row.source, "reason": "high-impact retrieval requires tier-1 or tier-2 sources"})
                continue
            provisional_facts.append(entry)
            key = _title_key(row.title)
            grouped_titles.setdefault(key, []).append(entry)
        else:
            assumptions.append(entry)
            if not citation_ok:
                blocked_sources.append({"source_id": row.source, "reason": "missing citation_ref for fact-grade use"})
            if freshness == "soft_stale":
                blocked_sources.append({"source_id": row.source, "reason": "review_date is older than 1 year; confidence decay applied"})

    contradicted_ids: set[str] = set()
    for key, entries in grouped_titles.items():
        if len(entries) < 2:
            continue
        sorted_entries = sorted(entries, key=lambda x: float(x.get("confidence_score") or 0), reverse=True)
        highest = float(sorted_entries[0].get("confidence_score") or 0)
        lowest = float(sorted_entries[-1].get("confidence_score") or 0)
        sources = {str(e.get("source") or "") for e in entries}
        if len(sources) > 1 and (highest - lowest) >= 0.2:
            for e in entries:
                contradicted_ids.add(str(e.get("item_id")))
            blocked_sources.append(
                {
                    "source_id": ",".join(sorted(sources)),
                    "reason": f"contradiction detected for title '{key}' (confidence spread {highest - lowest:.2f})",
                }
            )

    for entry in provisional_facts:
        if str(entry.get("item_id")) in contradicted_ids:
            assumptions.append(entry)
            continue
        facts.append(entry)

    if contradicted_ids:
        escalation_reasons.append("contradictions detected; human review required before high-impact use")

    if high_impact:
        if not facts:
            escalation_reasons.append("no high-confidence fact-grade evidence available for high-impact request")
        if any(f.get("freshness_state") == "soft_stale" for f in facts):
            escalation_reasons.append("high-impact request uses stale evidence older than 1 year")

    facts.sort(
        key=lambda e: (
            1 if payload.jurisdiction and e.get("jurisdiction") == payload.jurisdiction else 0,
            int(e.get("source_trust_rank") or 0),
            float(e.get("confidence_score") or 0),
            float(e.get("quality_score") or 0),
            e.get("review_date") or "",
        ),
        reverse=True,
    )

    return KnowledgeRetrieveOut(
        question=payload.question,
        facts=facts,
        assumptions=assumptions,
        blocked_sources=blocked_sources,
        human_review_required=len(escalation_reasons) > 0,
        escalation_reasons=escalation_reasons,
    )


@router.post("/knowledge/ingest", response_model=KnowledgeIngestOut)
def ingest_knowledge(payload: KnowledgeIngestIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)

    trigger_type = _normalize_trigger_type(payload.trigger_type)
    mode = _normalize_mode(payload.mode)

    source = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == payload.source_id).first()
    if source is None:
        raise HTTPException(status_code=404, detail="source_id not found")
    if not source.active:
        raise HTTPException(status_code=409, detail="source is inactive")

    allowlist_raw = _loads(source.mode_allowlist_json, [])
    if allowlist_raw:
        allowed_modes = {m for m in (_normalize_mode(v) for v in allowlist_raw)}
    else:
        allowed_modes = _default_allowlist_for_data_class(source.data_class)
    if mode not in allowed_modes:
        raise HTTPException(
            status_code=409,
            detail=f"source '{source.source_id}' with data_class '{source.data_class}' is not allowed in mode '{mode}'",
        )

    if mode in {"practice", "test"} and source.data_class == "live":
        _assert_source_shadow_ready(source)

    if trigger_type in {"scheduled", "event"} and not payload.robots_allowed:
        raise HTTPException(status_code=409, detail="robots policy blocks non-push ingestion")

    blocked_reason = _permission_or_license_blocked(payload.permission_status, payload.license_status)
    if blocked_reason is not None:
        raise HTTPException(status_code=409, detail=blocked_reason)

    injection = _contains_prompt_injection(payload.content_excerpt)
    if injection is None:
        injection = _contains_prompt_injection(payload.notes)
    if injection is None:
        injection = _contains_prompt_injection(payload.title)
    if injection is not None:
        raise HTTPException(status_code=409, detail=f"prompt-injection pattern detected: {injection}")

    poisoned = _contains_poisoned_data_pattern(payload.content_excerpt)
    if poisoned is None:
        poisoned = _contains_poisoned_data_pattern(payload.notes)
    if poisoned is None:
        poisoned = _contains_poisoned_data_pattern(payload.title)
    if poisoned is not None:
        raise HTTPException(status_code=409, detail=f"poisoned-data pattern detected: {poisoned}")

    sensitive = _contains_sensitive_data(payload.content_excerpt)
    if sensitive is None:
        sensitive = _contains_sensitive_data(payload.notes)
    if sensitive is not None:
        raise HTTPException(status_code=409, detail=f"sensitive data pattern detected: {sensitive}")

    if mode == "live" and not str(payload.citation_ref or "").strip():
        raise HTTPException(status_code=409, detail="live ingestion requires citation_ref")

    exists = db.query(KnowledgeRegistryItem).filter(KnowledgeRegistryItem.item_id == payload.item_id).first()
    if exists is not None:
        raise HTTPException(status_code=409, detail="item_id already exists")

    retrieved_dt = payload.retrieved_at or datetime.now(timezone.utc)
    retrieved_date = retrieved_dt.date()
    review_date = payload.review_date or retrieved_date

    domain_title = f"{payload.domain.upper()} {payload.title.strip()}" if payload.domain else payload.title.strip()

    row = KnowledgeRegistryItem(
        item_id=payload.item_id,
        source=payload.source_id,
        source_type=source.source_type,
        title=domain_title,
        terminal_state=RegistryStates.ACTIVE_AND_VERIFIED,
        jurisdiction=payload.jurisdiction,
        market=payload.market,
        retrieved_date=retrieved_date,
        review_date=review_date,
        license_status=payload.license_status,
        permission_status=payload.permission_status,
        quality_score=0.8,
        confidence_score=0.8,
        version=payload.version,
        review_status="approved",
        citation_ref=payload.citation_ref,
        notes=(
            f"ingestion_id={payload.ingestion_id}; trigger={trigger_type}; mode={mode}; "
            f"source={payload.source_id}; robots_allowed={payload.robots_allowed}; "
            f"{payload.notes or ''}"
        ).strip(),
    )
    db.add(row)

    followup_task_id = None
    if payload.queue_followup_task:
        followup_task_id = f"LQ-INGEST-{payload.ingestion_id}"
        existing_task = db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.task_id == followup_task_id).first()
        if existing_task is None:
            db.add(
                LearningTaskQueueItem(
                    task_id=followup_task_id,
                    task_type="VERIFY_INGESTION_PROVENANCE",
                    status="queued",
                    priority="high" if mode == "live" else "normal",
                    domain=payload.domain.upper(),
                    jurisdiction=payload.jurisdiction,
                    business_scope=payload.market,
                    knowledge_item_id=payload.item_id,
                    reason=f"Verify ingestion provenance for {payload.item_id} ({trigger_type} trigger)",
                )
            )

    reverify_task_id = None
    freshness = _freshness_state(review_date)
    if freshness == "hard_stale":
        reverify_task_id = f"LQ-REVERIFY-{payload.item_id}"
        existing_reverify = db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.task_id == reverify_task_id).first()
        if existing_reverify is None:
            db.add(
                LearningTaskQueueItem(
                    task_id=reverify_task_id,
                    task_type="REVERIFY_KNOWLEDGE",
                    status="queued",
                    priority="critical",
                    domain=payload.domain.upper(),
                    jurisdiction=payload.jurisdiction,
                    knowledge_item_id=payload.item_id,
                    reason="Ingested item is hard-stale and requires immediate re-verification.",
                )
            )

    db.commit()

    return KnowledgeIngestOut(
        ingestion_id=payload.ingestion_id,
        status="ingested",
        item_id=payload.item_id,
        trigger_type=trigger_type,
        source_id=payload.source_id,
        followup_task_id=followup_task_id,
        reverify_task_id=reverify_task_id,
        freshness_state=freshness,
    )


def _ensure_shadow_source(
    db: Session,
    *,
    source_id: str,
    canonical_name: str,
    source_type: str,
    citation_ref: str,
    rights_statement_url: str,
) -> SourceRegistryItem:
    row = db.query(SourceRegistryItem).filter(SourceRegistryItem.source_id == source_id).first()
    if row is not None:
        return row

    row = SourceRegistryItem(
        source_id=source_id,
        canonical_name=canonical_name,
        source_type=source_type,
        data_class="live",
        citation_ref=citation_ref,
        permission_status="public",
        license_status="government_open_data",
        rights_statement_url=rights_statement_url,
        robots_policy="api",
        trust_tier="tier2",
        provenance_method="official_api",
        freshness_sla_hours=168,
        last_verified_at=datetime.now(timezone.utc),
        governance_status="approved",
        shadow_approved=True,
        mode_allowlist_json=json.dumps(["practice", "test"]),
        active=True,
        terminal_state=RegistryStates.ACTIVE_AND_VERIFIED,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _fetch_winnipeg_shadow_records(limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    parse_failures = 0
    source_failures = 0
    timeout = httpx.Timeout(20.0)
    per_source = max(10, min(25, limit // 2))

    with httpx.Client(timeout=timeout) as client:
        try:
            wpg_resp = client.get(f"https://data.winnipeg.ca/api/views.json?$limit={per_source}")
            wpg_resp.raise_for_status()
            wpg_data = wpg_resp.json()
            if not isinstance(wpg_data, list):
                raise ValueError("unexpected response shape")
            for row in wpg_data[:per_source]:
                try:
                    view_id = str(row.get("id") or "")
                    name = str(row.get("name") or "Untitled dataset")
                    desc = str(row.get("description") or "")
                    records.append(
                        {
                            "source_id": "SRC-WPG-OPEN-DATA",
                            "external_id": view_id,
                            "title": name,
                            "domain": "real_estate",
                            "citation_ref": f"https://data.winnipeg.ca/d/{view_id}",
                            "notes": f"real_shadow_source=winnipeg_open_data; category={row.get('category')}",
                            "content_excerpt": desc[:500],
                        }
                    )
                except Exception:
                    parse_failures += 1
        except Exception:
            source_failures += 1

        try:
            ca_resp = client.get(
                "https://open.canada.ca/data/en/api/3/action/package_search",
                params={"q": "winnipeg real estate", "rows": per_source},
            )
            ca_resp.raise_for_status()
            ca_payload = ca_resp.json() or {}
            results = ((ca_payload.get("result") or {}).get("results") or []) if isinstance(ca_payload, dict) else []
            for row in results[:per_source]:
                try:
                    pkg_id = str(row.get("id") or "")
                    title = str(row.get("title") or row.get("name") or "Government dataset")
                    notes = f"real_shadow_source=open_canada; organization={((row.get('organization') or {}).get('title') if isinstance(row.get('organization'), dict) else '')}"
                    excerpt = str(row.get("notes") or "")
                    records.append(
                        {
                            "source_id": "SRC-CANADA-OPEN-DATA",
                            "external_id": pkg_id,
                            "title": title,
                            "domain": "real_estate",
                            "citation_ref": f"https://open.canada.ca/data/en/dataset/{pkg_id}",
                            "notes": notes,
                            "content_excerpt": excerpt[:500],
                        }
                    )
                except Exception:
                    parse_failures += 1
        except Exception:
            source_failures += 1

    return {
        "records": records[:limit],
        "parse_failures": parse_failures,
        "source_failures": source_failures,
    }


def _derive_shadow_insufficiency_statuses(row: dict[str, Any]) -> list[str]:
    statuses: list[str] = []

    valuation_confidence = row.get("valuation_confidence")
    has_comp_strength = row.get("comps_strength")
    if valuation_confidence is None or has_comp_strength in {None, "weak", "stale", "absent"}:
        statuses.append("VALUATION_CONFIDENCE_LOW")

    if not bool(row.get("buyer_pool_verified", False)):
        statuses.append("BUYER_DATA_INSUFFICIENT")

    if not bool(row.get("contact_verified", False)):
        statuses.append("CONTACT_NOT_VERIFIED")

    return statuses


@router.post("/shadow/rehearsal/winnipeg", response_model=ShadowWinnipegRehearsalOut)
def run_shadow_winnipeg_rehearsal(payload: ShadowWinnipegRehearsalIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    mode = _normalize_mode(payload.mode)
    if mode not in {"practice", "test"}:
        raise HTTPException(status_code=409, detail="shadow rehearsal is restricted to practice/test modes")

    source_map = {
        "SRC-WPG-OPEN-DATA": _ensure_shadow_source(
            db,
            source_id="SRC-WPG-OPEN-DATA",
            canonical_name="City of Winnipeg Open Data",
            source_type="government",
            citation_ref="https://data.winnipeg.ca",
            rights_statement_url="https://data.winnipeg.ca/stories/s/Open-Data-Winnipeg-Terms-of-Use/4h5q-kw4n/",
        ),
        "SRC-CANADA-OPEN-DATA": _ensure_shadow_source(
            db,
            source_id="SRC-CANADA-OPEN-DATA",
            canonical_name="Government of Canada Open Data",
            source_type="government",
            citation_ref="https://open.canada.ca/data/en",
            rights_statement_url="https://open.canada.ca/en/open-government-licence-canada",
        ),
    }

    allowed_source_ids = set(payload.source_ids or [])
    if not allowed_source_ids:
        allowed_source_ids = set(source_map.keys())

    blocked = 0
    for source_id, source in source_map.items():
        if source_id in allowed_source_ids:
            _assert_source_shadow_ready(source)

    fetched_payload = _fetch_winnipeg_shadow_records(payload.limit)
    if isinstance(fetched_payload, dict):
        fetched_rows = list(fetched_payload.get("records") or [])
        parse_failures = int(fetched_payload.get("parse_failures") or 0)
        source_failures = int(fetched_payload.get("source_failures") or 0)
    else:
        fetched_rows = list(fetched_payload or [])
        parse_failures = 0
        source_failures = 0

    inserted = 0
    duplicates = 0
    rejected = 0
    valuation_confidence_low = 0
    buyer_data_insufficient = 0
    contact_not_verified = 0
    pending_human_review = 0

    for row in fetched_rows:
        source_id = str(row.get("source_id") or "")
        if not source_id:
            parse_failures += 1
            continue
        if source_id not in allowed_source_ids:
            blocked += 1
            continue

        external_id = str(row.get("external_id") or row.get("title") or "")
        if not external_id:
            parse_failures += 1
            continue
        digest = sha1(f"{source_id}:{external_id}".encode("utf-8")).hexdigest()[:16]
        item_id = f"KN-SHADOW-{digest}"

        exists = db.query(KnowledgeRegistryItem).filter(KnowledgeRegistryItem.item_id == item_id).first()
        if exists is not None:
            duplicates += 1
            continue

        source = source_map[source_id]
        now_date = datetime.now(timezone.utc).date()
        insufficiency_statuses = _derive_shadow_insufficiency_statuses(row)
        needs_human_review = len(insufficiency_statuses) > 0
        if "VALUATION_CONFIDENCE_LOW" in insufficiency_statuses:
            valuation_confidence_low += 1
        if "BUYER_DATA_INSUFFICIENT" in insufficiency_statuses:
            buyer_data_insufficient += 1
        if "CONTACT_NOT_VERIFIED" in insufficiency_statuses:
            contact_not_verified += 1
        if needs_human_review:
            pending_human_review += 1

        if not str(row.get("citation_ref") or "").strip():
            rejected += 1
            continue

        db.add(
            KnowledgeRegistryItem(
                item_id=item_id,
                source=source_id,
                source_type=source.source_type,
                title=f"REAL_SHADOW {row['title']}",
                terminal_state=RegistryStates.ACTIVE_AND_VERIFIED,
                jurisdiction="CA-MB",
                market="Winnipeg",
                retrieved_date=now_date,
                review_date=now_date,
                license_status=source.license_status,
                permission_status=source.permission_status,
                quality_score=0.75,
                confidence_score=0.7,
                version=payload.batch_id,
                review_status="PENDING_HUMAN_REVIEW" if needs_human_review else "approved",
                citation_ref=row["citation_ref"],
                notes=(
                    f"shadow_batch={payload.batch_id}; mode={mode}; source={source_id}; "
                    f"provenance={source.provenance_method}; insufficiency_statuses={','.join(insufficiency_statuses) if insufficiency_statuses else 'NONE'}; "
                    f"{row.get('notes') or ''}"
                ).strip(),
            )
        )
        inserted += 1

    db.commit()

    return ShadowWinnipegRehearsalOut(
        batch_id=payload.batch_id,
        mode=mode,
        requested_limit=payload.limit,
        fetched=len(fetched_rows),
        inserted=inserted,
        duplicates=duplicates,
        blocked=blocked,
        rejected=rejected,
        parse_failures=parse_failures,
        source_failures=source_failures,
        valuation_confidence_low=valuation_confidence_low,
        buyer_data_insufficient=buyer_data_insufficient,
        contact_not_verified=contact_not_verified,
        pending_human_review=pending_human_review,
        sources_used=sorted(list(allowed_source_ids)),
    )


@router.post("/learning/promotion/evaluate", response_model=LearningPromotionOut)
def evaluate_learning_promotion(payload: LearningPromotionIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    dataset = db.query(DatasetRegistryItem).filter(DatasetRegistryItem.dataset_id == payload.dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset_id not found")

    if dataset.dataset_type == "SYNTHETIC_OPERATIONAL" and payload.actual_outcome_class == "VERIFIED_REAL_OUTCOME":
        raise HTTPException(status_code=409, detail="synthetic outcome cannot be promoted to VERIFIED_REAL_OUTCOME")

    if dataset.dataset_type == "GOLD_BENCHMARK" and payload.actual_outcome_class == "LIVE_KPI":
        raise HTTPException(status_code=409, detail="gold benchmark cannot become live KPI evidence")

    state = "OBSERVED"
    reasons: list[str] = []

    if payload.sample_size >= 30 and payload.repeatable:
        state = "SUPPORTED"
    else:
        state = "CANDIDATE"
        reasons.append("sample size or repeatability insufficient")

    if payload.professional_required or payload.risk_level.lower() in {"high", "critical"}:
        state = "REVIEW_REQUIRED"
        reasons.append("professional or risk gate required")

    if payload.source_quality >= 0.85 and payload.sample_size >= 50 and payload.repeatable and payload.benchmark_result.lower() == "pass":
        state = "APPROVED"
        reasons.append("quality, sample, repeatability, and benchmark pass")

    if state == "APPROVED" and payload.actual_outcome_class == "VERIFIED_REAL_OUTCOME":
        state = "ACTIVE"
        reasons.append("verified real outcome present")

    if payload.benchmark_result.lower() == "fail":
        state = "REJECTED"
        reasons.append("benchmark failed")

    if state not in LEARNING_STATES:
        raise HTTPException(status_code=422, detail="invalid learning state")

    row = db.query(LearningPromotionRecord).filter(LearningPromotionRecord.learning_id == payload.learning_id).first()
    if row is None:
        row = LearningPromotionRecord(learning_id=payload.learning_id, dataset_id=payload.dataset_id, domain=payload.domain, current_state=state)
        db.add(row)
    row.dataset_id = payload.dataset_id
    row.domain = payload.domain
    row.current_state = state
    row.source_quality = payload.source_quality
    row.sample_size = payload.sample_size
    row.repeatable = payload.repeatable
    row.jurisdiction = payload.jurisdiction
    row.business_scope = payload.business_scope
    row.risk_level = payload.risk_level
    row.benchmark_result = payload.benchmark_result
    row.actual_outcome_class = payload.actual_outcome_class
    row.professional_required = payload.professional_required
    row.decision_reason = "; ".join(reasons) if reasons else "meets minimum policy"
    db.commit()

    return LearningPromotionOut(
        learning_id=payload.learning_id,
        dataset_id=payload.dataset_id,
        current_state=state,
        decision_reason=row.decision_reason or "meets minimum policy",
    )


@router.post("/learning/tasks", response_model=LearningTaskOut)
def create_learning_task(payload: LearningTaskCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    existing = db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.task_id == payload.task_id).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="task_id already exists")

    row = LearningTaskQueueItem(
        task_id=payload.task_id,
        task_type=payload.task_type,
        status=_normalize_task_status(payload.status),
        priority=_normalize_task_priority(payload.priority),
        domain=payload.domain,
        jurisdiction=payload.jurisdiction,
        business_scope=payload.business_scope,
        knowledge_item_id=payload.knowledge_item_id,
        learning_id=payload.learning_id,
        reason=payload.reason,
        assigned_to=payload.assigned_to,
        due_at=payload.due_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LearningTaskOut.model_validate(row)


@router.get("/learning/tasks", response_model=list[LearningTaskOut])
def list_learning_tasks(
    db: Session = Depends(get_db),
    status: str | None = None,
    domain: str | None = None,
    limit: int = 200,
):
    _ensure_registry_tables(db)
    q = db.query(LearningTaskQueueItem)
    if status:
        q = q.filter(LearningTaskQueueItem.status == _normalize_task_status(status))
    if domain:
        q = q.filter(LearningTaskQueueItem.domain == domain)
    rows = q.order_by(LearningTaskQueueItem.id.desc()).limit(max(1, min(limit, 1000))).all()
    return [LearningTaskOut.model_validate(row) for row in rows]


@router.post("/learning/tasks/reverify-stale", response_model=ReverifyStaleOut)
def enqueue_stale_reverification_tasks(db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    examined = 0
    created = 0
    existing_open = 0

    rows = db.query(KnowledgeRegistryItem).filter(KnowledgeRegistryItem.excluded.is_(False)).all()
    for row in rows:
        freshness = _freshness_state(row.review_date)
        if freshness != "hard_stale":
            continue

        examined += 1
        open_task = db.query(LearningTaskQueueItem).filter(
            LearningTaskQueueItem.knowledge_item_id == row.item_id,
            LearningTaskQueueItem.task_type == "REVERIFY_KNOWLEDGE",
            LearningTaskQueueItem.status.in_(["queued", "in_progress", "blocked"]),
        ).first()
        if open_task is not None:
            existing_open += 1
            continue

        task_id = f"LQ-REVERIFY-{row.item_id}"
        already = db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.task_id == task_id).first()
        if already is not None:
            existing_open += 1
            continue

        age_days = _review_age_days(row.review_date)
        task = LearningTaskQueueItem(
            task_id=task_id,
            task_type="REVERIFY_KNOWLEDGE",
            status="queued",
            priority="high",
            domain=(row.title.split(" ")[0].upper() if row.title else "OPERATIONS"),
            jurisdiction=row.jurisdiction,
            knowledge_item_id=row.item_id,
            reason=f"Knowledge item is hard-stale ({age_days} days since review). Re-verification required before fact-grade reuse.",
            due_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(task)
        created += 1

    db.commit()
    return ReverifyStaleOut(created=created, existing_open=existing_open, examined=examined)


@router.post("/learning/domains", response_model=LearningDomainOut)
def create_learning_domain(payload: LearningDomainCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)

    existing = db.query(LearningDomainRegistryItem).filter(LearningDomainRegistryItem.domain_id == payload.domain_id).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="domain_id already exists")

    row = LearningDomainRegistryItem(
        domain_id=payload.domain_id,
        canonical_name=payload.canonical_name,
        terminal_state=payload.terminal_state,
        jurisdiction=payload.jurisdiction,
        business_scope=payload.business_scope,
        owner=payload.owner,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(row)
    _create_learning_audit_event(
        db,
        event_id=f"LAE-DOMAIN-{payload.domain_id}",
        event_type="DOMAIN_REGISTERED",
        domain=payload.domain_id,
        message=f"Learning domain {payload.domain_id} registered",
        payload={"jurisdiction": payload.jurisdiction, "business_scope": payload.business_scope},
    )
    db.commit()
    db.refresh(row)
    return LearningDomainOut.model_validate(row)


@router.get("/learning/domains", response_model=list[LearningDomainOut])
def list_learning_domains(db: Session = Depends(get_db), jurisdiction: str | None = None):
    _ensure_registry_tables(db)
    q = db.query(LearningDomainRegistryItem)
    if jurisdiction:
        q = q.filter(
            (LearningDomainRegistryItem.jurisdiction == jurisdiction)
            | (LearningDomainRegistryItem.jurisdiction.is_(None))
        )
    rows = q.order_by(LearningDomainRegistryItem.id.desc()).limit(500).all()
    return [LearningDomainOut.model_validate(row) for row in rows]


@router.post("/learning/curricula", response_model=LearningCurriculumOut)
def create_learning_curriculum(payload: LearningCurriculumCreate, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    _ensure_terminal_state(payload.terminal_state)

    domain = db.query(LearningDomainRegistryItem).filter(LearningDomainRegistryItem.domain_id == payload.domain_id).first()
    if domain is None:
        raise HTTPException(status_code=404, detail="domain_id not found")

    existing = db.query(LearningCurriculumRegistryItem).filter(
        LearningCurriculumRegistryItem.curriculum_id == payload.curriculum_id
    ).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="curriculum_id already exists")

    row = LearningCurriculumRegistryItem(
        curriculum_id=payload.curriculum_id,
        domain_id=payload.domain_id,
        title=payload.title,
        version=payload.version,
        terminal_state=payload.terminal_state,
        jurisdiction=payload.jurisdiction,
        business_scope=payload.business_scope,
        learning_objectives_json=json.dumps(payload.learning_objectives),
        playbooks_json=json.dumps(payload.playbooks),
        benchmarks_json=json.dumps(payload.benchmarks),
        assessments_json=json.dumps(payload.assessments),
        promotion_gates_json=json.dumps(_promotion_gates(payload.promotion_gates)),
        status=payload.status,
        notes=payload.notes,
    )
    db.add(row)
    _create_learning_audit_event(
        db,
        event_id=f"LAE-CURRICULUM-{payload.curriculum_id}",
        event_type="CURRICULUM_REGISTERED",
        domain=payload.domain_id,
        curriculum_id=payload.curriculum_id,
        message=f"Curriculum {payload.curriculum_id} registered with objectives/playbooks/benchmarks/assessments",
        payload={
            "objectives": payload.learning_objectives,
            "playbooks": payload.playbooks,
            "benchmarks": payload.benchmarks,
            "assessments": payload.assessments,
        },
    )
    db.commit()
    db.refresh(row)

    return LearningCurriculumOut(
        curriculum_id=row.curriculum_id,
        domain_id=row.domain_id,
        title=row.title,
        version=row.version,
        terminal_state=row.terminal_state,
        jurisdiction=row.jurisdiction,
        business_scope=row.business_scope,
        learning_objectives=_loads(row.learning_objectives_json, []),
        playbooks=_loads(row.playbooks_json, []),
        benchmarks=_loads(row.benchmarks_json, []),
        assessments=_loads(row.assessments_json, []),
        promotion_gates=_promotion_gates(_loads(row.promotion_gates_json, {})),
        status=row.status,
    )


@router.get("/learning/curricula", response_model=list[LearningCurriculumOut])
def list_learning_curricula(
    db: Session = Depends(get_db),
    domain_id: str | None = None,
    jurisdiction: str | None = None,
):
    _ensure_registry_tables(db)
    q = db.query(LearningCurriculumRegistryItem)
    if domain_id:
        q = q.filter(LearningCurriculumRegistryItem.domain_id == domain_id)
    if jurisdiction:
        q = q.filter(
            (LearningCurriculumRegistryItem.jurisdiction == jurisdiction)
            | (LearningCurriculumRegistryItem.jurisdiction.is_(None))
        )
    rows = q.order_by(LearningCurriculumRegistryItem.id.desc()).limit(500).all()
    return [
        LearningCurriculumOut(
            curriculum_id=row.curriculum_id,
            domain_id=row.domain_id,
            title=row.title,
            version=row.version,
            terminal_state=row.terminal_state,
            jurisdiction=row.jurisdiction,
            business_scope=row.business_scope,
            learning_objectives=_loads(row.learning_objectives_json, []),
            playbooks=_loads(row.playbooks_json, []),
            benchmarks=_loads(row.benchmarks_json, []),
            assessments=_loads(row.assessments_json, []),
            promotion_gates=_promotion_gates(_loads(row.promotion_gates_json, {})),
            status=row.status,
        )
        for row in rows
    ]


@router.post("/learning/feedback", response_model=LearningFeedbackOut)
def record_learning_feedback(payload: LearningFeedbackIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)
    feedback_type = _normalize_feedback_type(payload.feedback_type)

    existing = db.query(LearningFeedbackRecord).filter(LearningFeedbackRecord.feedback_id == payload.feedback_id).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="feedback_id already exists")

    if payload.curriculum_id:
        curriculum = db.query(LearningCurriculumRegistryItem).filter(
            LearningCurriculumRegistryItem.curriculum_id == payload.curriculum_id
        ).first()
        if curriculum is None:
            raise HTTPException(status_code=404, detail="curriculum_id not found")

    row = LearningFeedbackRecord(
        feedback_id=payload.feedback_id,
        feedback_type=feedback_type,
        domain=payload.domain,
        curriculum_id=payload.curriculum_id,
        learning_id=payload.learning_id,
        jurisdiction=payload.jurisdiction,
        business_scope=payload.business_scope,
        benchmark_score=payload.benchmark_score,
        assessment_score=payload.assessment_score,
        operational_score=payload.operational_score,
        outcome_class=payload.outcome_class,
        high_impact=payload.high_impact,
        human_review_required=payload.human_review_required,
        notes=payload.notes,
    )
    db.add(row)
    _create_learning_audit_event(
        db,
        event_id=f"LAE-FEEDBACK-{payload.feedback_id}",
        event_type="LEARNING_FEEDBACK_CAPTURED",
        domain=payload.domain,
        curriculum_id=payload.curriculum_id,
        learning_id=payload.learning_id,
        severity="warning" if payload.human_review_required else "info",
        message=f"Learning feedback {payload.feedback_id} captured",
        payload={
            "feedback_type": feedback_type,
            "high_impact": payload.high_impact,
            "outcome_class": payload.outcome_class,
        },
    )
    db.commit()
    db.refresh(row)
    return LearningFeedbackOut.model_validate(row)


@router.get("/learning/feedback", response_model=list[LearningFeedbackOut])
def list_learning_feedback(
    db: Session = Depends(get_db),
    curriculum_id: str | None = None,
    domain: str | None = None,
    limit: int = 200,
):
    _ensure_registry_tables(db)
    q = db.query(LearningFeedbackRecord)
    if curriculum_id:
        q = q.filter(LearningFeedbackRecord.curriculum_id == curriculum_id)
    if domain:
        q = q.filter(LearningFeedbackRecord.domain == domain)
    rows = q.order_by(LearningFeedbackRecord.id.desc()).limit(max(1, min(limit, 1000))).all()
    return [LearningFeedbackOut.model_validate(row) for row in rows]


@router.post("/learning/mastery/evaluate", response_model=LearningMasteryOut)
def evaluate_learning_mastery(payload: LearningMasteryEvaluateIn, db: Session = Depends(get_db)):
    _ensure_registry_tables(db)

    curriculum = db.query(LearningCurriculumRegistryItem).filter(
        LearningCurriculumRegistryItem.curriculum_id == payload.curriculum_id
    ).first()
    if curriculum is None:
        raise HTTPException(status_code=404, detail="curriculum_id not found")
    if curriculum.domain_id != payload.domain:
        raise HTTPException(status_code=409, detail="domain does not match curriculum domain")

    gates = _promotion_gates(_loads(curriculum.promotion_gates_json, {}))

    open_reverify_q = db.query(LearningTaskQueueItem).filter(
        LearningTaskQueueItem.task_type == "REVERIFY_KNOWLEDGE",
        LearningTaskQueueItem.status.in_(["queued", "in_progress", "blocked"]),
        LearningTaskQueueItem.domain == payload.domain,
    )
    if payload.jurisdiction:
        open_reverify_q = open_reverify_q.filter(
            (LearningTaskQueueItem.jurisdiction == payload.jurisdiction)
            | (LearningTaskQueueItem.jurisdiction.is_(None))
        )
    open_reverify_tasks = open_reverify_q.count()

    mastery_score = round(
        (payload.assessment_score * 0.4)
        + (payload.benchmark_score * 0.3)
        + (payload.operational_score * 0.3),
        4,
    )

    reasons: list[str] = []
    human_review_required = False

    if payload.assessment_score < gates["assessment_min"]:
        reasons.append("assessment score below gate")
    if payload.benchmark_score < gates["benchmark_min"]:
        reasons.append("benchmark score below gate")
    if payload.operational_score < gates["operational_min"]:
        reasons.append("operational score below gate")
    if mastery_score < gates["mastery_min"]:
        reasons.append("mastery score below gate")
    if open_reverify_tasks > int(gates["max_open_reverify_tasks"]):
        reasons.append("open re-verification backlog exceeds gate")

    if payload.high_impact and (mastery_score < 0.9 or len(reasons) > 0):
        human_review_required = True
        reasons.append("high-impact promotion requires human review")

    if human_review_required:
        promotion_state = "HUMAN_REVIEW_REQUIRED"
    elif reasons:
        promotion_state = "HOLD"
    else:
        promotion_state = "PROMOTE_ACTIVE"

    feedback_id = f"FB-MASTERY-{payload.mastery_id}"
    existing_feedback = db.query(LearningFeedbackRecord).filter(LearningFeedbackRecord.feedback_id == feedback_id).first()
    if existing_feedback is None:
        db.add(
            LearningFeedbackRecord(
                feedback_id=feedback_id,
                feedback_type="mastery_evaluation",
                domain=payload.domain,
                curriculum_id=payload.curriculum_id,
                jurisdiction=payload.jurisdiction,
                business_scope=payload.business_scope,
                benchmark_score=payload.benchmark_score,
                assessment_score=payload.assessment_score,
                operational_score=payload.operational_score,
                outcome_class=promotion_state,
                high_impact=payload.high_impact,
                human_review_required=human_review_required,
                notes="; ".join(reasons) if reasons else "All promotion gates satisfied",
            )
        )

    _create_learning_audit_event(
        db,
        event_id=f"LAE-MASTERY-{payload.mastery_id}",
        event_type="MASTERY_EVALUATED",
        domain=payload.domain,
        curriculum_id=payload.curriculum_id,
        severity="warning" if human_review_required or reasons else "info",
        message=f"Mastery evaluated for curriculum {payload.curriculum_id}: {promotion_state}",
        payload={
            "mastery_score": mastery_score,
            "promotion_state": promotion_state,
            "open_reverify_tasks": open_reverify_tasks,
            "reasons": reasons,
        },
    )
    db.commit()

    return LearningMasteryOut(
        mastery_id=payload.mastery_id,
        curriculum_id=payload.curriculum_id,
        domain=payload.domain,
        mastery_score=mastery_score,
        promotion_state=promotion_state,
        human_review_required=human_review_required,
        open_reverify_tasks=open_reverify_tasks,
        reasons=reasons,
    )


@router.get("/learning/audit/events", response_model=list[LearningAuditOut])
def list_learning_audit_events(
    db: Session = Depends(get_db),
    domain: str | None = None,
    curriculum_id: str | None = None,
    limit: int = 200,
):
    _ensure_registry_tables(db)
    q = db.query(LearningAuditEvent)
    if domain:
        q = q.filter(LearningAuditEvent.domain == domain)
    if curriculum_id:
        q = q.filter(LearningAuditEvent.curriculum_id == curriculum_id)

    rows = q.order_by(LearningAuditEvent.id.desc()).limit(max(1, min(limit, 1000))).all()
    return [
        LearningAuditOut(
            event_id=row.event_id,
            event_type=row.event_type,
            domain=row.domain,
            curriculum_id=row.curriculum_id,
            learning_id=row.learning_id,
            severity=row.severity,
            message=row.message,
            payload=_loads(row.payload_json, {}),
        )
        for row in rows
    ]


@router.get("/summary")
def get_registry_summary(db: Session = Depends(get_db)):
    _ensure_registry_tables(db)

    def _state_counts(model):
        counts: dict[str, int] = {state: 0 for state in ALLOWED_TERMINAL_STATES}
        rows = db.query(model.terminal_state).all()
        for (state,) in rows:
            if state in counts:
                counts[state] += 1
        return counts

    def _engine_state_counts() -> dict[str, int]:
        counts: dict[str, int] = {state: 0 for state in sorted(ENGINE_ALLOWED_STATES)}
        rows = db.query(EngineRegistryItem.current_state).all()
        for (state,) in rows:
            if state in counts:
                counts[state] += 1
        return counts

    return {
        "knowledge": _state_counts(KnowledgeRegistryItem),
        "templates": _state_counts(TemplateRegistryItem),
        "scoring": _state_counts(ScoringRegistryItem),
        "sources": _state_counts(SourceRegistryItem),
        "datasets": _state_counts(DatasetRegistryItem),
        "scenarios": _state_counts(ScenarioRegistryItem),
        "learning_domains": _state_counts(LearningDomainRegistryItem),
        "learning_curricula": _state_counts(LearningCurriculumRegistryItem),
        "learning_feedback": {
            "total": db.query(LearningFeedbackRecord).count(),
            "human_review_required": db.query(LearningFeedbackRecord)
            .filter(LearningFeedbackRecord.human_review_required.is_(True))
            .count(),
        },
        "learning_audit_events": db.query(LearningAuditEvent).count(),
        "engine_registry": {
            "total": db.query(EngineRegistryItem).count(),
            "states": _engine_state_counts(),
            "planned_expected": len(PLANNED_ENGINE_CATALOG),
            "planned_represented": db.query(EngineRegistryItem)
            .filter(EngineRegistryItem.engine_id.in_(list(PLANNED_ENGINE_CATALOG.keys())))
            .count(),
        },
        "legacy_instances": {
            "total": db.query(LegacyInstanceRegistryItem).count(),
            "by_status": {
                "PASS": db.query(LegacyInstanceRegistryItem).filter(LegacyInstanceRegistryItem.status == "PASS").count(),
                "PARTIAL": db.query(LegacyInstanceRegistryItem).filter(LegacyInstanceRegistryItem.status == "PARTIAL").count(),
                "FAIL": db.query(LegacyInstanceRegistryItem).filter(LegacyInstanceRegistryItem.status == "FAIL").count(),
                "EXTERNAL_OWNER_ACTION_REQUIRED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.status == "EXTERNAL_OWNER_ACTION_REQUIRED")
                .count(),
            },
            "synchronization": {
                "SYNCED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.synchronization_status == "SYNCED")
                .count(),
                "DIVERGED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.synchronization_status == "DIVERGED")
                .count(),
                "BLOCKED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.synchronization_status == "BLOCKED")
                .count(),
                "PENDING": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.synchronization_status == "PENDING")
                .count(),
            },
            "failover": {
                "NOT_TRIGGERED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.failover_state == "NOT_TRIGGERED")
                .count(),
                "FAILED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.failover_state == "FAILED")
                .count(),
                "RECOVERED": db.query(LegacyInstanceRegistryItem)
                .filter(LegacyInstanceRegistryItem.failover_state == "RECOVERED")
                .count(),
            },
            "policy_sync": {
                "SYNCED": db.query(LegacyInstancePolicyState)
                .filter(LegacyInstancePolicyState.sync_status == "SYNCED")
                .count(),
                "DIVERGED": db.query(LegacyInstancePolicyState)
                .filter(LegacyInstancePolicyState.sync_status == "DIVERGED")
                .count(),
                "BLOCKED": db.query(LegacyInstancePolicyState)
                .filter(LegacyInstancePolicyState.sync_status == "BLOCKED")
                .count(),
            },
            "work_items": {
                "total": db.query(LegacyInstanceWorkItem).count(),
                "queued": db.query(LegacyInstanceWorkItem).filter(LegacyInstanceWorkItem.status == "queued").count(),
                "in_progress": db.query(LegacyInstanceWorkItem)
                .filter(LegacyInstanceWorkItem.status == "in_progress")
                .count(),
                "paused": db.query(LegacyInstanceWorkItem).filter(LegacyInstanceWorkItem.status == "paused").count(),
                "completed": db.query(LegacyInstanceWorkItem).filter(LegacyInstanceWorkItem.status == "completed").count(),
            },
            "orchestration_events": db.query(LegacyOrchestrationEvent).count(),
        },
        "learning_tasks": {
            "queued": db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.status == "queued").count(),
            "in_progress": db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.status == "in_progress").count(),
            "blocked": db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.status == "blocked").count(),
            "completed": db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.status == "completed").count(),
            "cancelled": db.query(LearningTaskQueueItem).filter(LearningTaskQueueItem.status == "cancelled").count(),
        },
    }
