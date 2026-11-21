"""Exercise Heimdall's deal stages against the canonical persistent models."""

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.models import AuditEvent
from app.leads.models import Lead
from app.models import daily_rhythm, life_timeline, pack_sw, pack_sz, pack_ta, pack_tb, philosophy, relationships
from app.models.contracts import Contract, ContractDocument, ContractEnvelope, ContractState, ContractTemplate
from app.models.deal import Deal
from app.offers.models import Offer
from app.services.heimdall_service import advance_stage_with_approval, analyze_deal


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'integrity.db'}")
    for model in (Lead, Deal, Offer, ContractTemplate, Contract, ContractEnvelope, ContractDocument, AuditEvent):
        model.__table__.create(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def deal_id(engine):
    with Session(engine) as db:
        lead = Lead(lead_name="Example Seller", lead_email="seller@example.test", lead_phone="555-0100", source="test")
        db.add(lead)
        db.flush()
        deal = Deal(lead_id=lead.id, title="Example deal", stage="draft", arv=150000)
        db.add(deal)
        db.commit()
        return deal.id


def advance(db, deal_id, stage, *, override=None, approver="operator"):
    return advance_stage_with_approval(
        deal_id, stage, approver, "Reviewed test evidence", override_reason=override, db=db,
    )


def test_pipeline_checks_target_stage_evidence_and_persists_across_sessions(engine, deal_id):
    with Session(engine) as db:
        assert analyze_deal(deal_id, db).recommended_stage == "lead_received"
        assert advance(db, deal_id, "lead_received")["result"] == "success"
        assert analyze_deal(deal_id, db).blocker_flags == ["missing_repair_cost"]
        assert advance(db, deal_id, "preliminary_analysis")["result"] == "rejected"
        db.get(Deal, deal_id).estimated_repair_cost = 0
        assert advance(db, deal_id, "preliminary_analysis")["result"] == "success"
        assert analyze_deal(deal_id, db).blocker_flags == ["no_offer_created"]
        db.add(Offer(deal_id=deal_id, offer_price=95000))
        assert analyze_deal(deal_id, db).offer_data["recommended_offer"] == 95000
        assert advance(db, deal_id, "offer_ready")["result"] == "success"
        assert advance(db, deal_id, "under_contract", override="Missing document")["result"] == "rejected"

        db.add(ContractTemplate(id="test-template", code="test", name="Test template"))
        contract = Contract(id="test-contract", template_id="test-template", title="Test contract", deal_id=str(deal_id))
        db.add(contract)
        assert advance(db, deal_id, "under_contract")["result"] == "rejected"
        contract.merge_data = {"address": "Example address"}
        assert advance(db, deal_id, "under_contract")["result"] == "success"
        assert advance(db, deal_id, "closed", override="Awaiting signature")["result"] == "rejected"
        contract.state = ContractState.FULLY_EXECUTED
        assert advance(db, deal_id, "closed")["result"] == "success"

    with Session(engine) as db:
        deal = db.get(Deal, deal_id)
        assert deal.stage == "closed"
        assert db.get(Lead, deal.lead_id).lead_name == "Example Seller"
        assert db.query(Offer).filter_by(deal_id=deal.id).one().offer_price == 95000
        assert db.get(Contract, "test-contract").deal_id == str(deal.id)
        actions = [item.action for item in db.query(AuditEvent).filter_by(entity_id=deal_id).order_by(AuditEvent.id)]
        assert [action for action in actions if action != "heimdall_stage_advance_rejected"] == [
            "heimdall_analyzed_deal", "heimdall_recommended_stage", "heimdall_stage_advanced",
        ] * 5
        events = db.query(AuditEvent).filter_by(action="heimdall_stage_advanced", entity_id=deal_id).order_by(AuditEvent.id).all()
        assert [item.new_value["stage"] for item in events] == [
            "lead_received", "preliminary_analysis", "offer_ready", "under_contract", "closed",
        ]
        assert events[-1].previous_value == {"stage": "under_contract"}
        assert events[-1].user_id == "operator"
        assert events[-1].notes == "Reviewed test evidence"


def test_rejects_skipped_backward_and_unattributed_transitions(engine, deal_id):
    with Session(engine) as db:
        assert advance(db, deal_id, "offer_ready", override="Try to skip")["result"] == "rejected"
        assert advance(db, deal_id, "unknown_stage")["result"] == "rejected"
        assert advance(db, deal_id, "lead_received", approver=" ")["result"] == "rejected"
        assert advance(db, deal_id, "lead_received")["result"] == "success"
        assert advance(db, deal_id, "draft")["result"] == "rejected"
    with Session(engine) as db:
        assert db.get(Deal, deal_id).stage == "lead_received"
        assert db.query(AuditEvent).filter_by(action="heimdall_stage_advance_rejected").count() == 4


def test_optional_override_is_recorded(engine, deal_id):
    with Session(engine) as db:
        advance(db, deal_id, "lead_received")
        assert advance(db, deal_id, "preliminary_analysis", override="  ")["result"] == "rejected"
        assert advance(db, deal_id, "preliminary_analysis", override="Repair estimate pending")["result"] == "success"
    with Session(engine) as db:
        audit = db.query(AuditEvent).filter_by(action="heimdall_stage_advanced").order_by(AuditEvent.id.desc()).first()
        assert audit.new_value["override_reason"] == "Repair estimate pending"


def test_audit_failure_rolls_back_stage_and_other_audit_rows(engine, deal_id):
    def fail_final_audit(mapper, connection, row):
        if row.action == "heimdall_stage_advanced":
            raise IntegrityError("insert audit event", {}, RuntimeError("simulated audit write failure"))

    event.listen(AuditEvent, "before_insert", fail_final_audit)
    try:
        with Session(engine) as db, pytest.raises(IntegrityError):
            advance(db, deal_id, "lead_received")
    finally:
        event.remove(AuditEvent, "before_insert", fail_final_audit)
    with Session(engine) as db:
        assert db.get(Deal, deal_id).stage == "draft"
        assert db.query(AuditEvent).count() == 0


@pytest.mark.parametrize(("owner", "attribute", "target", "other"), [
    (relationships.RelationshipProfile, "events", relationships.TrustEventLog, pack_ta.TrustEventLog),
    (pack_ta.RelationshipProfile, "trust_events", pack_ta.TrustEventLog, relationships.TrustEventLog),
    (pack_sw.LifeEvent, "milestones", pack_sw.LifeMilestone, life_timeline.LifeMilestone),
    (pack_sz.PhilosophyRecord, "principles", pack_sz.EmpirePrinciple, philosophy.EmpirePrinciple),
    (pack_tb.DailyRhythmProfile, "tempo_rules", pack_tb.TempoRule, daily_rhythm.TempoRule),
])
def test_orm_relationships_resolve_to_intended_table(owner, attribute, target, other):
    assert target.__name__ == other.__name__
    assert inspect(owner).relationships[attribute].mapper.class_ is target
