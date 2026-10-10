from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Literal


ReplayPartition = Literal["TRAINING_SET", "VALIDATION_SET", "BLIND_HOLDOUT_SET"]


def bounded(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def engine_routing_key(engine_id: str) -> str:
    e = str(engine_id or "").strip().lower()
    if e in {"wholesaling", "brrrr", "flips", "rentals", "multifamily", "commercial", "real_estate"}:
        return "real_estate"
    if e in {"ai_automation_services", "ai_microbusinesses"}:
        return "ai_automation"
    if e in {"micro_saas", "saas_subscription_products"}:
        return "micro_saas"
    if e in {"lead_generation"}:
        return "lead_generation"
    if e in {"business_acquisitions"}:
        return "business_acquisition"
    if e in {"funding_grants"}:
        return "funding_grants"
    if e in {"market_intelligence", "market_intelligence_data_products"}:
        return "market_intelligence"
    if e in {"ops_automation", "operations_automation"}:
        return "ops_automation"
    return "generic"


def _score(inp: dict[str, Any], key: str, default: float = 0.5) -> float:
    return float(bounded(float(inp.get(key, default)), 0.0, 1.0))


def specialist_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    routing = engine_routing_key(str(payload.get("engine_id") or ""))
    si = dict(payload.get("specialist_inputs") or {})

    if routing == "ai_automation":
        score = (
            _score(si, "customer_pain")
            + _score(si, "willingness_to_pay")
            + _score(si, "recurring_potential")
            + _score(si, "retention_potential")
            + (1.0 - _score(si, "implementation_effort"))
            + (1.0 - _score(si, "delivery_cost"))
            + (1.0 - _score(si, "customer_acquisition_difficulty"))
            + (1.0 - _score(si, "competition"))
            + _score(si, "automation_percentage")
        ) / 9.0
        return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}

    if routing == "micro_saas":
        score = (
            _score(si, "problem_severity")
            + _score(si, "addressable_niche")
            + _score(si, "pricing_power")
            + _score(si, "retention")
            + (1.0 - _score(si, "churn_risk"))
            + (1.0 - _score(si, "technical_build_effort"))
            + (1.0 - _score(si, "hosting_api_cost"))
            + (1.0 - _score(si, "support_burden"))
            + _score(si, "defensibility")
            + _score(si, "global_reach")
        ) / 10.0
        return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}

    if routing == "lead_generation":
        score = (
            _score(si, "buyer_demand")
            + _score(si, "lead_value")
            + _score(si, "source_legality")
            + (1.0 - _score(si, "acquisition_cost"))
            + _score(si, "qualification_rate")
            + _score(si, "conversion_potential")
            + _score(si, "repeat_customer_potential")
        ) / 7.0
        return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}

    if routing == "business_acquisition":
        score = (
            _score(si, "revenue_strength")
            + _score(si, "cash_flow_quality")
            + (1.0 - _score(si, "owner_dependence"))
            + (1.0 - _score(si, "customer_concentration"))
            + _score(si, "durability")
            + (1.0 - _score(si, "purchase_price_risk"))
            + _score(si, "financing_feasibility")
            + _score(si, "automation_opportunity")
            + (1.0 - _score(si, "integration_risk"))
            + (1.0 - _score(si, "management_burden"))
        ) / 10.0
        return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}

    if routing == "funding_grants":
        score = (
            _score(si, "eligibility")
            + _score(si, "amount_quality")
            + (1.0 - _score(si, "matching_burden"))
            + _score(si, "deadline_readiness")
            + _score(si, "preapproval_readiness")
            + (1.0 - _score(si, "reimbursement_risk"))
            + _score(si, "probability")
            + (1.0 - _score(si, "reporting_burden"))
            + _score(si, "strategic_usefulness")
        ) / 9.0
        return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}

    if routing == "market_intelligence":
        score = (
            _score(si, "data_uniqueness")
            + _score(si, "customer_value")
            + _score(si, "subscription_potential")
            + (1.0 - _score(si, "source_cost"))
            + _score(si, "source_rights")
            + _score(si, "update_frequency")
            + (1.0 - _score(si, "competition"))
            + _score(si, "automation_potential")
        ) / 8.0
        return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}

    score = (
        bounded(float(payload.get("strategic_value") or 0.5), 0.0, 1.0)
        + bounded(float(payload.get("evidence_confidence") or 0.5), 0.0, 1.0)
        + (1.0 - bounded(float(payload.get("downside_exposure") or 0.4), 0.0, 1.0))
    ) / 3.0
    return {"engine_specialist": routing, "fit_score": round(score, 4), "criteria": si}


def universal_loki_objections(payload: dict[str, Any], specialist: dict[str, Any]) -> list[dict[str, Any]]:
    objections: list[dict[str, Any]] = []
    fit = float(specialist.get("fit_score") or 0.0)
    if fit < 0.5:
        objections.append(
            {
                "objection_id": f"LOKI-U-{payload.get('opportunity_id')}-001",
                "claim_challenged": "opportunity has sufficient validation evidence",
                "objection_evidence": "specialist fit score below threshold",
                "severity": "warn",
                "materiality": "material",
                "resolved": False,
                "impact_on_recommendation": "PROCEED->RESEARCH_MORE",
            }
        )

    downside = float(payload.get("downside_exposure") or 0.0)
    if downside >= 0.72:
        objections.append(
            {
                "objection_id": f"LOKI-U-{payload.get('opportunity_id')}-002",
                "claim_challenged": "downside exposure is acceptable",
                "objection_evidence": f"downside exposure {downside:.2f} exceeds critical threshold",
                "severity": "critical",
                "materiality": "high",
                "resolved": False,
                "impact_on_recommendation": "PROCEED->REJECT",
            }
        )

    route = engine_routing_key(str(payload.get("engine_id") or ""))
    route_challenges = {
        "ai_automation": "Can customers solve this cheaply without Valhalla?",
        "micro_saas": "Why would anyone pay instead of existing tools?",
        "lead_generation": "Are leads truly monetizable and compliant?",
        "business_acquisition": "How much revenue disappears if the owner exits?",
        "funding_grants": "Is this actually non-dilutive grant value?",
        "real_estate": "Can this still survive a stressed downside scenario?",
    }
    if route in route_challenges:
        objections.append(
            {
                "objection_id": f"LOKI-U-{payload.get('opportunity_id')}-Q",
                "claim_challenged": "specialist recommendation",
                "objection_evidence": route_challenges[route],
                "severity": "warn",
                "materiality": "material",
                "resolved": False,
                "impact_on_recommendation": "PROCEED->RESEARCH_MORE",
            }
        )
    return objections


def universal_norns(payload: dict[str, Any], specialist: dict[str, Any], objections: list[dict[str, Any]]) -> dict[str, Any]:
    fit = float(specialist.get("fit_score") or 0.0)
    evidence = float(payload.get("evidence_confidence") or 0.45)
    critical = 1.0 if any(o.get("severity") == "critical" for o in objections) else 0.0
    worthwhile = bounded((fit * 0.45) + (evidence * 0.4) + (0.2 * (1.0 - critical)), 0.01, 0.99)
    first_revenue = bounded(worthwhile - 0.08 - (0.05 if int(payload.get("estimated_time_to_first_revenue_days") or 90) > 120 else 0.0), 0.01, 0.99)
    break_even = bounded(first_revenue - 0.06, 0.01, 0.99)
    repeatable = bounded(break_even - 0.04 + float(payload.get("scalability") or 0.5) * 0.1, 0.01, 0.99)
    timing = int(payload.get("estimated_time_to_validation_days") or 45)
    return {
        "model_state": "MODEL_ESTIMATE",
        "calibration_state": "NOT_YET_CALIBRATED",
        "probability_of_worthwhile_validation": round(worthwhile, 4),
        "probability_of_first_revenue": round(first_revenue, 4),
        "probability_of_break_even": round(break_even, 4),
        "probability_of_repeatable_profitability": round(repeatable, 4),
        "timing_estimate_days": timing,
    }


def universal_owner_envelope(payload: dict[str, Any], final_decision: str) -> dict[str, Any]:
    spend = float(payload.get("estimated_test_cost") or payload.get("required_capital") or 0.0)
    commitment = float(payload.get("required_capital") or spend)
    return {
        "recommended_action": final_decision.upper(),
        "maximum_spend": round(spend, 2),
        "maximum_commitment": round(max(commitment, spend), 2),
        "duration_days": int(payload.get("estimated_time_to_validation_days") or 45),
        "stop_loss": round(max(spend * 0.35, 0.0), 2),
        "permitted_external_actions": [],
        "required_reapproval_conditions": [
            "new_critical_loki_objection",
            "cost_increase_above_20pct",
            "compliance_state_changes_to_fail",
        ],
        "legal_review_required": False,
        "owner_approval_required": bool(payload.get("human_approval_required", True)),
        "approval_state": "PENDING_OWNER" if bool(payload.get("human_approval_required", True)) else "NOT_REQUIRED",
        "shadow_mode_external_execution_blocked": True,
    }


def universal_dimensions(payload: dict[str, Any], specialist: dict[str, Any], norns: dict[str, Any]) -> dict[str, float]:
    required_capital = float(payload.get("required_capital") or payload.get("estimated_test_cost") or 0.0)
    test_cost = float(payload.get("estimated_test_cost") or required_capital or 0.0)
    margin_low = payload.get("expected_margin_low")
    margin_high = payload.get("expected_margin_high")
    margin_mid = None
    if margin_low is not None and margin_high is not None:
        margin_mid = (float(margin_low) + float(margin_high)) / 2.0
    elif margin_high is not None:
        margin_mid = float(margin_high)
    elif margin_low is not None:
        margin_mid = float(margin_low)

    return {
        "PROBABILITY": float(norns["probability_of_worthwhile_validation"]),
        "CAPITAL_EFFICIENCY": round(bounded(1.0 - (test_cost / max(1.0, required_capital + test_cost + 1.0)), 0.0, 1.0), 4),
        "TIME_TO_CASH": round(bounded(1.0 - (float(payload.get("estimated_time_to_first_revenue_days") or 120) / 365.0), 0.0, 1.0), 4),
        "DOWNSIDE": round(bounded(1.0 - float(payload.get("downside_exposure") or 0.5), 0.0, 1.0), 4),
        "RECURRING_REVENUE": 1.0 if payload.get("revenue_type") in {"RECURRING", "SUBSCRIPTION"} else 0.45,
        "SCALABILITY": round(bounded(float(payload.get("scalability") or 0.5), 0.0, 1.0), 4),
        "AUTOMATION_FIT": round(bounded(float(payload.get("automation_potential") or 0.5), 0.0, 1.0), 4),
        "OWNER_TIME": round(bounded(1.0 - ((float(payload.get("owner_time_requirement_hours_weekly") or 20.0)) / 60.0), 0.0, 1.0), 4),
        "STRATEGIC_VALUE": round(bounded(float(payload.get("strategic_value") or 0.5), 0.0, 1.0), 4),
        "EVIDENCE_CONFIDENCE": round(bounded(float(payload.get("evidence_confidence") or specialist.get("fit_score") or 0.45), 0.0, 1.0), 4),
        "EXPECTED_MARGIN": round(bounded(float(margin_mid or 0.25), 0.0, 1.0), 4),
    }


def weighted_rank(dimensions: dict[str, float]) -> float:
    weights = {
        "PROBABILITY": 0.16,
        "CAPITAL_EFFICIENCY": 0.12,
        "TIME_TO_CASH": 0.1,
        "DOWNSIDE": 0.1,
        "RECURRING_REVENUE": 0.07,
        "SCALABILITY": 0.09,
        "AUTOMATION_FIT": 0.07,
        "OWNER_TIME": 0.06,
        "STRATEGIC_VALUE": 0.07,
        "EVIDENCE_CONFIDENCE": 0.06,
        "EXPECTED_MARGIN": 0.05,
        "EXIT_QUALITY": 0.05,
    }
    return round(sum(float(dimensions.get(k, 0.0)) * v for k, v in weights.items()) * 100.0, 4)


def _infer_exit_quality(payload: dict[str, Any]) -> float:
    options = payload.get("exit_options") or []
    blast = str(payload.get("blast_radius") or "MEDIUM").upper()
    surviv = float(payload.get("survival_capital") or 0.0)
    entry = float(payload.get("entry_capital") or payload.get("required_capital") or 0.0)
    ratio = 1.0 if entry <= 0 else bounded(surviv / max(entry, 1.0), 0.0, 2.0)
    blast_penalty = {"ISOLATED": 0.0, "LOW": 0.05, "MEDIUM": 0.12, "HIGH": 0.2, "SYSTEMIC": 0.35}.get(blast, 0.12)
    option_bonus = min(0.25, 0.05 * len(options))
    return round(bounded(0.45 + option_bonus + (ratio * 0.2) - blast_penalty, 0.0, 1.0), 4)


def baseline_scores(payload: dict[str, Any], dimensions: dict[str, float]) -> dict[str, Any]:
    capital = float(payload.get("required_capital") or 0.0)
    margin = float(dimensions.get("EXPECTED_MARGIN", 0.0))
    time_to_cash = int(payload.get("estimated_time_to_first_revenue_days") or 120)
    payback = margin / max(1.0, time_to_cash)
    simple_margin_capital = margin * bounded(1.0 - capital / max(1.0, capital + 50000.0), 0.0, 1.0)
    return {
        "rule_based_property_model": round(float(dimensions.get("DOWNSIDE", 0.0)) * 100.0, 4),
        "simple_payback_ranking": round(payback * 10000.0, 4),
        "simple_margin_capital_ranking": round(simple_margin_capital * 100.0, 4),
        "industry_average_heuristic": 50.0,
    }


def apply_lookahead_protection(payload: dict[str, Any], reveal_historical_outcomes: bool) -> dict[str, Any]:
    as_of_date = payload.get("as_of_date")
    events = list(payload.get("historical_events") or [])
    if not as_of_date or not events:
        return {
            "as_of_date": as_of_date,
            "future_events_excluded": 0,
            "future_information_hidden": bool(payload.get("future_information_hidden", True)),
            "valid": True,
        }

    if isinstance(as_of_date, str):
        asof = datetime.fromisoformat(as_of_date).date()
    elif isinstance(as_of_date, date):
        asof = as_of_date
    else:
        asof = datetime.now(timezone.utc).date()

    excluded = 0
    for ev in events:
        ts = ev.get("event_date") or ev.get("publication_date") or ev.get("source_timestamp")
        if not ts:
            continue
        d = datetime.fromisoformat(str(ts)).date()
        if d > asof:
            excluded += 1

    contaminated = excluded > 0 and reveal_historical_outcomes
    return {
        "as_of_date": asof.isoformat(),
        "future_events_excluded": excluded,
        "future_information_hidden": bool(payload.get("future_information_hidden", True)),
        "valid": not contaminated,
    }


def build_prediction_snapshot(
    payload: dict[str, Any],
    *,
    decision_model: str,
    final_decision: str,
    expected: dict[str, Any],
    previous_snapshot_id: str | None = None,
    correction_reason: str | None = None,
) -> dict[str, Any]:
    canonical = {
        "decision_model": decision_model,
        "opportunity_id": payload.get("opportunity_id"),
        "engine_id": payload.get("engine_id"),
        "as_of_date": payload.get("as_of_date"),
        "final_decision": final_decision,
        "expected": expected,
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    snap = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "prediction_snapshot_id": snap,
        "prediction_locked_at": datetime.now(timezone.utc).isoformat(),
        "immutable": True,
        "previous_prediction_snapshot_id": previous_snapshot_id,
        "correction_reason": correction_reason,
        "snapshot_version": "v1" if not previous_snapshot_id else "v2",
        "decision_model": decision_model,
    }


def build_outcome_contract(
    payload: dict[str, Any],
    *,
    decision_id: str,
    pantheon_snapshot_id: str | None,
    evidence_snapshot_id: str | None,
    final_decision: str,
    norns: dict[str, Any],
    expected: dict[str, Any],
    outcome_class: str,
    observability_state: str,
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "opportunity_id": payload.get("opportunity_id"),
        "engine_id": payload.get("engine_id"),
        "legacy": payload.get("legacy", "Legacy"),
        "jurisdiction": payload.get("jurisdiction"),
        "outcome_class": outcome_class,
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
        "as_of_date": payload.get("as_of_date"),
        "prediction_locked_at": datetime.now(timezone.utc).isoformat(),
        "evidence_snapshot_id": evidence_snapshot_id,
        "pantheon_snapshot_id": pantheon_snapshot_id,
        "heimdall_decision": final_decision.upper(),
        "expected_economics": expected.get("economics"),
        "expected_timing": expected.get("timing"),
        "expected_risk": expected.get("risk"),
        "expected_exit_path": expected.get("exit_path"),
        "actual_outcome": None,
        "actual_outcome_date": None,
        "actual_economics": None,
        "actual_timing": None,
        "outcome_confidence": None,
        "prediction_error": None,
        "decision_quality": None,
        "role_accuracy": None,
        "outcome_observability_state": observability_state,
        "norns_probability": norns.get("probability_of_worthwhile_validation"),
    }


def classify_regret(selected_value: float, best_observed_alternative_value: float | None) -> dict[str, Any]:
    if best_observed_alternative_value is None:
        return {"regret_class": "UNKNOWN", "confidence": "low", "delta": None}
    delta = best_observed_alternative_value - selected_value
    if delta <= 5.0:
        level = "REGRET_LOW"
    elif delta <= 20.0:
        level = "REGRET_MEDIUM"
    else:
        level = "REGRET_HIGH"
    return {"regret_class": level, "confidence": "medium", "delta": round(delta, 4)}


def evaluate_generic_opportunity(
    payload: dict[str, Any],
    *,
    decision_model: str,
    reveal_historical_outcomes: bool,
    expected_outcome_class: str,
) -> dict[str, Any]:
    specialist = specialist_analysis(payload)
    loki_objections = universal_loki_objections(payload, specialist)
    norns = universal_norns(payload, specialist, loki_objections)
    dimensions = universal_dimensions(payload, specialist, norns)
    exit_quality = _infer_exit_quality(payload)
    dimensions["EXIT_QUALITY"] = exit_quality

    unresolved_critical = any((o["severity"] == "critical" and not o["resolved"]) for o in loki_objections)
    unresolved_material = any((o["materiality"] == "material" and not o["resolved"]) for o in loki_objections)
    fit = float(specialist.get("fit_score") or 0.0)

    pre_loki_recommendation = "proceed" if fit >= 0.62 and norns["probability_of_worthwhile_validation"] >= 0.58 else "hold"
    if unresolved_critical:
        final_decision = "reject"
    elif pre_loki_recommendation == "proceed" and unresolved_material:
        final_decision = "research_more"
    elif pre_loki_recommendation == "proceed" and norns["probability_of_break_even"] >= 0.55:
        final_decision = "proceed"
    else:
        final_decision = "hold"

    checks = {
        "odin": {"allowed": fit >= 0.45, "severity": "info" if fit >= 0.45 else "warn", "reasons": [] if fit >= 0.45 else ["weak strategic fit"]},
        "loki": {
            "allowed": not unresolved_critical,
            "severity": "critical" if unresolved_critical else ("warn" if loki_objections else "info"),
            "reasons": [o["objection_evidence"] for o in loki_objections],
        },
        "tyr": {"allowed": True, "severity": "info", "reasons": []},
        "forseti": {"allowed": True, "severity": "info", "reasons": []},
        "vidar": {
            "allowed": float(payload.get("downside_exposure") or 0.4) <= 0.7,
            "severity": "warn" if float(payload.get("downside_exposure") or 0.4) > 0.7 else "info",
            "reasons": [] if float(payload.get("downside_exposure") or 0.4) <= 0.7 else ["downside resilience weak"],
        },
        "norns": {
            "allowed": norns["probability_of_worthwhile_validation"] >= 0.5,
            "severity": "info" if norns["probability_of_worthwhile_validation"] >= 0.5 else "warn",
            "reasons": [] if norns["probability_of_worthwhile_validation"] >= 0.5 else ["probability below threshold"],
        },
    }
    pantheon = {
        "overall_allowed": final_decision in {"proceed", "research_more", "hold"},
        "worst_severity": "critical" if unresolved_critical else ("warn" if loki_objections else "info"),
        "blocked_by": [k for k, v in checks.items() if not v.get("allowed", True)],
        "checks": checks,
    }

    owner_envelope = universal_owner_envelope(payload, final_decision)
    rank_value = weighted_rank(dimensions)
    route = engine_routing_key(str(payload.get("engine_id") or ""))

    baseline = baseline_scores(payload, dimensions)
    selected_baseline = baseline["simple_margin_capital_ranking"]
    regret = classify_regret(selected_baseline, None)

    expected = {
        "economics": {
            "required_capital": payload.get("required_capital"),
            "estimated_test_cost": payload.get("estimated_test_cost"),
            "expected_margin_low": payload.get("expected_margin_low"),
            "expected_margin_high": payload.get("expected_margin_high"),
        },
        "timing": {
            "estimated_time_to_first_revenue_days": payload.get("estimated_time_to_first_revenue_days"),
            "estimated_time_to_validation_days": payload.get("estimated_time_to_validation_days"),
        },
        "risk": {
            "downside_exposure": payload.get("downside_exposure"),
            "blast_radius": payload.get("blast_radius", "MEDIUM"),
        },
        "exit_path": payload.get("expected_exit_path") or "RESEARCH_MORE_OR_CONTAIN",
    }

    lookahead = apply_lookahead_protection(payload, reveal_historical_outcomes)
    snapshot = build_prediction_snapshot(
        payload,
        decision_model=decision_model,
        final_decision=final_decision,
        expected=expected,
        previous_snapshot_id=payload.get("previous_prediction_snapshot_id"),
        correction_reason=payload.get("correction_reason"),
    )

    decision_id = f"UO-{payload.get('opportunity_id')}-{snapshot['prediction_snapshot_id'][:10]}"
    observability = str(payload.get("outcome_observability_state") or "LOW").upper()
    if observability not in {"HIGH", "MEDIUM", "LOW", "OUTCOME_OBSERVABILITY_LOW"}:
        observability = "OUTCOME_OBSERVABILITY_LOW"

    outcome_contract = build_outcome_contract(
        payload,
        decision_id=decision_id,
        pantheon_snapshot_id=None,
        evidence_snapshot_id=snapshot["prediction_snapshot_id"],
        final_decision=final_decision,
        norns=norns,
        expected=expected,
        outcome_class=expected_outcome_class,
        observability_state=observability,
    )

    recovery_exit_protocol = {
        "primary_plan": payload.get("primary_plan") or "TEST_SMALL_VALIDATE_FAST",
        "failure_scenarios": payload.get("failure_scenarios") or ["NO_CUSTOMER_PULL", "COST_OVERRUN", "TIME_OVERRUN"],
        "early_warning_indicators": payload.get("early_warning_indicators") or ["CAC_SPIKE", "LOW_CONVERSION", "DELAYED_VALIDATION"],
        "maximum_capital_exposure": payload.get("maximum_capital_exposure") or payload.get("required_capital"),
        "maximum_monthly_burn": payload.get("maximum_monthly_burn") or payload.get("estimated_test_cost"),
        "maximum_time_without_validation": payload.get("maximum_time_without_validation") or payload.get("estimated_time_to_validation_days"),
        "minimum_performance_threshold": payload.get("minimum_performance_threshold") or "BASELINE_OR_BETTER",
        "maximum_tolerable_loss": payload.get("maximum_tolerable_loss") or owner_envelope["stop_loss"],
        "recovery_options": payload.get("recovery_options") or ["LEVEL_1_CORRECT", "LEVEL_2_CONTAIN", "LEVEL_3_RESTRUCTURE"],
        "exit_options": payload.get("exit_options") or ["LEVEL_4_PARTIAL_EXIT", "LEVEL_5_FULL_EXIT", "LEVEL_6_SHIELD"],
        "expected_salvage_value": payload.get("expected_salvage_value"),
        "blast_radius": payload.get("blast_radius") or "MEDIUM",
        "required_reserve_to_survive_failure": payload.get("required_reserve_to_survive_failure") or payload.get("survival_capital"),
    }

    capital_risk_exit_analysis = {
        "entry_capital": payload.get("entry_capital") or payload.get("required_capital"),
        "survival_capital": payload.get("survival_capital") or payload.get("required_reserve_to_survive_failure"),
        "liquidity_impact": payload.get("liquidity_impact", "UNKNOWN"),
        "reserve_impact": payload.get("reserve_impact", "UNKNOWN"),
        "blast_radius": recovery_exit_protocol["blast_radius"],
        "exit_quality": exit_quality,
        "hard_decision_rule_pass": bool(
            final_decision != "proceed"
            or (
                recovery_exit_protocol["required_reserve_to_survive_failure"] is not None
                and recovery_exit_protocol["exit_options"]
            )
        ),
    }

    return {
        "opportunity_id": payload.get("opportunity_id"),
        "engine_id": payload.get("engine_id"),
        "legacy": payload.get("legacy"),
        "jurisdiction": payload.get("jurisdiction"),
        "source": payload.get("source"),
        "discovered_at": payload.get("discovered_at") or datetime.now(timezone.utc).isoformat(),
        "title": payload.get("title"),
        "summary": payload.get("summary"),
        "status": payload.get("status"),
        "specialist_analysis": specialist,
        "pantheon": pantheon,
        "loki_objections": {
            "objection_count": len(loki_objections),
            "items": loki_objections,
            "pre_loki_recommendation": pre_loki_recommendation,
        },
        "norns": norns,
        "normalized_dimensions": dimensions,
        "rank_value": rank_value,
        "final_decision": final_decision,
        "approval_envelope": owner_envelope,
        "owner_recommendation": {
            "estimated_test_cost": payload.get("estimated_test_cost"),
            "expected_validation_period_days": payload.get("estimated_time_to_validation_days"),
            "probability": norns["probability_of_worthwhile_validation"],
            "confidence": "high" if dimensions["EVIDENCE_CONFIDENCE"] >= 0.75 else ("medium" if dimensions["EVIDENCE_CONFIDENCE"] >= 0.5 else "low"),
            "primary_downside": "downside_exposure_high" if float(payload.get("downside_exposure") or 0.0) >= 0.6 else "manageable_downside",
            "primary_loki_objection": loki_objections[0]["objection_evidence"] if loki_objections else None,
            "strategic_value": payload.get("strategic_value"),
            "recommended_action": final_decision.upper(),
            "heimdall_decision": final_decision.upper(),
            "message": "Bryan, this is currently the best justified use of Valhalla's resources. Do you approve?",
        },
        "pantheon_flow": [
            "DISCOVERY",
            "UNIVERSAL_OPPORTUNITY",
            "EVIDENCE",
            "SPECIALIST_ANALYSIS",
            "PANTHEON_WAR_TABLE",
            "CAPITAL_RISK_EXIT_ANALYSIS",
            "HEIMDALL_INITIAL_RECOMMENDATION",
            "HEIMDALL_FINAL_RECOMMENDATION",
            "OWNER_APPROVAL",
            "BOUNDED_EXECUTION",
            "ACTUAL_OUTCOME",
            "MIMIR_LEARNING",
        ],
        "replication_policy": {
            "replication_mode": payload.get("replication_mode"),
            "question": "Does replication expand the addressable market, or merely make Valhalla compete with itself?",
        },
        "outcome_learning_hook": {
            "endpoint": "/heimdall/decisions/outcomes",
            "fields": [
                "actual_spend",
                "actual_time_to_revenue",
                "actual_revenue",
                "actual_margin",
                "actual_conversion",
                "actual_customer_count",
                "actual_failure_reason",
            ],
        },
        "simulation_fixture": bool(payload.get("simulation_fixture", False)),
        "routing": route,
        "leakage_protection": lookahead,
        "prediction_snapshot": snapshot,
        "outcome_contract": outcome_contract,
        "baseline_comparison": baseline,
        "decision_regret": regret,
        "capital_risk_exit_analysis": capital_risk_exit_analysis,
        "recovery_exit_protocol": recovery_exit_protocol,
        "decision_model": decision_model,
        "replay_partition": payload.get("replay_partition"),
    }


def best_option_or_abstain(ranked: list[dict[str, Any]]) -> dict[str, Any]:
    if not ranked:
        return {"decision": "REJECT", "reason": "no opportunities provided"}
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    rank = float(top.get("rank_value") or 0.0)
    if top["final_decision"] in {"reject", "hold"} or rank < 55.0:
        return {
            "decision": "HOLD",
            "abstain": True,
            "reason": "NO CURRENT OPPORTUNITY JUSTIFIES DEPLOYMENT",
            "best_candidate": top["opportunity_id"],
        }
    return {
        "decision": top["final_decision"].upper(),
        "abstain": False,
        "best_candidate": top["opportunity_id"],
        "why_top_ranks": top["owner_recommendation"],
        "why_second_lower": None
        if second is None
        else {
            "opportunity_id": second["opportunity_id"],
            "rank_gap": round(rank - float(second.get("rank_value") or 0.0), 4),
            "lower_dimensions": [k for k, v in second["normalized_dimensions"].items() if v < top["normalized_dimensions"].get(k, 0.0)][:5],
        },
    }
