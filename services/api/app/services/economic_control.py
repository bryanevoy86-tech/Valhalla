"""Simulation-only economic controls using scoped Prime and Loki evidence."""
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import inspect, select, update
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
from app.models.foundry_evidence import FoundryEvidence
from app.schemas.economic_control import Containment, Liquidity, Mandate, Obligation, Opportunity, Performance, Plan
from app.services.foundry_discovery import checked_evidence, demand_evidence, economic_blockers, economics
from app.services.foundry_industry import read_industry
from app.services.specialist_triggers import enqueue_prime, enqueue_research, outcome_scope_key
from app.services.universal_opportunity_evaluator import rank_economic_options


ADVICE_TYPE = "economic_advice"
REVIEW_ROLES = frozenset({"HEIMDALL", "NJORD", "NORNS", "LOKI", "TYR", "ODIN", "MIMIR"})
RECORD_MODELS = {"MANDATE": Mandate, "PERFORMANCE": Performance, "LIQUIDITY": Liquidity, "OPPORTUNITY": Opportunity, "CONTAINMENT": Containment, "OBLIGATION": Obligation}
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
    scope_key = outcome_scope_key(scope)
    event_id = f"ECON-{record_id}"
    enqueue_research(db, scope_key, event_id, at, roles=REVIEW_ROLES)
    enqueue_prime(db, scope_key, event_id, at, subscription="on_economic_reassessment")


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
    active_reservations: dict[UUID, int] = field(default_factory=dict)
    opening_reservations: int = 0
    obligations: dict[str, Obligation] = field(default_factory=dict)
    containment_sequence: int = 0
    performance_sequence: int = 0
    recoveries: list[dict] = field(default_factory=list)

    @property
    def outstanding_reservations(self):
        return self.opening_reservations + sum(self.active_reservations.values())

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
            reserved = payload["reserved_simulation_minor"]
            current.simulated_funding += reserved
            if reserved:
                current.active_reservations[row.id] = reserved
            current.exit_proposed |= payload["action"] == "EXIT"
            if payload["action"] in {"SUSPEND", "EXIT"}:
                current.contained = True
                current.containment_sequence = row.sequence
            elif payload["action"] == "RESTART":
                current.contained = False
        elif row.kind == "RECOVERY":
            current.recoveries.append(payload)
        elif row.kind == "RELEASE":
            decision_id = UUID(payload["decision_id"])
            if current.active_reservations.pop(decision_id, None) != payload["released_simulation_minor"]:
                raise HTTPException(409, "Reservation release does not reconcile")
        else:
            record = RECORD_MODELS[row.kind].model_validate(payload)
            if row.kind == "MANDATE":
                if current.mandate is None:
                    current.cumulative_loss = record.opening_cumulative_loss
                    current.simulated_funding = record.opening_additional_funding
                    current.opening_reservations = record.opening_additional_funding
                current.mandate = record
                current.loss_limit = record.max_cumulative_loss if current.loss_limit is None else min(current.loss_limit, record.max_cumulative_loss)
                current.funding_limit = record.max_additional_funding if current.funding_limit is None else min(current.funding_limit, record.max_additional_funding)
            elif row.kind == "PERFORMANCE":
                current.performance = record
                current.performance_sequence = row.sequence
                current.cumulative_loss += max(0, record.operating_costs - record.operating_receipts)
            elif row.kind == "CONTAINMENT":
                current.contained = True
                current.containment_sequence = row.sequence
            elif row.kind == "OPPORTUNITY":
                current.opportunities[record.opportunity_key] = record
            elif row.kind == "OBLIGATION":
                current.obligations[record.obligation_key] = record
    if operation.sequence != last:
        raise HTTPException(409, "Economic journal head mismatch")
    return current


def current_performance(state, today):
    return state.performance is not None and today - timedelta(days=30) <= state.performance.end <= today


def verify_checkout_performance(db, performance, *, lock=False):
    if performance.checkout_order_id is None:
        return None
    from app.routers.foundry_checkout import closed_checkout_proof

    proof = closed_checkout_proof(db, performance.checkout_order_id, scope=performance.scope.model_dump(), lock=lock)
    settlement_dates = [date.fromisoformat(ref["posted_on"]) for ref in proof["settlements"]]
    if (proof["sha256"] != performance.checkout_sha256 or proof["net_minor"] != performance.operating_receipts
            or proof["fixture_cost_minor"] != performance.operating_costs
            or not all(performance.start <= posted <= performance.end for posted in settlement_dates)):
        raise HTTPException(409, "Checkout performance differs from the reconciled fixture or reported period")
    return proof


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
    return max(0, min(state.performance.uncommitted_local_cash - reserve - state.outstanding_reservations,
                      liquidity.unrestricted_pool_minor - pool.committed_minor))


def comparison(db, state, scope, currency, available, today, *, lock_sources=False):
    options = []
    reservations = None
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
                foundry = checked_evidence(row, scope, today, db=db)
                if foundry.currency != currency:
                    raise HTTPException(409, "Foundry currency mismatch")
                industry = read_industry(db, row, foundry, scope, today, lock=lock_sources)
                if industry is not None:
                    data["industry_diligence"] = industry
                    blockers.append("INDUSTRY_DEMAND_UNVERIFIED")
                measures = economics(foundry)
                acquisition = measures.get("acquisition") or {}
                blockers.extend(economic_blockers(foundry.kind, measures))
                data["foundry_economics"] = measures
                net = acquisition.get("monthly_available_cash_after_debt_minor", measures["estimated_monthly_operating_contribution_minor"])
                downside = acquisition.get("stress_monthly_available_cash_after_debt_minor", measures["stress_monthly_operating_contribution_minor"])
                assessed = {
                    "required_capital": max(foundry.startup_capital, acquisition.get("required_equity_and_reserve_minor", 0)),
                    "projected_annual_net": net * 12,
                    "maximum_downside": max(item.maximum_downside, -12 * downside),
                }
                learning = None
                trade = (industry or {}).get("skilled_trade")
                if trade:
                    base, stress = (trade["scenarios"][name] for name in ("BASE", "STRESS"))
                    blockers.extend(base["blockers"])
                    blockers.extend(stress["blockers"])
                    assessed.update(
                        required_capital=max(assessed["required_capital"], base["startup_cash_reserve_proxy_minor"],
                                             stress["startup_cash_reserve_proxy_minor"]),
                        projected_annual_net=12 * base["monthly_operating_contribution_minor"],
                        maximum_downside=max(assessed["maximum_downside"],
                                             -12 * stress["monthly_operating_contribution_minor"]),
                    )
                    from app.services.trade_learning import current_lesson

                    learning = current_lesson(db, row, scope, industry, item.id, today)
                    data["operating_recommendation"] = "VERIFY_DEMAND_AND_CAPACITY"
                    if learning:
                        data["trade_learning"] = learning
                        lesson = learning["lesson"]
                        blockers.extend(lesson["blockers"])
                        assessed["required_capital"] = max(assessed["required_capital"],
                                                           lesson["cash_shortfall_minor"])
                        if lesson["blockers"]:
                            data["operating_recommendation"] = "CONTAIN_AND_REESTIMATE"
                international = (industry or {}).get("international")
                if international:
                    base, stress = (international[name] for name in ("base", "stress"))
                    blockers.extend(international["blockers"])
                    assessed.update(
                        required_capital=max(assessed["required_capital"], stress["required_cash_cad_cents"]),
                        projected_annual_net=12 * base["monthly_net_cad_cents"],
                        maximum_downside=max(assessed["maximum_downside"], -12 * stress["monthly_net_cad_cents"]),
                    )
                if (industry or {}).get("strategy_inputs"):
                    from app.services.foundry_strategies import StrategyStudy, project, rehearsal_allowed

                    # Keep modeled proposals outside economic execution eligibility.
                    blockers.append("BUSINESS_STRATEGIES_FIXTURE_ONLY")
                    if rehearsal_allowed(db):
                        from app.services.workforce_capacity import active_reservations, calendar, now

                        study = StrategyStudy.model_validate(industry["strategy_inputs"])
                        capacity = None
                        if any(case.work_window for case in study.cases):
                            at = now()
                            if reservations is None:
                                reservations = active_reservations(db, at)
                            capacity = calendar(study, industry["findings"], reservations, at)
                            data["workforce_calendar"] = capacity
                        data["business_strategies"] = project(
                            study, scope["jurisdiction"], calendar=capacity,
                            available=available, international=international,
                            learning=learning["lesson"]["sha256"] if learning and learning["lesson"]["blockers"] else None,
                        )
                data["projection_differences"] = [
                    {"field": field, "declared_minor": data[field], "used_minor": amount}
                    for field, amount in assessed.items() if data[field] != amount
                ]
                data.update(assessed)
                data["foundry_sha256"] = row.digest
                data["foundry_source"] = {
                    "evidence_id": str(row.id), "citation": (foundry.provenance.citation if foundry.provenance else foundry.source_ref),
                    "kind": foundry.kind,
                    "evidence_class": foundry.evidence_class,
                    "observed_on": foundry.observed_on.isoformat(), "expires_on": foundry.expires_on.isoformat(),
                }
                demand = demand_evidence(foundry)
                if demand:
                    data["demand_bp"] = demand["sample_demand_bp"]
                    data["demand_evidence"] = demand
            except (HTTPException, ValueError):
                blockers.append("FOUNDRY_SOURCE_UNAVAILABLE")
        if data["maximum_downside"] > max(0, state.loss_limit - state.cumulative_loss):
            blockers.append("DOWNSIDE_EXCEEDS_LOSS_BUDGET")
        data.update(record_id=str(item.id), blockers=blockers, evidence_ref=item.evidence_ref)
        options.append(data)
    return rank_economic_options(options, available)


def opportunity_selection(ranked, blockers):
    """Prioritize research without promoting declaration-only evidence into authority."""
    research = []
    for item in ranked:
        source = item.get("foundry_source")
        missing = {
            "VERIFY_PAID_DEMAND", "VERIFY_REPEATABLE_NET_AND_OWNER_TIME", "VERIFY_LEGAL_AND_EXECUTION_SCOPE",
        }
        if not source:
            missing.add("OBTAIN_CURRENT_SCOPED_SOURCE")
        if not (item.get("demand_evidence") or {}).get("demand_count"):
            missing.add("OBTAIN_POSITIVE_RELEVANT_BUYER_SAMPLE")
        research.append({
            "opportunity_key": item["opportunity_key"],
            "scenario_blockers": item["blockers"],
            "research_required": sorted(missing),
        })
    first = next((item["opportunity_key"] for item in ranked if item["eligible"] and item.get("foundry_source")
                  and (item.get("demand_evidence") or {}).get("demand_count")), None)
    return {
        "decision": "RESEARCH_ONLY" if first and not blockers else "ABSTAIN",
        "reason": ("SOURCE_BOUND_FIXTURE_CAN_GUIDE_RESEARCH_ONLY" if first and not blockers
                   else "NO_CURRENT_ELIGIBLE_EVIDENCE_OR_SCOPE_HELD"),
        "first_research_candidate_key": first if not blockers else None,
        "commercial_selection_key": None,
        "verified_monthly_owner_income_minor": None,
        "scope_holds": sorted(set(blockers)),
        "research": research,
    }


def assessment(db, operation, state, pool, today, plan: Plan | None = None, *, lock_sources=False):
    from app.heimdall.authority import is_live
    from app.services.prime_business_execution import _emergency_stop_active
    from app.services.stripe_bank_booking import scoped_bank_blockers

    scope, mandate = operation.scope, state.mandate
    bank_blockers = scoped_bank_blockers(db, scope, live=is_live())
    liquidity = pool_liquidity(db, pool)
    open_obligations = [item for item in state.obligations.values() if item.status != "CLOSED_IN_FIXTURE"]
    related_hold = business_contained(db, scope, exclude_scope_key=operation.scope_key)
    performance = state.performance
    checkout_conflict = False
    if performance is not None and performance.checkout_order_id is not None:
        try:
            verify_checkout_performance(db, performance)
        except HTTPException:
            checkout_conflict = True
    available = (0 if related_hold or checkout_conflict or bank_blockers else
                 max(0, usable_cash(state, pool, liquidity, today) - sum(item.amount_minor for item in open_obligations)))
    remaining_exposure = max(0, mandate.max_exposure - (state.performance.outstanding_exposure if state.performance else 0)
                             - state.outstanding_reservations)
    comparison_budget = min(available, remaining_exposure, max(0, state.funding_limit - state.simulated_funding))
    ranked = comparison(db, state, scope, operation.currency, comparison_budget, today, lock_sources=lock_sources)
    blockers = sorted(bank_blockers) + (["RELATED_BUSINESS_CONTAINED"] if related_hold else [])
    if checkout_conflict:
        blockers.append("CHECKOUT_PERFORMANCE_EVIDENCE_CONFLICT")
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
    restarting = bool(plan and plan.action == "RESTART")
    if any(item.status == "DISPUTED" or item.due_on <= today for item in open_obligations) or (restarting and open_obligations):
        blockers.append("TRACKED_OBLIGATIONS_UNRESOLVED")
    if state.contained and not restarting:
        blockers.append("OPERATION_CONTAINED")
    if restarting:
        if not state.contained or state.exit_proposed:
            blockers.append("RESTART_REQUIRES_SUSPENSION_WITHOUT_EXIT")
        if state.performance_sequence <= state.containment_sequence:
            blockers.append("RESTART_REQUIRES_POST_CONTAINMENT_PERFORMANCE")
        if available <= 0:
            blockers.append("RESTART_REQUIRES_RESERVE_HEADROOM")
    if plan:
        required = plan.requested_additional_minor
        if plan.cross_business_support:
            blockers.append("CROSS_BUSINESS_SUPPORT_REQUIRES_SEPARATE_AUTHORITY")
        if required > available:
            blockers.append("PROTECTED_RESERVE_OR_UNAVAILABLE_FUNDS")
        if state.simulated_funding + required > state.funding_limit:
            blockers.append("CUMULATIVE_FUNDING_LIMIT")
        if performance and performance.outstanding_exposure + state.outstanding_reservations + required > mandate.max_exposure:
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
        "outstanding_reservations_minor": state.outstanding_reservations,
        "open_obligations_minor": sum(item.amount_minor for item in open_obligations),
        "obligation_receipt_ids": [str(item.id) for item in state.obligations.values()],
        "cumulative_loss_minor": state.cumulative_loss, "effective_loss_ceiling_minor": state.loss_limit,
        "effective_funding_limit_minor": state.funding_limit, "simulated_funding_minor": state.simulated_funding,
        "new_exposure_available_minor": available, "comparison_budget_minor": comparison_budget, "blockers": sorted(set(blockers)), "alternatives": ranked,
        "suggested_action": suggested,
        "best_eligible_alternative_key": best["opportunity_key"] if best else None,
        "opportunity_selection": opportunity_selection(
            ranked, [*blockers, *(["EMERGENCY_STOP"] if _emergency_stop_active(db) else [])],
        ),
        "last_performance_id": str(performance.id) if performance else None,
        "last_liquidity_id": str(liquidity.id) if liquidity else None,
        "basis": "RECONCILIATION_FIXTURE", "external_authority": False,
    }


def verify_performance_claim(db, scope, claim):
    """Bind a historical net result to the exact immutable performance fixture."""
    if (set(claim) != {"basis", "record_id", "sha256", "period_net_minor"}
            or not isinstance(claim["record_id"], str) or not isinstance(claim["sha256"], str)
            or len(claim["sha256"]) != 64 or type(claim["period_net_minor"]) is not int):
        raise HTTPException(422, "Invalid Mimir economic performance claim")
    try:
        record_id = UUID(claim["record_id"])
    except ValueError:
        raise HTTPException(422, "Invalid economic performance record ID") from None
    if not ready(db):
        raise HTTPException(503, "Economic performance proof unavailable")
    operation = db.get(EconomicOperation, operation_key(scope))
    row = db.get(EconomicRecord, record_id)
    if (operation is None or operation.scope != scope or row is None or row.scope_key != operation.scope_key
            or row.kind != "PERFORMANCE" or row.digest != claim["sha256"]):
        raise HTTPException(409, "Mimir economic claim lacks matching scoped evidence")
    data = Performance.model_validate(verified_payload(row))
    if (data.scope.model_dump() != scope or data.id != record_id or data.evidence_class != "RECONCILIATION_FIXTURE"
            or data.operating_receipts - data.operating_costs != claim["period_net_minor"]):
        raise HTTPException(409, "Mimir economic claim contradicts the performance receipt")
    checkout = verify_checkout_performance(db, data)
    binding = {"checkout_order_id": checkout["order_id"], "checkout_sha256": checkout["sha256"]} if checkout else {}
    return {**claim, **binding, "record_id": str(record_id), "evidence_scope": "ECONOMIC_PERFORMANCE_FIXTURE_ONLY",
            "verified_real_world_outcome": False}


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
        "NORNS": ("period_net_minor", "alternatives", "opportunity_selection"),
        "LOKI": ("cumulative_loss_minor", "effective_loss_ceiling_minor", "effective_funding_limit_minor"),
        "TYR": ("last_performance_id",),
        "ODIN": ("alternatives", "opportunity_selection"),
        "HEIMDALL": ("period_net_minor", "alternatives", "new_exposure_available_minor", "cumulative_loss_minor",
                     "last_performance_id", "opportunity_selection"),
        "MIMIR": ("last_performance_id", "cumulative_loss_minor"),
    }
    common.update({key: report[key] for key in role_fields[role]})
    if (state.performance is not None and "CHECKOUT_PERFORMANCE_EVIDENCE_CONFLICT" not in report["blockers"]
            and role in {"HEIMDALL", "LOKI", "MIMIR", "NJORD"}):
        row = db.get(EconomicRecord, state.performance.id)
        claim = {"basis": "ECONOMIC_PERFORMANCE_FIXTURE", "record_id": str(state.performance.id),
                 "sha256": row.digest, "period_net_minor": report["period_net_minor"]}
        common["verified_performance_claim"] = verify_performance_claim(db, scope, claim)
    if role in {"ODIN", "NJORD", "NORNS", "HEIMDALL"}:
        strategies = [{"opportunity_key": item["opportunity_key"], "evidence_id": item["foundry_source"]["evidence_id"],
                       **item["business_strategies"]}
                      for item in report["alternatives"] if "business_strategies" in item]
        if strategies:
            common["business_strategy_assessments"] = strategies
    if role == "NORNS":
        common["forward_recovery"] = [
            {"opportunity_key": item["opportunity_key"], "declared_uncertainty_bp": item["uncertainty_bp"],
             "adjusted_forward_value_minor": item["adjusted_forward_value_minor"],
             "downside_minor": item["maximum_downside"], "is_calibrated_probability": False}
            for item in report["alternatives"]
        ]
    if role in {"MIMIR", "NORNS", "HEIMDALL"}:
        lessons = [item["trade_learning"] for item in report["alternatives"] if item.get("trade_learning")]
        if lessons:
            common["trade_learning"] = lessons
    if role == "MIMIR":
        scoped_capacity = [{"opportunity_key": item["opportunity_key"],
                            "alternatives": [row for row in item["business_strategies"]["alternatives"]
                                             if "timed_capacity" in row]}
                           for item in report["alternatives"] if "workforce_calendar" in item]
        if scoped_capacity:
            from app.services.workforce_capacity import recent_scope_events

            common["synthetic_capacity_observations"] = scoped_capacity
            common["synthetic_capacity_history"] = recent_scope_events(db, scope)
        common["last_internal_decision"] = state.latest_decision
        common["recent_recovery_fixtures"] = state.recoveries[-5:]
        common["verified_real_world_outcome"] = False
    if role == "TYR":
        common["tracked_open_obligations_minor"] = report["open_obligations_minor"]
        common["obligations"] = state.mandate.obligations
        common["obligations_status"] = state.performance.obligations_status if state.performance else "UNKNOWN"
    return {"economic_reassessment": common}


def business_operations(db, business_id):
    return db.scalars(select(EconomicOperation).where(
        EconomicOperation.scope["business_id"].as_string() == business_id,
    ).execution_options(populate_existing=True)).all()


def lock_capital_pools(db):
    # A new mirror or alternate currency cannot race admission past a business hold.
    # All multi-pool writers acquire the existing pools in the same order.
    currencies = db.scalars(select(EconomicPool.currency).order_by(EconomicPool.currency)).all()
    return {currency: lock_pool(db, currency) for currency in currencies}


def business_contained(db, scope, *, exclude_scope_key=None):
    for candidate in business_operations(db, scope["business_id"]):
        if candidate.scope_key == exclude_scope_key:
            continue
        if candidate.scope_key == operation_key(scope) and candidate.scope != scope:
            raise HTTPException(409, "Economic mandate applies to this operating identity")
        state = load_state(db, candidate)
        if state.contained or state.cumulative_loss >= state.loss_limit:
            return True
    return False


def require_no_containment(db: Session, scope: dict):
    """Gate dispatch and funding across all operating scopes of the same business."""
    if not ready(db):
        if inspect(db.connection()).has_table(EconomicOperation.__tablename__):
            raise HTTPException(503, "Economic containment evidence unavailable")
        return
    if not business_operations(db, scope["business_id"]):
        return
    lock_capital_pools(db)
    if business_contained(db, scope):
        raise HTTPException(409, "Economic containment blocks this operation")
