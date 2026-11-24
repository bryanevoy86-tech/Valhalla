"""A Loki placeholder must never masquerade as a verified audit.

These are actual router-function tests, using inert database doubles.
No AI provider, credentials, funds, trust documents or production DB involved.
"""
from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.loki.models import LokiReviewStatus
from app.routers.loki import create_loki_review, get_loki_verdict
from app.services.universal_opportunity_evaluator import universal_loki_objections


class FakeDB:
    def __init__(self, review):
        self.review = review

    def execute(self, _statement):
        return self

    def scalar_one_or_none(self):
        return self.review


def test_loki_review_cannot_report_completed_from_unconnected_stub():
    with pytest.raises(HTTPException) as err:
        create_loki_review(payload=None, db=None)
    assert err.value.status_code == 503
    assert err.value.detail == "LOKI_INDEPENDENT_AUDIT_ENGINE_NOT_CONNECTED"


def test_loki_verdict_requires_existing_review():
    with pytest.raises(HTTPException) as err:
        get_loki_verdict(review_id=uuid4(), db=FakeDB(None))
    assert err.value.status_code == 404


def test_queued_loki_review_cannot_be_presented_as_final_audit():
    db = FakeDB(SimpleNamespace(
        status=LokiReviewStatus.QUEUED,
        result_severity=None,
        raw_output=None,
        summary=None,
    ))
    with pytest.raises(HTTPException) as err:
        get_loki_verdict(review_id=uuid4(), db=db)
    assert err.value.status_code == 409
    assert err.value.detail == "LOKI_AUDIT_NOT_COMPLETE"


def test_legacy_stub_completed_does_not_count_as_real_audit():
    db = FakeDB(SimpleNamespace(
        status=LokiReviewStatus.COMPLETED,
        result_severity="warn",
        raw_output={"independent_audit_verified": True},
        summary="Loki stub analysis ran. Replace with real AI logic.",
    ))
    with pytest.raises(HTTPException) as err:
        get_loki_verdict(review_id=uuid4(), db=db)
    assert err.value.status_code == 503
    assert err.value.detail == "LOKI_VERIFIED_VERDICT_PROVIDER_NOT_CONNECTED"


def test_no_unsupported_loki_approval_even_with_fake_ok_flags():
    db = FakeDB(SimpleNamespace(
        status=LokiReviewStatus.COMPLETED,
        result_severity="ok",
        raw_output={"independent_audit_verified": True},
        summary="AI claimed all verified without provider evidence",
    ))
    with pytest.raises(HTTPException) as err:
        get_loki_verdict(review_id=uuid4(), db=db)
    assert err.value.status_code == 503


def test_universal_loki_objections_mark_critical_unresolved_downside():
    claims = {
        "opportunity_id": "ci-loki-1",
        "engine_id": "micro_saas",
        "downside_exposure": 0.91,
    }
    findings = universal_loki_objections(claims, {"fit_score": 0.95})
    assert any(
        f["severity"] == "critical"
        and f["resolved"] is False
        and f["impact_on_recommendation"] == "PROCEED->REJECT"
        for f in findings
    )


def test_loki_generic_challenge_is_not_mislabelled_as_independent_audit():
    claims = {
        "opportunity_id": "ci-loki-2",
        "engine_id": "micro_saas",
        "downside_exposure": 0.1,
    }
    findings = universal_loki_objections(claims, {"fit_score": 0.85})
    assert any(
        f["severity"] == "warn"
        and f["materiality"] == "material"
        and not f["resolved"]
        for f in findings
    )
