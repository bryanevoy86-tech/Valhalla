"""Simulation-only economic controls using scoped Prime and Loki evidence."""
from dataclasses import dataclass, field
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import inspect, select, update
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
from app.models.foundry_evidence import FoundryEvidence
from app.models.specialist_assignment import SpecialistAssignment
from app.schemas.economic_control import Containment, Liquidity, Mandate, Opportunity, Performance, Plan
from app.services.foundry_discovery import checked_evidence, economics
from app.services.specialist_triggers import outcome_scope_key
from app.services.universal_opportunity_evaluator import rank_economic_options


ADVICE_TYPE = "economic_advice"
REVIEW_ROLES = frozenset({"HEIMDALL", "NJORD", "NORNS", "LOKI", "TYR", "ODIN", "MIMIR"})
RECORD_MODELS = {"MANDATE": Mandate, "PERFORMANCE": Performance, "LIQUIDITY": Liquidity, "OPPORTUNITY": Opportunity, "CONTAINMENT": Containment}
CONTAINMENT = {"SUSPEND", "RESTRUCTURE", "EXIT"}


def ready(db):
    schema = inspect(db.connection())
    return all(schema.has_table(model.__tablename__) for model in (EconomicOperation, EconomicPool, EconomicRecord))


def operation_key(scope):
    # A changed engine or currency must not create a new accounting identity.
    return outcome_scope_key({key: scope[key] for key in ("legacy_instance_id", "business_id", "jurisdiction")})


def lock_pool(db, currency):
    # A write lock also serializes SQLite rehearsals. Postgres callers queue by currency.
    result = db.execute(update(EconomicPool).where(EconomicPool.currency == currency)
                        .values(sequence=EconomicPool.sequence + 1))
    if result.rowcount != 1:
        raise HTTPException(503, "Economic currency pool unavailable")
    return db.get(EconomicPool, currency, populate_existing=True)


def verified_payload(row: EconomicRecord) -> dict:
    name = f"economic_{row.kind.lower()}"
    if row.digest != artifact_digest(name, str(row.id), {
        "scope_key": row.scope_key, "sequence": row.sequence, "receipt_key": row.receipt_key, "content": row.payload,
    }):
        raise HTTPException(409, "Economic journal evidence failed integrity")
    return row.payload


def store_record(db, operation, kind, payload, *, receipt_ref=None):
    identifier = UUID(payload["id"])
    receipt_key = artifact_digest("economic_statement", "global", receipt_ref) if receipt_ref else None
    operation.sequence += 1
    signature = {"scope_key": operation.scope_key, "sequence": operation.sequence,
                 "receipt_key": receipt_key, "content": payload}
    row = EconomicRecord(id=identifier, scope_key=operation.scope_key, sequence=operation.sequence, kind=kind,
                         receipt_key=receipt_key, payload=payload,
                         digest=artifact_digest(f"economic_{kind.lower()}", str(identifier), signature))
    db.add(row)
    return row


def trigger_reassessment(db, scope, record_id, at):
    if inspect(db.connection()).has_table(SpecialistAssignment.__tablename__):
        assignment = SpecialistAssignment
        with db.no_autoflush:
            db.execute(update(assignment).where(
                assignment.scope_key == outcome_scope_key(scope), assignment.role.in_(REVIEW_ROLES),
                assignment.state == "active", assignment.expires_at > at, assignment.pending_event_id.is_(None),
            ).values(pending_event_id=f"ECON-{record_id}"))


def verify_trigger(db, scope, event):
    try:
        row = db.get(EconomicRecord, UUID(event.removeprefix("ECON-")))
        if row is not None and row.scope_key == operation_key(scope):
            return verified_payload(row)["scope"] == scope
    except ValueError:
        pass
    return False


@dataclass
class State:
    mandate: Mandate | None = None
    performance: Performance | None = None
    opportunities: dict[str, Opportunity] = field(default_factory=dict)
    cumulative_loss: int = 0
    simulated_funding: int = 0
    exit_proposed: bool = False
    contained: bool = False
    latest_decision: dict | None = None
    loss_limit: int | None = None
    funding_limit: int | None = None


def load_state(db, operation):
    current = State()
    rows = db.scalars(select(EconomicRecord).where(EconomicRecord.scope_key == operation.scope_key)
                      .order_by(EconomicRecord.sequence))
    last = 0
    for row in rows:
        payload = verified_payload(row)
        if row.sequence != last + 1 or payload["scope"] != operation.scope:
            raise HTTPException(409, "Economic journal sequence or scope mismatch")
        last = row.sequence
        if row.kind == "DECISION":
            current.latest_decision = payload
            current.simulated_funding += payload["reserved_simulation_minor"]
            current.exit_proposed |= payload["action"] == "EXIT"
            current.contained |= payload["action"] in {"SUSPEND", "EXIT"}
        else:
            record = RECORD_MODELS[row.kind].model_validate(payload)
            if row.kind == "MANDATE":
                if current.mandate is None:
                    current.cumulative_loss = record.opening_cumulative_loss
                    current.simulated_funding = record.opening_additional_funding
                current.mandate = record
                current.loss_limit = record.max_cumulative_loss if current.loss_limit is None else min(current.loss_limit, record.max_cumulative_loss)
                current.funding_limit = record.max_additional_funding if current.funding_limit is None else min(current.funding_limit, record.max_additional_funding)
            elif row.kind == "PERFORMANCE":
                current.performance = record
                current.cumulative_loss += max(0, record.operating_costs - record.operating_receipts)
            elif row.kind == "CONTAINMENT":
                current.contained = True
            elif row.kind == "OPPORTUNITY":
                current.opportunities[record.opportunity_key] = record
    if operation.sequence != last:
        raise HTTPException(409, "Economic journal head mismatch")
    return current


def current_performance(state, today):
    return state.performance is not None and today - timedelta(days=30) <= state.performance.end <= today


def pool_liquidity(db, pool):
    if pool.liquidity_id is None:
        return None
    row = db.get(EconomicRecord, pool.liquidity_id)
    if row is None or row.kind != "LIQUIDITY":
        raise HTTPException(409, "Economic liquidity evidence is missing")
    verified = verified_payload(row)
    operation = db.get(EconomicOperation, row.scope_key)
    if operation is None or operation.currency != pool.currency or operation.scope != verified["scope"]:
        raise HTTPException(409, "Economic liquidity evidence currency or scope mismatch")
    return Liquidity.model_validate(verified)


def fresh_liquidity(liquidity, today):
    return liquidity is not None and today - timedelta(days=7) <= liquidity.as_of <= today


def usable_cash(state, pool, liquidity, today):
    if pool.liquidity_conflict or not current_performance(state, today) or not fresh_liquidity(liquidity, today):
        return 0
    reserve = state.mandate.min_operating_reserve
    # The same committed funds cannot be allocated by another venture. Protected
    # balances are informational and never included in either inequality.
    return max(0, min(state.performance.uncommitted_local_cash - reserve - state.simulated_funding,
                      liquidity.unrestricted_pool_minor - pool.committed_minor))


def comparison(db, state, scope, currency, available, today, *, lock_sources=False):
    options = []
    for item in state.opportunities.values():
        blockers = []
        data = item.model_dump(mode="json", include={
            "opportunity_key", "title", "origin", "status", "required_capital", "projected_annual_net", "maximum_downside",
            "uncertainty_bp", "demand_bp", "operational_independence_bp", "time_to_revenue_days", "human_hours_weekly",
        })
        if item.valid_through < today:
            blockers.append("STALE_OPPORTUNITY")
        if item.status in {"SUSPENDED", "REJECTED"}:
            blockers.append("INACTIVE_OPTION")
        if item.compliance != "SATISFIED_IN_FIXTURE":
            blockers.append("COMPLIANCE")
        if item.unresolved_dependency_count:
            blockers.append("DEPENDENCIES_UNRESOLVED")
        if item.foundry_evidence_id:
            if not inspect(db.connection()).has_table(FoundryEvidence.__tablename__):
                raise HTTPException(503, "Foundry source schema unavailable")
            row = db.get(FoundryEvidence, item.foundry_evidence_id, populate_existing=True, with_for_update=lock_sources)
            try:
                if row is None:
                    raise HTTPException(409, "Missing Foundry source")
                foundry = checked_evidence(row, scope, today)
                if foundry.currency != currency:
                    raise HTTPException(409, "Foundry currency mismatch")
                measures = economics(foundry)
                acquisition = measures.get("acquisition") or {}
                net = acquisition.get("monthly_available_cash_after_debt_minor", measures["estimated_monthly_operating_contribution_minor"])
                downside = acquisition.get("stress_monthly_available_cash_after_debt_minor", measures["stress_monthly_operating_contribution_minor"])
                data["required_capital"] = max(foundry.startup_capital, acquisition.get("required_equity_and_reserve_minor", 0))
                data["projected_annual_net"] = net * 12
                data["maximum_downside"] = max(item.maximum_downside, -12 * downside)
                data["foundry_sha256"] = row.digest
            except (HTTPException, ValueError):
                blockers.append("FOUNDRY_SOURCE_UNAVAILABLE")
        if data["maximum_downside"] > max(0, state.loss_limit - state.cumulative_loss):
            blockers.append("DOWNSIDE_EXCEEDS_LOSS_BUDGET")
        data.update(record_id=str(item.id), blockers=blockers, evidence_ref=item.evidence_ref)
        options.append(data)
    return rank_economic_options(options, available)


def assessment(db, operation, state, pool, today, plan: Plan | None = None, *, lock_sources=False):
    scope, mandate = operation.scope, state.mandate
    liquidity = pool_liquidity(db, pool)
    available = usable_cash(state, pool, liquidity, today)
    remaining_exposure = max(0, mandate.max_exposure - (state.performance.outstanding_exposure if state.performance else 0)
                             - state.simulated_funding)
    comparison_budget = min(available, remaining_exposure, max(0, state.funding_limit - state.simulated_funding))
    ranked = comparison(db, state, scope, operation.currency, comparison_budget, today, lock_sources=lock_sources)
    blockers = []
    performance = state.performance
    if not current_performance(state, today):
        blockers.append("MISSING_OR_STALE_PERFORMANCE")
    if not fresh_liquidity(liquidity, today):
        blockers.append("MISSING_OR_STALE_LIQUIDITY")
    if pool.liquidity_conflict:
        blockers.append("CONFLICTING_LIQUIDITY")
    if today >= mandate.review_by:
        blockers.append("MANDATE_REVIEW_DUE")
    if performance is None or performance.obligations_status != "SATISFIED":
        blockers.append("OBLIGATIONS_UNRESOLVED")
    if state.cumulative_loss >= state.loss_limit:
        blockers.append("CUMULATIVE_LOSS_LIMIT")
    period_net = performance.operating_receipts - performance.operating_costs if performance else None
    if period_net is not None and period_net < mandate.minimum_period_net:
        blockers.append("BELOW_MINIMUM_PERFORMANCE")
    if performance is not None and performance.outstanding_exposure > mandate.max_exposure:
        blockers.append("EXPOSURE_LIMIT")
    if state.contained:
        blockers.append("OPERATION_CONTAINED")
    if plan:
        required = plan.requested_additional_minor
        if plan.cross_business_support:
            blockers.append("CROSS_BUSINESS_SUPPORT_REQUIRES_SEPARATE_AUTHORITY")
        if required > available:
            blockers.append("PROTECTED_RESERVE_OR_UNAVAILABLE_FUNDS")
        if state.simulated_funding + required > state.funding_limit:
            blockers.append("CUMULATIVE_FUNDING_LIMIT")
        if performance and performance.outstanding_exposure + state.simulated_funding + required > mandate.max_exposure:
            blockers.append("EXPOSURE_LIMIT")
        if plan.alternative_key:
            eligible = [item for item in ranked if item["eligible"]]
            chosen = next((item for item in eligible if item["opportunity_key"] == plan.alternative_key), None)
            if chosen is None or chosen is not eligible[0] or required != chosen["required_capital"]:
                blockers.append("REDEPLOYMENT_ALTERNATIVE_UNJUSTIFIED")
    best = next((item for item in ranked if item["eligible"]), None)
    incumbent = next((item for item in ranked if item["status"] == "OPERATING_REPORTED"), None)
    suggested = "CONTINUE"
    if state.exit_proposed or state.cumulative_loss >= state.loss_limit:
        suggested = "EXIT"
    elif blockers:
        suggested = "SUSPEND"
    elif best and incumbent and best["opportunity_key"] != incumbent["opportunity_key"]:
        suggested = "REDEPLOY"
    return {
        "scope": scope, "currency": operation.currency, "as_of": today.isoformat(),
        "mandate_id": str(mandate.id), "operation_sequence": operation.sequence,
        "pool_committed_minor": pool.committed_minor, "period_net_minor": period_net,
        "cumulative_loss_minor": state.cumulative_loss, "effective_loss_ceiling_minor": state.loss_limit,
        "effective_funding_limit_minor": state.funding_limit, "simulated_funding_minor": state.simulated_funding,
        "new_exposure_available_minor": available, "comparison_budget_minor": comparison_budget, "blockers": sorted(set(blockers)), "alternatives": ranked,
        "suggested_action": suggested,
        "best_eligible_alternative_key": best["opportunity_key"] if best else None,
        "last_performance_id": str(performance.id) if performance else None,
        "last_liquidity_id": str(liquidity.id) if liquidity else None,
        "basis": "RECONCILIATION_FIXTURE", "external_authority": False,
    }


def specialist_economics(db, role, scope, today):
    if role not in REVIEW_ROLES or not ready(db):
        return {}
    operation = db.get(EconomicOperation, operation_key(scope))
    if operation is None or operation.scope != scope:
        return {}
    state = load_state(db, operation)
    pool = db.get(EconomicPool, operation.currency)
    if pool is None:
        raise HTTPException(503, "Economic currency pool unavailable")
    report = assessment(db, operation, state, pool, today)
    common = {key: report[key] for key in ("mandate_id", "basis", "blockers", "suggested_action", "external_authority")}
    role_fields = {
        "NJORD": ("period_net_minor", "cumulative_loss_minor", "new_exposure_available_minor", "pool_committed_minor"),
        "NORNS": ("period_net_minor", "alternatives"),
        "LOKI": ("cumulative_loss_minor", "effective_loss_ceiling_minor", "effective_funding_limit_minor"),
        "TYR": ("last_performance_id",),
        "ODIN": ("alternatives",),
        "HEIMDALL": ("period_net_minor", "alternatives", "new_exposure_available_minor"),
        "MIMIR": ("last_performance_id", "cumulative_loss_minor"),
    }
    common.update({key: report[key] for key in role_fields[role]})
    if role == "NORNS":
        common["forward_recovery"] = [
            {"opportunity_key": item["opportunity_key"], "declared_uncertainty_bp": item["uncertainty_bp"],
             "adjusted_forward_value_minor": item["adjusted_forward_value_minor"],
             "downside_minor": item["maximum_downside"], "is_calibrated_probability": False}
            for item in report["alternatives"]
        ]
    if role == "MIMIR":
        common["last_internal_decision"] = state.latest_decision
        common["verified_real_world_outcome"] = False
    if role == "TYR":
        common["obligations"] = state.mandate.obligations
        common["obligations_status"] = state.performance.obligations_status if state.performance else "UNKNOWN"
    return {"economic_reassessment": common}


def require_no_containment(db: Session, scope: dict):
    """Existing Factory execution accepts no enrolled operation under containment."""
    if not ready(db):
        return
    operation = db.get(EconomicOperation, operation_key(scope))
    if operation is None:
        return
    lock_pool(db, operation.currency)
    db.refresh(operation)
    if operation.scope != scope:
        raise HTTPException(409, "Economic mandate applies to this operating identity")
    state = load_state(db, operation)
    if state.contained or state.cumulative_loss >= state.loss_limit:
        raise HTTPException(409, "Economic containment blocks this operation")
