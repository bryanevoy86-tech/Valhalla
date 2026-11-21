"""Market evidence, replay integrity, and adapters for scoped specialist workers."""
from datetime import timezone
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent, SourceRegistryItem
from app.models.market_intelligence import MarketEvidence
from app.models.norns_forecast import NornsMarketForecast
from app.schemas.market_intelligence import FXBatch, MarketEvidenceIn, MacroBatch, SecurityBatch
from app.services.market_replay import research_snapshot
from app.services.specialist_triggers import outcome_scope_key


REPLAY_EVENT = "MARKET_PAPER_REPLAY_RECORDED"
MARKET_ROLES = frozenset({"HEIMDALL", "ODIN", "NJORD", "TYR", "LOKI", "NORNS", "MIMIR", "HUGINN", "MUNINN", "FORSETI", "FENRIR"})


def market_schema(db: Session) -> bool:
    schema = inspect(db.connection())
    return all(schema.has_table(model.__tablename__)
               for model in (MarketEvidence, SourceRegistryItem, LegacyOrchestrationEvent))


def authorized_source(db: Session, source_id: str, jurisdiction: str, evidence_class: str, *,
                      lock: bool = False) -> SourceRegistryItem:
    query = select(SourceRegistryItem).filter_by(source_id=source_id)
    source = db.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)
    try:
        modes = json.loads(source.mode_allowlist_json or "[]") if source else []
    except (ValueError, TypeError):
        modes = []
    if (source is None or not source.active or not source.shadow_approved
            or source.terminal_state not in {"PASS", "PARTIAL"}
            or (source.jurisdiction and source.jurisdiction != jurisdiction)
            or not isinstance(modes, list) or "practice" not in modes
            or (source.permission_status or "").lower().strip() in {"denied", "forbidden", "disallowed", "no_permission", "blocked"}
            or (source.license_status or "").lower().strip() in {"forbidden", "restricted", "proprietary_no_derivatives", "no_redistribution"}
            or (evidence_class == "OPERATOR_REPORTED" and source.data_class != "live")):
        raise HTTPException(409, "Market source is outside licensed practice scope")
    return source


def require_source(db: Session, record: MarketEvidenceIn, *, lock: bool = False) -> SourceRegistryItem:
    return authorized_source(db, record.source_id, record.scope.jurisdiction, record.evidence_class, lock=lock)


def evidence_digest(payload: dict, evidence_id: UUID) -> str:
    return artifact_digest("market_evidence", str(evidence_id), payload)


def checked_record(db: Session, row: MarketEvidence, scope: dict) -> MarketEvidenceIn:
    if (not isinstance(scope, dict) or row.revoked_at is not None or row.scope_key != outcome_scope_key(scope)
            or evidence_digest(row.payload, row.id) != row.digest):
        raise HTTPException(409, "Market evidence is revoked, outside scope, or fails integrity")
    try:
        record = MarketEvidenceIn.model_validate(row.payload)
        if record.scope.model_dump() != scope or row.kind != record.data.kind or record.evidence_id != row.id:
            raise ValueError("metadata")
    except ValueError:
        raise HTTPException(409, "Market evidence metadata failed validation") from None
    require_source(db, record)
    return record


def source_detail(row: MarketEvidence, record: MarketEvidenceIn) -> dict:
    at = row.received_at
    received = at.astimezone(timezone.utc) if at.tzinfo else at.replace(tzinfo=timezone.utc)
    return {"id": str(row.id), "sha256": row.digest, "source_id": record.source_id,
            "source_ref": record.source_ref, "received_at": received.isoformat(),
            "evidence_class": record.evidence_class}


def replay_event_id(run_id: UUID) -> str:
    return f"MARKET-PAPER-{run_id}"


def check_replay_event(event: LegacyOrchestrationEvent) -> dict:
    try:
        receipt = json.loads(event.payload_json)
        digest = receipt.pop("receipt_sha256")
        if (receipt["scope"]["legacy_instance_id"] != event.legacy_instance_id
                or replay_event_id(UUID(receipt["run_id"])) != event.event_id
                or digest != artifact_digest("market_paper_replay", event.event_id, receipt)):
            raise ValueError
    except (KeyError, AttributeError, TypeError, ValueError):
        raise HTTPException(409, "Market replay integrity check failed") from None
    return {**receipt, "receipt_sha256": digest}


def market_observations(db: Session, role: str, scope: dict, at) -> dict:
    if role not in MARKET_ROLES or not market_schema(db):
        return {}
    rows = db.scalars(select(MarketEvidence).where(
        MarketEvidence.scope_key == outcome_scope_key(scope), MarketEvidence.revoked_at.is_(None),
    ).order_by(MarketEvidence.received_at.desc(), MarketEvidence.id).limit(12)).all()
    if not rows:
        return {}
    now = at.replace(tzinfo=timezone.utc)
    summaries, invalid = [], []
    for row in rows:
        try:
            record = checked_record(db, row, scope)
        except HTTPException:
            invalid.append(str(row.id))
            continue
        data = record.data
        item = {"source": source_detail(row, record), "kind": data.kind}
        if isinstance(data, SecurityBatch):
            item["research"] = research_snapshot(data, now)
        elif isinstance(data, FXBatch):
            item["fresh_quote_count"] = sum(q.at <= now < q.expires_at and (now - q.at).total_seconds() <= 60 for q in data.quotes)
            item["quote_count"] = len(data.quotes)
            item["settlement_bound_seconds"] = max(q.settlement_seconds for q in data.quotes)
        elif isinstance(data, MacroBatch):
            item["research"] = data.model_dump(mode="json")
        summaries.append(item)

    alerts = ["SOURCE_RECHECK_REQUIRED"] if invalid else []
    if any(item["kind"] == "FX" and not item["fresh_quote_count"] for item in summaries):
        alerts.append("FX_QUOTES_EXPIRED_OR_TOO_OLD")
    if any(item["source"]["evidence_class"] == "SIMULATION" for item in summaries):
        alerts.append("SIMULATION_INPUT_PRESENT")
    if role in {"TYR", "LOKI", "FORSETI", "FENRIR"}:
        alerts.append("CHECK_RIGHTS_ASSUMPTIONS_AND_AUTHORITY")
    learning = []
    if role in {"MIMIR", "MUNINN", "HEIMDALL", "NORNS", "LOKI"}:
        events = db.scalars(select(LegacyOrchestrationEvent).filter_by(
            legacy_instance_id=scope["legacy_instance_id"], event_type=REPLAY_EVENT,
        ).order_by(LegacyOrchestrationEvent.id.desc()).limit(20))
        for event in events:
            try:
                receipt = check_replay_event(event)
            except HTTPException:
                continue
            if receipt["scope"] == scope:
                learning.append({key: receipt[key] for key in ("run_id", "receipt_sha256", "kind", "result")})
            if len(learning) == 3:
                break
    facts = {"sources": summaries, "invalid_evidence_ids": invalid, "alerts": alerts,
             "replay_receipts": learning, "external_execution_authorized": False, "verified_real_world_outcomes": False}
    if role == "NORNS" and inspect(db.connection()).has_table(NornsMarketForecast.__tablename__):
        forecast = NornsMarketForecast
        pending = db.execute(select(forecast.evidence_class, func.count()).where(
            forecast.scope_key == outcome_scope_key(scope), forecast.observed_outcome.is_(None),
        ).group_by(forecast.evidence_class)).all()
        facts["pending_market_forecasts_by_input_class"] = dict(pending)
    return {"market_intelligence": facts}
