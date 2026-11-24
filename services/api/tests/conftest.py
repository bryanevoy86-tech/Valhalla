"""Isolated database for HTTP tests that exercise canonical private deal routes."""

from contextlib import contextmanager
from threading import Thread
import socket
import time

import httpx
import uvicorn
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def deal_client(monkeypatch, request, tmp_path):
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
    if getattr(request, "param", None) == "disk":
        engine = create_engine(f"sqlite:///{tmp_path / 'valhalla-rehearsal.db'}")
    else:
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


@pytest.fixture
def contract_client(deal_client, monkeypatch, tmp_path):
    from app.core.settings import settings
    from app.models.contracts import (
        Contract, ContractDocument, ContractEnvelope, ContractEvent, ContractParty, ContractTemplate,
    )

    client, engine = deal_client
    for model in (ContractTemplate, Contract, ContractEnvelope, ContractDocument, ContractEvent, ContractParty):
        model.__table__.create(engine)
    key = "isolated-contract-builder-key"
    monkeypatch.setattr(settings, "BUILDER_KEY", key)
    monkeypatch.setenv("CONTRACT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("CONTRACT_STORAGE_LOCAL_DIR", str(tmp_path / "contracts"))
    monkeypatch.setenv("SIGN_PROVIDER", "sandbox")
    client.headers["X-API-Key"] = key
    return client, engine



@pytest.fixture
def legacy_http_client(deal_client, monkeypatch):
    from app.core.engines import guard_runtime
    from app.core.settings import settings
    from app.models.builder import BuilderTask
    from app.models.capital import CapitalIntake
    from app.models.engine_state import EngineStateRow
    from app.models.go_live_state import GoLiveState
    from app.models.grants import GrantRecord, GrantSource
    from app.models.intake import LeadIntake
    from app.models.notify import Outbox
    from app.models.pending_action import PendingAction
    from app.models.research import Playbook, ResearchDoc, ResearchSource
    from app.models.sandbox_event import SandboxEvent
    from app.models.telemetry import IntegrityEvent
    from app.models.telemetry_event import TelemetryEvent

    client, engine = deal_client
    for model in (BuilderTask, CapitalIntake, EngineStateRow, GoLiveState, GrantSource, GrantRecord, LeadIntake,
                  Outbox, PendingAction, ResearchSource, ResearchDoc, Playbook, SandboxEvent, IntegrityEvent, TelemetryEvent):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(GoLiveState(id=1, go_live_enabled=False, kill_switch_engaged=True))
        db.commit()

    def test_guard_session():
        with Session(engine) as db:
            yield db

    monkeypatch.setattr(guard_runtime, "get_db_session", test_guard_session)
    key = "isolated-legacy-http-builder-key"
    monkeypatch.setattr(settings, "BUILDER_KEY", key)
    client.headers["X-API-Key"] = key
    return client, engine



@contextmanager
def _serve_loopback(client, *, app=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app if app is not None else client.app, lifespan="off", log_level="error"))
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.02)
            assert server.started, "Disposable HTTP server failed to start"
            with httpx.Client(
                base_url=f"http://127.0.0.1:{port}", headers=client.headers, trust_env=False, timeout=10,
            ) as network:
                yield network
        finally:
            server.should_exit = True
            thread.join(10)
            assert not thread.is_alive()


@pytest.fixture
def loopback_api(legacy_http_client):
    client, _ = legacy_http_client
    with _serve_loopback(client) as network:
        yield network


@pytest.fixture
def disposable_http_server():
    return _serve_loopback


@pytest.fixture
def loopback_contract_api(contract_client):
    client, _ = contract_client
    with _serve_loopback(client) as network:
        network.base_url = network.base_url.join("/api/")
        yield network


@pytest.fixture
def browser_acceptance(deal_client):
    """Drive the disposable browser client at operating workflow checkpoints."""
    import json
    import os
    from pathlib import Path
    import subprocess

    if os.environ.get("VALHALLA_BROWSER_ACCEPTANCE") != "1":
        return None

    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.staticfiles import StaticFiles

    root = Path(__file__).resolve().parents[3] / "tests" / "browser-acceptance"
    client, _ = deal_client
    app = Starlette(routes=[
        Mount("/__acceptance", app=StaticFiles(directory=root, html=True)),
        Mount("/", app=client.app),
    ])

    def run(**fixture):
        with _serve_loopback(client, app=app) as network:
            result = subprocess.run(
                ["node", str(root / "run.cjs")], text=True, capture_output=True, timeout=90,
                input=json.dumps({"origin": str(network.base_url), **fixture}),
            )
        assert result.returncode == 0, result.stderr
        print("BROWSER_ACCEPTANCE " + json.dumps(json.loads(result.stdout), sort_keys=True))

    return run
