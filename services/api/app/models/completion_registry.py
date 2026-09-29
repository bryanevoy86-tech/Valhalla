from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text

from app.models.base import Base


class RegistryStates:
    ACTIVE_AND_VERIFIED = "ACTIVE_AND_VERIFIED"
    BUILT_TESTED_FEATURE_GATED = "BUILT_TESTED_FEATURE_GATED"
    PROFESSIONALLY_GATED = "PROFESSIONALLY_GATED"
    EXTERNALLY_BLOCKED = "EXTERNALLY_BLOCKED"
    SUPERSEDED_REJECTED_NOT_APPLICABLE = "SUPERSEDED_REJECTED_NOT_APPLICABLE"


class KnowledgeRegistryItem(Base):
    __tablename__ = "knowledge_registry_items"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(80), unique=True, nullable=False, index=True)
    source = Column(String(255), nullable=False)
    source_type = Column(String(80), nullable=False)
    title = Column(String(255), nullable=False)
    jurisdiction = Column(String(80), nullable=True)
    market = Column(String(120), nullable=True)
    effective_date = Column(Date, nullable=True)
    retrieved_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    expires_date = Column(Date, nullable=True)
    license_status = Column(String(80), nullable=True)
    permission_status = Column(String(80), nullable=True)
    quality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    version = Column(String(40), nullable=True)
    superseded_by = Column(String(80), nullable=True)
    review_status = Column(String(80), nullable=True)
    allowed_systems_json = Column(Text, nullable=True)
    citation_ref = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    refresh_schedule = Column(String(120), nullable=True)
    excluded = Column(Boolean, nullable=False, default=False)
    terminal_state = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TemplateRegistryItem(Base):
    __tablename__ = "template_registry_items"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(80), unique=True, nullable=False, index=True)
    family = Column(String(120), nullable=False)
    purpose = Column(String(255), nullable=False)
    audience = Column(String(120), nullable=False)
    channel = Column(String(80), nullable=True)
    jurisdiction = Column(String(80), nullable=True)
    entity = Column(String(120), nullable=True)
    version = Column(String(40), nullable=False)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    superseded_by = Column(String(80), nullable=True)
    source_owner = Column(String(120), nullable=True)
    required_variables_json = Column(Text, nullable=True)
    optional_variables_json = Column(Text, nullable=True)
    required_attachments_json = Column(Text, nullable=True)
    approval_required = Column(Boolean, nullable=False, default=True)
    professional_review_required = Column(Boolean, nullable=False, default=False)
    professional_review_status = Column(String(80), nullable=True)
    signature_required = Column(Boolean, nullable=False, default=False)
    status = Column(String(80), nullable=False)
    template_hash = Column(String(128), nullable=True)
    test_cases_ref = Column(String(255), nullable=True)
    terminal_state = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ScoringRegistryItem(Base):
    __tablename__ = "scoring_registry_items"

    id = Column(Integer, primary_key=True, index=True)
    score_id = Column(String(80), unique=True, nullable=False, index=True)
    canonical_name = Column(String(180), nullable=False)
    business_purpose = Column(Text, nullable=False)
    input_fields_json = Column(Text, nullable=True)
    formula_description = Column(Text, nullable=False)
    rules_json = Column(Text, nullable=True)
    weights_json = Column(Text, nullable=True)
    thresholds_json = Column(Text, nullable=True)
    normalization = Column(String(120), nullable=True)
    version = Column(String(40), nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    jurisdiction = Column(String(80), nullable=True)
    market = Column(String(120), nullable=True)
    owner_approval_status = Column(String(80), nullable=False)
    professional_approval_status = Column(String(80), nullable=True)
    confidence_handling = Column(Text, nullable=True)
    missing_data_behavior = Column(Text, nullable=True)
    bias_compliance_notes = Column(Text, nullable=True)
    benchmark_ref = Column(String(255), nullable=True)
    acceptable_error_range = Column(String(120), nullable=True)
    drift_policy = Column(Text, nullable=True)
    override_policy = Column(Text, nullable=True)
    rollback_policy = Column(Text, nullable=True)
    prohibited_actions = Column(Text, nullable=True)
    terminal_state = Column(String(64), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SourceRegistryItem(Base):
    __tablename__ = "source_registry_items"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(80), unique=True, nullable=False, index=True)
    canonical_name = Column(String(180), nullable=False)
    source_type = Column(String(80), nullable=False)
    data_class = Column(String(40), nullable=False)
    owner = Column(String(120), nullable=True)
    jurisdiction = Column(String(80), nullable=True)
    market = Column(String(120), nullable=True)
    citation_ref = Column(String(255), nullable=True)
    mode_allowlist_json = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    terminal_state = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DatasetRegistryItem(Base):
    __tablename__ = "dataset_registry_items"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    dataset_type = Column(String(80), nullable=False)
    purpose = Column(Text, nullable=False)
    domain = Column(String(120), nullable=False)
    jurisdiction = Column(String(80), nullable=True)
    business_engine = Column(String(120), nullable=True)
    record_count = Column(Integer, nullable=False, default=0)
    generation_method = Column(String(120), nullable=True)
    generator_version = Column(String(80), nullable=True)
    seed = Column(String(120), nullable=True)
    created_at_source = Column(DateTime, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    learning_eligibility = Column(Boolean, nullable=False, default=False)
    live_kpi_eligibility = Column(Boolean, nullable=False, default=False)
    accounting_eligibility = Column(Boolean, nullable=False, default=False)
    external_execution_eligibility = Column(Boolean, nullable=False, default=False)
    do_not_contact = Column(Boolean, nullable=False, default=True)
    expected_behavior = Column(Text, nullable=True)
    isolation_policy = Column(Text, nullable=True)
    purge_archive_procedure = Column(Text, nullable=True)
    test_coverage = Column(Text, nullable=True)
    status = Column(String(80), nullable=False)
    source_id = Column(String(80), nullable=True)
    terminal_state = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ScenarioRegistryItem(Base):
    __tablename__ = "scenario_registry_items"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(80), nullable=False)
    domain = Column(String(120), nullable=False)
    jurisdiction = Column(String(80), nullable=True)
    business_engine = Column(String(120), nullable=True)
    difficulty = Column(String(40), nullable=False)
    initial_state = Column(String(120), nullable=False)
    input_dataset = Column(String(80), nullable=False)
    expected_allowed_actions_json = Column(Text, nullable=True)
    expected_prohibited_actions_json = Column(Text, nullable=True)
    expected_owner_message = Column(Text, nullable=True)
    expected_specialist_reviews_json = Column(Text, nullable=True)
    expected_approval_requirement = Column(String(120), nullable=True)
    expected_final_state = Column(String(120), nullable=False)
    expected_audit_events_json = Column(Text, nullable=True)
    failure_injection = Column(Text, nullable=True)
    recovery_path = Column(Text, nullable=True)
    practice_safe = Column(Boolean, nullable=False, default=True)
    external_side_effects_allowed = Column(Boolean, nullable=False, default=False)
    version = Column(String(40), nullable=False)
    status = Column(String(80), nullable=False)
    terminal_state = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ScenarioExecutionRecord(Base):
    __tablename__ = "scenario_execution_records"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(80), unique=True, nullable=False, index=True)
    scenario_id = Column(String(80), nullable=False, index=True)
    mode = Column(String(20), nullable=False)
    status = Column(String(40), nullable=False, default="instantiated")
    run_kind = Column(String(40), nullable=False, default="synthetic")
    input_payload_json = Column(Text, nullable=True)
    actual_result_json = Column(Text, nullable=True)
    comparison_json = Column(Text, nullable=True)
    audit_evidence_json = Column(Text, nullable=True)
    replay_of_execution_id = Column(String(80), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class LearningPromotionRecord(Base):
    __tablename__ = "learning_promotion_records"

    id = Column(Integer, primary_key=True, index=True)
    learning_id = Column(String(80), unique=True, nullable=False, index=True)
    dataset_id = Column(String(80), nullable=False, index=True)
    domain = Column(String(120), nullable=False)
    current_state = Column(String(40), nullable=False)
    source_quality = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    repeatable = Column(Boolean, nullable=True)
    jurisdiction = Column(String(80), nullable=True)
    business_scope = Column(String(120), nullable=True)
    risk_level = Column(String(40), nullable=True)
    benchmark_result = Column(String(80), nullable=True)
    actual_outcome_class = Column(String(80), nullable=True)
    professional_required = Column(Boolean, nullable=False, default=False)
    decision_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LearningTaskQueueItem(Base):
    __tablename__ = "learning_task_queue_items"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(80), unique=True, nullable=False, index=True)
    task_type = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False, default="queued")
    priority = Column(String(20), nullable=False, default="normal")
    domain = Column(String(120), nullable=False)
    jurisdiction = Column(String(80), nullable=True)
    business_scope = Column(String(120), nullable=True)
    knowledge_item_id = Column(String(80), nullable=True, index=True)
    learning_id = Column(String(80), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    assigned_to = Column(String(120), nullable=True)
    due_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
