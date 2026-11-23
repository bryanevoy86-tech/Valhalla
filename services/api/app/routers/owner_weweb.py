"""Write-side owner browser routes over the existing private JARVIS store."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.routers.auth_weweb import private_owner_response, require_owner_session
from app.services.owner_document_requests import (
    DocumentApplyIn, DocumentRequestIn, apply_document_request, document_request_status, request_document_action,
)
from app.pantheon.roles import Role
from app.schemas.market_intelligence import MarketScope
from app.services.owner_specialist_context import pantheon_report_index, prime_decision_context, specialist_context
from app.services.prime_business_execution import require_owner_mandate_key
from app.services.owner_startup import StartupPlanIn, prepare_startup
from app.services.startup_dependencies import LaunchLane, startup_dependency_checklist
from app.services.startup_independence import StartupIndependenceIn, review_startup_independence
from app.services.commercial_targets import CommercialTargetsIn, review_commercial_targets
from app.services.startup_funding import FundingReviewIn, FundingSourceIn, review_funding, stage_funding_source
from app.services.acquisition_comparison import ComparisonIn
from app.services.wealth_scenario import PersonalAllocationIn, recommend_personal_allocation
from app.services.owner_conversation import (
    ThreadIn, TurnIn, UploadIn, attachment_summaries, bounded_upload, create_conversation, local_extraction,
    store_attachment, submit_turn,
)

class PrivateStartupRoute(APIRoute):
    def get_route_handler(self):
        handle = super().get_route_handler()

        async def with_private_errors(request: Request):
            try:
                return await handle(request)
            except RequestValidationError:
                return private_owner_response({"detail": "Invalid private startup planning data"}, status_code=422)
            except HTTPException as error:
                response = private_owner_response({"detail": error.detail}, status_code=error.status_code)
                for name, value in (error.headers or {}).items():
                    if name.lower() not in {"cache-control", "vary"}:
                        response.headers[name] = value
                return response

        return with_private_errors


router = APIRouter(prefix="/api/weweb", tags=["weweb-owner-conversation"],
                   dependencies=[Depends(require_owner_session)])
startup_router = APIRouter(prefix="/owner-startup", route_class=PrivateStartupRoute)


@router.post("/owner-conversations", status_code=201)
def owner_create_conversation(payload: ThreadIn, db: Session = Depends(get_db)):
    return private_owner_response(create_conversation(payload, db), status_code=201)


@router.post("/owner-conversations/{conversation_id}/turns", status_code=201)
def owner_submit_turn(conversation_id: UUID, payload: TurnIn, db: Session = Depends(get_db)):
    return private_owner_response(submit_turn(conversation_id, payload, db, local_only=True), status_code=201)


@router.post("/owner-conversations/{conversation_id}/attachments", status_code=201)
def owner_upload_attachment(conversation_id: UUID, payload: UploadIn = Depends(bounded_upload),
                            db: Session = Depends(get_db)):
    return private_owner_response(store_attachment(conversation_id, payload, db), status_code=201)


@router.post("/owner-conversations/{conversation_id}/attachments/{attachment_id}/extract")
def owner_extract_attachment(conversation_id: UUID, attachment_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(local_extraction(conversation_id, attachment_id, db))


@router.get("/owner-conversations/{conversation_id}/attachments")
def owner_list_attachments(conversation_id: UUID, limit: int = 50, db: Session = Depends(get_db)):
    return private_owner_response(attachment_summaries(conversation_id, limit, db))


@startup_router.get("/dependencies")
def owner_startup_dependencies(lane: LaunchLane = "ONE_TIME_CAD"):
    return private_owner_response(startup_dependency_checklist(lane))


@startup_router.post("/provider-readback/{provider}", dependencies=[Depends(require_owner_mandate_key)])
def owner_startup_provider_readback(provider: Literal["quickbooks", "docusign", "google-drive"]):
    from app.heimdall.authority import is_live
    from app.integrations.commissioning import read_drive_fixture
    from app.integrations.docusign.client import read_envelope_fixture
    from app.integrations.quickbooks.client import read_account_fixture

    if is_live():
        raise HTTPException(409, "Commissioning readbacks require an isolated non-live environment")
    readers = {"quickbooks": read_account_fixture, "docusign": read_envelope_fixture, "google-drive": read_drive_fixture}
    return private_owner_response(readers[provider]())


@startup_router.post("/compare")
def startup_comparison(payload: StartupPlanIn):
    return private_owner_response(prepare_startup(payload))


@startup_router.post("/independence-review")
def owner_startup_independence(payload: StartupIndependenceIn, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    return private_owner_response(review_startup_independence(db, payload, datetime.now(timezone.utc).date()))


@startup_router.post("/commercial-targets")
def owner_commercial_targets(payload: CommercialTargetsIn, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    return private_owner_response(review_commercial_targets(db, payload, datetime.now(timezone.utc).date()))


@startup_router.post("/funding-evidence", status_code=201)
def owner_stage_funding(payload: FundingSourceIn, db: Session = Depends(get_db),
                        owner_id: int = Depends(require_owner_session)):
    from datetime import datetime, timezone

    return private_owner_response(stage_funding_source(db, payload, owner_id, datetime.now(timezone.utc).date()),
                                  status_code=201)


@startup_router.post("/funding-review")
def owner_review_funding(payload: FundingReviewIn, db: Session = Depends(get_db),
                         owner_id: int = Depends(require_owner_session)):
    from datetime import datetime, timezone

    return private_owner_response(review_funding(db, payload, owner_id, datetime.now(timezone.utc).date()))


@router.post("/owner-personal-allocation")
def owner_personal_allocation(payload: PersonalAllocationIn, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    return private_owner_response(recommend_personal_allocation(db, payload, datetime.now(timezone.utc).date()))


@router.post("/owner-acquisition/{campaign_id}/settled-review")
def owner_acquisition_review(campaign_id: int, payload: MarketScope, db: Session = Depends(get_db)):
    from app.routers.foundry_checkout import _attribution_schema, schema
    from app.services.acquisition_rehearsal import settled_campaign
    from app.services.prime_business_execution import _check_legacy

    schema(db)
    _attribution_schema(db)
    scope = payload.model_dump()
    _check_legacy(db, **scope)
    return private_owner_response(settled_campaign(db, campaign_id, scope))


@router.post("/owner-acquisition/comparisons")
def owner_acquisition_comparison(payload: ComparisonIn, db: Session = Depends(get_db)):
    from app.routers.foundry_checkout import compare_acquisition_campaigns, schema

    schema(db)
    return private_owner_response(compare_acquisition_campaigns(payload, db))


@router.get("/owner-stripe-orders/{order_id}")
def owner_stripe_order(order_id: UUID, db: Session = Depends(get_db)):
    from app.heimdall.authority import is_live
    from app.services.stripe_orders import inspect_binding

    from app.services.stripe_bank_booking import bank_batch_summary
    from app.services.stripe_revenue_release import delivery_evidence_summary

    live = is_live()
    projection = inspect_binding(db, order_id, live=live)
    bank = bank_batch_summary(db, order_id, projection, live=live)
    delivery = delivery_evidence_summary(db, order_id, projection, bank, live=live)
    return private_owner_response({**projection, "bank_batch": bank, "delivery_evidence": delivery})


@router.post("/owner-operating-scope")
def owner_operating_scope(payload: MarketScope, db: Session = Depends(get_db)):
    from sqlalchemy import inspect

    from app.heimdall.authority import is_live
    from app.models.completion_registry import LegacyInstanceRegistryItem
    from app.routers.economic_control import assess, require_schema
    from app.services.prime_business_execution import _check_legacy
    from app.services.stripe_recurring import scoped_subscription_outcomes
    from app.services.treasury_reconciliation import observe_statement_heads

    if not inspect(db.connection()).has_table(LegacyInstanceRegistryItem.__tablename__):
        raise HTTPException(503, "Legacy registry unavailable")
    scope = payload.model_dump()
    legacy = _check_legacy(db, **scope)
    require_schema(db)
    try:
        report = assess(payload, db)
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        capital = None
    else:
        capital = {key: report[key] for key in (
            "currency", "basis", "as_of", "mandate_id", "period_net_minor", "outstanding_reservations_minor",
            "open_obligations_minor", "cumulative_loss_minor", "new_exposure_available_minor", "blockers",
            "suggested_action",
        )}
    return private_owner_response({
        "scope": scope, "legacy": {"display_name": legacy.display_name, "status": legacy.status},
        "capital_fixture": capital, "statement_fixtures": {
            purpose: observe_statement_heads(db, scope, purpose=purpose, detailed=True)
            for purpose in ("BUSINESS", "HOUSEHOLD", "OPERATING_RESERVE")
        },
        "recurring_paid_periods": scoped_subscription_outcomes(db, scope, live=is_live()),
        "actual_accessible_funds_minor": None, "execution_authorized": False,
    })


class AttentionAcknowledgmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notification_id: str = Field(min_length=3, max_length=128)


class AttentionEntry(BaseModel):
    notification_id: str
    category: Literal["integrity", "prime_integrity", "review", "prime_advisory", "economic", "discovery", "schedule"]
    reference: str


class AttentionInboxOut(BaseModel):
    entries: list[AttentionEntry]
    acknowledged_ids: list[str]
    view: Literal["PRIVATE_IN_APP"]
    delivery_attempted: Literal[False]
    execution_authorized: Literal[False]


class AttentionAcknowledgmentOut(BaseModel):
    notification_id: str
    acknowledged: Literal[True]
    delivery_attempted: Literal[False]
    execution_authorized: Literal[False]


@router.get("/owner-attention", response_model=AttentionInboxOut)
def attention_inbox(db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    from app.services.owner_operating_brief import owner_attention_with_acknowledgments

    inbox = AttentionInboxOut.model_validate(owner_attention_with_acknowledgments(db, owner_id))
    return private_owner_response(inbox)


@router.post("/owner-attention/acknowledge", response_model=AttentionAcknowledgmentOut)
def attention_acknowledge(payload: AttentionAcknowledgmentIn, db: Session = Depends(get_db),
                          owner_id: int = Depends(require_owner_session)):
    from app.services.owner_operating_brief import acknowledge_owner_attention

    receipt = AttentionAcknowledgmentOut.model_validate(acknowledge_owner_attention(db, owner_id, payload.notification_id))
    return private_owner_response(receipt)


@router.post("/owner-conversations/{conversation_id}/attachments/{attachment_id}/requests", status_code=201)
def stage_document_request(conversation_id: UUID, attachment_id: UUID, payload: DocumentRequestIn,
                           db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    return private_owner_response(request_document_action(db, owner_id, conversation_id, attachment_id, payload),
                                  status_code=201)


@router.get("/owner-document-requests/{request_id}")
def owner_document_request(request_id: UUID, db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    return private_owner_response(document_request_status(db, owner_id, request_id))


@router.post("/owner-document-requests/{request_id}/apply", dependencies=[Depends(require_owner_mandate_key)])
def owner_apply_document_request(request_id: UUID, payload: DocumentApplyIn,
                                 db: Session = Depends(get_db), owner_id: int = Depends(require_owner_session)):
    return private_owner_response(apply_document_request(db, owner_id, request_id, payload.expected_sha256))


@router.get("/owner-prime-decisions/{decision_id}")
def owner_prime_decision(decision_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(prime_decision_context(db, decision_id))


@router.get("/owner-specialist-schedules/{schedule_id}")
def owner_specialist_receipt(schedule_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(specialist_context(db, schedule_id, require_digest=True))


@router.get("/owner-pantheon/reports")
def owner_pantheon_reports(role: Role | None = None, after: UUID | None = None,
                           limit: int = Query(10, ge=1, le=25), db: Session = Depends(get_db)):
    from app.pantheon.monitor import assignment_schema

    assignment_schema(db)
    return private_owner_response(pantheon_report_index(db, role, after, limit))


router.include_router(startup_router)
