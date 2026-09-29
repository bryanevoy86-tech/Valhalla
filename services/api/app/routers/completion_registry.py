from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.completion_registry import (
    DatasetRegistryItem,
    KnowledgeRegistryItem,
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


class KnowledgeRetrieveOut(BaseModel):
    question: str
    facts: list[dict[str, Any]]
    assumptions: list[dict[str, Any]]
    blocked_sources: list[dict[str, Any]]


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


def _is_stale(review_date: date | None, stale_after_days: int = 30) -> bool:
    if review_date is None:
        return True
    return review_date < (datetime.now(timezone.utc).date() - timedelta(days=stale_after_days))


def _source_trust_rank(source_type: str | None) -> int:
    key = str(source_type or "").strip().lower()
    return SOURCE_TRUST_RANKS.get(key, 0)


def _title_key(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


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
    provisional_facts: list[dict[str, Any]] = []
    grouped_titles: dict[str, list[dict[str, Any]]] = {}

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

        entry = {
            "item_id": row.item_id,
            "source": row.source,
            "title": row.title,
            "citation_ref": row.citation_ref,
            "review_status": row.review_status,
            "jurisdiction": row.jurisdiction,
            "confidence_score": row.confidence_score,
            "quality_score": row.quality_score,
            "review_date": row.review_date.isoformat() if row.review_date else None,
            "source_trust_rank": _source_trust_rank(row.source_type),
            "source_type": row.source_type,
        }
        quality_ok = (row.quality_score or 0) >= 0.7 and (row.confidence_score or 0) >= 0.7
        reviewed_ok = str(row.review_status or "").lower() in {"approved", "verified"}
        citation_ok = bool((row.citation_ref or "").strip())
        if quality_ok and reviewed_ok and not _is_stale(row.review_date) and citation_ok:
            provisional_facts.append(entry)
            key = _title_key(row.title)
            grouped_titles.setdefault(key, []).append(entry)
        else:
            assumptions.append(entry)
            if not citation_ok:
                blocked_sources.append({"source_id": row.source, "reason": "missing citation_ref for fact-grade use"})

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

    return {
        "knowledge": _state_counts(KnowledgeRegistryItem),
        "templates": _state_counts(TemplateRegistryItem),
        "scoring": _state_counts(ScoringRegistryItem),
        "sources": _state_counts(SourceRegistryItem),
        "datasets": _state_counts(DatasetRegistryItem),
        "scenarios": _state_counts(ScenarioRegistryItem),
    }
