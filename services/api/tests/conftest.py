"""Isolated database for HTTP tests that exercise canonical private deal routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def deal_client(monkeypatch):
    from app.core.db import get_db
    from app.leads.models import Lead
    from app.main import app
    from app.models.audit_log import AuditLog
    from app.models.deal import Deal, DealBriefLink
    from app.models.freeze_events import FreezeEvent
    from app.models.buyer_liquidity import BuyerFeedbackEvent, BuyerLiquidityNode
    from app.models.followup_task import FollowupTask
    from app.models.kpi_event import KPIEvent
    from app.models.offer_evidence import OfferEvidence
    from app.models.offer_policy import OfferPolicy
    from app.models.match import Buyer, DealBrief
    from app.offers.models import Offer

    key = "historical-deal-test-prime-key"
    monkeypatch.setenv("VALHALLA_PRIME_CONTROL_KEY", key)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for model in (Lead, Deal, DealBrief, DealBriefLink, Buyer, FreezeEvent, Offer, AuditLog, FollowupTask,
                  KPIEvent, BuyerLiquidityNode, BuyerFeedbackEvent, OfferPolicy, OfferEvidence):
        model.__table__.create(engine)

    def isolated_db():
        with Session(engine) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_db)
    try:
        yield TestClient(app, headers={"X-Prime-Control-Key": key}), engine
    finally:
        engine.dispose()
