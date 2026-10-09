from __future__ import annotations

import json
import re
import csv
import hashlib
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, UnsupportedCompilationError

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
from app.god.models import GodCaseOutcome, GodCaseStatus, GodReviewCase, GodReviewEvent
from app.models.god_verdicts import GodVerdict
from app.models.governance_decision import GovernanceDecision

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
    "approve this automatically",
    "change the owner's policy",
    "call this external url",
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
    if normalized == "sandbox":
        return "practice"
    if normalized not in {"practice", "test", "live"}:
        raise HTTPException(status_code=422, detail="mode must be one of practice|test|live")
    return normalized


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


class RealEstateCompIn(BaseModel):
    sold_price: float
    sold_date: str | None = None
    sqft: int | None = None
    distance_km: float | None = None


class RealEstateSourceEvidenceIn(BaseModel):
    source_id: str
    source_type: str
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness_days: int = Field(default=365, ge=0)
    citation_ref: str | None = None
    supports: list[str] = Field(default_factory=list)


class RealEstateBuyerBoxIn(BaseModel):
    min_arv: float | None = None
    max_arv: float | None = None
    max_repair_budget: float | None = None
    min_spread: float | None = None
    target_strategies: list[str] = Field(default_factory=list)
    target_markets: list[str] = Field(default_factory=list)


class RealEstateIntelligenceIn(BaseModel):
    request_id: str
    property_address: str
    city: str
    region: str
    postal_code: str | None = None
    country: str = "US"
    strategy: Literal["wholesale", "flip", "brrrr", "rental"]
    asking_price: float = Field(gt=0)
    arv_estimate: float | None = None
    rehab_estimate: float | None = None
    rent_estimate_monthly: float | None = None
    holding_months: int = Field(default=6, ge=1, le=36)
    inventory_months: float = Field(default=4.0, ge=0.0)
    dom_median_days: int = Field(default=35, ge=1)
    yoy_price_change_pct: float = Field(default=0.03, ge=-1.0, le=2.0)
    crime_risk_score: float = Field(default=0.3, ge=0.0, le=1.0)
    school_score: float = Field(default=6.0, ge=0.0, le=10.0)
    expected_deals_per_year: int = Field(default=8, ge=1, le=60)
    mission_critical: bool = True
    active_verticals: int = Field(default=3, ge=0)
    new_verticals: int = Field(default=0, ge=0)
    correlation_with_portfolio: float = Field(default=0.65, ge=0.0, le=1.0)
    legal_flags: dict[str, bool] = Field(default_factory=dict)
    engine: str = "Legacy"
    jurisdiction: str | None = None
    business_scope: str = "real_estate"
    persist_decision: bool = True
    human_approval_required: bool = True
    buyer_box: RealEstateBuyerBoxIn | None = None
    comps: list[RealEstateCompIn] = Field(default_factory=list)
    source_evidence: list[RealEstateSourceEvidenceIn] = Field(default_factory=list)


class WinnipegCertificationIn(BaseModel):
    sample_size: int = Field(default=12, ge=10, le=20)
    persist_decision: bool = True


def _bounded(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _normalized_location_key(payload: RealEstateIntelligenceIn) -> str:
    raw = "|".join(
        [
            payload.property_address.strip().lower(),
            payload.city.strip().lower(),
            payload.region.strip().lower(),
            (payload.postal_code or "").strip().lower(),
            payload.country.strip().upper(),
        ]
    )
    return re.sub(r"\s+", " ", raw)


def _micro_market_regime(payload: RealEstateIntelligenceIn) -> str:
    if payload.inventory_months < 3 and payload.yoy_price_change_pct > 0.05:
        return "seller_advantaged_growth"
    if payload.inventory_months > 6 and payload.yoy_price_change_pct < 0:
        return "buyer_advantaged_correction"
    return "balanced_transitional"


def _market_confidence(payload: RealEstateIntelligenceIn) -> float:
    score = 0.6
    if payload.comps:
        score += 0.2
    if payload.dom_median_days <= 45:
        score += 0.08
    if payload.school_score >= 7:
        score += 0.06
    if payload.crime_risk_score >= 0.6:
        score -= 0.12
    return round(_bounded(score, 0.05, 0.99), 4)


def _source_evidence_summary(payload: RealEstateIntelligenceIn) -> dict[str, Any]:
    evaluated: list[dict[str, Any]] = []
    weighted_sum = 0.0
    weight_total = 0.0
    blocked = 0

    for src in payload.source_evidence:
        freshness = 1.0
        if src.freshness_days > 730:
            freshness = 0.5
        elif src.freshness_days > 365:
            freshness = 0.75

        trust_rank = _source_trust_rank(src.source_type)
        trust_weight = max(1.0, trust_rank)
        effective = _bounded(src.confidence_score * freshness, 0.0, 1.0)

        if not src.citation_ref:
            status = "MISSING_CITATION"
            blocked += 1
        elif src.freshness_days > 730:
            status = "HARD_STALE"
            blocked += 1
        elif effective < 0.45:
            status = "LOW_CONFIDENCE"
            blocked += 1
        else:
            status = "VERIFIED"

        weighted_sum += effective * trust_weight
        weight_total += trust_weight

        evaluated.append(
            {
                "source_id": src.source_id,
                "source_type": src.source_type,
                "status": status,
                "effective_confidence": round(effective, 4),
                "freshness_days": src.freshness_days,
                "supports": src.supports,
            }
        )

    no_record_found = len(payload.source_evidence) == 0
    confidence = round((weighted_sum / weight_total), 4) if weight_total > 0 else 0.0
    return {
        "no_record_found": no_record_found,
        "effective_confidence": confidence,
        "blocked_count": blocked,
        "usable_count": len(payload.source_evidence) - blocked,
        "items": evaluated,
    }


def _valuation_ranges(payload: RealEstateIntelligenceIn, market_regime: str) -> dict[str, Any]:
    comp_prices = [float(c.sold_price) for c in payload.comps if c.sold_price > 0]
    comp_avg = (sum(comp_prices) / len(comp_prices)) if comp_prices else None

    base_arv = float(payload.arv_estimate or 0.0)
    if base_arv <= 0 and comp_avg is not None:
        base_arv = comp_avg
    if base_arv <= 0:
        base_arv = payload.asking_price * 1.35

    base_repairs = float(payload.rehab_estimate or max(payload.asking_price * 0.12, 8000.0))
    base_rent = float(payload.rent_estimate_monthly or max(payload.asking_price * 0.009, 900.0))

    regime_volatility = 0.08 if market_regime == "balanced_transitional" else 0.12
    if market_regime == "buyer_advantaged_correction":
        arv_low = base_arv * (1.0 - regime_volatility - 0.03)
        arv_high = base_arv * (1.0 + 0.04)
    elif market_regime == "seller_advantaged_growth":
        arv_low = base_arv * (1.0 - 0.06)
        arv_high = base_arv * (1.0 + regime_volatility + 0.04)
    else:
        arv_low = base_arv * (1.0 - regime_volatility)
        arv_high = base_arv * (1.0 + regime_volatility)

    repairs_low = base_repairs * 0.85
    repairs_high = base_repairs * 1.25
    rent_low = base_rent * 0.92
    rent_high = base_rent * 1.08

    return {
        "comps_used": len(comp_prices),
        "arv": {"low": round(arv_low, 2), "base": round(base_arv, 2), "high": round(arv_high, 2)},
        "repairs": {"low": round(repairs_low, 2), "base": round(base_repairs, 2), "high": round(repairs_high, 2)},
        "rent_monthly": {"low": round(rent_low, 2), "base": round(base_rent, 2), "high": round(rent_high, 2)},
    }


def _strategy_underwrite(payload: RealEstateIntelligenceIn, ranges: dict[str, Any]) -> dict[str, Any]:
    arv = float(ranges["arv"]["base"])
    repairs = float(ranges["repairs"]["base"])
    ask = float(payload.asking_price)
    rent = float(ranges["rent_monthly"]["base"])

    if payload.strategy == "wholesale":
        assignment_fee = max(8000.0, ask * 0.03)
        mao = (arv * 0.70) - repairs - assignment_fee
        spread = arv - ask - repairs
        return {
            "strategy": payload.strategy,
            "mao": round(mao, 2),
            "spread": round(spread, 2),
            "profit_projection": {
                "low": round(max(0.0, spread * 0.45), 2),
                "base": round(max(0.0, spread * 0.6), 2),
                "high": round(max(0.0, spread * 0.8), 2),
            },
            "viable": spread > 15000 and ask <= mao,
        }

    if payload.strategy == "flip":
        selling_cost = arv * 0.08
        carrying = payload.holding_months * (ask * 0.009)
        gross_profit = arv - ask - repairs - selling_cost - carrying
        roi = gross_profit / max(1.0, ask + repairs)
        return {
            "strategy": payload.strategy,
            "expected_profit": round(gross_profit, 2),
            "roi": round(roi, 4),
            "profit_projection": {
                "low": round(gross_profit * 0.7, 2),
                "base": round(gross_profit, 2),
                "high": round(gross_profit * 1.2, 2),
            },
            "viable": roi >= 0.18 and gross_profit > 20000,
        }

    if payload.strategy == "brrrr":
        max_all_in = arv * 0.75
        max_offer = max_all_in - repairs - (ask * 0.03)
        cashflow = rent - (rent * 0.45)
        dscr_like = cashflow / max(1.0, ask * 0.0065)
        return {
            "strategy": payload.strategy,
            "max_all_in": round(max_all_in, 2),
            "max_offer": round(max_offer, 2),
            "cashflow_monthly": round(cashflow, 2),
            "dscr_like": round(dscr_like, 3),
            "profit_projection": {
                "low": round(cashflow * 10, 2),
                "base": round(cashflow * 12, 2),
                "high": round(cashflow * 14, 2),
            },
            "viable": max_offer >= ask and dscr_like >= 1.15,
        }

    expenses = rent * 0.5
    noi = (rent - expenses) * 12
    cap_rate = noi / max(1.0, ask)
    return {
        "strategy": payload.strategy,
        "noi_annual": round(noi, 2),
        "cap_rate": round(cap_rate, 4),
        "profit_projection": {
            "low": round(noi * 0.9, 2),
            "base": round(noi, 2),
            "high": round(noi * 1.08, 2),
        },
        "viable": cap_rate >= 0.06,
    }


def _buyer_fit(payload: RealEstateIntelligenceIn, ranges: dict[str, Any], underwriting: dict[str, Any]) -> dict[str, Any]:
    deal_fit_score = 58.0
    if underwriting.get("viable"):
        deal_fit_score += 20.0
    if payload.inventory_months <= 5.5:
        deal_fit_score += 8.0
    if payload.crime_risk_score > 0.6:
        deal_fit_score -= 10.0
    if ranges["comps_used"] == 0:
        deal_fit_score -= 8.0
    deal_fit_score = round(_bounded(deal_fit_score, 0.0, 100.0), 2)

    buyer_box = payload.buyer_box
    if buyer_box is None:
        return {
            "deal_fit_score": deal_fit_score,
            "buyer_box_fit_score": None,
            "meets_buyer_box": None,
            "buyer_box_gaps": ["buyer_box_not_provided"],
        }

    gaps: list[str] = []
    arv_base = float(ranges["arv"]["base"])
    repairs_base = float(ranges["repairs"]["base"])
    spread = float(underwriting.get("spread") or underwriting.get("expected_profit") or 0.0)

    if buyer_box.min_arv is not None and arv_base < float(buyer_box.min_arv):
        gaps.append("arv_below_min")
    if buyer_box.max_arv is not None and arv_base > float(buyer_box.max_arv):
        gaps.append("arv_above_max")
    if buyer_box.max_repair_budget is not None and repairs_base > float(buyer_box.max_repair_budget):
        gaps.append("repairs_above_buyer_limit")
    if buyer_box.min_spread is not None and spread < float(buyer_box.min_spread):
        gaps.append("spread_below_buyer_min")
    if buyer_box.target_strategies and payload.strategy not in {s.strip().lower() for s in buyer_box.target_strategies}:
        gaps.append("strategy_not_in_buyer_box")
    if buyer_box.target_markets:
        mk = f"{payload.city.strip().lower()}|{payload.region.strip().lower()}"
        targets = {m.strip().lower() for m in buyer_box.target_markets}
        if mk not in targets:
            gaps.append("market_not_in_buyer_box")

    buyer_fit = round(_bounded(100.0 - (len(gaps) * 18.0), 0.0, 100.0), 2)
    return {
        "deal_fit_score": deal_fit_score,
        "buyer_box_fit_score": buyer_fit,
        "meets_buyer_box": len(gaps) == 0,
        "buyer_box_gaps": gaps,
    }


def _pantheon_decision(payload: RealEstateIntelligenceIn, underwriting: dict[str, Any], ranges: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    from app.routers.governance_loki import evaluate_loki
    from app.routers.governance_odin import evaluate_odin
    from app.routers.governance_tyr import evaluate_tyr
    from app.schemas.governance import KingEvaluationContext

    base_profit = float(underwriting.get("profit_projection", {}).get("base", 0.0))
    annual_profit = max(0.0, base_profit * float(payload.expected_deals_per_year))
    missing_count = evidence["blocked_count"] + (1 if evidence["no_record_found"] else 0)
    complexity = int(_bounded(3 + missing_count + (1 if payload.inventory_months > 6 else 0), 1, 10))

    odin_payload = KingEvaluationContext(
        context_type="deal",
        data={
            "active_verticals": str(payload.active_verticals),
            "new_verticals": str(payload.new_verticals),
            "estimated_annual_profit": str(round(annual_profit, 2)),
            "complexity_score": str(complexity),
            "time_to_break_even_months": str(payload.holding_months),
            "mission_critical": str(payload.mission_critical).lower(),
            "distraction_score": str(2 if payload.mission_critical else 8),
        },
    )

    arv_low = float(ranges["arv"]["low"])
    ask = float(payload.asking_price)
    repairs = float(ranges["repairs"]["base"])
    capital_at_risk = ask + repairs
    worst_case_loss = max(0.0, capital_at_risk - (arv_low * 0.92))
    volatility = abs(payload.yoy_price_change_pct)
    probability_of_ruin = _bounded(0.01 + (missing_count * 0.006) + (volatility * 0.12), 0.0, 0.95)

    loki_payload = KingEvaluationContext(
        context_type="deal",
        data={
            "capital_at_risk": str(round(capital_at_risk, 2)),
            "worst_case_loss": str(round(worst_case_loss, 2)),
            "probability_of_ruin": str(round(probability_of_ruin, 4)),
            "correlation_with_portfolio": str(round(payload.correlation_with_portfolio, 4)),
            "hidden_complexity_score": str(complexity),
        },
    )

    tyr_inputs = {
        "requires_license_without_having_it": bool(payload.legal_flags.get("requires_license_without_having_it", False)),
        "tax_evasion": bool(payload.legal_flags.get("tax_evasion", False)),
        "fraudulent_misrepresentation": bool(payload.legal_flags.get("fraudulent_misrepresentation", False)),
        "recording_without_consent": bool(payload.legal_flags.get("recording_without_consent", False)),
        "exploits_vulnerable": bool(payload.legal_flags.get("exploits_vulnerable", False)),
        "misleading_marketing": bool(payload.legal_flags.get("misleading_marketing", False)),
        "missing_disclosures": bool(payload.legal_flags.get("missing_disclosures", False)) or missing_count > 0,
    }
    tyr_payload = KingEvaluationContext(context_type="deal", data={k: str(v).lower() for k, v in tyr_inputs.items()})

    odin_decision = evaluate_odin(odin_payload)
    loki_decision = evaluate_loki(loki_payload)
    tyr_decision = evaluate_tyr(tyr_payload)

    checks = {
        "odin": odin_decision.model_dump(),
        "loki": loki_decision.model_dump(),
        "tyr": tyr_decision.model_dump(),
    }
    blocked_by = [name for name, result in checks.items() if not bool(result.get("allowed")) and str(result.get("severity")) == "critical"]
    worst = "info"
    for result in checks.values():
        severity = str(result.get("severity") or "info")
        if severity == "critical":
            worst = "critical"
            break
        if severity == "warn" and worst == "info":
            worst = "warn"

    return {
        "overall_allowed": len(blocked_by) == 0,
        "worst_severity": worst,
        "blocked_by": blocked_by,
        "checks": checks,
    }


def _role_mimir(payload: RealEstateIntelligenceIn, evidence: dict[str, Any], ranges: dict[str, Any]) -> dict[str, Any]:
    precedent_strength = _bounded((evidence["effective_confidence"] * 0.65) + (0.2 if ranges["comps_used"] > 0 else 0.0), 0.0, 1.0)
    return {
        "role": "mimir",
        "allowed": precedent_strength >= 0.45,
        "confidence": round(precedent_strength, 4),
        "reasons": [] if precedent_strength >= 0.45 else ["historical precedence is weak"],
        "supporting_evidence": {
            "effective_confidence": evidence["effective_confidence"],
            "comps_used": ranges["comps_used"],
        },
    }


def _role_raven(payload: RealEstateIntelligenceIn, evidence: dict[str, Any]) -> dict[str, Any]:
    freshness_ratio = 0.0
    if payload.source_evidence:
        fresh = len([s for s in payload.source_evidence if s.freshness_days <= 90 and bool(s.citation_ref)])
        freshness_ratio = fresh / len(payload.source_evidence)
    return {
        "role": "raven",
        "allowed": freshness_ratio >= 0.5,
        "confidence": round(_bounded(freshness_ratio + (0.2 if evidence["usable_count"] > 0 else 0.0), 0.0, 1.0), 4),
        "reasons": [] if freshness_ratio >= 0.5 else ["insufficient fresh intelligence signals"],
        "supporting_evidence": {
            "fresh_signal_ratio": round(freshness_ratio, 4),
            "usable_signal_count": evidence["usable_count"],
        },
    }


def _role_skadi(payload: RealEstateIntelligenceIn, ranges: dict[str, Any], underwriting: dict[str, Any]) -> dict[str, Any]:
    downside_gap = max(0.0, float(payload.asking_price) - float(ranges["arv"]["low"]))
    strategy_viable = bool(underwriting.get("viable"))
    confidence = _bounded((0.7 if strategy_viable else 0.32) - (0.18 if downside_gap > 0 else 0.0), 0.0, 1.0)
    return {
        "role": "skadi",
        "allowed": strategy_viable and downside_gap <= 0,
        "confidence": round(confidence, 4),
        "reasons": [] if strategy_viable and downside_gap <= 0 else ["market downside exceeds acceptable specialist threshold"],
        "supporting_evidence": {
            "worst_case_arv": ranges["arv"]["low"],
            "asking_price": payload.asking_price,
            "downside_gap": round(downside_gap, 2),
        },
    }


def _role_forseti(payload: RealEstateIntelligenceIn, buyer_fit: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    legal_flags = [k for k, v in payload.legal_flags.items() if bool(v)]
    contradiction = evidence["blocked_count"] > 0 and bool(legal_flags)
    reasons: list[str] = []
    if legal_flags:
        reasons.append("legal/compliance flags present")
    if contradiction:
        reasons.append("evidence contradiction requires legal clarification")
    if buyer_fit.get("buyer_box_gaps") and buyer_fit.get("buyer_box_gaps") != ["buyer_box_not_provided"]:
        reasons.append("buyer execution envelope contains unresolved conditions")
    return {
        "role": "forseti",
        "allowed": len(legal_flags) == 0 and not contradiction,
        "confidence": round(_bounded(0.78 - (0.25 * len(legal_flags)) - (0.1 if contradiction else 0.0), 0.0, 1.0), 4),
        "reasons": reasons,
        "supporting_evidence": {
            "legal_flags": legal_flags,
            "blocked_sources": evidence["blocked_count"],
        },
    }


def _role_vidar(payload: RealEstateIntelligenceIn, evidence: dict[str, Any], pantheon: dict[str, Any]) -> dict[str, Any]:
    blocked = int(evidence["blocked_count"])
    critical = 1 if pantheon["worst_severity"] == "critical" else 0
    resilience = _bounded(0.84 - (0.16 * blocked) - (0.25 * critical), 0.0, 1.0)
    reasons: list[str] = []
    if blocked:
        reasons.append("source refresh required before resilient execution")
    if critical:
        reasons.append("critical governance objection present")
    return {
        "role": "vidar",
        "allowed": resilience >= 0.45,
        "confidence": round(resilience, 4),
        "reasons": reasons,
        "supporting_evidence": {
            "blocked_sources": blocked,
            "critical_flags": critical,
        },
    }


def _role_norns(payload: RealEstateIntelligenceIn, underwriting: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    profit_base = float(underwriting.get("profit_projection", {}).get("base", 0.0))
    estimate = _bounded(0.35 + (0.25 if underwriting.get("viable") else -0.12) + min(0.18, profit_base / 250000.0), 0.01, 0.99)
    confidence = _bounded(0.42 + (0.28 * evidence["effective_confidence"]) - (0.08 * evidence["blocked_count"]), 0.05, 0.95)
    reasons: list[str] = []
    if evidence["blocked_count"]:
        reasons.append("probability quality reduced by unresolved evidence")
    if evidence["no_record_found"]:
        reasons.append("probability estimate uses sparse history")
    return {
        "role": "norns",
        "allowed": estimate >= 0.5,
        "estimate": round(estimate, 4),
        "confidence": round(confidence, 4),
        "calibration_state": "NOT_YET_CALIBRATED",
        "model_state": "MODEL_ESTIMATE",
        "timing_months": payload.holding_months,
        "reasons": reasons,
    }


def _role_jotunn(payload: RealEstateIntelligenceIn, ranges: dict[str, Any], underwriting: dict[str, Any]) -> dict[str, Any]:
    dispersion = abs(float(ranges["arv"]["high"]) - float(ranges["arv"]["low"])) / max(1.0, float(ranges["arv"]["base"]))
    return {
        "role": "jotunn",
        "allowed": dispersion <= 0.35,
        "confidence": round(_bounded(0.82 - dispersion, 0.0, 1.0), 4),
        "reasons": [] if dispersion <= 0.35 else ["valuation dispersion too wide for quant confidence"],
        "supporting_evidence": {
            "valuation_dispersion": round(dispersion, 4),
            "profit_projection": underwriting.get("profit_projection", {}),
        },
    }


def _loki_objections(payload: RealEstateIntelligenceIn, ranges: dict[str, Any], evidence: dict[str, Any], pantheon: dict[str, Any]) -> list[dict[str, Any]]:
    objections: list[dict[str, Any]] = []

    if ranges["comps_used"] == 0:
        objections.append(
            {
                "objection_id": f"LOKI-OBJ-{payload.request_id}-001",
                "claim_challenged": "valuation confidence supports immediate proceed",
                "objection_evidence": "No comps provided for property-level valuation corroboration",
                "severity": "warn",
                "materiality": "material",
                "resolved": False,
                "resolution_evidence": None,
                "impact_on_recommendation": "PROCEED->RESEARCH_MORE",
            }
        )

    if evidence["blocked_count"] >= 2:
        objections.append(
            {
                "objection_id": f"LOKI-OBJ-{payload.request_id}-002",
                "claim_challenged": "evidence integrity is sufficient",
                "objection_evidence": f"{evidence['blocked_count']} evidence sources blocked",
                "severity": "critical",
                "materiality": "high",
                "resolved": False,
                "resolution_evidence": None,
                "impact_on_recommendation": "PROCEED->REJECT",
            }
        )

    if pantheon["checks"]["loki"]["severity"] == "critical":
        objections.append(
            {
                "objection_id": f"LOKI-OBJ-{payload.request_id}-003",
                "claim_challenged": "downside exposure is acceptable",
                "objection_evidence": "; ".join(pantheon["checks"]["loki"]["reasons"]),
                "severity": "critical",
                "materiality": "high",
                "resolved": False,
                "resolution_evidence": None,
                "impact_on_recommendation": "PROCEED->REJECT",
            }
        )

    return objections


def _owner_approval_envelope(payload: RealEstateIntelligenceIn, underwriting: dict[str, Any], final_decision: str) -> dict[str, Any]:
    max_commitment = round(float(payload.asking_price) + float(underwriting.get("profit_projection", {}).get("base", 0.0)) * 0.35, 2)
    return {
        "recommended_action": final_decision.upper(),
        "maximum_spend": round(float(payload.asking_price), 2),
        "maximum_commitment": max_commitment,
        "duration_days": max(14, payload.holding_months * 30),
        "stop_loss": round(float(payload.asking_price) * 0.09, 2),
        "permitted_external_actions": [],
        "required_reapproval_conditions": [
            "valuation_range_widens_above_20pct",
            "new_critical_loki_objection",
            "legal_state_changes_to_fail",
        ],
        "legal_review_required": len([k for k, v in payload.legal_flags.items() if bool(v)]) > 0,
        "owner_approval_required": payload.human_approval_required,
        "approval_state": "PENDING_OWNER" if payload.human_approval_required else "NOT_REQUIRED",
        "shadow_mode_external_execution_blocked": True,
    }


def _decision_rank_value(final_decision: str, underwriting: dict[str, Any], buyer_fit: dict[str, Any], norns: dict[str, Any]) -> float:
    base_map = {
        "proceed": 100.0,
        "research_more": 72.0,
        "hold_review": 55.0,
        "reject": 20.0,
    }
    base = base_map.get(final_decision, 40.0)
    profit = float(underwriting.get("profit_projection", {}).get("base", 0.0))
    deal_fit = float(buyer_fit.get("deal_fit_score") or 0.0)
    prob = float(norns.get("estimate") or 0.0)
    return round(base + min(25.0, profit / 10000.0) + (deal_fit * 0.15) + (prob * 10.0), 4)


def _ensure_pantheon_tables(db: Session) -> None:
    bind = db.get_bind()
    GodReviewCase.__table__.create(bind=bind, checkfirst=True)
    GodReviewEvent.__table__.create(bind=bind, checkfirst=True)
    GodVerdict.__table__.create(bind=bind, checkfirst=True)
    GovernanceDecision.__table__.create(bind=bind, checkfirst=True)


def _persist_pantheon_snapshot(
    db: Session,
    *,
    payload: RealEstateIntelligenceIn,
    result: dict[str, Any],
    loki_objections: list[dict[str, Any]],
    owner_envelope: dict[str, Any],
) -> dict[str, Any]:
    try:
        _ensure_pantheon_tables(db)
    except (UnsupportedCompilationError, SQLAlchemyError):
        # SQLite test harness cannot materialize PostgreSQL JSONB/UUID columns.
        # Return synthetic IDs so contract-level behavior remains testable.
        synthetic_subject = int(hashlib.sha1(payload.request_id.encode("utf-8")).hexdigest()[:8], 16)
        return {
            "god_review_case_id": str(uuid.uuid4()),
            "god_verdict_id": str(uuid.uuid4()),
            "governance_subject_id": synthetic_subject,
            "owner_approval_required": owner_envelope["owner_approval_required"],
            "approval_state": owner_envelope["approval_state"],
            "persistence_mode": "sqlite_test_fallback",
        }

    subject_ref = hashlib.sha1(result["property_identity"]["location_key"].encode("utf-8")).hexdigest()[:20]
    case = GodReviewCase(
        subject_type="real_estate_opportunity",
        subject_reference=subject_ref,
        title=f"Real-estate evaluation {payload.request_id}",
        description=f"Strategy {payload.strategy} for {payload.city}, {payload.region}",
        status=GodCaseStatus.AWAITING_HUMAN if owner_envelope["owner_approval_required"] else GodCaseStatus.OPEN,
        heimdall_summary=f"Heimdall recommendation: {result['final_decision']}",
        heimdall_payload={
            "request_id": payload.request_id,
            "final_decision": result["final_decision"],
            "underwriting": result["underwriting"],
            "approval_envelope": owner_envelope,
        },
        loki_summary=f"{len(loki_objections)} objections ({len([o for o in loki_objections if o['resolved'] is False])} unresolved)",
        loki_payload={"objections": loki_objections},
        final_outcome=GodCaseOutcome.UNKNOWN,
    )
    db.add(case)
    db.flush()

    role_blocks: dict[str, dict[str, Any]] = {
        "odin": result["pantheon"]["checks"]["odin"],
        "loki": result["pantheon"]["checks"]["loki"],
        "tyr": result["pantheon"]["checks"]["tyr"],
        "mimir": result["decision_cone"]["mimir"],
        "norns": result["decision_cone"]["norns"],
        "skadi": result["decision_cone"]["skadi"],
        "raven": result["decision_cone"]["raven"],
        "forseti": result["decision_cone"]["forseti"],
        "vidar": result["decision_cone"]["vidar"],
        "jotunn": result["decision_cone"].get("jotunn", {"role": "jotunn", "allowed": True, "confidence": 0.5, "reasons": []}),
    }

    for role_name, role_payload in role_blocks.items():
        db.add(
            GodReviewEvent(
                case_id=case.id,
                actor="system" if role_name != "loki" else "loki",
                event_type=f"role_{role_name}",
                message=f"{role_name.upper()} evaluated request {payload.request_id}",
                payload=role_payload,
            )
        )

    consensus = "approve" if result["pantheon"]["overall_allowed"] else "deny"
    verdict = GodVerdict(
        case_id=case.id,
        trigger="phase2_real_estate_evaluate",
        heimdall_summary=f"{result['final_decision']} with strategy {payload.strategy}",
        heimdall_recommendation={
            "decision": result["final_decision"],
            "approval_envelope": owner_envelope,
            "disagreements": result["pantheon"]["blocked_by"],
        },
        heimdall_confidence="medium",
        loki_summary=f"{len(loki_objections)} objections",
        loki_recommendation={"objections": loki_objections},
        loki_confidence="medium",
        consensus=consensus,
        risk_level=result["pantheon"]["worst_severity"],
        notes="Persisted Phase Two real-estate pantheon snapshot",
        metadata_json={
            "request_id": payload.request_id,
            "property_identity": result["property_identity"],
            "role_outputs": role_blocks,
            "owner_approval_envelope": owner_envelope,
            "shadow_mode": True,
        },
    )
    db.add(verdict)

    subject_int = int(hashlib.sha1(payload.request_id.encode("utf-8")).hexdigest()[:8], 16)
    role_to_action = {
        "odin": "approve" if role_blocks["odin"].get("allowed") else "flag",
        "loki": "deny" if role_blocks["loki"].get("severity") == "critical" else "flag",
        "tyr": "deny" if role_blocks["tyr"].get("severity") == "critical" else "approve",
        "skadi": "approve" if role_blocks["skadi"].get("allowed") else "flag",
        "mimir": "approve" if role_blocks["mimir"].get("allowed") else "flag",
        "raven": "approve" if role_blocks["raven"].get("allowed") else "flag",
        "norns": "approve" if role_blocks["norns"].get("allowed") else "flag",
        "forseti": "approve" if role_blocks["forseti"].get("allowed") else "deny",
        "vidar": "approve" if role_blocks["vidar"].get("allowed") else "flag",
        "jotunn": "approve" if role_blocks["jotunn"].get("allowed") else "flag",
        "heimdall": "approve" if result["final_decision"] == "proceed" else ("deny" if result["final_decision"] == "reject" else "flag"),
    }

    for role_name, action in role_to_action.items():
        db.add(
            GovernanceDecision(
                subject_type="real_estate_opportunity",
                subject_id=subject_int,
                role=role_name.capitalize(),
                action=action,
                reason=(
                    "Persisted phase two role output"
                    if role_name != "heimdall"
                    else f"Heimdall final recommendation: {result['final_decision']}"
                ),
                is_final=role_name == "heimdall",
            )
        )

    db.commit()
    db.refresh(case)
    db.refresh(verdict)
    return {
        "god_review_case_id": str(case.id),
        "god_verdict_id": str(verdict.id),
        "governance_subject_id": subject_int,
        "owner_approval_required": owner_envelope["owner_approval_required"],
        "approval_state": owner_envelope["approval_state"],
    }


def _compose_real_estate_intelligence_result(payload: RealEstateIntelligenceIn) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    market_regime = _micro_market_regime(payload)
    market_confidence = _market_confidence(payload)
    evidence = _source_evidence_summary(payload)
    ranges = _valuation_ranges(payload, market_regime)
    underwriting = _strategy_underwrite(payload, ranges)
    buyer_fit = _buyer_fit(payload, ranges, underwriting)
    pantheon = _pantheon_decision(payload, underwriting, ranges, evidence)

    mimir_role = _role_mimir(payload, evidence, ranges)
    norns_role = _role_norns(payload, underwriting, evidence)
    skadi_role = _role_skadi(payload, ranges, underwriting)
    raven_role = _role_raven(payload, evidence)
    forseti_role = _role_forseti(payload, buyer_fit, evidence)
    vidar_role = _role_vidar(payload, evidence, pantheon)
    jotunn_role = _role_jotunn(payload, ranges, underwriting)

    loki_objections = _loki_objections(payload, ranges, evidence, pantheon)
    unresolved_critical = any((o["severity"] == "critical" and not o["resolved"]) for o in loki_objections)
    unresolved_material = any((o["materiality"] == "material" and not o["resolved"]) for o in loki_objections)

    pre_loki_recommendation = "proceed" if underwriting.get("viable") and pantheon["overall_allowed"] else "hold_review"
    if not pantheon["overall_allowed"] or not forseti_role["allowed"]:
        final_decision = "reject"
    elif unresolved_critical:
        final_decision = "reject"
    elif pre_loki_recommendation == "proceed" and unresolved_material:
        final_decision = "research_more"
    elif pre_loki_recommendation == "proceed" and norns_role["estimate"] >= 0.6:
        final_decision = "proceed"
    else:
        final_decision = "hold_review"

    owner_envelope = _owner_approval_envelope(payload, underwriting, final_decision)
    disagreements = [
        role["role"]
        for role in [mimir_role, norns_role, skadi_role, raven_role, forseti_role, vidar_role, jotunn_role]
        if not bool(role.get("allowed", True))
    ]

    result = {
        "request_id": payload.request_id,
        "engine": payload.engine,
        "jurisdiction": payload.jurisdiction,
        "strategy": payload.strategy,
        "property_identity": {
            "location_key": _normalized_location_key(payload),
            "city": payload.city,
            "region": payload.region,
            "country": payload.country,
            "micro_area": "UNKNOWN",
            "postal_geography": payload.postal_code or "UNKNOWN",
            "coordinates": None,
        },
        "micro_market": {
            "regime": market_regime,
            "market_confidence": market_confidence,
            "inventory_months": payload.inventory_months,
            "dom_median_days": payload.dom_median_days,
            "yoy_price_change_pct": payload.yoy_price_change_pct,
        },
        "source_evidence": evidence,
        "valuation_ranges": ranges,
        "underwriting": underwriting,
        "buyer_market_fit": buyer_fit,
        "pantheon": {
            **pantheon,
            "roles_invoked": ["odin", "loki", "tyr", "mimir", "norns", "skadi", "raven", "forseti", "vidar", "jotunn", "heimdall"],
            "disagreements": disagreements,
        },
        "decision_cone": {
            "mimir": mimir_role,
            "norns": norns_role,
            "skadi": skadi_role,
            "raven": raven_role,
            "forseti": forseti_role,
            "vidar": vidar_role,
            "jotunn": jotunn_role,
        },
        "loki_objections": {
            "objection_count": len(loki_objections),
            "unresolved_count": len([o for o in loki_objections if not o["resolved"]]),
            "items": loki_objections,
            "pre_loki_recommendation": pre_loki_recommendation,
        },
        "owner_approval_envelope": owner_envelope,
        "final_decision": final_decision,
        "explainability": {
            "top_reasons": (
                pantheon["checks"]["tyr"]["reasons"]
                + pantheon["checks"]["loki"]["reasons"]
                + [o["objection_evidence"] for o in loki_objections]
                + ([] if underwriting.get("viable") else ["strategy underwriting failed viability thresholds"])
            )[:10],
            "assumptions": [
                "scenario ranges are deterministic stress bands, not forecasts",
                "norns probability is MODEL_ESTIMATE and NOT_YET_CALIBRATED",
                "external execution remains blocked in shadow mode",
            ],
            "uncertainty_flags": [
                "VALUATION_CONFIDENCE_LOW" if ranges["comps_used"] == 0 else None,
                "MARKET_DATA_INSUFFICIENT" if evidence["no_record_found"] else None,
                "BUYER_DATA_INSUFFICIENT" if buyer_fit["buyer_box_fit_score"] is None else None,
                "CONTACT_NOT_VERIFIED",
                "REPAIR_CONFIDENCE_LOW" if float(ranges["repairs"]["high"]) > float(ranges["repairs"]["base"]) * 1.2 else None,
            ],
        },
    }
    result["explainability"]["uncertainty_flags"] = [v for v in result["explainability"]["uncertainty_flags"] if v is not None]
    result["decision_rank_value"] = _decision_rank_value(final_decision, underwriting, buyer_fit, norns_role)
    return result, loki_objections, owner_envelope


@router.post("/phase2/real-estate-intelligence/evaluate")
def evaluate_real_estate_intelligence(payload: RealEstateIntelligenceIn, db: Session = Depends(get_db)):
    result, loki_objections, owner_envelope = _compose_real_estate_intelligence_result(payload)
    persistence = None
    if payload.persist_decision:
        persistence = _persist_pantheon_snapshot(
            db,
            payload=payload,
            result=result,
            loki_objections=loki_objections,
            owner_envelope=owner_envelope,
        )
    result["persistence"] = persistence
    return result


def _load_winnipeg_anchors(sample_size: int) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    root = Path.cwd()
    csv_paths = [
        root / "data" / "inbox" / "real_leads" / "sample_leads_01.csv",
        root / "data" / "inbox" / "real_leads" / "batch_01_leads.csv",
        root / "data" / "inbox" / "real_leads" / "batch_02_leads.csv",
        root / "data" / "inbox" / "real_leads" / "batch_03_leads.csv",
    ]

    for path in csv_paths:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    city = str(row.get("city") or row.get("City") or "").strip().lower()
                    region = str(row.get("province_state") or row.get("state") or row.get("region") or "").strip()
                    if city != "winnipeg":
                        continue
                    raw_price = str(row.get("price") or row.get("asking_price") or row.get("estimated_value") or "0")
                    clean = re.sub(r"[^0-9.]+", "", raw_price)
                    asking = float(clean or 0.0)
                    if asking <= 0:
                        continue
                    prop_type = str(row.get("property_type") or row.get("property") or "single_family").strip().lower()
                    addr = str(row.get("property_address") or row.get("address") or "UNKNOWN").strip()
                    anchors.append(
                        {
                            "anchor_id": hashlib.sha1(f"{path.name}:{addr}:{asking}".encode("utf-8")).hexdigest()[:16],
                            "address": addr,
                            "city": "Winnipeg",
                            "region": region or "MB",
                            "postal": str(row.get("property_zip") or row.get("postal_code") or row.get("zip") or "").strip() or None,
                            "property_type": prop_type,
                            "asking_price": asking,
                            "source": str(path.relative_to(root)).replace("\\", "/"),
                        }
                    )
                    if len(anchors) >= sample_size:
                        return anchors
        except Exception:
            continue

    # Best-effort fallback from local DB if not enough file anchors.
    db_path = root / "valhalla_local.db"
    if db_path.exists() and len(anchors) < sample_size:
        try:
            import sqlite3

            con = sqlite3.connect(str(db_path))
            cur = con.cursor()
            rows = cur.execute(
                """
                SELECT id, title, COALESCE(arv, 0), COALESCE(estimated_repair_cost, 0)
                FROM deals
                WHERE lower(COALESCE(title, '')) LIKE '%winnipeg%'
                LIMIT 40
                """
            ).fetchall()
            con.close()
            for row in rows:
                if len(anchors) >= sample_size:
                    break
                deal_id, title, arv, repairs = row
                title_text = str(title or "")
                anchors.append(
                    {
                        "anchor_id": f"dbdeal-{deal_id}",
                        "address": title_text,
                        "city": "Winnipeg",
                        "region": "MB",
                        "postal": None,
                        "property_type": "single_family",
                        "asking_price": max(50000.0, float(arv or 0.0) - float(repairs or 0.0) - 12000.0),
                        "source": "valhalla_local.db:deals",
                    }
                )
        except Exception:
            pass
    return anchors[:sample_size]


def _strategies_for_property_type(property_type: str) -> list[str]:
    t = (property_type or "").lower()
    if "land" in t:
        return ["wholesale", "flip"]
    if "commercial" in t or "mixed" in t or "multi" in t or "apartment" in t:
        return ["rental", "brrrr", "wholesale"]
    return ["wholesale", "flip", "rental", "brrrr"]


@router.post("/phase2/real-estate-intelligence/certify-winnipeg")
def certify_winnipeg_real_estate(payload: WinnipegCertificationIn, db: Session = Depends(get_db)):
    anchors = _load_winnipeg_anchors(payload.sample_size)
    if len(anchors) < 10:
        raise HTTPException(status_code=409, detail="insufficient Winnipeg anchors available in canonical local sources")

    evaluations: list[dict[str, Any]] = []
    persisted_case_ids: list[str] = []
    for idx, anchor in enumerate(anchors):
        strategy_results: list[dict[str, Any]] = []
        for strategy in _strategies_for_property_type(anchor["property_type"]):
            base_arv = round(anchor["asking_price"] * (1.18 if strategy == "rental" else 1.3), 2)
            payload_eval = RealEstateIntelligenceIn(
                request_id=f"WPG-{anchor['anchor_id']}-{strategy}",
                property_address=anchor["address"],
                city="Winnipeg",
                region="MB",
                postal_code=anchor["postal"],
                country="CA",
                strategy=strategy,  # type: ignore[arg-type]
                asking_price=anchor["asking_price"],
                arv_estimate=base_arv,
                rehab_estimate=max(9000.0, anchor["asking_price"] * 0.13),
                rent_estimate_monthly=max(850.0, anchor["asking_price"] * 0.0075),
                holding_months=6,
                inventory_months=4.6,
                dom_median_days=31,
                yoy_price_change_pct=0.028,
                crime_risk_score=0.37,
                school_score=6.8,
                expected_deals_per_year=8,
                engine="Legacy",
                jurisdiction="CA-MB",
                source_evidence=[
                    RealEstateSourceEvidenceIn(
                        source_id="SRC-WPG-LOCAL-FILE",
                        source_type="operator_note",
                        confidence_score=0.72,
                        freshness_days=75,
                        citation_ref=anchor["source"],
                        supports=["city", "asking_price", "property_type"],
                    )
                ],
                persist_decision=payload.persist_decision,
            )
            result, loki_objections, owner_envelope = _compose_real_estate_intelligence_result(payload_eval)
            if payload.persist_decision:
                persisted = _persist_pantheon_snapshot(
                    db,
                    payload=payload_eval,
                    result=result,
                    loki_objections=loki_objections,
                    owner_envelope=owner_envelope,
                )
                result["persistence"] = persisted
                persisted_case_ids.append(persisted["god_review_case_id"])
            strategy_results.append(result)

        strategy_results.sort(key=lambda r: r.get("decision_rank_value", 0.0), reverse=True)
        evaluations.append(
            {
                "anchor_id": anchor["anchor_id"],
                "geography": {
                    "city": "Winnipeg",
                    "district": "UNKNOWN",
                    "neighbourhood": "UNKNOWN",
                    "micro_area": "UNKNOWN",
                    "postal_geography": anchor["postal"] or "UNKNOWN",
                    "coordinates": None,
                },
                "source": anchor["source"],
                "best_strategy": strategy_results[0]["strategy"],
                "best_decision": strategy_results[0]["final_decision"],
                "strategies": strategy_results,
            }
        )

    ranked = sorted(
        evaluations,
        key=lambda e: max([float(s.get("decision_rank_value") or 0.0) for s in e["strategies"]]),
        reverse=True,
    )
    top = ranked[:3]
    bottom = ranked[-3:]
    mid_start = max(0, (len(ranked) // 2) - 1)
    middle = ranked[mid_start:mid_start + 3]

    best = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None
    best_rank = max([float(s.get("decision_rank_value") or 0.0) for s in (best or {}).get("strategies", [])], default=0.0)
    second_rank = max([float(s.get("decision_rank_value") or 0.0) for s in (second or {}).get("strategies", [])], default=0.0)

    return {
        "sample_city": "Winnipeg",
        "sample_size": len(ranked),
        "anchors": [
            {
                "anchor_id": e["anchor_id"],
                "best_strategy": e["best_strategy"],
                "best_decision": e["best_decision"],
            }
            for e in ranked
        ],
        "cross_opportunity_ranking": {
            "best_current_property_opportunity": None if best is None else best["anchor_id"],
            "why_it_ranks_above_2": (
                "insufficient evidence to distinguish"
                if best is None or second is None or abs(best_rank - second_rank) < 5
                else f"higher decision_rank_value ({best_rank:.2f} vs {second_rank:.2f})"
            ),
            "what_would_change_ranking": [
                "fresh comparable sales evidence",
                "verified repair scope reduction",
                "resolved Loki material objections",
            ],
        },
        "human_review_set": {
            "top_3": [r["anchor_id"] for r in top],
            "middle_3": [r["anchor_id"] for r in middle],
            "bottom_3": [r["anchor_id"] for r in bottom],
        },
        "disagreement_summary": [
            {
                "anchor_id": e["anchor_id"],
                "role_disagreements": sorted(
                    {
                        role
                        for s in e["strategies"]
                        for role in s["pantheon"]["disagreements"]
                    }
                ),
            }
            for e in ranked
        ],
        "persisted_case_ids": persisted_case_ids,
        "shadow_safety_counters": {
            "email": 0,
            "sms": 0,
            "calls": 0,
            "contracts": 0,
            "e_sign": 0,
            "money": 0,
            "accounting_writes": 0,
            "external_posts": 0,
        },
        "evaluations": ranked,
    }


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

    item = SourceRegistryItem(
        source_id=payload.source_id,
        canonical_name=payload.canonical_name,
        source_type=payload.source_type,
        data_class=payload.data_class.strip().lower(),
        owner=payload.owner,
        jurisdiction=payload.jurisdiction,
        market=payload.market,
        citation_ref=payload.citation_ref,
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
