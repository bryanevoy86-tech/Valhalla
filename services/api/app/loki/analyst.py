"""Independent local proposal checks. No Prime evaluator and no model transport."""
from math import isfinite
import re

from app.loki.evidence import artifact_digest
from app.loki.schemas import IndependentFinding, IndependentReviewIn
from app.services.checkout_operating_signals import checkout_operating_blockers


def _finding(category, field, message, *, critical=False):
    return IndependentFinding(category=category, evidence_ref=f"artifact:/{field}", message=message,
                              severity="critical" if critical else "warn", material=True)


def _number(proposal, field):
    value = proposal.get(field)
    return value if type(value) in {float, int} and isfinite(value) else None


def _consumer_findings(research, field):
    if (not isinstance(research, dict) or research.get("confidence") != "AGGREGATE_DESCRIPTIVE_ONLY"
            or any(research.get(key) is not False for key in (
                "causality_verified", "settled_conversion_verified", "independent_study_source_verified",
                "external_action_authorized",
            ))):
        return [_finding("consumer_claim_overreach", field,
                         "Aggregate research cannot establish causality, settlement, or action authority.", critical=True)]
    return [_finding("consumer_evidence_limits", field,
                     "Check cohort selection, transparent terms, pricing uncertainty, and transfer to this market before reliance.")]


def _commercial_findings(case):
    field = "specialist_inputs/commercial_validation"
    costs = ("labour_minor", "tools_and_fees_minor", "reserve_minor", "acquisition_minor")
    keys = ("price_minor", *costs, "stress_labour_minor", "stress_acquisition_minor")
    if (not isinstance(case, dict) or case.get("basis") != "CAD_RESEARCH_HYPOTHESIS"
            or case.get("currency") != "CAD" or case.get("verified_customer_outcomes") is not False
            or case.get("external_action_authorized") is not False):
        return [_finding("commercial_authority_conflict", field,
                         "Market hypotheses cannot assert verified customer outcomes or action authority.", critical=True)]
    if (any(type(case.get(key)) is not int or case[key] < 0 for key in keys)
            or case["price_minor"] == 0 or case["stress_labour_minor"] < case["labour_minor"]
            or case["stress_acquisition_minor"] < case["acquisition_minor"]):
        return [_finding("commercial_cost_basis", field,
                         "Provide a positive CAD price, complete base costs and a downside case with no lower labour or acquisition cost.",
                         critical=True)]
    base = case["price_minor"] - sum(case[key] for key in costs)
    downside = base + case["labour_minor"] + case["acquisition_minor"] - (
        case["stress_labour_minor"] + case["stress_acquisition_minor"]
    )
    findings = [_finding("customer_demand_unproven", field,
                         "Check willingness to pay, actual acquisition cost and repeat demand in the target cohort before commercial reliance.")]
    if base <= 0:
        findings.append(_finding("commercial_base_loss", field, "Base contribution is nonpositive.", critical=True))
    elif downside <= 0:
        findings.append(_finding("commercial_stress_loss", field,
                                 "Higher labour and acquisition costs eliminate contribution. Cap exposure and set a stop condition."))
    return findings


def _opportunity_selection_findings(analysis):
    field = "analysis/opportunity_selection"
    selection, ranked = analysis["opportunity_selection"], analysis.get("alternatives")
    if (not isinstance(selection, dict) or not isinstance(ranked, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("opportunity_key"), str)
        or type(item.get("adjusted_forward_value_minor")) is not int
        or type(item.get("eligible")) is not bool or not isinstance(item.get("blockers"), list)
        for item in ranked
    )):
        return [_finding("opportunity_selection_invalid", field, "The ranking inputs are incomplete.", critical=True)]
    ordered = sorted(ranked, key=lambda row: (
        not row["eligible"], -row["adjusted_forward_value_minor"], row["opportunity_key"],
    ))
    expected = next((item["opportunity_key"] for item in ordered if item["eligible"]
                     and isinstance(item.get("foundry_source"), dict) and isinstance(item.get("demand_evidence"), dict)
                     and type(item["demand_evidence"].get("demand_count")) is int
                     and item["demand_evidence"]["demand_count"] > 0), None)
    selected = selection.get("first_research_candidate_key")
    valid = selection.get("commercial_selection_key") is None and selection.get("verified_monthly_owner_income_minor") is None
    holds = selection.get("scope_holds")
    blockers = analysis.get("blockers")
    valid = valid and isinstance(blockers, list) and all(isinstance(blocker, str) for blocker in blockers)
    valid = valid and (holds == blockers or holds == sorted(set([*blockers, "EMERGENCY_STOP"])))
    if expected is not None and not holds:
        valid = valid and selection.get("decision") == "RESEARCH_ONLY" and selected == expected
    else:
        valid = valid and selection.get("decision") == "ABSTAIN" and selected is None
    if (ranked != ordered or not valid or len({row["opportunity_key"] for row in ranked}) != len(ranked)
            or any(row["eligible"] != (not row["blockers"]) for row in ranked)):
        return [_finding("opportunity_ranking_conflict", field,
                         "The proposed selection disagrees with the scoped ranking or asserts unverified commercial authority.",
                         critical=True)]
    for row in ranked:
        basis = row.get("ranking_basis")
        net = basis.get("risk_adjusted_operating_net_minor") if isinstance(basis, dict) else None
        charge = basis.get("capital_and_downside_charge_minor") if isinstance(basis, dict) else None
        if (type(net) is not int or type(charge) is not int or charge < 0
                or net - charge != row["adjusted_forward_value_minor"]
                or basis.get("verified_monthly_owner_income_minor") is not None):
            return [_finding("opportunity_value_conflict", "analysis/alternatives",
                             "The forward value does not reconcile to its disclosed components.", critical=True)]
    return [_finding("opportunity_ranking_evidence", field,
                     "Verify the buyer sample, sustainable net, owner hours, legal scope and relative ranking before reliance.")]


def challenge(item: dict) -> IndependentReviewIn:
    kind, proposal = item["artifact_type"], item["raw_input"]
    digest = artifact_digest(kind, item["reference"], proposal)
    if digest != item["artifact_sha256"]:
        raise ValueError("Queued artifact digest mismatch")
    findings = []
    if kind == "universal_opportunity":
        specialist = proposal.get("specialist_inputs")
        if isinstance(specialist, dict) and "public_market_context" in specialist:
            context = specialist["public_market_context"]
            if (not isinstance(context, dict) or context.get("basis") != "PUBLIC_SECONDARY_CONTEXT"
                    or any(context.get(flag) is not False for flag in (
                        "first_party_demand_verified", "paid_outcomes_verified", "external_action_authorized",
                    ))):
                findings.append(_finding("public_context_overreach", "specialist_inputs/public_market_context",
                                         "Public context cannot establish buyer validation or action authority.", critical=True))
            else:
                findings.append(_finding("public_context_requires_validation", "specialist_inputs/public_market_context",
                                         "Independently verify comparability, source rights and buyer-level evidence. Public context is advisory."))
        if isinstance(specialist, dict) and "consumer_research" in specialist:
            findings.extend(_consumer_findings(specialist["consumer_research"], "specialist_inputs/consumer_research"))
        if isinstance(specialist, dict) and "commercial_validation" in specialist:
            findings.extend(_commercial_findings(specialist["commercial_validation"]))
        lower = _number(proposal, "expected_margin_low")
        upper = _number(proposal, "expected_margin_high")
        cost = _number(proposal, "estimated_test_cost")
        exposure = _number(proposal, "maximum_capital_exposure")
        safe = _number(proposal, "available_safe_capital")
        if lower is not None and upper is not None and lower > upper:
            findings.append(_finding("inconsistent_forecast", "expected_margin_low", "The lower margin bound exceeds the upper bound."))
        if cost is not None and (cost < 0 or (exposure is not None and cost > exposure)):
            findings.append(_finding("capital_limit", "estimated_test_cost", "Test cost is outside the declared exposure limit.", critical=True))
        if exposure is not None and (exposure < 0 or (safe is not None and exposure > safe)):
            findings.append(_finding("capital_limit", "maximum_capital_exposure", "Exposure exceeds declared safe capital.", critical=True))
        if not proposal.get("jurisdiction") or not proposal.get("point_of_no_return"):
            findings.append(_finding("reconsideration_scope", "point_of_no_return", "Jurisdiction or point of no return is missing."))
        if proposal.get("simulation_fixture") is True or proposal.get("historical_outcome") is not None:
            findings.append(_finding("simulation", "simulation_fixture", "Replay or simulated input cannot support live execution.", critical=True))
        # Static checks compare claims present in the exact version. They do not
        # independently establish source truth or professional eligibility.
        findings.append(_finding(
            "source_verification_required", "specialist_inputs",
            "Local coherence checks do not verify underlying source evidence. Reconsider the provenance and any material assumptions.",
        ))
    elif kind == "economic_advice":
        plan, evidence = proposal["plan"], proposal["analysis"]
        if "opportunity_selection" in evidence:
            findings.extend(_opportunity_selection_findings(evidence))
        checks = set(evidence["blockers"])
        if plan["past_spend_minor"]:
            findings.append(_finding("sunk_cost", "plan/past_spend_minor",
                                     "Past expenditure is not evidence for renewing funding. Reassess future cash and recovery."))
        if checks and plan["action"] not in {"SUSPEND", "RESTRUCTURE", "EXIT"}:
            findings.append(_finding("loss_limit_bypass", "analysis/blockers",
                                     "The proposed path conflicts with current capital or obligations constraints.", critical=True))
        if plan["cross_business_support"] or proposal["execution_authorized"] is not False:
            findings.append(_finding("authority", "plan/cross_business_support",
                                     "Cross-business support is beyond this private planning mandate.", critical=True))
        findings.append(_finding("reconcile_forward_case", "analysis",
                                 "Review forward alternatives, continuity of cash and obligations, and asset recovery assumptions."))
    elif kind == "acquisition_comparison":
        if (proposal.get("basis") != "SETTLED_CAMPAIGN_FIXTURE_COMPARISON"
                or any(proposal.get(key) is not False for key in (
                    "verified_commercial_revenue", "external_action_authorized", "causality_verified",
                ))):
            findings.append(_finding("acquisition_comparison_overreach", "basis",
                                     "Settled fixtures grant no commercial, causal or external authority.", critical=True))
        minimum = _number(proposal, "minimum_visits")
        arms = proposal.get("arms")
        if isinstance(arms, list) and len(arms) <= 5:
            for index, arm in enumerate(arms):
                if not isinstance(arm, dict) or arm.get("decision") != "SCALE_REVIEW":
                    continue
                visits, contribution = _number(arm, "visits"), _number(arm, "contribution_minor")
                if (minimum is None or minimum < 20 or visits is None or visits < minimum or contribution is None
                        or contribution <= 0 or _number(arm, "unresolved_orders") != 0
                        or arm.get("acquisition_cost_covered") is not True
                        or proposal.get("customer_identity_coverage_complete") is not True):
                    findings.append(_finding("acquisition_scale_evidence_incomplete", f"arms/{index}",
                                             "Scale review requires sufficient settled visits, covered costs and positive contribution.",
                                             critical=True))
        findings.append(_finding("acquisition_comparison_review", "arms",
                                 "Recheck cohort separation, attribution and complete costs before relying on expansion advice."))
    elif kind == "personal_allocation":
        eligible = _number(proposal, "eligible_distributable_profit_minor")
        personal = _number(proposal, "recommended_personal_minor")
        cash = _number(proposal, "fixture_cash_headroom_minor")
        profit = _number(proposal, "fixture_period_profit_after_tax_reserve_minor")
        breakdown = proposal.get("personal_breakdown")
        if not isinstance(breakdown, dict):
            breakdown = {}
        parts = [_number(breakdown, key) for key in ("essentials_minor", "reserve_minor", "remaining_personal_minor")]
        if (not all(type(value) is int and value >= 0 for value in [eligible, personal, cash, profit, *parts])
                or not personal <= eligible <= min(cash, profit) or sum(parts) != personal
                or (proposal.get("blockers") and eligible)):
            findings.append(_finding("allocation_capital_conflict", "eligible_distributable_profit_minor",
                                     "The allocation does not reconcile to protected cash, profit and household limits.",
                                     critical=True))
        if (proposal.get("basis") != "RECONCILIATION_FIXTURE" or proposal.get("funds_movement_authorized") is not False
                or proposal.get("standing_mandate_approved") is not False
                or proposal.get("actual_accessible_funds_minor") is not None):
            findings.append(_finding("allocation_authority_conflict", "funds_movement_authorized",
                                     "Fixture evidence cannot authorize a personal payment.", critical=True))
        findings.append(_finding("allocation_review_required", "business_protections_minor",
                                 "Independently reconcile cash, liabilities, tax reserve and the applicable payment classification."))
    elif kind == "pantheon_report":
        sources = proposal.get("observations")
        if not isinstance(sources, dict) or proposal.get("status") != "observed":
            findings.append(_finding("missing_evidence", "observations", "The specialist did not produce observable evidence."))
        if proposal.get("external_authority") is not False:
            findings.append(_finding("scope_excess", "external_authority", "An advisory report claims execution authority.", critical=True))
        market = sources.get("market_intelligence") if isinstance(sources, dict) else None
        if market is not None:
            findings.append(_finding(
                "market_simulation", "observations/market_intelligence",
                "Check quote freshness, settlement sequencing, execution costs and source rights independently. "
                "A paper receipt does not establish executable liquidity or operator authority.",
                critical=(not isinstance(market, dict) or market.get("external_execution_authorized") is not False
                          or market.get("verified_real_world_outcomes") is not False
                          or bool(market.get("invalid_evidence_ids"))),
            ))
        if isinstance(sources, dict):
            if sources.get("consumer_research_holds"):
                findings.append(_finding("consumer_evidence_hold", "observations/foundry_signals",
                                         "Refresh stale or changed consumer evidence before reliance.", critical=True))
            signals = sources.get("foundry_signals")
            if isinstance(signals, list):
                for index, signal in enumerate(signals):
                    if isinstance(signal, dict) and "consumer_research" in signal:
                        findings.extend(_consumer_findings(signal["consumer_research"],
                                                           f"observations/foundry_signals/{index}/consumer_research"))
            acquisition = sources.get("acquisition_rehearsal")
            if isinstance(acquisition, list) and any(
                isinstance(item, dict) and (item.get("basis") == "EVIDENCE_HOLD"
                                            or item.get("verified_commercial_revenue") is not False
                                            or item.get("external_action_authorized") is not False)
                for item in acquisition
            ):
                findings.append(_finding(
                    "acquisition_evidence_conflict", "observations/acquisition_rehearsal",
                    "Review attribution and settlement integrity before relying on this campaign.", critical=True,
                ))
            checkout = sources.get("checkout_learning")
            checkout_blockers = checkout_operating_blockers(checkout) if isinstance(checkout, list) else set()
            if "CHECKOUT_EVIDENCE_CONFLICT" in checkout_blockers:
                findings.append(_finding(
                    "checkout_evidence_conflict", "observations/checkout_learning",
                    "Reconcile the scoped checkout receipts before relying on the report.", critical=True,
                ))
            if checkout_blockers & {"CHECKOUT_FULFILLMENT_HELD", "CHECKOUT_REFUND_REVIEW_REQUIRED"}:
                findings.append(_finding(
                    "checkout_review_pending", "observations/checkout_learning",
                    "Resolve the held fulfillment or refund support before material reliance.", critical=True,
                ))
            paid_deliveries = sources.get("paid_delivery_outcomes")
            if isinstance(paid_deliveries, list) and any(
                not isinstance(item, dict) or item.get("status") in {
                    "DELIVERY_REVIEW_REQUIRED", "DELIVERY_EVIDENCE_CONFLICT",
                } or item.get("external_authority") is not False or item.get("available_cash_minor") is not None
                or (item.get("basis") == "SYNTHETIC_LIABILITY_RELEASE_PREVIEW"
                    and item.get("recognized_revenue_minor") is not None)
                for item in paid_deliveries
            ):
                findings.append(_finding(
                    "paid_delivery_evidence_review", "observations/paid_delivery_outcomes",
                    "Resolve the exact delivery or correction receipts before relying on this outcome.", critical=True,
                ))
            recurring = sources.get("recurring_paid_periods")
            if recurring is not None and (
                not isinstance(recurring, dict) or recurring.get("status") != "OBSERVED"
                or recurring.get("basis") not in {"STRIPE_TEST_PAID_PERIODS", "STRIPE_LIVE_PAID_PERIODS"}
                or recurring.get("available_cash_minor") is not None
                or recurring.get("recognized_revenue_minor") is not None
                or recurring.get("external_authority") is not False
            ):
                findings.append(_finding(
                    "recurring_payment_evidence_review", "observations/recurring_paid_periods",
                    "Reconcile recurring payment evidence and keep paid periods separate from booked income or cash.",
                    critical=True,
                ))
            factory = sources.get("factory_evidence_reconciliation")
            if isinstance(factory, dict) and factory.get("contradictions"):
                findings.append(_finding(
                    "factory_evidence_conflict", "observations/factory_evidence_reconciliation",
                    "Reconcile the approval, artifact and learning receipts cited in this report.", critical=True,
                ))
            economic = sources.get("economic_reassessment")
            if isinstance(economic, dict) and "CHECKOUT_PERFORMANCE_EVIDENCE_CONFLICT" in economic.get("blockers", []):
                findings.append(_finding(
                    "checkout_performance_conflict", "observations/economic_reassessment",
                    "Revalidate the economic result against the exact closed checkout fixture.", critical=True,
                ))
            if isinstance(economic, dict) and {"STRIPE_BANK_EVIDENCE_CONFLICT", "STRIPE_BANK_CORRECTION_REQUIRED"}.intersection(
                economic.get("blockers", [])
            ):
                findings.append(_finding(
                    "bank_batch_correction_required", "observations/economic_reassessment",
                    "Reconcile the scoped bank batch, signed reversals and existing journal before relying on cash.",
                    critical=True,
                ))
            proof = economic.get("verified_performance_claim") if isinstance(economic, dict) else None
            if proof is not None and (
                not isinstance(proof, dict) or proof.get("verified_real_world_outcome") is not False
                or proof.get("basis") != "ECONOMIC_PERFORMANCE_FIXTURE"
                or proof.get("evidence_scope") != "ECONOMIC_PERFORMANCE_FIXTURE_ONLY"
                or not isinstance(proof.get("record_id"), str) or not proof["record_id"]
                or not isinstance(proof.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", proof["sha256"])
                or type(proof.get("period_net_minor")) is not int
                or ("period_net_minor" in economic and proof.get("period_net_minor") != economic["period_net_minor"])
                or ("last_performance_id" in economic and proof.get("record_id") != economic["last_performance_id"])
            ):
                findings.append(_finding(
                    "economic_fixture_contradiction", "observations/economic_reassessment",
                    "The claimed performance disagrees with the cited fixture identity, basis, or net result.", critical=True,
                ))
            treasury = sources.get("treasury_statement_evidence")
            if treasury is not None:
                accounts = treasury.get("accounts", []) if isinstance(treasury, dict) else None
                if (not isinstance(accounts, list) or treasury.get("actual_accessible_funds_minor") is not None
                        or any(not isinstance(row, dict) or row.get("status") == "EVIDENCE_CONFLICT"
                               for row in accounts)):
                    findings.append(_finding(
                        "treasury_statement_conflict", "observations/treasury_statement_evidence",
                        "Reconcile the scoped statement head. A sampled statement cannot establish accessible cash.",
                        critical=True,
                    ))
        findings.append(_finding(
            "evidence_reassessment", "observations",
            "Reassess the specialist's scoped observations before relying on them for a material action.",
        ))
    else:
        raise ValueError("Unsupported artifact type")
    return IndependentReviewIn(
        artifact_sha256=digest, analysis_ref=f"independent-local-v1:{digest}",
        summary="Completed independent local consistency and scope checks. Material findings require reconsideration.",
        findings=findings,
    )
