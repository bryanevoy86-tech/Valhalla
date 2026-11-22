"""Independent local proposal checks. No Prime evaluator and no model transport."""
from math import isfinite

from app.loki.evidence import artifact_digest
from app.loki.schemas import IndependentFinding, IndependentReviewIn


def _finding(category, field, message, *, critical=False):
    return IndependentFinding(category=category, evidence_ref=f"artifact:/{field}", message=message,
                              severity="critical" if critical else "warn", material=True)


def _number(proposal, field):
    value = proposal.get(field)
    return value if type(value) in {float, int} and isfinite(value) else None


def challenge(item: dict) -> IndependentReviewIn:
    kind, proposal = item["artifact_type"], item["raw_input"]
    digest = artifact_digest(kind, item["reference"], proposal)
    if digest != item["artifact_sha256"]:
        raise ValueError("Queued artifact digest mismatch")
    findings = []
    if kind == "universal_opportunity":
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
            checkout = sources.get("checkout_learning")
            if isinstance(checkout, list) and any(
                isinstance(row, dict) and (row.get("status") == "EVIDENCE_CONFLICT"
                                           or row.get("verified_commercial_revenue") is not False)
                for row in checkout
            ):
                findings.append(_finding(
                    "checkout_evidence_conflict", "observations/checkout_learning",
                    "Reconcile the scoped checkout receipts before relying on the report.", critical=True,
                ))
            factory = sources.get("factory_evidence_reconciliation")
            if isinstance(factory, dict) and factory.get("contradictions"):
                findings.append(_finding(
                    "factory_evidence_conflict", "observations/factory_evidence_reconciliation",
                    "Reconcile the approval, artifact and learning receipts cited in this report.", critical=True,
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
