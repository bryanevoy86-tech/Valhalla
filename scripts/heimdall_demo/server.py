"""Private local composition of existing Heimdall endpoints and demo fixtures."""

import hashlib
import json
import os
from pathlib import Path
import socket
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent / "web"
ROUTES = {
    ("/api/weweb/login", "POST"),
    ("/api/weweb/logout", "POST"),
    ("/api/weweb/owner-conversations", "POST"),
    ("/api/weweb/owner-conversations/{conversation_id}/turns", "POST"),
    ("/api/weweb/owner-pantheon/reports", "GET"),
}


def require_disposable_environment():
    database = urlsplit(os.environ["DATABASE_URL"])
    if (Path.cwd() != Path(os.environ["HEIMDALL_DEMO_DIR"]).resolve()
            or not (Path.cwd() / "postgres" / "postmaster.pid").is_file()
            or database.scheme != "postgresql+psycopg2" or database.hostname != "127.0.0.1"
            or database.username != "heimdall_demo" or database.path != "/postgres"
            or not database.password or database.query or database.fragment
            or os.environ.get("VALHALLA_EMERGENCY_STOP") != "true"):
        raise RuntimeError("A fresh loopback database and engaged stop are required")


def seed(engine):
    from sqlalchemy.orm import Session
    from app.loki.analyst import challenge
    from app.loki.evidence import artifact_digest
    from app.loki.models import LokiReview
    from app.loki.review_service import publish_receipt
    from app.models.completion_registry import KnowledgeRegistryItem, LegacyOrchestrationEvent, SourceRegistryItem
    from app.models.go_live_state import GoLiveState
    from app.models.specialist_assignment import SpecialistAssignment
    from app.pantheon.monitor import REPORT_EVENT
    from app.security.auth import pbkdf2_hash_password
    from app.users.models import AccountSettings, UserProfile

    now = datetime.now(timezone.utc)
    timestamp = now.replace(tzinfo=None)
    assignment = uuid4()
    reference = "GOD-" + hashlib.sha256(str(assignment).encode()).hexdigest()
    scope = {"legacy_instance_id": "demo-legacy", "business_id": "demo-incorporation",
             "engine_id": "micro_saas", "jurisdiction": "CA-MB"}
    report = {"assignment_id": str(assignment), "report_event_id": reference, "role": "MIMIR", "scope": scope,
              "observed_at": now.isoformat(), "status": "observed", "trigger": "DEMO_SEED",
              "external_authority": False, "observations": {"synthetic_source": "demo:incorporation-notes"}}
    digest = artifact_digest("pantheon_report", reference, report)
    with Session(engine) as db:
        owner = UserProfile(first_name="Demo", last_name="Owner", email=os.environ["VALHALLA_OWNER_EMAIL"])
        db.add(owner)
        db.flush()
        db.add(AccountSettings(user_id=owner.user_id, account_locked=False,
                               password_hash=pbkdf2_hash_password(os.environ["VALHALLA_OWNER_PASSWORD"])))
        state = db.get(GoLiveState, 1)
        if state is None:
            state = GoLiveState(id=1)
            db.add(state)
        state.go_live_enabled = False
        state.kill_switch_engaged = True
        db.add(SourceRegistryItem(source_id="demo-incorporation-source", canonical_name="Synthetic demo note",
                                 source_type="internal", data_class="synthetic", jurisdiction="CA-MB",
                                 mode_allowlist_json='["practice"]',
                                 terminal_state="ACTIVE_AND_VERIFIED"))
        db.add(KnowledgeRegistryItem(item_id="demo-incorporation-note", source="demo-incorporation-source",
                                    title="Incorporation demo: keep filing and approvals separate",
                                    source_type="internal", jurisdiction="CA-MB", terminal_state="ACTIVE_AND_VERIFIED",
                                    review_status="approved", review_date=now.date(), allowed_systems_json='["Heimdall"]',
                                    citation_ref="demo:incorporation-notes", quality_score=0.95, confidence_score=0.95,
                                    notes="Synthetic teaching record only. No filing, authorization or professional opinion."))
        db.add(SpecialistAssignment(id=assignment, role="MIMIR", scope_key=assignment.hex, scope=scope,
                                    cadence_seconds=600, next_due_at=timestamp, expires_at=timestamp + timedelta(days=1),
                                    state="active", last_report_event_id=reference))
        db.add(LegacyOrchestrationEvent(event_id=reference, legacy_instance_id=scope["legacy_instance_id"],
                                       event_type=REPORT_EVENT, message="Synthetic Heimdall demonstration receipt",
                                       payload_json=json.dumps({**report, "report_sha256": digest})))
        review = LokiReview(input_source="owner-demo-fixture", artifact_type="pantheon_report",
                            heimdall_reference_id=reference, raw_input=report, artifact_sha256=digest, status="queued")
        db.add(review)
        db.commit()
        result = challenge({"artifact_type": "pantheon_report", "reference": reference,
                            "raw_input": report, "artifact_sha256": digest})
        publish_receipt(db, review.id, "demo-local-loki", result)


def main():
    require_disposable_environment()
    from alembic import command
    from alembic.config import Config
    import dotenv
    from fastapi import FastAPI, Request
    from fastapi.responses import PlainTextResponse
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    from starlette.staticfiles import StaticFiles
    import uvicorn

    # Alembic imports its own environment module. Suppress discovery even on old dotenv versions.
    dotenv.load_dotenv = lambda *args, **kwargs: False
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    port = int(os.environ["HEIMDALL_DEMO_PORT"])
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", port))
        from app.core.db import engine

        with engine.connect() as db:
            actual_directory = Path(db.exec_driver_sql("SHOW data_directory").scalar_one()).resolve()
        if actual_directory != Path.cwd() / "postgres":
            raise RuntimeError("PostgreSQL did not identify the disposable cluster; no migrations were applied")
        command.upgrade(config, "head")
        from app.routers import auth_weweb, owner_weweb

        seed(engine)
        app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1"])
        origin = f"http://127.0.0.1:{port}"

        @app.middleware("http")
        async def same_origin(request: Request, call_next):
            if request.url.path.startswith("/api/") and (
                request.headers.get("sec-fetch-site") not in (None, "same-origin", "none")
                or request.headers.get("origin") not in (None, origin)
            ):
                return PlainTextResponse("Local demo requests must come from this page.", status_code=403)
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                "form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
            )
            return response

        included = set()
        for router in (auth_weweb.router, owner_weweb.router):
            for route in router.routes:
                pair = (route.path, next(iter(route.methods))) if len(route.methods) == 1 else None
                if pair in ROUTES:
                    app.router.routes.append(route)
                    included.add(pair)
        if included != ROUTES:
            raise RuntimeError("An expected canonical demo route is missing")
        app.mount("/demo", StaticFiles(directory=ASSETS, html=True))
        listener.listen()
        print(f"\nHEIMDALL DEMONSTRATION — synthetic records only\nOpen {origin}/demo/")
        print(f"Demo email: {os.environ['VALHALLA_OWNER_EMAIL']}")
        print(f"One-run demo password: {os.environ['VALHALLA_OWNER_PASSWORD']}\nPress Ctrl+C here to stop.")
        uvicorn.Server(uvicorn.Config(app, log_level="warning", access_log=False, proxy_headers=False)).run(
            sockets=[listener]
        )


if __name__ == "__main__":
    main()
