"""PACK-CORE-PRELAUNCH-01: Daily Ops - Service"""

from datetime import date

from sqlalchemy.orm import Session

from . import models, schemas


def run_morning_briefing(db: Session) -> models.DailySnapshot:
    today = date.today()

    # TODO: pull from real engines (finance, risk, tasks, alerts)
    financial_summary = {"status": "UNKNOWN"}
    risk_summary = {"status": "UNKNOWN"}
    tasks_today = []
    alerts_summary = {}

    snapshot = models.DailySnapshot(
        snapshot_date=today,
        financial_summary=financial_summary,
        risk_summary=risk_summary,
        tasks_today=tasks_today,
        alerts_summary=alerts_summary,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def run_night_shutdown(db: Session) -> models.NightlySnapshot:
    today = date.today()

    # TODO: pull from real task tracker, projections, risk engine
    completed_tasks = []
    missed_tasks = []
    projection_changes = {}
    risk_changes = {}

    snapshot = models.NightlySnapshot(
        snapshot_date=today,
        completed_tasks=completed_tasks,
        missed_tasks=missed_tasks,
        projection_changes=projection_changes,
        risk_changes=risk_changes,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_today_snapshots(db: Session) -> dict:
    today = date.today()
    daily = (
        db.query(models.DailySnapshot)
        .filter(models.DailySnapshot.snapshot_date == today)
        .order_by(models.DailySnapshot.created_at.desc())
        .first()
    )
    nightly = (
        db.query(models.NightlySnapshot)
        .filter(models.NightlySnapshot.snapshot_date == today)
        .order_by(models.NightlySnapshot.created_at.desc())
        .first()
    )
    return {"daily": daily, "nightly": nightly}
