"""Independent local proposal checks. No Prime evaluator and no model transport."""
from math import isfinite

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


def challenge(item: dict) -> IndependentReviewIn:
    kind, proposal = item["artifact_type"], item["raw_input"]
    digest = artifact_digest(kind, item["reference"], proposal)
    if digest != item["artifact_sha256"]:
        raise ValueError("Queued artifact digest mismatch")
    findings = []
    if kind == "universal_opportunity":
        specialist = proposal.get("specialist_inputs")
        if isinstance(specialist, dict) and "consumer_research" in specialist:
            findings.extend(_consumer_findings(specialist["consumer_research"], "specialist_inputs/consumer_research"))
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
                critical=market.get("external_execution_authorized") is not False,
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
            if isinstance(proof, dict) and (
                proof.get("verified_real_world_outcome") is not False
                or proof.get("basis") != "ECONOMIC_PERFORMANCE_FIXTURE"
                or ("period_net_minor" in economic and proof.get("period_net_minor") != economic["period_net_minor"])
                or ("last_performance_id" in economic and proof.get("record_id") != economic["last_performance_id"])
            ):
                findings.append(_finding(
                    "economic_fixture_contradiction", "observations/economic_reassessment",
                    "The claimed performance disagrees with the cited fixture identity, basis, or net result.", critical=True,
                ))
            treasury = sources.get("treasury_statement_evidence")
            if isinstance(treasury, dict):
                accounts = treasury.get("accounts")
                if isinstance(accounts, list) and any(
                    isinstance(row, dict) and row.get("status") == "EVIDENCE_CONFLICT" for row in accounts
                ):
                    findings.append(_finding(
                        "treasury_statement_conflict", "observations/treasury_statement_evidence",
                        "Reconcile the current scoped statement head before relying on this fixture.", critical=True,
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
